# Sula Sync Impact Model

Sula classifies managed-file sync changes so maintainers can review the right files first.

## Levels

### `high`

Review carefully before syncing because the change can alter tool behavior or high-risk operating procedures.

Current examples:

- `CODEX.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.github/copilot-instructions.md`
- `.cursor/rules/project.mdc`
- `docs/runbooks/auth-and-session.md`
- `docs/runbooks/deploy-and-rollback.md`

### `medium`

Review in the same sync batch because the change affects reusable operating guidance, architecture expectations, or runbooks.

Current examples:

- `docs/ops/*`
- `docs/architecture/*`
- profile runbooks not classified as `high`

### `low`

Review for completeness, but these changes should not normally alter operating behavior by themselves.

Current examples:

- `docs/README.md`
- low-risk managed documentation wording

## Usage Rule

Run `python3 scripts/sula.py sync --project-root <project> --dry-run` before every real sync. The command prints each pending managed-file change with its impact level and scope.
