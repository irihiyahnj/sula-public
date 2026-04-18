# GitHub Copilot Instructions

Read [AGENTS.md](AGENTS.md) before proposing or generating changes.

## Repository Rules

- Repository root is `OKOKTOTO v5`.
- Highest rule: `frontend-only orchestration over ERPNext-native capabilities`
- GitHub is the durable source of truth. Approved work should be committed and pushed, not left only locally.
- Working branches use `codex/*`.
- Deployment branch is `okoktoto-v5`.
- Keep primary integration logic centralized in [src/api/erpnext.ts](src/api/erpnext.ts).
- Use [docs/README.md](docs/README.md) as the documentation map.
- If the project enables formal document design rules, follow them for planning, proposal, report, process, and training documents.
- For substantial changes, validate with `npm run build`.

If these instructions conflict with `AGENTS.md`, `AGENTS.md` wins.
