# CLAUDE.md

Primary repository instructions are in [AGENTS.md](AGENTS.md). Read that file first.

If this file conflicts with `AGENTS.md`, `AGENTS.md` wins.

## Critical Reminders

- Repository root = `OKOKTOTO v5`.
- Highest rule: `frontend-only orchestration over ERPNext-native capabilities`
- Keep primary integration logic centralized in [src/api/erpnext.ts](src/api/erpnext.ts).
- Use [docs/README.md](docs/README.md) as the documentation map.
- Use [docs/ops/team-operating-model.md](docs/ops/team-operating-model.md) as the default execution flow.
- If the project enables formal document design rules, follow them when producing formal planning, proposal, report, process, or training documents.
- If a reusable Sula-managed issue is found and fixed locally, capture it with `python3 scripts/sula.py feedback capture --project-root . ...` before leaving the project on local drift alone.
- Working branches use `codex/*`.
- Deployment branch = `okoktoto-v5`.
- Validate substantial changes with `npm run build`.
