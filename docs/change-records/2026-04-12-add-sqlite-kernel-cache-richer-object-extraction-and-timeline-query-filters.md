# Add SQLite kernel cache, richer object extraction, and timeline query filters

## Metadata

- date: 2026-04-12
- executor: Codex
- branch: codex/bootstrap-sula
- related commit(s): pending
- status: completed

## Background

The first kernel/query milestone established object catalogs, relation indexes, and lexical local retrieval, but it still lacked a scalable local cache, richer object kinds, and stronger structured query controls.

## Analysis

- JSON catalogs remain the right truth-adjacent export format, but larger projects need a more efficient local query surface than reparsing JSON for every lookup.
- The vNext kernel target explicitly called for richer object kinds such as task, decision, risk, person, agreement, and milestone.
- Query needed stronger structured filters and a true timeline mode so new sessions can recover project state faster without reading entire documents.
- The cache still had to stay disposable and rebuildable so portability and removability remain intact.

## Chosen Plan

- add `.sula/cache/kernel.db` as a rebuildable local SQLite index over sources, objects, relations, events, and query documents
- enrich object extraction from status sections, records, and markdown source sections
- extend `query` with adapter, status, path-prefix, date-range, and timeline controls
- keep JSON catalogs and markdown exports as the durable truth/export layers while SQLite remains a derived cache

## Execution

- updated `scripts/sula.py` to rebuild `.sula/cache/kernel.db` during kernel refresh
- extended doctor checks to validate the SQLite cache shape
- added richer object extraction for `task`, `decision`, `risk`, `person`, `agreement`, and `milestone`
- upgraded `query` to support structured filters, timeline output, lower-noise ranking that suppresses duplicate low-signal source/document hits when richer object results already exist for the same path, and path-level family compaction that exposes `related_kinds` while keeping `--kind` queries literal
- expanded tests to cover the SQLite cache, richer object kinds, and filtered timeline queries
- updated README, status, changelog, and change-record indexes to reflect the new retrieval contract

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/sula.py sync --project-root .`
- `python3 scripts/sula.py sync --project-root examples/okoktoto`
- `python3 scripts/sula.py doctor --project-root . --strict`
- `python3 scripts/sula.py doctor --project-root examples/okoktoto --strict`
- `python3 scripts/sula.py query --project-root . --q kernel --limit 5`
- `python3 scripts/sula.py query --project-root . --q \"\" --timeline --limit 10`

## Rollback

- revert this change batch
- remove `.sula/cache/kernel.db` from adopted projects
- fall back to JSON-backed query and the prior object model until a replacement local cache exists

## Data Side-effects

- adopted projects now gain `.sula/cache/kernel.db` as a rebuildable local index
- object catalogs can now surface richer project structure without rewriting project-owned documents
- query results can now expose dated timeline entries and stronger filtered slices of local kernel state

## Follow-up

- improve result ranking and deduplication between source, object, and event results
- decide whether optional semantic expansion is worthwhile on top of the current lexical-plus-structured baseline
- continue moving profile-specific behavior toward reusable adapter composition

## Architecture Boundary Check

- highest rule impact: preserved; SQLite remains a disposable cache, while project-owned truth stays in project files and Sula-managed exports remain namespaced and removable
