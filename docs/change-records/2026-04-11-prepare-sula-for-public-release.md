# Prepare Sula for public release

## Metadata

- date: 2026-04-11
- executor: Codex
- branch: codex/bootstrap-sula
- related commit(s): public-readiness batch on codex/bootstrap-sula
- status: completed

## Background

Sula is being prepared for eventual public release. That requires more than working software: the repository needs governance files, consistent public-facing guidance, and a documented safety decision about whether the existing git history is suitable for publication.

## Analysis

- Public readiness is partly a working-tree problem and partly a history problem.
- The current tracked files were audit-scanned for obvious absolute paths, secret material, and inconsistent public bootstrap wording.
- The git history still contains unrelated pre-Sula application history and local author metadata, which is acceptable for private work but below the bar for a clean public release.

## Chosen Plan

- add the open-source governance files expected from a high-quality public project
- document public-release readiness and history requirements explicitly
- clean up traceability placeholders that would look unfinished in a public repository
- avoid rewriting history silently inside this maintenance branch

## Execution

- added `CONTRIBUTING.md`, `SECURITY.md`, and `CODE_OF_CONDUCT.md`
- added issue templates and a pull request template under `.github/`
- added `docs/reference/public-release-readiness.md`
- updated `README.md` to link governance and public-release references
- replaced `pending local commit` placeholders in durable records with real or stable references

## Verification

- searched tracked files for local absolute paths and secret-like patterns
- searched git history for local-path, secret, and author-metadata risk signals
- reviewed the current repo layout for public project governance gaps
- ran repository validation after the documentation and governance changes

## Rollback

- remove the public-governance files if Sula remains private-only
- keep the public-release-readiness document as the source of truth for future launch work if governance docs are retained

## Data Side-effects

- no runtime or production data side-effects
- repository-only governance and documentation files were added

## Follow-up

- decide the public license explicitly before launch
- publish from a clean Sula-only history rather than exposing the current historical lineage as-is
- replace repository URLs with the canonical bootstrap domain once it exists publicly

## Architecture Boundary Check

- highest rule impact: preserved; these changes improve release governance without changing the boundary between centrally managed operating-system files and project-owned business truth
