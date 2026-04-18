# Sula Project Memory Model

Sula treats project memory as durable repository state, not as chat history.

## Memory Layers

### 1. Stable Facts

Store long-lived project facts in:

- `.sula/project.toml`
- `AGENTS.md`
- architecture docs
- runbooks

### 2. Current State

Store current operating context in `STATUS.md`.

This should answer:

- what is happening now
- whether the project is healthy
- what is blocked
- what must be reviewed next

### 3. Decisions And Change History

Use:

- `CHANGE-RECORDS.md` as the index
- `docs/change-records/YYYY-MM-DD-topic.md` for detail

Detailed records should capture reasoning, verification, rollback, and architecture-boundary impact.

### 4. Release And Incident History

Use:

- `docs/releases/`
- `docs/incidents/`

These should exist only to preserve operational context that is too important to leave in commits or chat.

### 5. Generated Recall Layer

Use `.sula/memory-digest.md` or the configured digest path as a generated summary for quick recall.

This digest is derived from source documents. It must never become the source of truth.

### 6. Staged Session Layer

Use `.sula/state/session/captures.jsonl` for temporary session findings that still need review.

These captures are:

- temporary
- reviewable
- promotable
- disposable if they do not become durable operating knowledge

Staged captures must not silently become canonical truth.

### 7. Promotion Layer

Use the configured promotion file, which defaults to `docs/ops/session-promotions.md`, to preserve reviewed operating insights that should become durable project context.

Promotion is the bridge between:

- temporary session findings
- durable rules, state updates, workflow artifacts, tasks, decisions, and risks

### 8. Memory Maintenance Layer

Use `.sula/state/jobs/` for memory-maintenance job history such as digest regeneration, capture promotion, and derived-cache clearing.

This layer exists to make memory upkeep inspectable without turning logs into truth.

## Maintenance Rules

- one concern, one source of truth
- staged captures require review before promotion
- promotions should land in a durable source document, not in a hidden parallel truth file
- the stable operator loop is capture, review, promote, query, clear
- index files stay short and link to detailed records
- generated summaries are disposable and reproducible
- non-trivial work should leave a durable trace
- architecture exceptions should point back to change records
