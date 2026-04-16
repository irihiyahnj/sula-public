# Add artifact materialization for docs and sheets

## Metadata

- date: 2026-04-12
- executor: Codex
- branch: codex/bootstrap-sula
- related commit(s): pending
- status: completed

## Background

Provider-backed artifact identity solved the indexing side of cross-device project files, but real teams still needed a practical way to turn project-owned source files into concrete deliverables quickly. Waiting for full Google OAuth and direct Docs/Sheets adapters would block immediate work.

## Analysis

- A low-friction bridge was needed so projects could keep Markdown and tabular files as truth while still producing import-ready documents and spreadsheets.
- The feature needed to stay dependency-light and portable, with no mandatory third-party Python packages.
- The existing artifact workflow was the right place to add this because materialized files are still project artifacts and should be routed, registered, and queryable like any other deliverable.

## Chosen Plan

- Add `artifact materialize` as a first-class artifact subcommand.
- Support built-in local materialization for document and spreadsheet sources.
- Use standard-library generation where possible, and optional platform tooling where already available.

## Execution

- added `artifact materialize` for concrete file generation from project source files
- added local document materialization from `.md`, `.txt`, and `.html` to `.html`
- added macOS `.docx` materialization through `textutil`
- added built-in `.xlsx` generation from `.csv`, `.tsv`, and `.json`
- registered materialized outputs back into `.sula/artifacts/catalog.json` with `derived_from` links
- updated README and reference docs with the bridge workflow for Google Docs and Google Sheets import

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_artifact_materialize_markdown_to_html_registers_output`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_artifact_materialize_csv_to_xlsx_registers_output`

## Rollback

- remove the `artifact materialize` command and helper logic from `scripts/sula.py`
- stop registering materialized derivatives if the project returns to a source-only workflow

## Data Side-effects

- materialized `.html`, `.docx`, or `.xlsx` files are written under the routed artifact slot
- materialized outputs are registered as normal project artifacts and may reference their source via `derived_from`

## Follow-up

- add direct Google Docs and Google Sheets adapters once OAuth and provider-side document creation are ready
- decide whether Markdown tables should gain richer spreadsheet-oriented parsing rules
- add PDF generation only after a dependency-light path is stable enough for cross-project use

## Architecture Boundary Check

- highest rule impact: preserved; project truth can stay in project-owned source files while materialized deliverables remain removable operating outputs tracked through the artifact layer
