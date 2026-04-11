# AGENTS.md

This file is the primary instruction source for AI coding agents working in the Sula repository.

## Repository Identity

- Repository root is `Sula`.
- Sula is a reusable project operating system, not a single application product.
- Sula manages reusable ops structure, profiles, manifests, and sync tooling.

## Highest Rule

- Preserve the split between centrally managed operating-system files and project-owned business truth.
- Do not turn Sula into a one-project template repository.

## Working Rules

- Keep Sula improvements portable across adopted projects.
- Prefer profile-level abstractions over project-specific wording.
- Keep bootstrap scripts dependency-light.
- Do not make Python 3.11+ or third-party packages mandatory without a strong reason.
- When changing managed templates, consider sync impact on existing projects.
- When changing scaffold templates, keep them as starters, not as centrally enforced truth.
- Update Sula docs when introducing new profiles, manifest fields, or sync behavior.

## Current Scope

- Core managed files
- `react-frontend-erpnext` profile
- `sula-core` profile
- project manifest schema and example
- `adopt`, `init`, `sync`, `doctor`, `record`, and `memory digest` commands

## Out Of Scope For Now

- automatic GitHub app integration
- remote sync service
- stack profiles not yet backed by real project use
