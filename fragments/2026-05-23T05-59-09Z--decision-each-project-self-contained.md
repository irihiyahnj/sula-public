---
id: 2026-05-23T05-59-09Z--decision-each-project-self-contained
time: 2026-05-23T05:59:09Z
kind: decision
refs: [2026-05-23T05-59-09Z--correction-cross-project-shared-tools-path, 2026-05-23T05-50-10Z--decision-trust-is-reader-side]
tags: [architecture, portability, self-contained, project-boundary, meta-principle]
author: jing
---
Crystallised principle: **Every Sula vector is self-contained. A project's
folder includes everything needed to boot it on any device, by any team, with
any LLM, with no reference to any external machine state.**

This means every project carries:
- AGENTS.md (host operating protocol)
- fragments/ (all project memory + Tier A–E principle fragments)
- tools/sula_vector/ (render.py + skills/ + supporting docs)

What is NOT shared across projects:
- The tools directory's content (each has its own copy; updates are per-project
  decisions made by that project's owner)
- The fragment history (each project owns its own truth)
- The host LLM session state (each project boots fresh)

What IS naturally shared:
- The convention spec (publicly readable, ship-frozen at v1.0)
- The principles (each project copies them as fragments at adoption time)

This is the dimensional cure to the broken cross-project path bug. Trying to
"save space" by having one central tools/ directory was an E5 violation
(invent a substrate dependency where none was needed). The right layer is:
the project IS the substrate. The project boundary IS the portability
boundary. Each project owns its tools/ as a normal artefact.

Operationally:
- A project can be zipped, transferred, forked, archived, deployed elsewhere
  without any path edits.
- A team picking up someone else's vector reads ONE folder; nothing else
  needs to be installed or configured.
- Updates to render.py or skills propagate by the project owner explicitly
  copying new versions in. There is no automatic sync (E5 forbids it). This
  is correct: it preserves project-level autonomy.

This decision supersedes any prior implicit assumption that projects could
share a "central Sula install" via path.
