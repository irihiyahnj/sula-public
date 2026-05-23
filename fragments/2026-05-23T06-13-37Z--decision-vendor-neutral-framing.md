---
id: 2026-05-23T06-13-37Z--decision-vendor-neutral-framing
time: 2026-05-23T06:13:37Z
kind: decision
refs: [2026-05-23T05-14-14Z--decision-skills-extension-model, 2026-05-23T05-42-48Z--chronicle-sula-vector-v1-0-design-genealogy]
tags: [framing, vendor-neutral, editorial-correction, naming]
author: jing
---
Editorial correction: Sula Vector public docs were over-anchored on Codex
(an OpenAI product brand). The original drafting framed the skills
extension model as "Codex-style superpowers" — implying Sula Vector is
"Codex for projects". This is wrong. Sula Vector is a generic, vendor-
agnostic protocol; the extension model is "skills"; what skills enable
is "agent superpowers" or simply "capabilities".

Codex's superpowers article was a thought reference informing the design
direction, not a specification to be re-implemented. The chronicle fragment
records this honestly. The convention itself, the renderer, the migrator,
and the three reference skills are all vendor-agnostic shell programs and
text conventions.

Public-facing docs (README.md, docs/sula-vector-convention.md,
tools/sula_vector/RELEASE-NOTES.md) updated:
  - "Codex-style superpowers" → "agent superpowers"
  - "Codex capability" → "capability"
  - "Every Codex superpower" → "Every agent superpower"

Vendor names still appear in genuinely-multi-vendor contexts: e.g. a list
"works with Claude, Codex, Kiro, Gemini, any future model" is itself
neutral by listing multiple. Those stay.

This decision should guide all future drafting: when describing what
Sula Vector is or does, prefer the generic protocol language. Vendor
names appear only as illustrative examples, never as branding for the
core.
