---
id: 2026-05-23T05-38-31Z--assessment-sula-vector-1-0-self-evaluation
time: 2026-05-23T05:38:31Z
kind: assessment
refs: [2026-05-23T05-33-46Z--release-sula-vector-1-0-ga]
tags: [v1-0, self-evaluation, dimension-shift]
author: jing
---
v1.0 self-assessment along three axes.

Significance:
- Real for the operator (Jing): cross-LLM/cross-device project memory carrier; immediate.
- Possible for the field: a concrete proposal for a vendor-neutral, agent-readable/writable project layer. Currently N=1; significance is potential until additional adoption occurs.
- Not: another project-management tool, a SaaS, a training framework.

Implementation form:
- Engineering depth: deliberately minimal (hand-rolled YAML subset, linear-scan render, shell-script skills). Not impressive by traditional engineering metrics.
- Dimensional correctness: the chosen dimension (project = ordered fragment stream + pure render) absorbs Codex superpowers and four project-type domains without adding new dimensions. One primitive (append), one function (render), zero daemons. Self-similar enforcement: principles ship as fragments and prepend through the same render path.
- Trade-offs are deliberate: D1 stdlib-only forbids a "better" YAML parser; C2 anti-fight forbids premature indexing.
- Conclusion: high-level by dimensional standards, minimal by engineering standards. The two metrics disagree on purpose.

Value:
- Operator: significant and immediate (cross-LLM, cross-device, no maintenance cascade).
- Adopted projects: significant (append-only memory, two-step boot, mechanical goal closure, painless upgrade).
- Wider ecosystem: potential, unrealised. Depends on whether other operators adopt the convention.
- Not delivered: IDE/build/deploy replacement, autonomous execution, no-tuning scaling beyond ~10k fragments, GUI.

Deepest claim: the artefact itself plus a reproducible dimension-collapse demonstration. The method (apply Tier A–E to a bloated project, find the essential dimension, ship the minimal form, prove coverage of prior capabilities) is itself reusable on other targets.

Honest assessment: current value > investment cost. Potential value >> current value. Realisation of the potential depends entirely on whether the convention gets used to manage other projects.
