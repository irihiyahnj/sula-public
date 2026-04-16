# Sula Project Memory Guide

This file defines the durable memory contract for the repository.

The goal is simple:

- stable facts live in stable files
- current status lives in one place
- non-trivial decisions are written once and then linked
- releases and incidents keep their own operational history
- generated summaries never replace source documents

## Source Of Truth Layers

### Stable Project Facts

- `.sula/project.toml`
- `AGENTS.md`
- `docs/architecture/*`
- `docs/runbooks/*`

### Current State

- [STATUS.md](../STATUS.md)

### Decision And Delivery History

- [CHANGE-RECORDS.md](../CHANGE-RECORDS.md)
- [docs/change-records/](../docs/change-records)

### Release And Incident History

- [docs/releases/](../docs/releases)
- [docs/incidents/](../docs/incidents)

### Generated Recall Layer

- [.sula/memory-digest.md](../.sula/memory-digest.md)

This digest is generated for fast recall. It is not a source of truth and should not be edited manually.

## Required Update Rules

1. Keep `STATUS.md` current after non-trivial work.
2. Record non-trivial changes in `docs/change-records/` and index them from `CHANGE-RECORDS.md`.
3. If a release has material rollout risk, add a release note.
4. If an incident affects availability, permissions, data, or deployment safety, add an incident record.
5. Every architecture exception should reference a change record.
6. If work touches `STATUS.md`, `CHANGE-RECORDS.md`, `docs/change-records/*`, `.sula/state/current.md`, `.sula/events/log.jsonl`, or `.sula/memory-digest.md`, finish by running `python3 scripts/sula.py check --project-root .` and require `SULA CHECK OK`.

## Freshness Target

- `STATUS.md` should normally be updated at least every `14` days while the project is active.

## Anti-patterns

- keeping key reasoning only in chat history
- mixing temporary task notes into stable architecture docs
- writing release reasoning into commit messages only
- editing the generated memory digest instead of the underlying records
- editing generated `.sula/*` state by hand when a Sula command can rebuild it
