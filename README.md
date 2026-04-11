# Sula

Sula is a reusable project operating system for AI-native software teams.

It standardizes how projects define rules, accept requests, execute work, verify changes, ship releases, and keep durable traceability across repositories.

Sula is not a product template for one stack. It is a coordination layer with:

- a reusable documentation and operations core
- profile-specific templates for project families
- a project manifest that captures each repository's facts
- an inspect-report-approve adoption flow for one-sentence onboarding
- scripts to initialize, sync, and audit project adoption
- a governed rollout path for sync impact and release discipline
- a single-project memory model for durable status, decisions, releases, and incidents

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

Current profiles:

- `react-frontend-erpnext`
- `sula-core`

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
registry/
scripts/
tests/
templates/
  core/
    managed/
    scaffold/
  profiles/
    react-frontend-erpnext/
      managed/
      scaffold/
    sula-core/
      managed/
      scaffold/
examples/
```

## Quick Start

### Adopt Sula into a repository

In a live agent session, the target request should be as short as:

```text
Please take over this repository using the Sula bootstrap protocol: first read https://sula.1stp.monster/, inspect the repo and produce an adoption report, wait for my approval, then adopt it and report the changes, risks, and how to use it.
```

The CLI equivalent is:

```bash
python3 scripts/sula.py adopt --project-root /path/to/project
python3 scripts/sula.py adopt --project-root /path/to/project --approve
```

The first command inspects the repository, detects the likely profile, and prints an approval-ready report. The second command applies the adoption, validates the result with `doctor --strict`, creates initial traceability, and prints the follow-up usage commands.

Use `init` only when you need low-level manual control over manifest values before the approval-based adoption flow can infer them safely.

### Bootstrap site assets

The public bootstrap site lives in this repository under `site/`:

- `site/index.html`: landing page with the canonical copyable bootstrap lines
- `site/bootstrap/index.html`: behavioral contract for inspect, report, approve, adopt
- `site/sula.json`: machine-readable bootstrap descriptor

These assets are designed for eventual hosting at `https://sula.1stp.monster/`.

Current deployment state:

- live Fly preview: `https://sula.fly.dev/`
- live custom domain: `https://sula.1stp.monster/`
- machine-readable descriptor: `https://sula.1stp.monster/sula.json`
- custom domain routing: active through Fly-managed DNS targets

### Sync improvements into an existing project

```bash
python3 scripts/sula.py sync --project-root /path/to/project --dry-run
python3 scripts/sula.py sync --project-root /path/to/project
python3 scripts/sula.py doctor --project-root /path/to/project
python3 scripts/sula.py doctor --project-root /path/to/project --strict
```

Use `--dry-run` before every real sync so you can review which managed files would change and how risky they are.

### Create durable project memory

```bash
python3 scripts/sula.py record new \
  --project-root /path/to/project \
  --title "Explain the non-trivial change"

python3 scripts/sula.py memory digest --project-root /path/to/project
```

This creates durable project memory without mixing managed operating-system files with project-owned history.

## Current Version

Sula version: `0.4.0`

Versioning rules are in [docs/versioning.md](docs/versioning.md).

## Operating Sula Core

Sula itself is a maintained project. Before releasing changes that will later sync into adopted repositories:

1. Run `python3 -m unittest discover -s tests -v`
2. Review [CHANGELOG.md](CHANGELOG.md) and capture sync impact
3. Review [registry/adopted-projects.toml](registry/adopted-projects.toml)
4. Dry-run sync against canary projects before broad rollout
5. Regenerate committed canary memory digests if the project policy uses them

Release discipline and impact rules live in:

- [docs/README.md](docs/README.md)
- [docs/release-process.md](docs/release-process.md)
- [docs/reference/project-memory-model.md](docs/reference/project-memory-model.md)
- [docs/reference/sync-impact-model.md](docs/reference/sync-impact-model.md)
- [docs/reference/adoption-registry.md](docs/reference/adoption-registry.md)

## Recommended Adoption Order

1. Adopt Sula Core
2. Run `adopt` to inspect and report
3. Approve the adoption and review scaffold files
4. Commit the generated operating system to the project
5. Use `sync --dry-run` for future shared improvements

## References

- [docs/philosophy.md](docs/philosophy.md)
- [docs/README.md](docs/README.md)
- [docs/adoption-playbook.md](docs/adoption-playbook.md)
- [docs/reference/adoption-agent.md](docs/reference/adoption-agent.md)
- [docs/reference/public-release-readiness.md](docs/reference/public-release-readiness.md)
- [docs/release-process.md](docs/release-process.md)
- [docs/versioning.md](docs/versioning.md)
- [docs/reference/project-memory-model.md](docs/reference/project-memory-model.md)
- [docs/reference/sync-impact-model.md](docs/reference/sync-impact-model.md)
- [docs/reference/adoption-registry.md](docs/reference/adoption-registry.md)
- [docs/reference/project-manifest.md](docs/reference/project-manifest.md)
- [schema/project.schema.json](schema/project.schema.json)
- [schema/project.example.toml](schema/project.example.toml)
- [registry/adopted-projects.toml](registry/adopted-projects.toml)
- [site/index.html](site/index.html)
- [site/bootstrap/index.html](site/bootstrap/index.html)
- [site/sula.json](site/sula.json)

## Project Governance

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [SECURITY.md](SECURITY.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
