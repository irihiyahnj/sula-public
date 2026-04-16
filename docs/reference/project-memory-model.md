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

## Maintenance Rules

- one concern, one source of truth
- index files stay short and link to detailed records
- generated summaries are disposable and reproducible
- non-trivial work should leave a durable trace
- architecture exceptions should point back to change records
