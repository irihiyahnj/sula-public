---
id: 2026-05-23T06-29-04Z--operation-v1-0-1-tag-and-fleet-refresh
time: 2026-05-23T06:29:04Z
kind: operation
refs: [2026-05-23T05-33-46Z--release-sula-vector-1-0-ga, 2026-05-23T06-22-58Z--correction-agents-md-legacy-vs-vector-ambiguity, 2026-05-23T06-22-58Z--decision-update-mechanism-is-migrate-py]
tags: [release, v1-0-1, fleet-refresh, patch]
author: jing
remote: https://github.com/irihiyahnj/sula-vector.git
tag: sula-vector-v1.0.1
tag_commit: cf074eb
---
v1.0.1 patch tag pushed; all 14 adopted projects on this device
re-confirmed at canonical state via migrate.py.

Tag: sula-vector-v1.0.1 (cf074eb on main)

Patches collected since v1.0.0:
- Public repo renamed sula-public → sula-vector (URL update; old URL 301)
- Vendor-neutral framing in public docs (no more "Codex-style" branding)
- B6 fix: AGENTS.md priority notice prepended (legacy-vs-vector
  ambiguity resolved structurally)
- migrate.py established as the canonical update path (idempotent)
- New tools/sula_vector/update-from-canonical.sh (operator helper)

Convention itself unchanged at v1.0 (frozen for v1.x). All adopted v1.0
projects refresh-compatible by re-running migrate.py.

Fleet refresh evidence (this operation):
- 14/14 projects: AGENTS.md status = already-vector (priority notice intact)
- 13/13 external projects: render.py sha256 matches canonical 053f235236a7
- Sample boot (madcut): renders correctly, prepends Tier A–E principles
- Tooling-files copied: 9 per project (idempotent overwrite, same content)
- Zero new fragments emitted in any project (idempotence holds end-to-end)

This operation completes the v1.0.1 rollout. The fleet is at canonical
state. Future operator updates: re-run migrate.py per project, or use
update-from-canonical.sh as a one-line wrapper.
