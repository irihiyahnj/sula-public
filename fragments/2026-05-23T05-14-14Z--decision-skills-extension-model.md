---
id: 2026-05-23T05-14-14Z--decision-skills-extension-model
time: 2026-05-23T05:14:14Z
kind: decision
refs: [2026-05-23T05-14-14Z--decision-adopt-sula-vector-convention]
tags: [extensibility, skills, superpowers]
author: jing
---
Codex-style superpowers (durable threads, voice, steering, queuing, goals,
verifiers, automations, side-panel artifacts, browser/MCP/computer-use)
implement as **skills** under `tools/sula_vector/skills/`. Each skill is a
standalone program: read fragments → do work → append new fragments → exit.

The "registry" is `ls skills/`. No manifest, no SDK, no plugin descriptor.
Adding a skill is dropping a script in. Removing one is `rm`. The core
render.py never grows when capabilities are added.

First reference skill shipped: verifier-shell.py (122 lines).
