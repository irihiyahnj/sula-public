---
id: 2026-05-23T05-50-10Z--decision-trust-is-reader-side
time: 2026-05-23T05:50:10Z
kind: decision
refs: [2026-05-23T05-33-46Z--release-sula-vector-1-0-ga, 2026-05-23T05-45-41Z--correction-chronicle-broken-assessment-ref]
tags: [trust-model, meta-principle, audit-posture, dimension-shift]
author: jing
---
Sula Vector v1.0 trust posture, crystallised as an explicit meta-principle:

  Trust is a property of the READER, not of the convention.

The convention does not, and cannot, prevent a fragment from making a false
claim. What the convention does is structural:

  1. Append-only — any false claim, once written, cannot be deleted (B1).
  2. byte-stable replay — the trail of all claims and counter-claims is
     reproducible from the same fragments (B5).
  3. refs graph — claims, evidence, disputes, and corrections all reference
     each other; readers can traverse the graph freely (B3, open kind).
  4. Substrate handles concurrency — multiple authors append in parallel; the
     filesystem / git / Drive resolves order (B7).

Together: any deception leaves a permanent trace; any reader can see the
claim, the counter-claim, the supporting evidence, and the correction trail
side by side, then judge for themselves.

This is the dimensional solution to the otherwise-uncoverable problem of
"how do we prevent every form of false claim?" — we don't. We make every
form of false claim permanently visible and freely disputable. Truth is
derived by readers traversing the refs graph, not enforced by the
convention.

Concrete consequences for v1.0:

- Identity: not enforced; fragments carry author: as a claim. Cryptographic
  identity is a future skill (kind: signature), not a core feature.
- Verification evidence density: not enforced; verification-fact bodies are
  open. Evidence audits are a future skill (kind: audit / kind: audit-flag).
- Decision after-effect verification: not enforced; if a decision's effect
  must be tracked, append a follow-up goal with verifier_ref. The decision
  fragment itself records the choice, not the verification of the choice.
- Disputes and corrections: kind: correction (live-demonstrated this session)
  and kind: dispute are open patterns; either can be appended at any time
  with refs to the disputed fragment.

Why this is the right layer:

Listing every form of falsifiable claim and writing a regex/policy for each
would defend at the wrong layer (Tier C2). Each new form of fraud would
require a new policy. The right layer is the substrate of visibility: the
convention provides total signal preservation; specific verification
mechanisms compose on top as removable skills.

This decision should be read alongside the v1.0 release fragment and the
chronicle. It explains why v1.0 deliberately did not include cryptographic
signing, mandatory evidence-density checks, or per-decision verifier
enforcement — those were not omissions, they were correct architectural
boundaries.
