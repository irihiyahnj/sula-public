# OKOKTOTO v5 Documentation Map

This directory organizes the reusable project operating system for `OKOKTOTO v5`.

Sula manages the cross-project operational layer so this repository can benefit from future improvements without rewriting its local business truth.

## Recommended Reading Order

### 1. Hard Rules

- [AGENTS.md](../AGENTS.md): repository-specific hard rules
- `CODEX.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`, and `.cursor/rules/project.mdc`: AI adapters when the `ai-tooling` projection pack is enabled
- [README.md](../README.md): product and architecture overview

### 2. Team Operation

- [ops/team-operating-model.md](ops/team-operating-model.md): default request-to-delivery flow
- `ops/document-design-principles.md`: formal document structure rules when the `document-design` projection pack is enabled
- [ops/request-template.md](ops/request-template.md): efficient request format
- [ops/project-memory.md](ops/project-memory.md): how durable project memory is stored and updated
- [ops/release-checklist.md](ops/release-checklist.md): pre-push and pre-release checks
- [ops/smoke-test-checklist.md](ops/smoke-test-checklist.md): change validation checklist
- [ops/architecture-exception-register.md](ops/architecture-exception-register.md): approved architecture exceptions

### 3. System And Module Structure

- `architecture/`: profile-specific architecture docs when the `profile-architecture` projection pack is enabled

### 4. Reference

- `reference/`: durable contracts, capability models, and design references for Sula Core

### 5. Runbooks

- `runbooks/`: operational runbooks when the `profile-runbooks` projection pack is enabled

### 6. Traceability

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
