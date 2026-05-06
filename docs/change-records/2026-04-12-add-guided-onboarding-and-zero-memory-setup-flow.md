# Add guided onboarding and zero-memory setup flow

## Metadata

- date: 2026-04-12
- executor: Codex
- branch: codex/bootstrap-sula
- related commit(s): pending
- status: completed

## Background

Sula could already inspect a project, generate a manifest, and adopt it safely, but the first-time experience still expected the operator to understand Sula's internal flags and file-routing rules. That contradicted the target user model: the user should connect a project, answer questions, and then understand exactly what Sula will manage without memorizing the system.

## Analysis

- `adopt` is still the right low-level inspect-report-approve primitive, but it is not the right first-touch UX for most users.
- External tools needed a structured question set and a structured operating summary so they can run onboarding conversations without scraping prose.
- The previous JSON apply path still leaked helper output from `memory digest` and `doctor`, which made it unsafe as a single machine protocol envelope.

## Chosen Plan

- add a new `onboard` command as the human-first and machine-first interview flow
- generate suggested answers for name, description, workflow pack, storage provider, and portfolio fields
- print or emit a "what you get" operating summary before adoption
- keep `adopt` as the lower-level primitive underneath the guided flow
- make JSON apply paths emit a single envelope only

## Execution

- added `onboard` with interactive prompts, `--json`, and `--accept-suggested`
- added onboarding question payloads and a summary contract that explains workflow slots, artifact routing, storage metadata, and next commands
- added an existing-consumer response so already-adopted projects do not look like onboarding failures
- fixed `apply_adoption()` so JSON mode suppresses nested `doctor` and `memory digest` output
- updated docs to make guided onboarding the preferred entrypoint

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_onboard_json_returns_questions_and_summary tests.test_sula.SulaCliTests.test_onboard_accept_suggested_approve_applies_project tests.test_sula.SulaCliTests.test_onboard_interactive_uses_defaults_and_waits_for_apply_confirmation tests.test_sula.SulaCliTests.test_adopt_approve_json_emits_single_payload -v`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/sula.py sync --project-root .`
- `python3 scripts/sula.py sync --project-root examples/okoktoto`
- `python3 scripts/sula.py doctor --project-root . --strict`
- `python3 scripts/sula.py doctor --project-root examples/okoktoto --strict`

## Rollback

- revert the commit that introduced `onboard` and the single-envelope JSON apply behavior
- continue to use `adopt` as the only onboarding primitive until the guided flow is redesigned
- remove only the new docs and tests if the user-facing contract is being revised without changing the kernel

## Data Side-effects

- no new persistent file contract beyond the existing adoption kernel
- existing projects are unaffected until they sync to the new version lock and kernel metadata
- future onboarding callers gain a stable question-and-summary protocol before adoption

## Follow-up

- decide whether onboarding answers should later be persisted as a resumable interview state
- evaluate whether portfolio registration should become an explicit post-onboarding step or an optional last question in the guided flow
- validate the guided flow against the first real Google Drive client workspace

## Architecture Boundary Check

- highest rule impact: preserved; guided onboarding only changes how users arrive at the same manifest and managed/scaffold boundary, without reclassifying project-owned truth
