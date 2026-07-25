---
id: 2026-07-25T11-00-12Z--assessment-vector-audit-capture-fidelity-and-reader-resolution
time: 2026-07-25T11:00:12Z
kind: assessment
refs:
  - 2026-05-23T05-38-31Z--assessment-sula-vector-1-0-self-evaluation
  - 2026-05-23T05-45-41Z--correction-chronicle-broken-assessment-ref
  - 2026-05-23T09-03-40Z--decision-update-check-at-boot-not-cron
tags: [audit, render, capture, integrity]
---
Read-only audit of this vector at 361 fragments (231 event, 74 decision, 23 release, 5 principle). Tests 34/34 PASS, worktree clean, `load_fragments` on the full vector takes ~13 ms — storage and speed are not the constraint. The two real constraints are **capture fidelity** (what reaches `fragments/`) and **reader resolution** (what `render` resolves for the reader).

Verified findings:

1. Capture depends on agent goodwill. No mechanical link exists between a commit and the fragment that explains it. `git` already holds the ground truth of every change; nothing witnesses it into the vector. Traceability is currently behavioural, not structural.
2. Four dangling `refs` live in the vector and nothing detects them: `…05-37-XX--assessment-…` (placeholder timestamp), `…06-04-37Z--operation-public-release-v1-0` (real file is `06-05-07Z`), and two `2026-06-06T…decision-…` ids that were never migrated out of `docs/change-records/`. Under B1 these are permanent; only detection plus a `correction` can repair them.
3. `render` does not resolve supersession. `--for-agent` lists the last 10 decisions by time with no marker for decisions later corrected or superseded. Append-only only pays off if render collapses each chain — otherwise boot context drifts toward confident misinformation.
4. Boot selection is recency, not signal. 231 of 361 fragments are machine events; any chatty skill can flood the digest window. `_summarize` takes the first body line truncated at 200 chars, and median body length is 54 chars, so most digest lines carry little meaning.
5. Intents never close. `_is_satisfied` closes only goals (via `verification-fact`) and intents carrying `done_when`. Two 2026-05-23 heartbeat test intents have appeared as "open" in every boot for two months. The open list grows monotonically.
6. Host-file conflict with Tier A. `CLAUDE.md`, `CODEX.md`, `.cursor/rules/project.mdc`, and `.github/copilot-instructions.md` still assert the legacy highest rule ("preserve the split between centrally managed operating-system files and project-owned business truth") and route work through `scripts/sula.py`. Four of five host entrypoints boot into the pre-vector world; the cross-LLM continuity claim does not hold for them today.
7. Legacy surface still sits at the repository root: `scripts/sula.py` (928 KB), `.sula/` (108 KB of derived state), `docs/change-records/` (280 KB), `STATUS.md` and `.sula/state/current.md` (both stale, both instructing agents to run `sula check`). This is E1/E2/B4 shape preserved in place, and it is the most likely cause of an agent adopting the wrong operating model before it reaches AGENTS.md.
8. Three overlapping update paths now exist (`migrate.py`, `update-from-canonical.sh`, `skills/auto-update-from-canonical.py`), and boot invokes the network before the agent has read any context — pressure against B6's two-step boot.

No remediation performed. This fragment records the audit only.
