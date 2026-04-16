# Sula vNext Project Kernel

## Status

- state: proposed target architecture
- intent: make one project understandable and manageable across sessions, devices, and source types
- non-goal for this document: claiming that the current CLI already implements this design

## Why This Exists

Current Sula is strong at repository adoption, managed documentation, and profile-driven rollout. That is useful, but it does not yet satisfy the stronger goal:

- a project that is already in progress should still be adoptable without reset or restructuring
- any single project should be able to adopt Sula with very low effort
- the same project should remain understandable across fresh sessions and different devices
- contracts, people, decisions, tasks, and code should be first-class project objects, not separate systems
- the project should be easy to detach from Sula later

The key refinement is:

- extreme portability means extreme removability

If Sula can be attached easily but not removed cleanly, it is not portable enough for real use.

## Product Goal

Sula vNext should behave like a single-project operating kernel.

That kernel should let a user start from one sentence or one command, attach Sula to the project, preserve the project's truth sources, build structured recall and indexing, and keep future sessions aligned without depending on prior chat windows.

## Design Principles

### 1. Plug-And-Play First

Any project should be able to adopt a minimal `generic-project` kernel without first matching a specialized profile.

That includes:

- brand-new projects
- messy in-progress projects
- projects with mixed source types
- projects that do not use Git at all

### 2. Portable Means Removable

Every Sula-owned write should be:

- easy to identify
- easy to review before creation
- easy to remove later
- safe to rebuild if it is derived state

### 3. One Truth Source Per Concern

Sula must not replace the project's real sources of truth.

- code stays in code files
- contracts stay in their source documents or registered external references
- project state stays in explicit state records
- generated summaries never become canonical truth

### 4. Local-First, Dependency-Light

The default system should work from the project directory plus Python standard library capabilities.

- no mandatory hosted database
- no mandatory remote sync service
- no mandatory third-party package
- no mandatory Git repository

### 5. Scientific Retrieval

The system must prefer reproducible retrieval over vague recall.

- exact path and anchor lookup before semantic guessing
- structured query fields before free-form synthesis
- freshness tracking on state and indexes
- answerable provenance for every non-trivial claim

### 6. Bounded Growth

Indexes, summaries, and caches must have explicit size and rebuild rules so the project does not accumulate uncontrolled storage or latency costs.

## Non-Goals

Sula vNext should not:

- turn chat transcripts into the primary truth source
- force all projects into a single stack-specific template
- require copying all source content into a central database
- require semantic embeddings for core functionality
- require Git before a project can adopt the kernel
- mutate project-owned truth silently

## Architecture Layers

### Truth Layer

This is the project's real source material.

Typical truth sources include:

- repository files
- plain workspace files outside Git
- project documents
- contract files or registered external contract references
- staffing notes
- meeting notes
- release records
- issue trackers or external systems referenced through source descriptors

Sula should register these sources, not replace them.

### Kernel Layer

All machine-readable Sula state should live under a single namespaced directory:

```text
.sula/
  project.toml
  kernel.toml
  sources/
  state/
  events/
  indexes/
  cache/
  exports/
```

Design rule:

- if it is Sula-owned machine state, it belongs under `.sula/`

This keeps adoption review, migration, backup, and removal simple.

### Object Layer

Sula should use a generic object model for one project.

Core object kinds:

- `source`
- `file`
- `document`
- `task`
- `decision`
- `risk`
- `person`
- `agreement`
- `milestone`
- `event`
- `session`

Important boundary:

- a contract is not a root operating mode
- it is one kind of project object, usually represented as `agreement`

Every object should support:

- stable `id`
- `kind`
- title or label
- status
- timestamps
- tags
- source anchors
- related object ids
- freshness metadata

### Event Layer

Cross-session continuity should be driven by an append-only event ledger, not by old chat transcripts.

Event types should cover at least:

- source registered
- object created
- object updated
- task moved
- decision made
- risk raised
- checkpoint recorded
- export regenerated

Canonical shape:

- append events to `.sula/events/`
- keep events immutable after write
- derive summaries and current views from events plus source material

### State Layer

Projects still need a direct "what is happening now" view.

Sula should keep a canonical current-state snapshot in `.sula/state/current.*` with fields such as:

- project summary
- active workstreams
- open blockers
- next actions
- owners or responsible roles
- current risks
- last-refresh timestamp

This snapshot is canonical for current state, but meaningful changes should also emit events.

### Index Layer

The index layer is derived state.

It exists to make retrieval fast and precise, but it must always be safe to delete and rebuild.

Primary index families:

- source/path index
- object index
- relation index
- event timeline index
- anchor index
- lexical full-text index
- optional semantic retrieval cache

Recommended implementation direction:

- canonical state stays in text files such as TOML, JSON, Markdown, or JSONL
- derived indexes can use a local SQLite file under `.sula/cache/` because SQLite ships with Python and is easy to delete or move
- semantic caches remain optional and disposable

### Export Layer

Human-readable project views should be exportable from the kernel.

Examples:

- `STATUS.md`
- `CHANGE-RECORDS.md`
- `docs/change-records/*`
- `.sula/memory-digest.md`

In vNext, these exports should be treated as views over kernel state plus source material, not as the only machine-readable representation.

## Adapters And Profiles

Sula vNext should separate the minimal kernel from optional adapters.

### Mandatory Base Adapter

Every project gets:

- `generic-project`

This adapter provides:

- source registration
- object and event storage
- current-state snapshots
- exact and structured retrieval
- export hooks for human-readable views

### Optional Adapters

Examples:

- `repo`
- `docs`
- `contracts`
- `people`
- `timeline`
- `deploy`
- `tickets`

An adapter should define:

- how to discover relevant sources
- how to anchor references
- what object kinds it extracts or maintains
- what health checks it adds
- what exports it can generate
- how sources are bound back to the adapter contract

Important rule:

- `repo` is an optional adapter, not a universal requirement
- projects without Git should still adopt through `generic-project` plus non-repo adapters

### Profiles Become Bundles

Current profiles should evolve into named adapter bundles.

Examples:

- `react-frontend-erpnext` becomes a bundle layered on top of `generic-project + repo + deploy + docs`
- `sula-core` becomes a bundle for operating-system repositories

This preserves reuse without blocking unknown project types.

## Source Registration And Anchors

The kernel must be able to answer, "Where did this come from?"

Each registered source should have:

- a stable source id
- a source kind
- a locator
- optional revision metadata
- optional trust level
- anchor rules

Anchor examples:

- local file line ranges
- Markdown headings
- section ids in imported documents
- external document ids plus paragraph or block references
- record ids in structured logs

Git-specific anchors such as commit hashes or blame metadata are useful when available, but they must be treated as optional enrichments rather than baseline requirements.

Non-trivial responses should cite anchors whenever possible.

## Retrieval Model

Sula should not rely on one retrieval strategy.

The retrieval order should be:

1. exact identity lookup
2. structured field filters
3. path and anchor lookup
4. lexical full-text retrieval
5. semantic retrieval when needed
6. synthesis with cited anchors and freshness metadata

This is the core of "scientific" indexing for Sula:

- explicit identifiers
- clear provenance
- deterministic filters
- semantic help only after exact methods

## Incremental Indexing Strategy

To avoid document and database bloat, indexing must be incremental.

### Required Mechanics

- fingerprint every source or segment
- re-index only changed segments
- keep natural chunk boundaries such as headings, sections, or file-level units
- store one canonical extracted form per concern
- compact stale caches and old summaries

### Storage Controls

- size budgets for caches and indexes
- doctor checks for orphaned indexes
- doctor checks for stale snapshots
- doctor checks for duplicate or oversized exported summaries
- configurable retention for low-value transient session events

### Anti-Bloat Rules

- do not duplicate full source documents unless explicitly requested
- store references and anchors before storing copies
- keep semantic embeddings optional
- make cache garbage collection a normal maintenance path

## Adoption Flow

The long-term adoption flow should be:

1. inspect the target project or project workspace
2. attach the `generic-project` kernel in report mode
3. discover truth sources and candidate adapters
4. produce an adoption report with:
   - detected sources
   - proposed adapters
   - managed writes
   - preserved files
   - storage impact
   - removal plan
5. wait for approval
6. write `.sula/` kernel state
7. optionally generate exported human-readable views
8. build the initial indexes and current-state snapshot
9. print follow-up commands for health checks, sync, and removal

Important behavior:

- missing specialized profile must not block adoption
- `generic-project` is always the safe baseline
- specialized bundles are enhancements, not admission gates
- an in-progress project must adopt in place rather than being forced through a clean-start template flow
- Git discovery may enrich the report, but lack of Git must not block inspection, adoption, indexing, or removal

## In-Progress Project Adoption

Sula vNext must assume that many real projects are already underway when adoption happens.

That means the default behavior should be:

- inspect before prescribing structure
- register existing truth sources before generating new views
- preserve local naming and layout unless a managed write is explicitly approved
- build current-state and event history from what already exists
- avoid any requirement to "restart the project under Sula"

The product promise is not "best on greenfield".

The product promise is:

- usable on day zero of adoption, even when the project is already active

## Session Workflow

Within one adopted project, any new session should follow this pattern:

1. read current state
2. read recent events
3. retrieve the most relevant anchored sources
4. execute work
5. append events
6. refresh current state and affected exports

That is how Sula becomes cross-session without pretending the model itself remembers everything.

## Removal Flow

Extreme portability requires extreme removability.

The long-term removal flow should be:

1. run `remove --dry-run`
2. print a full removal report
3. list Sula-owned paths to delete
4. list project-owned paths to preserve
5. list optional exported views that can be kept or removed
6. wait for approval
7. remove namespaced kernel state and chosen generated exports
8. verify that no hidden dependency on Sula remains

Removal design rules:

- all derived indexes must be disposable
- all generated exports must be identifiable
- Sula must never require an external service to detach safely
- the project must still make sense after Sula leaves

Git rollback remains a second safety layer, but removal should work even without reverting the whole repository history.

## Compatibility With Current Sula

Sula should not throw away the current model.

The compatibility path should be:

- preserve `.sula/project.toml` as a stable manifest entrypoint
- keep current profiles working
- gradually move profile logic toward adapter bundles
- keep `STATUS.md`, `CHANGE-RECORDS.md`, and memory digests as supported exports
- allow existing adopted repositories to migrate incrementally
- allow non-Git projects to adopt the kernel now and add the `repo` adapter only if Git becomes relevant later

## Acceptance Criteria

Sula vNext is ready only when all of the following are true:

- a new project can attach with one sentence or one command
- an unknown project still adopts through `generic-project`
- an already-running project can adopt without needing a reset, restructure, or Git migration
- a fresh session can recover current state without reading the full repository
- non-trivial answers can point to specific anchors
- indexes can be rebuilt locally without special infrastructure
- the removable footprint is obvious before approval
- detaching Sula does not damage project-owned truth

## Main Risks

### Risk: Over-Modeling

If the kernel schema becomes too abstract, the system gets heavy and fragile.

Mitigation:

- keep the canonical schema narrow
- move specialization into adapters

### Risk: Stale Or Incorrect Summaries

Mitigation:

- track freshness
- keep exports derived
- cite anchors

### Risk: Storage Bloat

Mitigation:

- use source registration before duplication
- enforce cache budgets
- rebuild indexes incrementally

### Risk: Adapter Sprawl

Mitigation:

- require `generic-project` compatibility first
- treat bundles as reusable packages, not one-project hacks

### Risk: Hidden Lock-In

Mitigation:

- keep all machine state namespaced
- design removal first
- avoid mandatory hosted dependencies

### Risk: Git-Centric Assumptions

Mitigation:

- treat Git as an optional adapter
- require source registration and anchors to work on plain files and external documents
- verify adoption and removal flows on at least one non-Git project canary

## Recommended Implementation Order

1. define the `generic-project` kernel and `.sula/` layout
2. add structured event and current-state storage
3. add exact, structured, and lexical indexes
4. add adapter registration and bundle composition
5. add object catalog and local query capabilities
6. migrate current profiles into bundles
7. add `remove --dry-run` and `remove --approve`
8. add optional semantic retrieval caches

## Final Rule

Sula should attach to any project by default, specialize only when useful, and leave without residue when asked.
