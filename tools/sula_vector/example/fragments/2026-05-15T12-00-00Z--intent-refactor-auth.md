---
id: 2026-05-15T12-00-00Z--intent-refactor-auth
time: 2026-05-15T12:00:00Z
kind: intent
done_when: backend/src/auth tests pass and bundle size has not grown
verifier_ref: skill:run-auth-tests
tags: [code, refactor, auth]
author: jing
---
Refactor backend/src/auth to fold session and JWT logic into a single layer.
Acceptance: a verification-fact referencing this intent with passed: true.
