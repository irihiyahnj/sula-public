---
id: 2026-05-23T06-22-58Z--decision-update-mechanism-is-migrate-py
time: 2026-05-23T06:22:58Z
kind: decision
refs: [2026-05-23T06-22-58Z--correction-agents-md-legacy-vs-vector-ambiguity, 2026-05-23T05-59-09Z--decision-each-project-self-contained]
tags: [update-mechanism, fleet, idempotence]
author: jing
---
Crystallised: **the canonical update mechanism for an already-adopted Sula
vector project is to re-run migrate.py on it.**

migrate.py is structurally idempotent end-to-end:
- install_tooling: shutil.copy2 over the canonical files (overwrite-equal
  is idempotent at content level)
- install_agents_template: sentinel-protected, only adds missing pieces
- emit_migration_decision: skips if a migration decision already exists
- migrate_change_records / releases / incidents / etc.: per-fragment
  filename idempotence (same source → same fragment id → skip)
- migrate_events: deduplicated by (timestamp, event_type, summary)
- install_principles: skipped per existing filename

So running migrate.py twice (or N times) is safe; the first run does the
work, subsequent runs only catch new things.

For one-line refresh from the GitHub canonical without manually cloning:

  /path/to/canonical/tools/sula_vector/update-from-canonical.sh \
    --project-root /path/to/your-project

This wrapper clones the canonical to a temp dir, runs migrate.py, and
exits. Operator-level only — does not get installed inside each project.

Why no automatic push from the central canonical to adopted projects:
- E5 (don't invent new substrate)
- E6 (don't wrap in SaaS-shape orchestration)
- B7 (each project's substrate handles its own state; 14 different teams
  on 14 different devices have no shared central runtime)
- C7 (don't churn — most projects don't need every canonical update)

Each project owner reads the RELEASE-NOTES of new canonical versions and
decides whether to refresh. If they don't refresh, their vector keeps
working at its current version. If they do refresh, they get every fix
and improvement at once, with full idempotence guarantees.
