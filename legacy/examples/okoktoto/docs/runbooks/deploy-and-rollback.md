# OKOKTOTO v5 Deploy And Rollback Runbook

This runbook covers the standard release path for this profile.

## Branch Model

- primary branch: `main`
- working branch prefix: `codex/`
- deployment branch: `okoktoto-v5`

## Standard Flow

1. implement in a working branch
2. run project checks
3. update traceability
4. push working branch
5. promote only when release risk is acceptable

## Minimum Checks

- `npx tsc --noEmit`
- `npm run build`
- release checklist
- smoke checklist for impacted flows

## Rollback Notes

- code rollback is not always data rollback
- if rollout depends on ERPNext setup, rollback instructions must cover that dependency explicitly
