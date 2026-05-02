# Release Sula 0.12.0 freshness, workflow, and Unicode source-id fixes

## Metadata

- date: 2026-04-16
- executor: Codex
- branch: main
- status: released

## Scope

Released Sula 0.12.0 on the canonical Git branch so adopted projects can pick up collaborative truth-source freshness checks, the daily `check` workflow, stronger workflow/release governance, and the Unicode-safe discovered source id fix in one synchronized source state.

## Risks

- adopted projects that sync to this release may see a broader managed guidance surface and stricter daily close-out expectations, so rollout should still review the changed docs and commands instead of assuming a no-op patch
- projects with existing Unicode-heavy source trees will rebuild discovered `source:` ids on the next sync, which is the desired repair path but may change cached low-signal query identities
- public bootstrap users should only treat this release as externally available after the published public source and hosted site descriptor are updated to the same source state

## Verification

- `python3 -m unittest tests.test_sula.SulaCliTests.test_chinese_locale_renders_localized_status_and_supports_doctor -v`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_adopt_handles_chinese_source_paths_without_duplicate_registry_ids -v`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_doctor_reports_duplicate_source_ids_in_registry -v`
- `python3 scripts/sula.py sync --project-root .`
- `python3 scripts/sula.py sync --project-root examples/okoktoto`
- `python3 scripts/sula.py sync --project-root examples/field-ops-generic`
- `python3 scripts/sula.py sync --project-root examples/client-service-gdrive`
- `python3 scripts/sula.py memory digest --project-root .`
- `python3 scripts/sula.py canary verify --project-root . --all`
- `python3 scripts/sula.py doctor --project-root . --strict`

## Rollback

- revert the `0.12.0` release batch from Git if the combined freshness, workflow, and Unicode source-id repair surface should not become the canonical downstream sync target
- resync affected canary or adopted projects back to the previous Sula release if rollout must be withdrawn

## Follow-up

- update the published public source repository and hosted `site/sula.json` deployment so external bootstrap flows can resolve the same `0.12.0` source state
- validate the first external Unicode-heavy adopted project rollout and confirm no downstream tooling assumed discovered `source:` ids were ASCII-only
