# Agent instructions — VSCode Codex / any AI dev agent

**This file is auto-loaded by Codex CLI / VSCode Codex extension. It's the entry point.**

## Session start protocol — do this BEFORE writing any code

Read these files in order:

1. `HANDOFF.md` (repo root) — workflow rules, current state, locked decisions
2. `CLAUDE.md` (repo root) — project-wide instructions
3. `memory-bank/progress.md` — **tail 300 lines only** (last 3 Step entries + the `📌 项目锁定状态` section). Do NOT read from top of that file; it's 1000+ lines and will bloat context.
4. `implementation-plan.md` — the section for the Step you're about to do

Then in your **first turn back to the user**, summarize:

- The **5 workflow hard rules** (from `HANDOFF.md` §2)
- **Current build state** (Phase progress + next Step ID from `HANDOFF.md` §1)
- **Your understanding of the specific Step you're about to implement** + its plan-mandated `**验证**` checklist

Wait for the user's explicit confirmation of that summary before starting implementation.

## After each step — the non-negotiable ritual

1. Implement per plan
2. Run automated verification (`_check_*_api.py` or equivalent)
3. **Present result to user + describe how the user can manually verify (copy-pasteable command + what "通过" looks like)**
4. **Wait for user's explicit OK** (`ok` / `通过` / `下一步` / affirmative Chinese)
5. Only then: append entry to `memory-bank/progress.md` (BEFORE the `📌 项目锁定状态` heading)
6. Only then: `git commit` with `feat(backend|frontend): Step X.Y - <title>` message
7. Only then: proceed to next Step (announce next Step's goal first, wait for OK to start)

**Never auto-commit even when auto-tests pass.**

## Detailed rules & context

All the "why" and edge-case rules live in `HANDOFF.md`. If HANDOFF.md and this file conflict, HANDOFF.md wins.

If any project convention isn't clear from these docs — **ask the user**, don't guess. Default posture is conservative and explicit.
