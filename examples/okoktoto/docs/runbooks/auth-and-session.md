# OKOKTOTO v5 Auth And Session Runbook

This runbook covers the standard auth/session lane for the React + ERPNext profile.

## Expected Model

- auth is handled through browser session cookies
- CSRF behavior must remain compatible with ERPNext expectations
- session expiry codes: `401, 440`
- permission denied codes: `403`

## Typical Investigation Order

1. shell and initialization flow in [src/App.tsx](../../src/App.tsx)
2. integration behavior in [src/api/erpnext.ts](../../src/api/erpnext.ts)
3. global state in [src/store/useStore.ts](../../src/store/useStore.ts)

## Common Failure Modes

- app stays visually logged in after session expiry
- permission denied is misclassified as session expiry
- initial anonymous probe and keep-alive behavior diverge

## Change Discipline

When changing session behavior:

- keep expiry handling centralized
- avoid spreading auth decisions across page components
- record any durable behavior change in change records
