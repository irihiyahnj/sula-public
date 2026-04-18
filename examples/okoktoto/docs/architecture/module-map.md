# OKOKTOTO v5 Module Map

This profile maps the common code lanes for a React frontend over ERPNext.

## Core Paths

| Path | Responsibility |
| --- | --- |
| `src/App.tsx` | app shell, initialization, session and global layout |
| `src/api/erpnext.ts` | centralized ERPNext integration layer |
| `src/store/useStore.ts` | global front-end state |
| `src/components/` | reusable components and local interaction logic |
| `src/tabs/` or `src/pages/` | feature-level UI flows |
| `STATUS.md` | current project state |
| `CHANGE-RECORDS.md` | change-record index and rules |

## Modification Rules

- integration changes should land in `src/api/erpnext.ts`
- shell and initialization changes should land in `src/App.tsx`
- cross-page state changes should land in `src/store/useStore.ts`
- feature-specific UI should stay in page or component layers

## Coordination Rule

If a request changes both product behavior and project rules, update:

1. code
2. runbooks or architecture docs if the new behavior is durable
3. `CHANGE-RECORDS.md`
4. `STATUS.md`
