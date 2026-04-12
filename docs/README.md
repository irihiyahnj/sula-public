# Sula Documentation Map

This directory organizes the reusable project operating system for `Sula`.

Sula manages the cross-project operational layer so this repository can benefit from future improvements without rewriting its local business truth.

## Recommended Reading Order

### 1. Hard Rules

- [AGENTS.md](../AGENTS.md): repository-specific hard rules
- [CODEX.md](../CODEX.md): Codex default execution adapter
- [README.md](../README.md): product and architecture overview

### 2. Team Operation

- [ops/team-operating-model.md](ops/team-operating-model.md): default request-to-delivery flow
- [ops/document-design-principles.md](ops/document-design-principles.md): formal document structure rules
- [ops/request-template.md](ops/request-template.md): efficient request format
- [ops/project-memory.md](ops/project-memory.md): how durable project memory is stored and updated
- [ops/release-checklist.md](ops/release-checklist.md): pre-push and pre-release checks
- [ops/smoke-test-checklist.md](ops/smoke-test-checklist.md): change validation checklist
- [ops/architecture-exception-register.md](ops/architecture-exception-register.md): approved architecture exceptions

### 3. System And Module Structure

- [architecture/system-map.md](architecture/system-map.md)
- [architecture/module-map.md](architecture/module-map.md)

### 4. Runbooks

- [runbooks/](runbooks)

### 5. Traceability

- [STATUS.md](../STATUS.md)
- [CHANGE-RECORDS.md](../CHANGE-RECORDS.md)
- [change-records/](change-records)
- [releases/](releases)
- [incidents/](incidents)
- [.sula/memory-digest.md](../.sula/memory-digest.md): generated summary if present

## Document Layers

| Layer | Role |
| --- | --- |
| Rules | Hard constraints and AI alignment |
| Ops | Intake, execution, verification, release, exceptions, and formal document design |
| Architecture | Durable structure and module boundaries |
| Runbooks | High-risk operational knowledge |
| Traceability | Status, decisions, release reasoning, incident context |

## Maintenance Rule

When adding durable ops, architecture, or runbook documents, update this map in the same change.
