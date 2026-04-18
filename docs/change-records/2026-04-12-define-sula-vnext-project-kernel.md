# Define Sula vNext project kernel

## Metadata

- date: 2026-04-12
- executor: Codex
- branch: main
- related commit(s): pending
- status: proposed architecture recorded

## Background

Sula's current model is profile-driven and repository-centered. That works for managed documentation and repeatable adoption, but it does not yet reach the stronger product goal discussed in-session: a single adopted project should remain understandable across fresh sessions, different devices, and mixed source types such as code, documents, contracts, staffing notes, and project decisions.

The strongest requirement that emerged was:

- extreme portability must mean extreme removability

A second hard requirement followed immediately after:

- an already-running project must be adoptable in place, even when it does not use Git

That requirement forces a more disciplined kernel design than "add more profiles". The system needs a generic base that can attach to unknown projects safely, maintain scientific indexing and traceability, and detach without leaving hard-to-remove operational residue.

## Analysis

- Current Sula supports only `react-frontend-erpnext` and `sula-core` as adoption-time profiles.
- Unknown project types currently block at profile detection rather than falling back to a safe generic kernel.
- Durable memory exists, but it is still primarily expressed through repository-facing documents rather than a richer machine-readable project kernel.
- The current model is good enough for repository operating system management, but not yet for cross-session single-project continuity across multiple object types.

## Chosen Plan

- Record a formal vNext architecture target before implementing scattered tactical changes.
- Define `generic-project` as the mandatory base adapter for every future adoption.
- Reframe profiles as adapter bundles rather than hard admission gates.
- Make `.sula/` the canonical home for machine-readable kernel state so adoption, portability, and removal stay bounded.
- Treat exported human-readable files as supported views, not the only structured state.
- Treat Git as an optional adapter, not as a prerequisite for project adoption.

## Execution

- added `docs/reference/sula-vnext-project-kernel.md`
- documented the future kernel, object model, event model, index model, adapter strategy, adoption flow, and removal flow
- documented explicit anti-bloat and anti-lock-in rules
- documented removal as a first-class design requirement rather than a rollback afterthought
- documented in-progress and non-Git adoption as first-class requirements
- updated root references, docs map, status, and change-record index to make this architecture discoverable

## Verification

- reviewed current README, philosophy, memory-model, and status docs to keep the new record aligned with current stated behavior
- limited the change to architecture and traceability documents so implementation claims remain accurate

## Rollback

- remove `docs/reference/sula-vnext-project-kernel.md`
- remove this change record and its index references
- revert the related README and status wording if the architecture direction changes

## Data Side-effects

- none at runtime
- documentation only

## Follow-up

- define the concrete `.sula/` kernel layout and compatibility contract
- design the first `generic-project` adoption report format
- design the `remove --dry-run` and `remove --approve` flows before broadening adoption scope
- decide which current human-readable exports remain canonical and which become derived views
- test the future kernel contract against both Git and non-Git in-progress projects

## Architecture Boundary Check

- highest rule impact: preserved; this record expands the future operating-system model without collapsing project-owned truth into centrally managed templates
