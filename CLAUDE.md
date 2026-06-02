# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Hackathon project for 美团 AI 命题三：「美甲 AI 试戴与智能运营」. Dual-end web product: a consumer-side try-on flow + an operator-side dashboard sharing one data closed loop. The product brief, technical design, and step-by-step build plan are written down before code — read them first.

**Authoritative planning documents (root):**

- `design-docu.md` — product+system design (modules U0–U6 user-side, O1–O7 ops-side, DB schema, API contract, data flow)
- `tech-stack.md` — selected tech and "what we explicitly do NOT introduce"
- `implementation-plan.md` — 55 numbered build steps, each with a verifiable check; do not skip steps

Identical copies live in `memory-bank/` plus two empty placeholders (`progress.md`, `architecture.md`) intended to be filled in as build state evolves.

## Current build state vs. plan

The planning docs prescribe **React + Vite + FastAPI + SQLite + monorepo (`backend/` + `frontend/`)**. The product code (`backend/` + `frontend/`) does not exist yet — Phase 0 of `implementation-plan.md` builds it.

What does exist:

- `data-prep/` — one-off Python utilities for contest dataset preparation. **Not product code**, isolated from `backend/`:
  - `download_dataset.py` reads the contest xlsx and pulls 63 images (13 hand + 25×2 style) to `d:\美团AI HACKATHON\dataset\`. Already run; safe to re-run (idempotent).
  - `tag_male_styles.py` tags the 15 user-added male styles via PPIO Qwen3-VL-30B-MoE (the 72B was rate-limited). Resumable and 429-retry safe.
  - `auto_tag_styles.py` calls PPIO VLM (Qwen2.5-VL-72B + GLM-4.1V) to tag the 25 enhanced style images; supports resume and 429-retry
  - `probe_*.py` — one-off PPIO connectivity / model-id probes
- `Meijia/` — an **abandoned Next.js 15 + React 19 + Tailwind v4 frontend prototype**. Decision recorded: do NOT use it as the build foundation. Reason: React 19 / Next 15 / Tailwind v4 are too new for reliable AI-assisted coding; the chosen Vite + React 18 + Tailwind 3 stack is the LLM sweet spot and matches `implementation-plan.md` verbatim. Three pages exist (`/`, `/user`, `/merchant`) — keep them as **visual reference only**. Do not import code from `Meijia/` into `frontend/`. Do not mention `Meijia/` in any new product doc.

## External data and resources

- Dataset: `d:\美团AI HACKATHON\dataset\` (outside repo). Contents:
  - `hands/01.png ~ 17.png` — 17 hand samples (13 from contest, 4 user-added). Shared by both genders; no gender split.
  - `styles/f_01_enh.png ~ f_25_enh.png` + `f_NN_orig.{png|jpg}` — 25 female styles from contest, all keyed `f_*`.
  - `styles/tags_qwen.json` — Qwen2.5-VL-72B tags for the 25 female styles (keys `f_NN_enh.png`).
  - `styles/male/m_01.jpg ~ m_15.jpg` — 15 male styles (user-added). No `_orig`/`_enh` distinction since these were not enhanced.
  - `styles/male/tags_qwen.json` — Qwen3-VL-30B-MoE tags for the 15 male styles (keys `m_NN.jpg`). The 72B model was 429-blocked at the time so we fell back to the 30B MoE variant.
  - Female 25 has 0 cool-tone styles and 1 short-length style; the male 15 supplies 7 cool + 9 short, making the overall recommendation pool well-balanced. Do not regenerate styles with image-gen APIs.
- `.env` (gitignored) at repo root holds `PPIO_API_KEY` / `PPIO_BASE_URL`. PPIO is the single LLM/VLM supplier — no dashscope, no direct OpenAI. Future backend should add `LLM_QUICK_MODEL`, `LLM_STRONG_MODEL`, `JIMENG_API_KEY`, and SMTP keys per `tech-stack.md §7.3`.

## Commands

Currently no backend or test suite exists. Available commands operate on the two existing surfaces:

**Next.js prototype** (run from `Meijia/`):
- `npm run dev` — dev server at `http://localhost:3000`
- `npm run build` / `npm run start` — production build & serve
- Or double-click `Meijia/start-dev.bat` on Windows
- Note: `package.json` scripts use `set NEXT_TELEMETRY_DISABLED=1` cmd-style syntax. Works in PowerShell because `set X=Y && cmd` is interpreted by the shell that npm spawns, but if you edit the scripts use PowerShell-safe forms.

**Dataset / tagging scripts** (run from repo root, all live in `data-prep/`):
- `python data-prep/download_dataset.py` — idempotent, skips already-downloaded files
- `python data-prep/auto_tag_styles.py` — idempotent, only re-tags entries whose status ≠ `ok` in `tags_{label}.json`. GLM-Thinking branch can take 30–60s per image; cancel and re-run is safe.
- Both require `httpx`, `openpyxl`, `openai`, `python-dotenv`, `pillow` in the active Python env. Use `python -X utf8` with `$env:PYTHONIOENCODING="utf-8"` when CJK paths are involved (PowerShell mojibakes them otherwise).

## Architecture you can't see by browsing files

Read this so you don't have to reverse-engineer it from the planning docs:

**Data closed loop (the product's core idea):** Every user-side try-on writes to `tryons` and atomically UPSERTs `style_stats` in the same transaction (design-docu §10.3). The ops-side overview/trending/cold endpoints aggregate from `style_stats`. Operator actions (boost/demote/offline via `/api/ops/actions` or the AI assistant) mutate `styles.display_order` / `is_active`, which immediately changes what the next user sees in `/api/styles` and `/api/recommend`. Demo viability depends on this loop being real and synchronous.

**AI services are strictly cloud APIs:** No local model serving. The image-gen Provider is abstracted (`ImageGenProvider`) so the demo can fall back to `MockProvider` that copies the enhanced style image as the "try-on result" — this is the safety net for offline / API-down scenarios and must always work.

**Scheduler is in-process:** APScheduler runs inside the FastAPI process (no Celery, no Redis). Daily report 09:00, weekly Monday 09:00. Manual trigger (`POST /api/ops/reports/generate`) executes the **same function** with `trigger_source="manual"`. Both paths write `reports` row → `notifications` row → async email send. Bell badge polls `/api/ops/notifications/unread-count` every 5s.

**Recommendation has gender as a hard pre-filter,** then 4-dim scoring (skin 35% / hand 30% / heat 20% / diversity 15%) within that pool. LLM only generates the per-card reason text; it does not pick which styles to show.

**Style tag schema** (from `tags_qwen.json`): `gender ∈ {female, male, both}` · `style_tags[]` · `color_main` (hex) · `color_tone ∈ {warm, cool, neutral}` · `length_pref ∈ {short, medium, long}` · `complexity ∈ 1..5` · `occasion[]`. Database `styles.style_tags` stores the array as JSON.

## How to work in this repo

- **Plan-first culture is intentional.** The user has put thought into design-docu / tech-stack / implementation-plan. If a request implies deviating from them, surface the conflict explicitly rather than silently doing something different. Update the docs in lockstep when the design actually changes.
- **Step-by-step plan is the source of truth for build order.** When implementing, follow `implementation-plan.md` step IDs (e.g. "Step 4.5"). Each step's "验证" block is the definition of done — do not mark a step done until you can demonstrate the verification.
- **Focus on product and engineering, not presentation framing.** Per user preference recorded in personal memory (`feedback-focus-on-product`): avoid sections / phrasing oriented around "答辩 / 评审 / PPT / 评委 / 加分 / 演示话术". Business value, competitive analysis, and innovation points belong in product docs as substance, not as pitch material. This rule applies to any new docs you write here.
- **No code in `implementation-plan.md`.** That file is for instructions to AI developers; it deliberately contains zero code. Don't "improve" it by adding snippets.
- **Mock dataset is desensitized contest data.** `dataset/styles/*_enh.png` already shows nails on a hand model. Don't treat them as bare design swatches.
- **Windows + Chinese paths.** Native commands run via this harness sometimes get wrapped stderr noise but still succeed; check `Test-Path` / file size, not exit code, when in doubt. Always emit `.env`-style files without BOM (PowerShell's default `Out-File -Encoding utf8` writes BOM — use `[System.IO.File]::WriteAllText` with `UTF8Encoding(false)` instead).
