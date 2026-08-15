---
id: 2026-05-24T09-05-00Z--decision-session-shim-retired
time: 2026-05-24T09:05:00Z
kind: decision
refs: [2026-05-15T12-00-00Z--intent-refactor-auth]
tags: [auth, shim]
governs: [src/auth/session_shim.py]
summary: 会话兼容层由 token verifier 取代，不再保留双路径
---
The session shim existed only to keep pre-token clients working during the
rollout. Those clients are gone, and keeping both paths meant every auth change
had to be reasoned about twice.

This judgment declares its subject with `governs`. The 2026-05-24 capture
records `src/auth/session_shim.py` as removed, so `--view decay` now reports this
judgment as decayed — a judgment about a file that no longer exists still spends
the next agent's attention, and nothing else would have said so.
