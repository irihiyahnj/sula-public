# Add bootstrap site assets for the public Sula protocol

## Metadata

- date: 2026-04-11
- executor: Codex
- branch: codex/bootstrap-sula
- related commit(s): bootstrap-site batch on codex/bootstrap-sula
- status: completed

## Background

The Sula bootstrap contract needed a public-facing home. The protocol already existed in docs and CLI behavior, but there was no deployable website that a user or agent could open and immediately copy the canonical bootstrap line from.

## Analysis

- A bootstrap domain is only useful if it serves stable artifacts, not just a placeholder homepage.
- The page needs to support both human understanding and machine-assisted routing, so the minimum useful set is a landing page, a protocol page, and a machine-readable descriptor.
- The site should stay deployment-light. A static bundle is enough for the current stage.

## Chosen Plan

- add a static landing page under `site/` with copyable long-form Chinese and English bootstrap prompts
- add a `/bootstrap` page that describes the actual inspect, report, approve, adopt, validate, and result-report flow
- add `site/sula.json` as the first machine-readable bootstrap descriptor
- wire repository docs and project memory to these assets

## Execution

- created `site/index.html`, `site/bootstrap/index.html`, `site/styles.css`, `site/app.js`, `site/404.html`, and `site/sula.json`
- placed the long-form Chinese and English bootstrap prompts on both the homepage and protocol page
- described the expected pre-approval and post-approval outputs on the protocol page
- updated root docs and status tracking so the site assets are part of Sula Core's recorded operating state

## Verification

- `python3 -m json.tool site/sula.json`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/sula.py doctor --project-root . --strict`
- `python3 scripts/sula.py doctor --project-root examples/okoktoto --strict`

## Rollback

- remove the `site/` directory if the bootstrap domain strategy changes
- keep the bootstrap contract in repository docs even if the site is redesigned later

## Data Side-effects

- no runtime or production data side-effects
- repository-only static site assets were added for future public hosting

## Follow-up

- attach the domain to a static hosting target and remove the current `502`
- decide whether the future public source link should point to a new clean repository or a rewritten history
- keep the homepage prompt and `/bootstrap` behavior contract aligned with the actual CLI flow

## Architecture Boundary Check

- highest rule impact: preserved; the new site exposes the bootstrap contract more clearly without changing the managed versus project-owned boundary inside adopted repositories
