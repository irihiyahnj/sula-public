---
id: 2026-05-23T05-20-55Z--decision-add-turn-mark-view
time: 2026-05-23T05:20:55Z
kind: decision
refs: [2026-05-23T05-14-14Z--decision-skills-extension-model]
tags: [visibility, turn-mark, render-view]
author: jing
---
Added `render --view changes-summary [--since <ISO>]`, a one-line user-visible
mark hosts can surface at the end of a turn (e.g. "[sula] +3 (2 decision, 1
verification-fact)"). Silent if nothing was appended.

Principle audit: complies with C5 (minimal interaction), C7 (no churn — empty
turns produce a string the host should not display), B2 (session-start lives
in the host, Sula stays stateless), B6 (boot protocol unchanged), C2 (just a
view on top of the existing --since filter, no new substrate).

This makes the user experience of "Sula was used this turn" explicit without
forcing ceremony when nothing happened.
