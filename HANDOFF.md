# Handoff Brief — 美甲 AI 试戴与智能运营 Demo

**Purpose:** give an incoming AI dev agent (Codex / any) the invisible context
that the previous session accumulated but never made explicit in the repo.

## 0. Read this order (before touching code)

1. **This file** (HANDOFF.md) — workflow rules + current state + locked decisions
2. **CLAUDE.md** — project instructions (root-level, always applies)
3. **`memory-bank/progress.md` — tail ~300 lines only** (last 3 Step entries + `📌 项目锁定状态` section). File is 1000+ lines; do NOT read from top or context will bloat.
4. **`implementation-plan.md`** — jump to the section for the Step you're about to do

Then before writing any code, **summarize the 5 workflow rules + current state + Step goal** back to the user for confirmation.

## 1. Current build state (as of 2026-08-28)

- **Phase 0-9 done.** Everything except Phase 10 (E2E smoke): full user flow, full ops frontend (O1/O2/O3/O5/O6/O7 + report detail + live bell), assistant FC loop, report/notification subsystem with APScheduler (Asia/Shanghai, daily 09:00 / weekly Mon 09:00).
- **Email so far verified with ZERO real SMTP traffic** (server run with `SMTP_HOST=smtp-disabled.invalid` → real failed-path). The live "sent" test is pending user approval; start the backend WITHOUT that override to restore real sending.
- **Next: Phase 10 (10.1–10.4)** — data-loop smoke, IMAGE_PROVIDER=seedream switch test (user edits .env), report full-path with REAL email (user-gated), full-story smoke.
- Rate-limit reality: BOTH PPIO tiers minute-limited (~5 req/min class); chat degrades to data-grounded template replies on 429; report generation takes ~30-60s (reasoning model).
- Reseed does NOT touch reports/notifications/ops_actions — verification residue survives; clean demo needs manual DELETE or acceptance.
- `git log --oneline -20` shows the trail. Batch records: progress.md "Batch A/B/C" entries.

## 2. Workflow — five hard rules

These override any general "auto-continue" behavior your default settings might have.

1. **Follow `implementation-plan.md` step IDs strictly.** Don't skip. Don't merge steps into one commit. Each step's `**验证**` block is the definition of done.

2. **Human-in-the-loop gate — batch mode since 2026-08-27 (user-approved).** Low-risk steps with established patterns run as batches: implement + auto-verify + commit per step WITHOUT waiting, then **one user review gate at batch end** (user visually inspects all pages/behavior at once). progress.md gets one batch entry. Steps with concentrated risk still gate individually: Step 8.1 tool schemas (pause before 8.2), anything touching real SMTP sends, and any visual/AI-quality judgment. HANDOFF §7 stop conditions (destructive ops / secrets / new deps / plan deviation) always apply regardless of mode. If the user revokes batch mode, revert to per-step waiting.

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

## 6. Next step: Phase 10 — E2E smoke (final phase, 4 steps)

**Plan reference:** `implementation-plan.md` §10.1–§10.4 + 收尾清单.

**Step-specific gates & facts:**
- **10.1 data-loop smoke**: full user flow → O1 KPIs move within 10s; 60x batch tryons on one style → it appears in O2 trending. Reseed FIRST (time windows) — reseed leaves reports/notifications/ops_actions untouched.
- **10.2 IMAGE_PROVIDER switch**: `.env` edit is the USER's action (AI does not touch .env). seedream generates real images via PPIO (~¥0.2/张); compare file sizes in static/cache (real ≥ hundreds of KB, mock = cover copy). Locked: Seedream 4.5, V1 short prompt.
- **10.3 report full path**: needs REAL SMTP — user approval required, then start backend WITHOUT the SMTP_HOST override. Verify: bell within 5s, list within ~60s (LLM), email_status pending→sent, inbox HTML renders, detail matches email.
- **10.4 full-story smoke**: incognito / → /upload redirect... user flow → ops flow → assistant 3 rounds. Perf targets: recommend <8s, batch tryon <15s, dashboards <3s, report <60s (plan says 30s but strong-tier reasoning generation measured 30-60s — report reality, don't fake it).

**Known cleanup items (post-Phase-10, ask user which to take):**
- antd v6 deprecation warnings: `Tag bordered={false}` → `variant="filled"`, `Drawer width` → `size` (across O-side pages).
- Main JS chunk 2.4MB (echarts + react-markdown full import) — route-level code splitting is now legitimate per Step 7.1's deferral note.
- PPIO key rotation still pending (Step 4.5 partial exposure; user does it in PPIO console).

## 7. If you're not sure — ask, don't guess

Genuine ambiguities users have wanted to be asked about (not silently decided):
- Data-destructive operations (reseed wipes real tryons/collect actions from previous testing)
- Any change to `IMAGE_PROVIDER`, LLM model IDs, or PPIO_API_KEY
- Adding new dependencies (`pip install ...` or `npm i ...`)
- Modifying files under `data-prep/` (one-off scripts; changing behavior may re-cost dataset prep)
- Anything that changes the answer to "did the user's OK from last step still apply here"

Default posture: **conservative + explicit**. This project prefers "I'm about to X, is that right?" over "I did X".
