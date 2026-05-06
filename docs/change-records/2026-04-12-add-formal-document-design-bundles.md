# Add formal document design bundles

## Metadata

- date: 2026-04-12
- executor: Codex
- branch: pending
- related commit(s): pending
- status: released

## Background

Sula could already register artifacts, materialize bridge files, and prepare provider import plans, but it still treated formal source documents as mostly generic shells. That was too weak for schedule, proposal, report, process, and training work where the document structure itself is part of the deliverable quality contract.

## Analysis

- Project-level prompts alone are not enough if Sula is meant to carry this behavior across adopted projects.
- The capability needs a first-class manifest contract, managed operating docs, and runtime template logic so adoption, sync, and artifact generation stay aligned.
- Source-first delivery must remain the default so Google Docs or Sheets outputs stay derived and traceable instead of becoming the only maintained copy.

## Chosen Plan

- add a first-class `[document_design]` manifest section with reusable bundle configuration
- ship a managed `docs/ops/document-design-principles.md` rulebook into adopted projects
- teach `artifact create` to infer formal document genre and render production-ready source bundles for schedule, proposal, report, process, and training documents
- extend workflow routing, schema, examples, docs, and regression tests so the contract is durable

## Execution

- added `[document_design]` support to manifest defaults, adoption manifests, rendering, validation, schema, and manifest reference docs
- added reusable managed guidance in `docs/ops/document-design-principles.md` and linked it from the AI adapter docs plus the team operating model
- extended workflow-pack artifact routing for proposal, plan, process, runbook, SOP, training, and timeline style artifacts
- replaced the single generic artifact shell with genre-aware source templates, including the required schedule bundle with monthly overview, role-split gantt, dual action tables, and responsibility matrix
- added regression coverage for init/onboard manifest defaults and the new formal document bundles

## Verification

- ran `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- ran `python3 scripts/sula.py sync --project-root . --dry-run`
- ran `python3 scripts/sula.py sync --project-root .`
- ran `python3 scripts/sula.py doctor --project-root . --strict`
- ran `python3 -m unittest discover -s tests -v`

## Rollback

- revert the change that introduces `[document_design]`, the managed document-design rulebook, and the formal artifact bundles
- re-run `sula sync --project-root <project>` on affected repositories to restore the prior managed-file set

## Data Side-effects

- adopted projects now record formal document design policy in `.sula/project.toml`
- future formal artifacts can carry richer source structure before any derived `.docx`, `.html`, `.xlsx`, or provider-native output is created

## Follow-up

- decide whether provider import tooling should eventually materialize some schedule bundles into richer tabular bridge artifacts automatically
- consider localized managed copy for `document-design-principles.md` now that the structure contract is stable

## Architecture Boundary Check

- highest rule impact: preserved; Sula now adds reusable operating-system guidance and artifact-source structure without turning project-owned business truth into centrally enforced one-project content
