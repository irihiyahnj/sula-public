# Choose fresh public repository as the default release path

## Metadata

- date: 2026-04-16
- executor: Codex
- branch: main
- related commit(s): pending
- status: completed

## Background

Sula had already implemented release-readiness auditing and clean-tree export, but the public release decision still lived in a vague two-option state. The site descriptor and launcher continued to imply that a canonical public repository already existed, which was misleading because the real remaining blocker was historical lineage in this repository.

## Analysis

- the repository history issue is structural, not a content-quality problem
- the least risky path is to keep this repository private and publish from a fresh exported tree
- the site contract should be honest before it is convenient; an unpublished public source must not be represented as canonical

## Chosen Plan

- promote `fresh-public-repo` from fallback to default public-release strategy
- make the launcher fail clearly when no published public source exists instead of guessing a pre-public repository
- align release and smoke-test docs with the export-first publication path

## Execution

- updated `site/sula.json` to mark the public source as pending and record `fresh-public-repo` as the chosen strategy
- updated `site/launch/bootstrap.py` so clone-based launch requires an actual published public source instead of guessing old repository coordinates
- extended `release readiness` and `release export-public` output so maintainers get explicit next steps for creating the fresh public repository
- updated status, release docs, and smoke-test guidance to treat the fresh public repository as the normal publication path

## Verification

- `python3 -m py_compile scripts/sula.py site/launch/bootstrap.py tests/test_sula.py`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_site_bootstrap_requires_explicit_source_until_public_repo_exists -v`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_release_export_public_creates_clean_tree_manifest -v`
- `python3 scripts/sula.py release readiness --project-root . --json`
- `python3 scripts/sula.py release export-public --project-root . --output /tmp/sula-public-export --overwrite --json`

## Rollback

- restore the previous site descriptor and bootstrap defaults that point at the pre-public repository coordinates
- remove the new release-readiness recommendations if maintainers later choose a sanitized-history rewrite as the primary path
- revert the status and doc updates that describe `fresh-public-repo` as default

## Data Side-effects

- launch metadata now distinguishes unpublished public-source state from published canonical-source state
- public exports now include stronger initialization guidance for creating the fresh public repository

## Follow-up

- create the actual public repository from the exported clean tree
- configure the public repository with an explicit public-safe git identity before its first commit
- update `site/sula.json` and launcher defaults to the real public repository URL and ref after publication

## Architecture Boundary Check

- highest rule impact: preserved; the public launch contract is now more explicit about where truth lives and refuses to invent a canonical source before one exists
