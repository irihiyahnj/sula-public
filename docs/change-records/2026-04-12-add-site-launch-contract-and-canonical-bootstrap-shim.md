# Add site launch contract and canonical bootstrap shim

## Metadata

- date: 2026-04-12
- executor: Codex
- branch: codex/bootstrap-sula
- related commit(s): pending
- status: completed

## Background

Sula's public site still acted mostly like a documentation homepage. It described the protocol, but it did not actually resolve the main startup pain: a new session could read the site and still fail because there was no stable local `sula` command, no installable package, and no clear launcher URL to follow.

## Analysis

- A site contract is only complete if it includes both human-readable instructions and a machine-consumable launcher path.
- The site already had `/bootstrap/` and `sula.json`, but startup still depended on guessing local commands or package names.
- The missing piece was a canonical bootstrap shim that could resolve vendored Sula, an explicit local source checkout, or clone the canonical source into a stable local directory.

## Chosen Plan

- add `/launch/` as the short, URL-first contract page
- add `site/launch/bootstrap.py` as the canonical bootstrap shim
- upgrade `site/sula.json` with launcher metadata, source ref, and no-global-lookup rules
- retarget homepage prompts to the shorter launch URL

## Execution

- created `site/launch/index.html` as the canonical launch contract page
- created `site/launch/bootstrap.py` with vendored-source, explicit-source-dir, and cloned-source resolution modes
- updated `site/index.html` and `site/bootstrap/index.html` to point to the new launch contract
- upgraded `site/sula.json` to describe the canonical launcher URLs and startup rules
- added CLI tests for the site bootstrap shim using a local source checkout

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py site/launch/bootstrap.py`
- `python3 -m json.tool site/sula.json`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_site_bootstrap_uses_local_source_to_onboard_project tests.test_sula.SulaCliTests.test_site_bootstrap_reviews_existing_consumer -v`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/sula.py sync --project-root .`
- `python3 scripts/sula.py sync --project-root examples/okoktoto`
- `python3 scripts/sula.py doctor --project-root . --strict`
- `python3 scripts/sula.py doctor --project-root examples/okoktoto --strict`

## Rollback

- remove `site/launch/` and revert the site prompt changes if the launch strategy changes
- keep `sula.json` and the older bootstrap page if the team needs to fall back to a docs-only public contract temporarily
- revert the launcher tests if the canonical shim path is redesigned

## Data Side-effects

- no project data side-effects
- static site assets and one launcher script were added to the repository
- future public deployments can now host a real startup path instead of just explanatory pages

## Follow-up

- decide whether the bootstrap shim should later install from releases instead of cloning a branch ref
- add a tiny shell shim only if real environments show Python-first launch is insufficient
- validate the hosted `/launch/` and `/launch/bootstrap.py` pages against an external session that has no local Sula source at all

## Architecture Boundary Check

- highest rule impact: preserved; the new site launcher only improves discovery and source resolution, and does not alter the managed versus project-owned contract inside adopted projects
