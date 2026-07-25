# Document memory capability implementation plan

## Metadata

- date: 2026-04-18
- executor: Codex
- branch: codex/release-main
- related commit(s): pending
- status: completed

## Background

Sula needed a durable internal plan for the next phase of project-memory work. The goal was not to add another broad architecture note, but to define a concrete implementation sequence for stronger session staging, rule indexing, promotion flows, deterministic routing, and future optional semantic caches while preserving Sula's source-first operating model.

## Analysis

- Sula already has strong durable memory surfaces such as `STATUS.md`, change records, `.sula/state/current.md`, and `.sula/memory-digest.md`, but the split between temporary operator context and promoted durable state is still implicit.
- Project rules such as `AGENTS.md`, workflow policy, and document-design constraints are high-value operating knowledge, yet they are not consistently modeled as first-class kernel objects.
- Retrieval quality can improve significantly through better routing, richer rule extraction, and explicit maintenance jobs before any optional semantic layer is attempted.

## Chosen Plan

- add a new reference plan that defines the target memory capability model in Sula's own product language
- prioritize staged session captures, rule objects, promotion flows, job tracking, and deterministic query routing
- keep semantic caches optional, canary-only, and disposable
- document publication hygiene so public Sula materials do not present internal capability absorption work as external dependency lineage

## Execution

- added a new reference plan at `docs/reference/memory-capability-implementation-plan.md`
- updated the documentation map so the new durable reference is discoverable
- updated the change-record index with this planning document

## Verification

- reviewed the existing project-memory model, vNext kernel contract, and documentation-map rules before drafting the plan
- checked the new plan against Sula's highest-rule constraints around portability, removability, and source-first truth

## Rollback

- remove `docs/reference/memory-capability-implementation-plan.md`
- remove this change record and its index entry if the plan is replaced by a different memory roadmap

## Data Side-effects

- no runtime behavior changed
- Sula now has a durable implementation plan for the next memory-capability slice

## Follow-up

- decide whether the first implementation slice should begin with rule indexing or staged session captures
- extend the manifest and query model only after one minimal canary proves the proposed promotion loop

## Architecture Boundary Check

- highest rule impact: preserved; the plan strengthens Sula's memory layer without replacing project-owned truth or introducing mandatory heavy infrastructure
