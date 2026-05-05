# Execute Sula 0.17.0 agent-native project OS upgrade

## Metadata

- date: 2026-05-05
- kind: review
- project: Sula
- workflow pack: operating-system
- workflow slot: operations
- storage provider: local-fs
- review policy: task-checkpoints
- testing policy: verify-first
- closeout policy: explicit

## Summary

Review checkpoint and closeout evidence for the Sula 0.17.0 agent-native upgrade package.

## Reviewed Scope

- `docs/reference/sula-0-17-0-agent-native-project-os-whitepaper.md`
- `docs/sula-overview.md`
- `README.md` reference links
- `docs/workflows/tasks.json`
- `docs/workflows/specs/2026-05-05-execute-sula-0-17-0-agent-native-project-os-upgrade.md`
- `docs/workflows/plans/2026-05-05-execute-sula-0-17-0-agent-native-project-os-upgrade.md`
- `docs/workflows/reviews/2026-05-05-execute-sula-0-17-0-agent-native-project-os-upgrade.md`

## Findings

- No blocking implementation findings remain after verification.
- The main continuing release risk is MCP write-class scope: MCP and provider work must stay an optional control surface, not a replacement for the CLI or a new core platform dependency.

## Regressions Checked

- Protected behaviors to check during implementation:
  - CLI remains independently usable.
  - Existing report/check/doctor/session lifecycle remains intact.
  - Sula-managed writes stay owned by Sula.
  - Existing profiles and canaries still pass.
  - Non-software projects do not inherit software-only rules.
- Implementation review notes:
  - MCP transport is dependency-light and stdio/CLI based.
  - Controlled write tools require local policy allowlisting and explicit write-class enablement.
  - Registry canary verification now refreshes digest after its own sync/doctor activity before final check.

## Validation

| Check | Command / Evidence | Result |
| --- | --- | --- |
| Planning artifact exists | Whitepaper plus spec/plan/review and task intake created | pass |
| Repository check | `python3 scripts/sula.py check --project-root .` | pass |
| Strict doctor | `python3 scripts/sula.py doctor --project-root . --strict` | pass |
| Unit tests | `python3 -m unittest discover -s tests -v` | pass, 116 tests |
| Canary verification | `python3 scripts/sula.py canary verify --project-root . --all` | pass, 4 canaries |

## Release Gate

- Availability: prepared for operator-requested commit/tag/publication; no commit was created in this session.
- Primary flow: read-only surface, controlled writes, policy/portfolio/provider reporting, PR closeout evidence, release metadata, and canary coverage are implemented.
- External setup: no external provider writes or production credentials are required for the initial implementation.
- Rollback clarity: revert the 0.17.0 implementation change record, release metadata, MCP command surface, PR closeout evidence additions, canary verify ordering change, and associated tests.

## Follow-up

- Commit, tag, and publish `v0.17.0` only when the operator explicitly requests it.
- Add host-specific MCP examples after the minimal stdio surface is used by a real client.
