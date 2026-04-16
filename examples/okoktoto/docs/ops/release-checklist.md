# OKOKTOTO v5 Release Checklist

Use this checklist before push or release.

## All Non-trivial Changes

- [ ] scope is clear
- [ ] highest rule impact is explicit
- [ ] traceability is updated
- [ ] unrelated changes are not mixed in
- [ ] reusable Sula-managed fixes have been captured as feedback if they should be considered upstream
- [ ] `STATUS.md` reflects the current state
- [ ] change record / release note / incident note updates are explicit if needed

## Validation

- [ ] project-appropriate verification was run
- [ ] `npx tsc --noEmit` if relevant
- [ ] `npm run build` for substantial code changes

## Before Pushing Working Branches

- [ ] commit batch is coherent
- [ ] branch is suitable for review and backup

## Before Pushing Deployment Branch

- [ ] app availability risk is understood
- [ ] login/session risk is understood
- [ ] primary flow risk is understood
- [ ] external setup dependency is understood
- [ ] rollback path is explicit

## Branch Model

- primary branch: `main`
- working branch prefix: `codex/`
- deployment branch: `okoktoto-v5`
