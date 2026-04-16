# Document Superpowers capability absorption plan

## Metadata

- date: 2026-04-16
- executor: Codex
- branch: codex/release-main
- related commit(s): pending
- status: completed

## Background

Sula needed a durable answer to whether an external agent workflow system such as `obra/superpowers` should be absorbed, ignored, or selectively mined for long-term value. The useful outcome was not a chat-only opinion, but a reusable proposal that clarifies where Superpowers aligns with Sula's operating-system role and where it does not.

## Analysis

- Superpowers provides a strong software-delivery methodology, but Sula is a broader project operating system that must stay portable across project types.
- The highest-value overlap is workflow governance, not platform-specific skill bootstrapping.
- The most reusable pieces are capability registration, source-first spec/plan/review artifacts, execution-mode policy, workspace isolation policy, and close-out verification.

## Chosen Plan

- record a formal proposal that explains what Sula should absorb from Superpowers
- keep the recommendation architecture-safe by rejecting mandatory adoption of strict brainstorming, strict TDD, and plugin-specific precedence rules
- propose a narrow manifest and command evolution path that fits Sula's current workflow-pack model

## Execution

- added a new reference proposal at `docs/reference/superpowers-capability-absorption-plan.md`
- updated the documentation map so the new reference surface is discoverable
- updated project traceability so the new proposal is visible from status and change records

## Verification

- reviewed Sula's current operating-model, manifest, and document-design rules before drafting the proposal
- verified the proposal against the public `obra/superpowers` repository structure and workflow descriptions
- ran `python3 scripts/sula.py memory digest --project-root .`
- ran `python3 scripts/sula.py check --project-root .`

## Rollback

- remove the new reference proposal and the associated traceability updates
- revert this change record entry if the proposal direction is superseded by a different workflow-governance design

## Data Side-effects

- no runtime behavior changed
- Sula now has a durable design reference for workflow-method absorption decisions

## Follow-up

- decide whether to implement Phase 1 manifest and schema changes from the proposal
- validate the proposed workflow contract on one real software-delivery canary repository before deeper automation

## Architecture Boundary Check

- highest rule impact: preserved; the proposal keeps Sula focused on reusable operating-system policy instead of importing one agent plugin's behavior as project truth
