---
id: 2026-05-23T05-59-09Z--correction-cross-project-shared-tools-path
time: 2026-05-23T05:59:09Z
kind: correction
refs: [2026-05-23T05-54-53Z--operation-fleet-upgrade-to-v1-0, 2026-05-23T05-54-53Z--correction-agents-md-relative-path-bug]
tags: [audit, architecture-fix, portability, self-contained]
author: jing
broken_behavior: "fleet upgrade made all 14 projects' AGENTS.md point to /home/jing/Project/projectdev/sula/tools/sula_vector/ (this device's absolute path)"
correct_behavior: "each project carries its own tools/sula_vector/ inside it; AGENTS.md uses relative path 'tools/sula_vector/render.py'; project is fully portable to any device or team"
---
The previous fleet upgrade introduced an architectural error: every project's
AGENTS.md hardcoded /home/jing/Project/projectdev/sula/tools/sula_vector/ as
the tools location. This made all 14 projects implicitly depend on the canonical
Sula tooling living at one specific path on this specific device.

The user's framing exposed the mistake: "imagine 14 different devices, 14
different teams. How could they share a path?" Correct: they cannot.

Fix applied:

1. migrate.py updated: install_tooling() now copies tools/sula_vector/{render.py,
   skills/, AGENTS.md, README.md, RELEASE-NOTES.md, principles/README.md} into
   each project's own tools/sula_vector/. install_agents_template() reverts to
   relative path "tools/sula_vector/render.py".

2. Fleet repair: all 14 projects had tools/sula_vector/ copied into them (Sula
   self skipped because its tools/sula_vector/ IS the canonical source). Each
   project's AGENTS.md sentinel block was replaced to use the relative path.

3. Verification: each project boots independently using its OWN render.py.
   Portability test: copying 1terminal to /tmp/moved-1terminal produces a
   working vector at the new location with no path edits.

The 14 projects are now genuinely independent. Each could be zipped and
handed to a different team on a different device, and would boot and operate
correctly with no reference back to this machine.

Tooling per project: ~9 files (~2000 lines). Each project chooses when to
update its local copy from a master Sula install (no automatic sync — that's
explicitly out of scope per Tier B7).
