# Handoff Brief — 美甲 AI 试戴与智能运营 Demo

**Purpose:** give an incoming AI dev agent (Codex / any) the invisible context
that the previous session accumulated but never made explicit in the repo.

## 0. Read this order (before touching code)

1. **This file** (HANDOFF.md) — workflow rules + current state + locked decisions
2. **CLAUDE.md** — project instructions (root-level, always applies)
3. **`memory-bank/progress.md` — tail ~300 lines only** (last 3 Step entries + `📌 项目锁定状态` section). File is 1000+ lines; do NOT read from top or context will bloat.
4. **`implementation-plan.md`** — jump to the section for the Step you're about to do

Then before writing any code, **summarize the 5 workflow rules + current state + Step goal** back to the user for confirmation.

## 1. Current build state (as of 2026-09-13) — COMPLETE, public-portfolio posture

- **All 55 plan steps done (Phase 0-10) + 收尾清单 5/5**, followed by a maintenance period (Batch E/F/G) and a user-playtest fix round (Batch H, 2026-09-13) — see progress.md "维护期" / "Batch H" entries.
- **Public face = GitHub repo + live Render deployment (user decision, 2026-09-12).** Repo: https://github.com/jiaoren07/nail-ai-tryon-ops (public, seed assets in-repo, any clone runs fully imaged). Live: https://nail-ai-tryon-ops.onrender.com (Render free tier, Docker, Singapore; sleeps after 15min idle, 30-60s cold start, DB re-seeds every cold start). Interview demos still run on localhost (screen-share).
- **Single-origin mode exists**: after `npm run build`, the backend alone on :8000 serves the whole app (SPA fallback, relative API URLs). Vite :5173 dev flow unchanged.
- Env guards: `DAILY_RESEED` (nightly 04:30 self-heal, for persistent-disk deploys), `SEEDREAM_DAILY_QUOTA` (spend cap → mock fallback). Quick model is `qwen/qwen3-235b-a22b-instruct-2507` (old 80b delisted by PPIO); `VLM_MODEL` (Batch H) powers the U1 hand-photo upload gate.
- **Email subsystem REMOVED (Batch H, user decision).** Reports are in-app only: history in O7 报告中心 + bell notifications. There is no SMTP config, no email.py, no 邮件状态 anywhere — the old `$env:SMTP_HOST="smtp-disabled.invalid"` isolation ritual is obsolete. Schema changed (reports table lost email columns): after pulling, delete `nail_demo.db` and reseed.
- Default local posture: IMAGE_PROVIDER=mock, reseed before demos.
- Remaining user-only actions (optional): pin repo on GitHub profile; Gitee mirror for mainland image loading.
- `git log --oneline -40` shows the trail. Batch records: progress.md "Batch A/B/C/D" + "维护期" + "Batch H" entries.

## 2. Workflow — five hard rules

These override any general "auto-continue" behavior your default settings might have.

1. **Follow `implementation-plan.md` step IDs strictly.** Don't skip. Don't merge steps into one commit. Each step's `**验证**` block is the definition of done.

2. **Human-in-the-loop gate — batch mode since 2026-08-27 (user-approved).** Low-risk steps with established patterns run as batches: implement + auto-verify + commit per step WITHOUT waiting, then **one user review gate at batch end** (user visually inspects all pages/behavior at once). progress.md gets one batch entry. Steps with concentrated risk still gate individually: Step 8.1 tool schemas (pause before 8.2) and any visual/AI-quality judgment. HANDOFF §7 stop conditions (destructive ops / secrets / new deps / plan deviation) always apply regardless of mode. If the user revokes batch mode, revert to per-step waiting.

3. **Every step report ends with a `手动验证方法` section.** Give the user a copy-pasteable command + describe what "通过" looks like. Don't wait to be asked. From Step 5 onward, one primary path (auto script → "ALL PASS") is enough; only add secondary paths if they have demo value or the primary is fragile.

4. **Reseed before verifying time-window interfaces.** `seed_all.py` anchors the spike to seed-time "today". After hours pass, rolling-window rules (`trending` 24h, `cold` 7d, `overview` today-vs-yesterday) drift. **Run `python scripts/seed_all.py` immediately before running any `_check_*_api.py`**. Users have hit this bug already (Step 6.2 verify came back empty after time drift).

5. **Visual/color judgments defer to the user's eyes, not `Read` tool.** Don't binary-classify colors from image pixels ("this is red vs blue"). If the user says a recommendation feels off, adjust the score table (`recommend.py`) or the CSS token — don't argue the pixel value.

## 3. Locked decisions — do NOT "improve" or "fix" these

| Item | Why locked | Would-be "fix" trap |
|---|---|---|
| `IMAGE_PROVIDER=mock` default | Demo safety net per design-docu §8.1. MockProvider intentionally copies the style cover as the "try-on result". | Don't try to make U5's compare slider show synthesized nails when `IMAGE_PROVIDER=mock` — that's Seedream's job. |
| Seedream 4.5 for real image gen | Step 3.2 benchmarked 4.0/4.5/5.0-lite/Qwen. Only 4.5 handles dark hands + style-image conditioning correctly. Re-evaluated in Step 6.2 era via `data-prep/probe_qwen_image_edit.py`, Qwen rejected (PPIO only accepts single image, needs text-workaround, quality lower). | Don't switch to Qwen or introduce a new provider without user asking. |
| PPIO quick tier limited to 5 req/min | Structural on this API key. Step 4.5 uses ONE batch call to produce 9 recommendation reasons because 9 parallel calls hit the limit and fall back to templates. | Don't "optimize" by reverting to `asyncio.gather` of 9 individual calls. |
| `frontend/public/samples/01-04.png` duplicated with `backend/static/samples/` | Sidesteps FastAPI's `StaticFiles` mount CORS edge case so U1's `fetch() → blob → File` works same-origin. | Don't dedupe or "clean up" the duplicate; changes to CORS config here have historically broken more than they fix. |
| No auth on ops endpoints | Demo scope. Prod would need admin token check. | Don't add auth middleware unless the user explicitly asks. |
| `_check_*.py` and `_diagnose_*.py` underscore-prefixed | Signals "not runtime code"; pytest won't auto-collect them. Committed in git for reproducibility. | Don't rename to `test_*.py` or move to `tests/`. |
| Frontend types shim `frontend/src/types/react-compare-image.d.ts` | Package ships no `.d.ts`; minimal shim keeps TS strict happy. | Don't `@ts-ignore` or `npm i @types/react-compare-image` (no such package). |
| `data-prep/` scripts are one-off, NOT product code | Kept in git for reproducibility of the contest dataset prep. | Don't try to integrate them into the backend runtime. |

## 4. Environment quirks

- **Windows + PowerShell.** Bash-style `&&` is a PS parse error. Use `; if ($?) { ... }` or `;` for unconditional chain. Multiline strings via here-strings `@'...'@` (single-quoted; `'@` must be at column 0).
- **CJK paths** (`d:\github仓库1\`). Set `$env:PYTHONIOENCODING="utf-8"` before running verify scripts, else Chinese in output turns into mojibake.
- **Git commit messages with Chinese.** Inline `git commit -m "..."` triggers PowerShell quote-escape hell. Convention: `Write` a `_COMMIT_MSG.tmp` at repo root, `git commit -F _COMMIT_MSG.tmp`, then delete.
- **Backend port 8000 (uvicorn), frontend port 5173 (vite).** Both must be running for full-flow verification. No proxy — CORS is configured for cross-origin dev. `localhost:8000` in browser will 404 (backend has no `/` route); use `localhost:5173` for the app.
- **Vite dev server binds IPv6 by default.** `curl 127.0.0.1:5173` may fail; use `curl localhost:5173`.
- **`_COMMIT_MSG.tmp` should be in `.gitignore`? Not currently.** Just remember to delete it after commit. If Codex forgets, it'll show up in `git status`.

## 5. Documentation deliverables per step (mandatory)

Every completed Step needs:

1. **`memory-bank/progress.md` entry** appended **BEFORE** the `### 📌 项目锁定状态` heading line (that heading stays at the bottom). Chinese template:
   ```
   ### ✅ Step X.Y · <title> — YYYY-MM-DD

   **做了什么：**
   - ...

   **Step X.Y 验证：**
   | 验证项 | 实测 |
   |---|---|
   | ... | ... |

   **几个设计选择（透明告知）：**
   1. ...

   **给后续开发者的提示：**
   - ...
   ```

2. **One git commit** with header `feat(backend|frontend): Step X.Y - <short title>` and body containing:
   - What was implemented
   - Verify results (X/X PASS)
   - Rationale for non-obvious design choices
   - Forward notes for the next Step

3. **Update `📌 项目锁定状态` section only when a locked decision actually changes** (rare — mostly for secret rotation events or model swaps).

## 6. Next step: none — demo/maintenance mode

The implementation plan is exhausted (55/55 + closing checklist). What remains is operational:

**Demo-day runbook:**
1. `cd backend; .venv\Scripts\python.exe -X utf8 scripts\seed_all.py` — anchors time windows to "now"; run again if a day rolls over mid-prep.
2. Backend: `.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000` (no email subsystem since Batch H — nothing to isolate; scheduled reports just write in-app rows).
3. Frontend: `cd frontend; npm run dev` → http://localhost:5173. (Or single-port: `npm run build` once, then backend alone serves http://localhost:8000.)
4. Chat demo pacing: ≥30s between assistant questions (rate limit); 429 degrades gracefully but LLM prose is nicer.
5. Real image generation: set `IMAGE_PROVIDER=seedream` in .env (user edit) or env var; ~¥0.2/张, ~25s/张; mock is the always-works fallback. The live Render site's provider is set in its Environment panel.

**Optional backlog (user picks, no order implied):** route-level code splitting (2.4MB chunk); dual-mode try-on (segmentation+recolor third `ImageGenProvider` impl, README roadmap).

## 7. If you're not sure — ask, don't guess

Genuine ambiguities users have wanted to be asked about (not silently decided):
- Data-destructive operations (reseed wipes real tryons/collect actions from previous testing)
- Any change to `IMAGE_PROVIDER`, LLM model IDs, or PPIO_API_KEY
- Adding new dependencies (`pip install ...` or `npm i ...`)
- Modifying files under `data-prep/` (one-off scripts; changing behavior may re-cost dataset prep)
- Anything that changes the answer to "did the user's OK from last step still apply here"

Default posture: **conservative + explicit**. This project prefers "I'm about to X, is that right?" over "I did X".
