# Add workflow policy and source-first workflow scaffolds

## Metadata

- date: 2026-04-16
- executor: Codex
- branch: codex/release-main
- related commit(s): pending
- status: completed

## Background

Sula had a documented proposal for selectively absorbing long-term value from reusable workflow-governance patterns, but the capability was still conceptual. Projects could not yet express workflow rigor in the manifest, assess whether a task should carry a spec or plan, or create durable workflow source documents through a first-class Sula command.

## Analysis

- The highest-value near-term absorption target was a project-owned workflow policy contract, not plugin-specific runtime behavior.
- Existing artifact and document-design flows already provided the right primitives, so the implementation should extend those lanes instead of inventing a separate subsystem.
- Durable workflow source documents should live under a source-first docs path instead of overloading the general artifact root.

## Chosen Plan

- extend `[workflow]` with explicit policy fields and a dedicated workflow docs root
- add a first-class `workflow` command family for assessment and source-document scaffolding
- register scaffolded `spec`, `plan`, and `review` documents in the artifact catalog so they stay queryable and traceable

## Execution

- added workflow manifest fields for `docs_root`, `execution_mode`, `design_gate`, `plan_gate`, `review_policy`, `workspace_isolation`, `testing_policy`, and `closeout_policy`
- added `python3 scripts/sula.py workflow assess --project-root ...` to evaluate task shape against the project's workflow policy
- added `python3 scripts/sula.py workflow scaffold --project-root ... --kind spec|plan|review` to create source-first workflow documents under `docs/workflows/`
- created dedicated scaffold templates for `spec` and `review`, while reusing the formal proposal bundle for `plan`
- extended status payloads, schema docs, the example manifest, and the Sula root manifest to expose the new workflow policy surface

## Verification

- `python3 -m py_compile scripts/sula.py`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_software_delivery_adoption_sets_workflow_policy_defaults -v`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_workflow_assess_recommends_spec_plan_and_review_for_complex_task -v`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_workflow_scaffold_creates_durable_source_documents -v`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/sula.py memory digest --project-root .`
- `python3 scripts/sula.py check --project-root .`

## Rollback

- remove the new workflow policy fields and `workflow` command family from `scripts/sula.py`
- remove the schema, manifest, README, and traceability updates tied to the new workflow surface
- revert the generated `.sula/*` state after restoring the previous source documents

## Data Side-effects

- new manifests now record workflow policy explicitly instead of leaving it implicit in agent instructions
- scaffolded workflow docs become queryable through the artifact catalog and kernel indexes
- the Sula root project now declares its own workflow policy in `.sula/project.toml`

## Follow-up

- decide whether to add `workflow branch` and `workflow close` after a canary validates the current policy model
- validate the new workflow docs path and policy defaults in the first external software-delivery project

## Architecture Boundary Check

- highest rule impact: preserved; the new surface keeps workflow rigor in project-owned manifest policy and source documents instead of importing external plugin behavior as centrally managed truth
