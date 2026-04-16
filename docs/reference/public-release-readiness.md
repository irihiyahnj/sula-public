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

As of 2026-04-16:

- current tracked files do not contain obvious local absolute paths or secret material
- scanned git history does not show obvious committed secret material under common key/token patterns
- public governance files are present
- the repository history exposes local author metadata such as `jing@MacBook-Pro.local`
- the chosen default release path is now `fresh-public-repo`, so the remaining work is to publish that exported clean lineage and update the site descriptor afterward

## Release Decision

The default public-release path is now `fresh-public-repo`.

Do not make this exact repository public in place unless maintainers explicitly choose a sanitized-history rewrite and complete it successfully. The normal release path is:

1. keep this repository as the private pre-public lineage
2. export a clean tracked-file tree with `release export-public`
3. create a new public repository from that exported tree
4. point the site descriptor at that new public repository only after it exists

## Impact On Adopted Repositories

Making the Sula repository public does not automatically change or sync adopted repositories.

Adopted repositories are affected only when maintainers intentionally:

- pull new Sula changes
- run `sync`
- change their own project manifests or managed files

## Recommended Public Launch Sequence

1. choose the public repository location and license
2. run `python3 scripts/sula.py release readiness --project-root .`
3. if git-history issues remain, accept `fresh-public-repo` as the release strategy instead of trying to publish this repository in place
4. export a clean tracked-file tree with `python3 scripts/sula.py release export-public --project-root . --output /tmp/sula-public`
5. create a new public repository from that exported tree with an explicit public-safe git identity
6. update `site/sula.json` and the launcher defaults so they point at the published public repository
7. verify canary adoption still passes from the public release lineage
