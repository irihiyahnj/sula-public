---
id: 2026-05-23T05-14-14Z--decision-adopt-sula-vector-convention
time: 2026-05-23T05:14:14Z
kind: decision
tags: [architecture, sula-vector, dimension-shift]
author: jing
---
Adopted the Sula Vector convention as the canonical replacement for the
945KB Sula 0.18.x runtime.

Rationale: applying MADCUT cinema-principle Tier A and C2 to Sula itself
revealed that the kernel + 12 parallel state directories were a wrong-layer
defence. The right dimension is "a project = an ordered, append-only folder
of typed text fragments; every view is render(fragments, conventions)".

Substrate (git / Drive / filesystem) handles storage and concurrency.
Universal across code, governance, client services, and creative projects.
