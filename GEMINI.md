# GEMINI.md

Read [AGENTS.md](AGENTS.md) before making changes.

If this file conflicts with `AGENTS.md`, `AGENTS.md` wins.

## Critical Reminders

- Repository root = `Sula`.
- Highest rule: `Preserve the split between centrally managed operating-system files and project-owned business truth.`
- Keep primary integration logic centralized in [scripts/sula.py](scripts/sula.py).
- Use [docs/README.md](docs/README.md) as the documentation map.
- Use [docs/ops/team-operating-model.md](docs/ops/team-operating-model.md) as the default execution flow.
- If the project enables formal document design rules, follow them for planning, proposal, report, process, and training documents.
- If a reusable Sula-managed issue is found and fixed locally, capture it with `python3 scripts/sula.py feedback capture --project-root . ...` before leaving the project on local drift alone.
- Working branches use `codex/*`.
- Deployment branch = `main`.
- Validate substantial changes with `python3 -m unittest discover -s tests -v`.
