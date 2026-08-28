"""Step 9.1: report generation + dispatch pipeline.

One function, three entry points (design-docu §7.7.3): APScheduler cron
(Step 9.2), the O7 manual button via POST /api/ops/reports/generate
(Step 9.3), and the AI assistant — all call
`generate_and_dispatch_report(report_type, trigger_source)`.

Pipeline: aggregate stats -> strong-tier LLM markdown (§7.4 prompts) ->
insert `reports` -> insert `notifications` -> fire-and-forget email task
-> email task updates email_status to sent/failed.

Failure policy (§7.7.7): LLM failure raises (nothing is written); email
failure only flips email_status="failed" + email_error — the report and
notification rows always survive.

Period semantics (recorded in progress.md):
  daily  — TODAY so far (Beijing) with yesterday-same-period ring compare,
           matching the O1 overview's口径 so a manually triggered demo
           report always has live data.
  weekly — the last COMPLETE Beijing week (Mon..Sun) as "this week",
           compared against the week before it; the Monday 09:00 cron
           therefore reports the week that just ended.

Module access pattern: llm / email are referenced as module attributes
(`llm.gen_text`, `email.send_email`) so check scripts can monkeypatch
them without touching real SMTP.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import date, datetime, timedelta, timezone

import markdown as md

from sqlalchemy import text

from app.db import async_session_maker
from app.models import Notification, Report
from app.services import email, llm

logger = logging.getLogger("nail_demo.report")

_BJT = timezone(timedelta(hours=8))

_NOTIFICATION_SUMMARY_LEN = 120
# deepseek-v4-pro is a reasoning model: max_tokens covers reasoning AND
# content. Verified failure modes: 2000 starves content to empty when the
# model does the ring-compare arithmetic itself (~3500 reasoning tokens);
# 4000 with long output blows the locked 60s timeout. Fix is structural —
# comparisons are precomputed in code and the prompt caps the body at 600
# chars — 3000 then covers a short think + full body comfortably.
_REPORT_MAX_TOKENS = 3000


class ReportError(Exception):
    """Raised for invalid report parameters (unknown type)."""


def _today_bjt() -> date:
    return datetime.now(_BJT).date()


def compute_period(report_type: str) -> tuple[date, date]:
    """Return (period_start, period_end) in Beijing dates."""
    today = _today_bjt()
    if report_type == "daily":
        return today, today
    if report_type == "weekly":
        # Last complete Mon..Sun week. On Monday this is last week —
        # exactly what the Monday-09:00 cron should cover.
        this_monday = today - timedelta(days=today.weekday())
        last_monday = this_monday - timedelta(days=7)
        return last_monday, last_monday + timedelta(days=6)
    raise ReportError(f"unknown report_type '{report_type}', use daily | weekly")


async def _window_stats(db, start: date, end: date) -> dict:
    """Core aggregates for one closed Beijing-date window [start, end]."""
    bounds = {"s": start.isoformat(), "e": end.isoformat()}

    totals = (await db.execute(text(
        "SELECT COUNT(*), SUM(CASE WHEN is_collected=1 THEN 1 ELSE 0 END) "
        "FROM tryons WHERE date(created_at,'localtime') BETWEEN :s AND :e"
    ), bounds)).one()
    tryons = int(totals[0] or 0)
    collects = int(totals[1] or 0)

    top_rows = (await db.execute(text(
        "SELECT t.style_id, s.name, COUNT(*) AS cnt, "
        "SUM(CASE WHEN t.is_collected=1 THEN 1 ELSE 0 END) AS coll "
        "FROM tryons t JOIN styles s ON t.style_id = s.id "
        "WHERE date(t.created_at,'localtime') BETWEEN :s AND :e "
        "GROUP BY t.style_id ORDER BY cnt DESC LIMIT 3"
    ), bounds)).all()

    best_conv_rows = (await db.execute(text(
        "SELECT t.style_id, s.name, COUNT(*) AS cnt, "
        "SUM(CASE WHEN t.is_collected=1 THEN 1 ELSE 0 END) AS coll "
        "FROM tryons t JOIN styles s ON t.style_id = s.id "
        "WHERE date(t.created_at,'localtime') BETWEEN :s AND :e "
        "GROUP BY t.style_id HAVING cnt >= 10 "
        "ORDER BY (coll * 1.0) / cnt DESC LIMIT 1"
    ), bounds)).all()

    gender_rows = (await db.execute(text(
        "SELECT user_gender, COUNT(*) FROM tryons "
        "WHERE date(created_at,'localtime') BETWEEN :s AND :e "
        "GROUP BY user_gender"
    ), bounds)).all()

    return {
        "tryon_total": tryons,
        "collect_total": collects,
        "collect_rate": round(collects / tryons, 4) if tryons else 0.0,
        "top3_by_tryons": [
            {
                "style_id": sid,
                "name": name,
                "tryon_count": int(cnt),
                "collect_rate": round((coll or 0) / cnt, 3) if cnt else 0.0,
            }
            for sid, name, cnt, coll in top_rows
        ],
        "best_conversion": (
            {
                "style_id": best_conv_rows[0][0],
                "name": best_conv_rows[0][1],
                "tryon_count": int(best_conv_rows[0][2]),
                "collect_rate": round(best_conv_rows[0][3] / best_conv_rows[0][2], 3),
            }
            if best_conv_rows
            else None
        ),
        "gender_split": {g: int(c) for g, c in gender_rows},
    }


async def _aggregate_stats(db, report_type: str, start: date, end: date) -> dict:
    """Assemble the stats JSON fed into the §7.4 prompt templates."""
    current = await _window_stats(db, start, end)

    # Cold + growth context reuses the assistant tools' semantics.
    from app.services.assistant_tools import find_cold, find_trending

    trending = await find_trending(db, growth_threshold=0.5, min_volume=50)
    cold = await find_cold(db, days_no_activity=7)
    current["trending_candidates"] = [
        {
            "style_id": it["style_id"],
            "name": it["name"],
            "growth_rate": it["growth_rate"],
            "last_24h_tryons": it["last_24h_tryons"],
        }
        for it in trending.get("items", [])
    ]
    current["cold_styles_count"] = len(cold.get("items", []))
    current["cold_styles"] = [
        {"style_id": it["style_id"], "name": it["name"]}
        for it in cold.get("items", [])[:5]
    ]

    if report_type == "daily":
        yesterday = start - timedelta(days=1)
        previous = await _window_stats(db, yesterday, yesterday)
        return {
            "period": f"{start} ~ {end}",
            "today": current,
            "yesterday": previous,
            "comparison_precomputed": _compare_windows(current, previous),
        }

    prev_start = start - timedelta(days=7)
    prev_end = end - timedelta(days=7)
    previous = await _window_stats(db, prev_start, prev_end)
    return {
        "period": f"{start} ~ {end}",
        "this_week": current,
        "last_week": previous,
        "comparison_precomputed": _compare_windows(current, previous),
    }


def _compare_windows(current: dict, previous: dict) -> dict:
    """Ring-compare numbers computed IN CODE so the reasoning model does
    not burn its token budget on arithmetic (observed: self-computed
    comparisons pushed reasoning past max_tokens, yielding empty content).
    """
    def pct(cur: float, prev: float) -> float | None:
        return round((cur - prev) / prev * 100, 1) if prev else None

    return {
        "tryon_total_change_percent": pct(
            current["tryon_total"], previous["tryon_total"]
        ),
        "collect_total_change_percent": pct(
            current["collect_total"], previous["collect_total"]
        ),
        "collect_rate_change_pp": round(
            (current["collect_rate"] - previous["collect_rate"]) * 100, 1
        ),
    }


def _build_prompt(report_type: str, stats: dict) -> str:
    """§7.4 templates verbatim, stats injected as compact JSON."""
    if report_type == "daily":
        return (
            "你是平台美甲品类的运营助手。基于以下数据，生成一份结构化日报。\n"
            f"数据：{json.dumps(stats, ensure_ascii=False)}\n"
            "要求章节：\n"
            "1. 数据概览：3 句话总结 KPI 与环比\n"
            "2. 重点亮点：列出 TOP3 试戴款、TOP3 增长款、转化率最高款\n"
            "3. 风险预警：冷门款数量、转化下降款、库存紧张款\n"
            "4. 运营建议：3–5 条可执行建议，每条须引用具体数据\n"
            "5. 关键问题：1–2 个需运营拍板的开放问题\n"
            "语言风格：简洁专业，避免空话。\n"
            "输出 Markdown 正文，用 ## 分节，全文 600 字以内；"
            "comparison_precomputed 内是已算好的环比，直接引用不要自行推算；"
            "数据中没有的维度（如库存）一句话说明暂无数据即可，不得编造。"
        )
    return (
        "你是平台美甲品类的运营助手。基于以下本周与上周对比数据，生成一份周报。\n"
        f"本周数据：{json.dumps(stats['this_week'], ensure_ascii=False)}\n"
        f"上周数据：{json.dumps(stats['last_week'], ensure_ascii=False)}\n"
        f"已算好的周环比：{json.dumps(stats['comparison_precomputed'], ensure_ascii=False)}\n"
        f"统计周期：{stats['period']}\n"
        "要求章节：\n"
        "1. 本周总览：试戴总量、转化率、活跃款式数（含周环比）\n"
        "2. 趋势亮点：连续上升 ≥ 3 天的款式、本周首次进入 TOP10 的款式\n"
        "3. 持续冷门：本周和上周都进入冷门预警的款式\n"
        "4. 性别分布：女性/男性用户试戴行为差异（如有显著变化）\n"
        "5. 运营建议：3–5 条针对下周的具体动作\n"
        "6. 待决问题：1–2 个需要拍板的运营决策\n"
        "语言风格：简洁专业，引用具体数字，体现\"周\"的时间维度。\n"
        "输出 Markdown 正文，用 ## 分节，全文 600 字以内；"
        "环比直接引用给定数值不要自行推算；数据中未提供的维度一句话说明暂无数据即可，不得编造。"
    )


def _build_title(report_type: str, start: date, end: date) -> str:
    if report_type == "daily":
        return f"美甲品类日报 {start.isoformat()}"
    return f"美甲品类周报 {start.isoformat()} ~ {end.isoformat()}"


async def send_report_email(report_id: int, title: str, content_md: str) -> None:
    """Background email task. Owns its own session; never raises."""
    status, error, sent_at = "sent", None, datetime.now(timezone.utc)
    try:
        from app.config import settings

        html = md.markdown(content_md, extensions=["tables", "fenced_code"])
        await email.send_email(
            to=settings.REPORT_RECIPIENT,
            subject=title,
            html_body=html,
            text_body=content_md,
        )
    except Exception as e:  # email failure must never crash the app (§7.7.7)
        status, error, sent_at = "failed", f"{type(e).__name__}: {e}", None
        logger.warning("report %s email failed: %s", report_id, error)

    async with async_session_maker() as db:
        report = await db.get(Report, report_id)
        if report is None:  # pragma: no cover — report deleted mid-flight
            return
        report.email_status = status
        report.email_error = error
        report.email_sent_at = sent_at
        await db.commit()


async def generate_and_dispatch_report(
    report_type: str, trigger_source: str = "scheduled"
) -> int:
    """Aggregate -> LLM markdown -> reports + notifications rows -> async
    email. Returns the new report id. Raises on LLM failure (no rows)."""
    period_start, period_end = compute_period(report_type)

    async with async_session_maker() as db:
        stats = await _aggregate_stats(db, report_type, period_start, period_end)

        prompt = _build_prompt(report_type, stats)
        # Strong-tier reasoning models occasionally return empty content
        # (all budget spent on reasoning); one immediate retry recovers it.
        content_md = ""
        for _attempt in range(2):
            content_md = await llm.gen_text(
                prompt, model="strong", max_tokens=_REPORT_MAX_TOKENS
            )
            if content_md.strip():
                break
            logger.warning("empty %s report content, retrying once", report_type)
        if not content_md.strip():
            raise llm.LLMError("empty report content from LLM after retry")

        title = _build_title(report_type, period_start, period_end)
        report = Report(
            type=report_type,
            title=title,
            content_md=content_md,
            period_start=period_start,
            period_end=period_end,
            trigger_source=trigger_source,
            email_status="pending",
        )
        db.add(report)
        await db.flush()

        summary = content_md.strip().replace("\n", " ")
        if len(summary) > _NOTIFICATION_SUMMARY_LEN:
            summary = summary[:_NOTIFICATION_SUMMARY_LEN] + "…"
        db.add(Notification(
            type="report",
            ref_id=report.id,
            title=title,
            summary=summary,
        ))
        await db.commit()
        report_id = report.id

    # Fire-and-forget so the caller (cron / HTTP / assistant) returns fast.
    asyncio.create_task(send_report_email(report_id, title, content_md))
    logger.info(
        "report %s generated (%s, %s, %s~%s)",
        report_id, report_type, trigger_source, period_start, period_end,
    )
    return report_id
