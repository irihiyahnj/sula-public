# Sula Memory Capability Implementation Plan

## Executive Summary

Sula should strengthen its project-memory layer without turning memory into a second truth system.

The correct direction is:

- keep project-owned source material as canonical truth
- make session findings explicit but temporary until promoted
- treat rules, current state, decisions, and freshness signals as first-class operating objects
- improve retrieval quality through better routing, richer indexes, and stronger promotion workflows
- keep all derived memory disposable, rebuildable, and easy to remove

This plan defines the high-return memory capabilities Sula should add next, how they fit the current kernel, and how rollout should be phased.

## Objectives And Scope

### Objectives

- make cross-session recovery faster without relying on old chat windows
- reduce the gap between temporary operator context and durable project truth
- make project rules and operating constraints queryable as first-class objects
- improve retrieval quality while preserving Sula's scientific retrieval order
- keep the memory layer portable across adopted projects and removable later

### Scope

- project-memory contracts inside `.sula/`
- manifest, command, and adapter implications for stronger recall
- promotion flows from temporary findings into durable state
- retrieval routing and background-memory maintenance

### Out Of Scope

- replacing source documents with a memory database
- making semantic indexing mandatory for core functionality
- storing full chat transcripts as canonical project history
- introducing hosted infrastructure as a baseline dependency
- turning Sula into an agent-memory product instead of a project operating system

## Design Rules

### Rule 1: Truth Stays In Source Material

Memory must point back to source anchors whenever possible.

Durable truth remains in:

- source files
- registered project documents
- `STATUS.md`
- `docs/change-records/`
- releases, incidents, and runbooks
- registered provider-backed artifacts

### Rule 2: Temporary Context Must Be Explicitly Staged

Sula should distinguish between:

- temporary session findings
- promoted durable state
- disposable generated summaries

Nothing should silently skip from a short-lived session note into canonical project truth.

### Rule 3: Rules Are Operating Objects

Project rules are not just text files. They are operating constraints that should be discoverable, queryable, and enforceable.

### Rule 4: Retrieval Must Stay Scientific

Sula should continue to prefer:

1. exact identity lookup
2. structured filters
3. path and anchor lookup
4. lexical retrieval
5. optional semantic help
6. synthesis with provenance and freshness

### Rule 5: Derived Memory Must Be Disposable

All indexes, snapshots, route hints, temporary captures, and generated summaries must remain safe to rebuild or delete.

## Capability Priorities

## High Priority

### 1. Staged Session Memory And Durable Promotion

Sula should add a formal split between temporary operating context and durable kernel state.

Recommended shape:

- keep temporary captures under `.sula/state/session/`
- give each capture a timestamp, source, operator, scope, and confidence
- require promotion before temporary captures affect canonical state exports
- record promotion as an explicit event

Expected return:

- much cleaner current-state maintenance
- less accidental drift from one-off operator assumptions
- stronger cross-session recovery with less noise

Acceptance signals:

- temporary captures can be listed, reviewed, promoted, or discarded
- promoted items update the relevant durable target instead of creating parallel truth
- `check` can detect stale unreviewed session captures

### 2. First-Class Rule Registry

Sula should treat project rules as first-class operating objects rather than passive documents.

Suggested rule sources:

- `AGENTS.md`
- managed AI instruction files when enabled
- workflow rules
- document-design rules
- project-specific operating constraints
- release and verification checklists

Kernel shape:

- add rule objects with stable ids, source anchors, status, tags, and scope
- index them into the existing object and relation model
- support `kind = rule` in query surfaces

Expected return:

- better onboarding and inspect reporting
- more accurate query results for "how should we do X here?"
- clearer governance for adapters and future automation

Acceptance signals:

- Sula can list active rules and their sources
- query can return rule hits with anchors
- `doctor` and `check` can report broken or duplicate rule references

### 3. Promotion Loop For Reusable Operating Insight

Sula should support turning repeated short-lived findings into durable reusable operating knowledge.

This applies to:

- recurring local fixes
- workflow conventions
- artifact freshness handling
- release and verification patterns
- project-specific exceptions

The important distinction is:

- do not preserve everything
- preserve what becomes stable operating knowledge

Recommended shape:

- temporary capture
- review
- promote into one of: state, rule, decision, risk, workflow artifact, or feedback bundle

Expected return:

- less repeated rediscovery
- better reuse across sessions and projects
- tighter connection between work performed and durable operating memory

Acceptance signals:

- every promoted item names its destination truth surface
- promotion leaves a traceable event
- projects can reject low-value captures instead of accumulating memory bloat

### 4. Background Memory Jobs And Status Surfaces

Sula already performs some expensive or multi-step memory operations. These should become first-class background jobs with status reporting.

Target operations:

- index rebuild
- provider refresh
- memory digest regeneration
- large query cache refresh
- future optional semantic cache refresh

Suggested shape:

- `.sula/state/jobs/`
- job id, job type, scope, start time, finish time, result, and failure details
- resumable phases where practical

Expected return:

- better reliability for long-running maintenance
- clearer failure recovery
- stronger machine-readable integration

Acceptance signals:

- users can inspect the latest job status without reading logs
- failures point to a concrete phase and next action
- `check` can surface stale or failed maintenance jobs

### 5. Query Routing By Intent

Sula should become smarter about where to look first without changing the retrieval order.

Examples:

- "current status" -> current-state snapshot first
- "why was this changed" -> change records and decisions first
- "what are the rules" -> rule objects first
- "what is stale" -> freshness metadata and provider-backed artifacts first
- "what happened recently" -> events timeline first

This is not a separate memory engine. It is better routing across the existing kernel.

Expected return:

- higher query relevance
- less low-signal result mixing
- better machine-consumable behavior

Acceptance signals:

- query results identify which route was used
- route selection remains deterministic and inspectable
- users can still force literal modes when needed

## Medium Priority

### 6. Clear Workspace / Project / Run Isolation

Sula should more clearly separate:

- workspace-level portfolio state
- one project's kernel state
- one run or session's temporary work

Expected return:

- cleaner portfolio operations
- less cache collision risk
- stronger future multi-project automation

### 7. Narrow Memory Command Surface

Sula has strong capability already, but memory actions are spread across several commands.

It should converge on a smaller operator mental model:

- capture
- review
- promote
- query
- clear derived memory

This can be implemented as a new command family or as a clearer top-level routing layer over existing commands.

Expected return:

- lower onboarding friction
- easier machine integration
- clearer daily use

### 8. Rule-Aware Onboarding And Adoption

Inspect, onboard, and adopt should summarize:

- what rule surfaces were found
- which rules are managed by Sula
- which rules remain project-owned
- where rule conflicts exist

Expected return:

- fewer adoption surprises
- better first-run understanding
- stronger managed versus project-owned boundary reporting

## Low Priority Or Rejected By Default

### Do Not Make These Core Assumptions

- full transcript retention as default memory
- mandatory semantic embeddings
- mandatory graph or vector infrastructure
- hidden repo-wide ingestion into a side database
- cloud-only memory services
- opaque memory updates without traceable promotion

These all weaken Sula's portability, removability, or source-first model.

## Proposed Kernel Additions

### New Or Expanded Paths

```text
.sula/
  state/
    current.md
    session/
      captures.jsonl
    jobs/
      latest.json
      history.jsonl
  objects/
    catalog.json
    rules.json
  indexes/
    catalog.json
    relations.json
    routes.json
  cache/
    kernel.db
    query-index.json
    semantic/          # optional and disposable
```

### Object Model Additions

Recommended additions or clarifications:

- `rule`
- `session_capture`
- `job`
- `promotion`

Relationship examples:

- `session_capture -> promotes_to -> decision`
- `rule -> constrains -> workflow`
- `rule -> derived_from -> source`
- `job -> refreshes -> artifact`

## Manifest Direction

Sula should add an optional `[memory]` section instead of hiding policy inside undocumented behavior.

Draft shape:

```toml
[memory]
capture_policy = "explicit"
promotion_policy = "review-required"
rule_registry = true
job_tracking = true
query_routing = "deterministic"
semantic_cache = "off"
session_retention_days = 7
```

Field intent:

- `capture_policy`: `off`, `explicit`, `guided`
- `promotion_policy`: `manual`, `review-required`, `auto-derived`
- `rule_registry`: whether rule extraction and indexing are enabled
- `job_tracking`: whether background memory job metadata is persisted
- `query_routing`: `literal`, `deterministic`, `deterministic-plus-hints`
- `semantic_cache`: `off`, `optional`, `canary`
- `session_retention_days`: cleanup horizon for unpromoted temporary captures

Default rule:

- core memory must work with `semantic_cache = "off"`

## Command Direction

The preferred shape is a narrow memory command family that complements existing commands rather than replacing them immediately.

Recommended first-pass surfaces:

- `python3 scripts/sula.py memory capture --project-root .`
- `python3 scripts/sula.py memory review --project-root .`
- `python3 scripts/sula.py memory promote --project-root .`
- `python3 scripts/sula.py memory clear --project-root . --derived`
- `python3 scripts/sula.py memory jobs --project-root .`

Command intent:

- `memory capture`: store temporary session findings
- `memory review`: list and inspect staged captures
- `memory promote`: move reviewed items into durable targets
- `memory clear --derived`: delete disposable caches and generated memory state
- `memory jobs`: inspect memory-related maintenance work

This should coexist with:

- `query`
- `check`
- `doctor`
- `artifact refresh`
- `memory digest`

## Adapter Implications

Adapters should expose rule and memory-aware behavior without becoming alternate truth systems.

Expected adapter responsibilities:

- project-specific rule discovery
- source anchoring
- object extraction
- health checks
- route hints for query

Adapters should not:

- silently persist alternate project state outside `.sula/`
- bypass promotion rules
- treat chat context as authoritative project truth

## Rollout Plan

### Phase 1: Contracts And Rule Indexing

Status: completed in `0.13.0`.

- add this memory capability contract to reference docs
- add `rule` as a first-class kernel object
- index discovered rule sources and expose them through `query`
- add basic rule validation to `doctor`

Exit criteria:

- rule objects exist in the kernel
- query can return rule hits with anchors
- docs and manifest examples explain the model

### Phase 2: Session Capture And Promotion

Status: completed in `0.13.0`.

- add staged session capture storage
- add review and promotion commands
- record promotion events
- connect promoted output to durable targets

Exit criteria:

- temporary captures never bypass review by default
- promotion writes are traceable
- `check` reports stale staged captures

### Phase 3: Background Jobs And Deterministic Routing

Status: completed in `0.13.0`.

- add job metadata for memory maintenance tasks
- add route hints and route inspection in query results
- improve current-state, rule, event, and freshness routing

Exit criteria:

- memory maintenance jobs have inspectable status
- query reports route choice
- result quality improves without semantic dependencies

### Phase 4: Narrow Memory UX

Status: completed in `0.13.0`.

- add the narrow memory command surface
- align inspect/onboard/adopt with rule-aware reporting
- document daily operating guidance

Exit criteria:

- the core operator mental model becomes capture, review, promote, query, clear
- onboarding explains memory behavior without requiring prior Sula knowledge

### Phase 5: Optional Semantic Cache Canary

Status: deferred after `0.13.0`; keep optional and canary-only.

- add an optional canary-only semantic cache
- keep it isolated under `.sula/cache/semantic/`
- verify usefulness against exact, structured, and lexical retrieval

Exit criteria:

- semantic help remains optional and disposable
- canary validation shows real recall benefit without damaging provenance or removability

## Verification And Release Gates

Before releasing any phase:

- verify the new memory surface does not replace project-owned truth
- verify all new state stays inside `.sula/`
- verify `remove` remains clean and understandable
- verify `doctor` and `check` can detect malformed new memory artifacts
- verify the manifest remains backward-compatible
- verify one canary project uses the new surface without workflow confusion

## Publication Hygiene

Public Sula materials should describe these capabilities as Sula's own operating design.

When implementing this plan:

- do not mention external research, repositories, or products in public docs, commit messages, release notes, or managed project files unless there is a separate legal or attribution requirement
- keep user-facing language centered on Sula's architecture, contracts, and operating outcomes
- record adoption reasoning in Sula terms such as portability, removability, source-first truth, and scientific retrieval

## Main Risks

- over-expanding the memory model before the basic promotion loop is proven
- creating duplicate truth between session captures and durable state
- letting rules become an uncontrolled pile of text instead of queryable objects
- making query routing hard to inspect
- adding semantic tooling before exact and structured retrieval are fully exploited

## Recommended Immediate Next Steps

1. add `rule` as a first-class object kind and index the main rule sources
2. define the staged session-capture schema under `.sula/state/session/`
3. add a minimal `memory review` plus `memory promote` flow
4. teach `check` to report stale staged captures and broken rule anchors
5. validate the narrow memory loop on one real canary before adding any optional semantic cache
