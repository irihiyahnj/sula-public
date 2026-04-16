# CODEX.md

Primary repository instructions are in [AGENTS.md](AGENTS.md). Read that file first.

If this file conflicts with `AGENTS.md`, `AGENTS.md` wins.

## Codex Role

- Codex is the default execution agent for this repository.
- Treat user requests as end-to-end delivery requests unless the user explicitly asks only for analysis, brainstorming, or a plan.
- Use [docs/README.md](docs/README.md) as the documentation map.
- Follow [docs/ops/team-operating-model.md](docs/ops/team-operating-model.md) as the default execution flow.
- If the project enables formal document design rules, follow them for planning, proposal, report, process, and training documents.

## Critical Reminders

- Repository root = `OKOKTOTO v5`.
- Highest rule: `frontend-only orchestration over ERPNext-native capabilities`
- Keep durable documentation organized through [docs/README.md](docs/README.md).
- Reuse the primary orchestration lane in [src/api/erpnext.ts](src/api/erpnext.ts) before creating new entrypoints.
- Keep the main project entry or operator-facing surface centered in [src/App.tsx](src/App.tsx).
- If work touches `STATUS.md`, `CHANGE-RECORDS.md`, `docs/change-records/*`, `.sula/state/current.md`, `.sula/events/log.jsonl`, or `.sula/memory-digest.md`, finish by running `python3 scripts/sula.py check --project-root .`.
- Treat `SULA CHECK OK` as the completion gate for status-sync work; if generated `.sula/*` files drift, rebuild them through Sula commands instead of hand-editing them.
- If a reusable Sula-managed issue is found and fixed locally, capture it with `python3 scripts/sula.py feedback capture --project-root . ...` before leaving the project on local drift alone.
- Working branches use `codex/*`.
- Deployment branch = `okoktoto-v5`.
- Validate substantial changes with `npm run build`.
