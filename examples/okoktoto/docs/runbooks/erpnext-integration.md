# OKOKTOTO v5 ERPNext Integration Runbook

This runbook covers the integration lane for React frontends over ERPNext.

## Core Rule

Business integration logic should stay centralized in [src/api/erpnext.ts](../../src/api/erpnext.ts).

## Expected Responsibilities Of The Integration Layer

- request construction
- auth/session handling
- ERPNext resource and method access
- reusable higher-level orchestration helpers

## Anti-patterns

- ad hoc business fetches scattered through components
- duplicating ERPNext semantics in multiple tabs or pages
- bypassing the integration layer for convenience

## Before Introducing New Backend Behavior

Stop and check the highest rule first:

`frontend-only orchestration over ERPNext-native capabilities`

If the request needs a backend-side executable change, treat it as an architecture exception candidate rather than a default implementation path.
