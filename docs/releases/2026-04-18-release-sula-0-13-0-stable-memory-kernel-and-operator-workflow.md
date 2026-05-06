# Release Sula 0.13.0 stable memory kernel and operator workflow

## Metadata

- date: 2026-04-18
- executor: Codex
- branch: main
- status: released

## Scope

Released Sula 0.13.0 on the canonical Git branch so adopted projects can pick up the stable staged-memory workflow in one synchronized source state: explicit session capture, durable promotion, rule-aware retrieval routing, inspectable memory jobs, and product-facing operator surfaces across `status`, `onboard`, and `adopt`.

## Risks

- adopted projects that sync to this release may fail `check` or `doctor --strict` if they have stale staged captures or malformed promotion files, so rollout should review old temporary memory instead of assuming a silent upgrade
- teams that previously treated temporary session notes as private scratch space now have a clearer promotion path, but they still need to decide what deserves durable project context and what should be discarded
- external canaries should validate whether the new memory workflow reads naturally to non-core operators before broad rollout treats it as fully routine

## Verification

- `python3 -m unittest discover -s tests -v`
- `python3 scripts/sula.py sync --project-root .`
- `python3 scripts/sula.py sync --project-root examples/okoktoto`
- `python3 scripts/sula.py sync --project-root examples/field-ops-generic`
- `python3 scripts/sula.py sync --project-root examples/client-service-gdrive`
- `python3 scripts/sula.py memory digest --project-root .`
- `python3 scripts/sula.py canary verify --project-root . --all`
- `python3 scripts/sula.py doctor --project-root . --strict`
- `python3 scripts/sula.py check --project-root .`

## Rollback

- revert the `0.13.0` release batch from Git if the combined staged-memory, promotion, and route-aware retrieval surface should not become the canonical downstream sync target
- resync affected canary or adopted projects back to the previous Sula release if rollout must be withdrawn

## Follow-up

- validate the first external 0.13.0 canaries and confirm that `capture -> review -> promote -> query -> clear` is understandable without source-repo context
- keep semantic memory help optional and canary-only until the exact, structured, and lexical retrieval baseline is proven to remain stronger than any optional cache
