# Sula

Sula is a reusable project operating system for AI-native software teams.

It standardizes how projects define rules, accept requests, execute work, verify changes, ship releases, and keep durable traceability across repositories.

Sula is not a product template for one stack. It is a coordination layer with:

- a reusable documentation and operations core
- profile-specific templates for project families
- a project manifest that captures each repository's facts
- scripts to initialize, sync, and audit project adoption

## What Sula Solves

Without a system, every repository drifts:

- AI tools each get slightly different instructions
- release checks live in people's heads
- architecture rules are implicit until they are violated
- status and change records become inconsistent
- improvements made in one project do not reach the others

Sula makes those concerns portable.

## Core Concepts

### 1. Sula Core

Reusable docs and tool adapters that should evolve once and benefit many projects:

- `CODEX.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.github/copilot-instructions.md`
- `.cursor/rules/project.mdc`
- `docs/README.md`
- `docs/ops/*`

### 2. Profile

A profile is a reusable project-family layer.

Current profile:

- `react-frontend-erpnext`

Profiles provide:

- managed architecture docs
- managed runbooks
- scaffold starters for project-owned files

### 3. Project Manifest

Each adopted project keeps a local `.sula/project.toml` that defines:

- project identity
- branch model
- highest architecture rule
- build and verification commands
- key source paths
- deploy expectations
- auth/session semantics

### 4. Managed vs Scaffold Files

Sula distinguishes two classes of files:

- managed files: overwritten by `sync`
- scaffold files: generated once if missing, then owned by the project

This avoids centralizing project truth that should remain local.

## Repository Layout

```text
docs/
  philosophy.md
  adoption-playbook.md
  versioning.md
  reference/
schema/
scripts/
templates/
  core/
    managed/
  profiles/
    react-frontend-erpnext/
      managed/
      scaffold/
examples/
```

## Quick Start

### Create a new project from Sula

1. Create or choose a repository to adopt.
2. Copy or clone this repository locally.
3. Run:

```bash
python3 scripts/sula.py init \
  --project-root /path/to/project \
  --name "My Project" \
  --slug "my-project" \
  --description "Short project description" \
  --profile react-frontend-erpnext
```

4. Review the generated scaffold files and fill in project-specific rules.
5. Commit the adoption inside the target project.

### Sync improvements into an existing project

```bash
python3 scripts/sula.py sync --project-root /path/to/project
python3 scripts/sula.py doctor --project-root /path/to/project
```

## Current Version

Sula version: `0.1.0`

Versioning rules are in [docs/versioning.md](docs/versioning.md).

## Recommended Adoption Order

1. Adopt Sula Core
2. Add a profile manifest
3. Review scaffold files
4. Commit the generated operating system to the project
5. Use `sync` for future shared improvements

## References

- [docs/philosophy.md](docs/philosophy.md)
- [docs/adoption-playbook.md](docs/adoption-playbook.md)
- [docs/versioning.md](docs/versioning.md)
- [docs/reference/project-manifest.md](docs/reference/project-manifest.md)
- [schema/project.schema.json](schema/project.schema.json)
- [schema/project.example.toml](schema/project.example.toml)
