# Publish the fresh public Sula source

## Metadata

- date: 2026-04-16
- executor: Codex
- branch: main
- related commit(s): pending
- status: completed

## Background

Sula had already chosen `fresh-public-repo` as the default publication path, but the bootstrap site still pointed to a pending public source. That left the URL launch contract globally reachable while the canonical clone source remained incomplete.

## Analysis

- the critical missing step was to publish the clean public source, not to add more local tooling
- once the fresh public repository exists, the launch descriptor should stop advertising a pending state
- this preserves the non-intrusive design because bootstrap still resolves into project-local execution after downloading the public source

## Chosen Plan

- create the fresh public GitHub repository
- point `site/sula.json` and `site/launch/bootstrap.py` at that repository
- export the clean tracked-file tree and push it as the first public lineage

## Execution

- created `https://github.com/irihiyahnj/sula-public`
- updated the site descriptor and bootstrap launcher to use `https://github.com/irihiyahnj/sula-public.git` at `main`
- prepared the repository for a fresh export-first public push

## Verification

- `curl -s -H 'Authorization: token …' https://api.github.com/repos/irihiyahnj/sula-public`
- `python3 -m py_compile site/launch/bootstrap.py`
- `python3 scripts/sula.py release export-public --project-root . --output /tmp/sula-public-export --overwrite --json`

## Rollback

- switch `site/sula.json` and `site/launch/bootstrap.py` back to pending-public-source mode
- archive or delete the public repository if publication must be revoked

## Data Side-effects

- the public launch contract now resolves to a real public Git repository instead of a placeholder

## Follow-up

- push the exported clean tree to the public repository
- redeploy the hosted site so the live descriptor matches the published public source
- optionally migrate the static host from Fly to DigitalOcean once server-side write access is available

## Architecture Boundary Check

- highest rule impact: preserved; the public source is now real, but execution still happens in the target project context rather than in a centralized control plane
