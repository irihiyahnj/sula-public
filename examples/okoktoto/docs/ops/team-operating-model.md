# OKOKTOTO v5 Team Operating Model

This file defines the default collaboration model for the repository.

The goal is that users mainly provide the request, constraints, and acceptance criteria, while the operating system carries the delivery workflow.

## Default Roles

Unless stated otherwise, Codex acts as:

1. intake owner
2. architecture gatekeeper
3. implementation owner
4. verification owner
5. release gatekeeper
6. traceability recorder

## Default Execution Flow

### 1. Intake

- read `AGENTS.md`
- audit current git state
- inspect the affected code or docs

### 2. Scope

- define what is in scope
- define what is explicitly out of scope
- decide whether the request touches the highest rule

### 3. Implement

- prefer existing architectural lanes over new ones
- keep primary orchestration logic centralized in [src/api/erpnext.ts](../src/api/erpnext.ts)
- keep shared state or durable coordination centered in [src/store/useStore.ts](../src/store/useStore.ts)
- keep the main project entry or operator-facing surface centered in [src/App.tsx](../src/App.tsx)
- if the `document-design` projection pack is enabled, follow its principles before drafting formal planning, proposal, report, process, and training docs
- classify formal document genre before drafting and keep the source file as the editable truth

### 4. Verify

- docs-only changes: verify references, traceability, and structure
- formal document changes: verify the genre-specific bundle is present and any derived deliverables stay traceable
- code changes: run validation proportional to the change
- if current-state or memory files changed, run `python3 scripts/sula.py check --project-root .` and require `SULA CHECK OK`
- release candidates: apply release and smoke checklists

### 5. Release Gate

Before recommending deployment, explicitly answer:

- can the app become unavailable
- can login or session flow break
- can primary business flows regress
- does rollout depend on external setup
- is rollback clear

### 6. Trace

- update `STATUS.md`
- update `CHANGE-RECORDS.md`
- add or update `docs/change-records/*`
- add release or incident records when risk history matters
- if a reusable Sula-managed problem was fixed locally, capture a feedback bundle before leaving the project on a one-off managed drift
- regenerate `.sula/memory-digest.md` after non-trivial changes if the project uses it
- prefer rebuilding `.sula/state/current.md`, `.sula/events/log.jsonl`, and `.sula/memory-digest.md` through Sula commands instead of editing them manually

## Definition Of Done

By default, a task is done only when:

1. the result is applied in the repository
2. verification is complete or clearly waived
3. risks and blockers are explicit
4. traceability is updated
5. the change is ready to commit and push, or the reason not to push is explicit
