# Document provider-backed artifact identity for cross-device project workspaces

## Metadata

- date: 2026-04-12
- executor: Codex
- branch: codex/bootstrap-sula
- related commit(s): pending
- status: completed

## Background

Sula already treats Google Drive as a storage adapter in local-sync mode, but the contract still needed a clearer statement about what actually belongs to the project versus what only belongs to one machine. Real client-service workspaces may be opened from different devices, may sit under different local sync roots, and may mix ordinary files with provider-native documents such as Google Docs or Google Sheets.

## Analysis

- Treating a local absolute path as the artifact identity would make the same project appear different on each device.
- Treating Google Docs and Google Sheets as provider-native artifacts keeps the model open for direct provider adapters without forcing Sula Core to become Google-specific.
- The contract needed to state that `workspace_root` is an access detail, while provider ids and project-relative placement carry the durable identity.
- The design also needed to state that AI should generate content once and let adapters materialize provider-native documents or exports, instead of making the final document format itself the only source of truth.

## Chosen Plan

- Add a dedicated reference document for provider-backed artifact identity across devices.
- Clarify the existing manifest and storage adapter contracts so `workspace_root` is not misread as a stable artifact identifier.
- Record the Google Drive case as the first concrete example without turning the design into a provider-specific special case.

## Execution

- added `docs/reference/provider-backed-artifact-identity.md`
- updated `docs/reference/project-manifest.md` to clarify the meaning of `storage.workspace_root`
- updated `docs/reference/portfolio-adapter-workflow-contract.md` to clarify provider-backed artifact identity and cross-device access
- updated `docs/README.md` so the new reference contract is part of the documentation map

## Verification

- verified the new reference links and filenames are consistent across `docs/README.md`, `docs/reference/project-manifest.md`, `docs/reference/portfolio-adapter-workflow-contract.md`, and `CHANGE-RECORDS.md`

## Rollback

- remove the new reference document if the contract is replaced by a different cross-device storage model
- revert the linked doc clarifications if Sula intentionally chooses machine-local path identity instead

## Data Side-effects

- no runtime data changes
- no manifest schema changes
- no sync behavior changes in adopted projects yet

## Follow-up

- extend `.sula/artifacts/catalog.json` with provider-backed artifact identity fields once real Google Drive project usage stabilizes
- add direct provider-native document registration only after the local-sync contract proves durable in production workspaces
- teach query dedupe to prefer provider identity plus project-relative location over absolute path when provider-backed artifacts are introduced

## Architecture Boundary Check

- highest rule impact: preserved; the new design keeps cross-device identity in removable Sula operating metadata and does not promote one machine's filesystem layout into project-owned truth
