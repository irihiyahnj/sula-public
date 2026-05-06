# Sula Feedback Bundle Lifecycle

This document defines how reusable fixes move from one adopted project back into Sula Core and then out again through normal versioned sync.

## Why This Exists

Adopted projects are allowed to stay productive. That means a team may patch a locally synced Sula-managed file when a real usage problem blocks work.

What must not happen is confusing that local patch with an upstream Sula Core change.

The lifecycle below preserves the boundary:

- adopted projects may change their local managed render to stay unblocked
- adopted projects must not treat that local drift as a direct write into Sula Core
- Sula Core remains the only place where reusable upstream decisions are accepted or rejected
- downstream rollout still happens through tagged versions plus `sync`, not silent remote mutation

## Roles

### Adopted Project

The project can:

- capture reusable feedback with `feedback capture`
- keep its own project-owned truth local
- keep a temporary local patch while waiting for upstream review

The project cannot:

- merge directly into Sula Core unless it has separate repository permissions
- assume its local managed drift is automatically canonical for all projects

### Sula Core

Sula Core can:

- ingest bundles into `registry/feedback/inbox/`
- review, accept, defer, reject, or mark them released
- absorb approved changes into `templates/`, scripts, docs, and releases
- distribute the approved change later through normal versioned sync

## Lifecycle

1. A project discovers a reusable Sula issue while working locally.
2. The project may apply a local managed-file fix immediately.
3. The project runs `feedback capture` and produces:
   - `bundle.json`
   - `doctor.json`
   - `sync-plan.json`
   - `changes.patch`
   - local and rendered snapshots for drifted managed files
   - a portable zip archive under `.sula/feedback/outbox/archives/`
4. Sula Core runs `feedback ingest` against that bundle.
5. Sula Core reviews the item and records a decision with `feedback decide`.
6. If accepted, maintainers implement the reusable change in Sula Core itself.
7. The accepted change is released under a new Sula version.
8. Adopted projects pick up the change later through `sync --dry-run`, `sync`, and `doctor --strict`.

## Bundle Contract

Project-side feedback bundles live under:

```text
.sula/feedback/outbox/
  bundles/<feedback-id>/
  archives/<feedback-id>.zip
```

Core-side ingested bundles live under:

```text
registry/feedback/
  catalog.json
  inbox/<feedback-id>/
```

`bundle.json` should carry at least:

- bundle schema version
- feedback id, title, summary, kind, severity
- reusable rationale
- source project identity and profile
- locked Sula version and capture-time Sula version
- current doctor state
- current managed sync plan
- drifted managed-file snapshots and diffs

## Decision States

Current Sula Core decisions are:

- `open`: captured and ingested, awaiting review
- `triaged`: reviewed and classified, but not yet accepted or rejected
- `accepted`: approved for upstream implementation
- `deferred`: valuable, but intentionally postponed
- `rejected`: should remain project-local or otherwise not enter Sula Core
- `released`: shipped in a published Sula version whose canonical Git repository state is ready for downstream sync

## Release Rule

Accepted feedback does not change other projects immediately.

It must still pass the normal Sula Core path:

- implement in Sula Core
- update docs and changelog
- run canary verification
- release a version
- let adopted projects sync intentionally

This keeps Sula portable, reviewable, and removable instead of turning it into an opaque remote-control layer.
