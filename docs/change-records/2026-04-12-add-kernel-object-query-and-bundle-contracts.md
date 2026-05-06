# Add kernel object, query, and bundle contracts

## Metadata

- date: 2026-04-12
- executor: Codex
- branch: codex/bootstrap-sula
- related commit(s): pending
- status: completed

## Background

Added object catalogs, relation indexes, local query retrieval, bundle metadata, and rebuildable query cache to the Sula kernel.

## Analysis

- The first kernel milestone already established adoption, removal, source registration, and adapter catalogs.
- The next missing layer was a machine-readable project object model and a local way to query it without re-scanning the whole project mentally in every session.
- Profile adapters were present, but profile-to-bundle expression was still implicit rather than explicit.
- A rebuildable local query cache was needed so retrieval could stay dependency-light while still improving query ergonomics.

## Chosen Plan

- add `.sula/objects/catalog.json` as a derived object layer for project, state, records, and discovered sources
- add `.sula/indexes/relations.json` to link objects back to source registry entries
- add `.sula/adapters/bundles.json` to express the active profile bundle explicitly
- add `query` for local exact, structured, and lexical retrieval over kernel objects and sources
- add a rebuildable local query cache under `.sula/cache/query-index.json`

## Execution

- updated `scripts/sula.py` to generate object catalogs, relation indexes, bundle catalogs, and query caches
- added `query --project-root ... --q ...` to search kernel objects and sources
- extended kernel doctor checks to validate adapter bundles, object catalogs, and relation indexes
- extended tests to cover query results plus invalid adapter and relation references
- updated README and changelog references to include the new query and bundle capabilities

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/sula.py sync --project-root .`
- `python3 scripts/sula.py sync --project-root examples/okoktoto`
- `python3 scripts/sula.py doctor --project-root . --strict`
- `python3 scripts/sula.py doctor --project-root examples/okoktoto --strict`
- `python3 scripts/sula.py query --project-root . --q kernel --limit 5`

## Rollback

- revert this change batch
- remove the generated object, relation, bundle, and query-cache files from adopted projects if the kernel contract changes
- fall back to source registry and adapter catalog only until a replacement object/query design exists

## Data Side-effects

- adopted projects now gain additional derived kernel files under `.sula/objects/`, `.sula/indexes/relations.json`, `.sula/adapters/bundles.json`, and `.sula/cache/query-index.json`
- local query results now depend on generated kernel artifacts rather than only on human-readable project docs

## Follow-up

- decide whether future query ranking should stay lexical-first or add optional semantic expansion
- extend the object model beyond project state and records into richer task, decision, and risk extraction
- decide how much deduplication should happen between object results and source results in query output

## Architecture Boundary Check

- highest rule impact: preserved; the new kernel layers remain derived, namespaced, and removable, while project-owned truth stays in original files and records
