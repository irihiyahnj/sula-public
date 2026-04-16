# GitHub Copilot Instructions

Read [AGENTS.md](AGENTS.md) before proposing or generating changes.

## Repository Rules

- Repository root is `Sula`.
- Highest rule: `Preserve the split between centrally managed operating-system files and project-owned business truth.`
- GitHub is the durable source of truth. Approved work should be committed and pushed, not left only locally.
- Working branches use `codex/*`.
- Deployment branch is `main`.
- Keep primary integration logic centralized in [scripts/sula.py](scripts/sula.py).
- Use [docs/README.md](docs/README.md) as the documentation map.
- If the project enables formal document design rules, follow them for planning, proposal, report, process, and training documents.
- For substantial changes, validate with `python3 -m unittest discover -s tests -v`.

If these instructions conflict with `AGENTS.md`, `AGENTS.md` wins.
