# Add provider import plans for Google Docs and Google Sheets

## Metadata

- date: 2026-04-12
- executor: Codex
- branch: codex/bootstrap-sula
- related commit(s): pending
- status: completed

## Background

Sula could already register provider-backed artifact identity and materialize local `.docx` or `.xlsx` bridge files, but external software still had to guess how to import those bridge files into Google Docs or Google Sheets and how to register the resulting provider-native item back into the project.

## Analysis

- The next useful step was not a hard Google OAuth dependency inside Sula Core.
- A machine-readable handoff layer was enough to turn bridge artifacts into a stable import workflow for external software.
- The handoff layer needed to stay provider-aware without baking Google-only semantics into the project truth or core artifact identity rules.

## Chosen Plan

- Add `artifact import-plan` as a first-class artifact subcommand.
- Let import planning reuse an existing import-ready local file when possible.
- Materialize a `.docx` or `.xlsx` bridge artifact automatically when the source file is not yet import-ready.
- Write a JSON import plan under `.sula/exports/provider-imports/` with follow-up registration metadata.

## Execution

- added `artifact import-plan` for Google Docs and Google Sheets style provider-native imports
- mapped `google-doc` import plans to `.docx` by default, with optional `.html` override
- mapped `google-sheet` import plans to `.xlsx`
- taught import planning to accept either a project `--source-path` or an existing `--artifact-id`
- wrote machine-readable import plans under `.sula/exports/provider-imports/*.json`
- returned a suggested `artifact register` command preview so human or machine callers can persist the provider item id and URL after the real import completes
- updated README, AGENTS, and the provider-backed artifact identity reference

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_artifact_import_plan_materializes_markdown_for_google_doc`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_artifact_import_plan_uses_artifact_id_for_google_sheet`

## Rollback

- remove `artifact import-plan` and its helper logic from `scripts/sula.py`
- stop writing `.sula/exports/provider-imports/*.json`
- keep existing `artifact register` and `artifact materialize` flows intact if the explicit handoff layer is intentionally backed out

## Data Side-effects

- projects may gain `.sula/exports/provider-imports/*.json` files after provider import planning
- import planning may create bridge artifacts such as `.docx` or `.xlsx` under the routed artifacts directory when the source file is not already import-ready
- bridge artifacts continue to be registered as normal project artifacts and remain removable operating outputs

## Follow-up

- add direct adapter execution for provider imports only after the import-plan contract stabilizes in real Drive-based projects
- consider plan status tracking if multiple external tools may consume the same import plan
- extend the same handoff layer to future providers such as Feishu Drive once the provider contract is shared

## Architecture Boundary Check

- highest rule impact: preserved; Sula still keeps provider import state in removable operating metadata while project-owned source files remain the primary business truth
