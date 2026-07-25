# Sula Module Map

This profile describes the durable modules inside Sula Core.

## Core Modules

### CLI And Rendering

- primary entry: [scripts/sula.py](../../scripts/sula.py)
- wrappers: `scripts/sula-adopt`, `scripts/sula-init`, `scripts/sula-sync`, `scripts/sula-doctor`, `scripts/sula-record`, `scripts/sula-memory`

### Managed Template System

- core templates: `templates/core/`
- profile templates: `templates/profiles/`

### Governance And Registry

- rollout registry: [registry/adopted-projects.toml](../../registry/adopted-projects.toml)
- release and version docs: `docs/release-process.md`, `docs/versioning.md`, `CHANGELOG.md`

### Canary Validation

- example consumer: `examples/okoktoto/`
- operator-facing overview: [README.md](../../README.md)

## Modification Rule

When changing one module, review the sync impact on:

1. adopted repositories
2. the in-repo canary
3. the release and registry metadata
