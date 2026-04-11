# Sula Team Operating Model

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
- keep primary orchestration logic centralized in [scripts/sula.py](../scripts/sula.py)
- keep shared state or durable coordination centered in [registry/adopted-projects.toml](../registry/adopted-projects.toml)
- keep the main project entry or operator-facing surface centered in [README.md](../README.md)

### 4. Verify

- docs-only changes: verify references, traceability, and structure
- code changes: run validation proportional to the change
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
- regenerate `.sula/memory-digest.md` after non-trivial changes if the project uses it

## Definition Of Done

By default, a task is done only when:

1. the result is applied in the repository
2. verification is complete or clearly waived
3. risks and blockers are explicit
4. traceability is updated
5. the change is ready to commit and push, or the reason not to push is explicit
