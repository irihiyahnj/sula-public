# Sula Public Release Readiness

This document defines the minimum bar before opening the Sula repository to the public.

## Working Tree Checks

Before making the repository public, confirm:

- no local absolute paths remain in tracked files
- no personal cloud-drive references remain in tracked files
- no secrets or private keys exist in tracked files
- public-facing docs describe the current bootstrap flow consistently
- contribution, security, conduct, issue, and PR workflows are present

## History Checks

A clean working tree is not enough. Review the full git history for:

- unrelated pre-Sula project history
- accidentally committed credentials, tokens, or private configuration
- local machine identifiers in commit metadata

## Current Audit Result

As of 2026-04-11:

- current tracked files do not contain obvious local absolute paths or secret material
- scanned git history does not show obvious committed secret material under common key/token patterns
- public governance files are present
- the repository history still contains unrelated pre-Sula application history
- the repository history exposes local author metadata such as `jing@MacBook-Pro.local`

## Release Decision

Do not make this exact repository public in place until one of these is true:

1. the git history is rewritten and sanitized
2. a new public repository is created from a clean Sula-only history

## Impact On Adopted Repositories

Making the Sula repository public does not automatically change or sync adopted repositories.

Adopted repositories are affected only when maintainers intentionally:

- pull new Sula changes
- run `sync`
- change their own project manifests or managed files

## Recommended Public Launch Sequence

1. choose the public repository location and license
2. run `python3 scripts/sula.py release readiness --project-root .`
3. export a clean tracked-file tree with `python3 scripts/sula.py release export-public --project-root . --output /tmp/sula-public`
4. publish from that clean Sula-only tree in a fresh public repository or after a sanitized-history rewrite
5. point docs and the future bootstrap domain at that public source
6. verify canary adoption still passes from the public release lineage
