---
id: 2026-07-25T15-37-50Z--snapshot-sula-vector-v1-1-boot-legacy
time: 2026-07-25T15:37:50Z
kind: snapshot
refs: [2026-07-25T15-24-14Z--goal-sula-vector-v1-1]
tags: [v1-1, handoff]
summary: Sula Vector v1.1 交接：boot 即交接，legacy 归档待确认
---
Handoff snapshot for Sula Vector v1.1. The correct handoff is the boot itself:
`python3 tools/sula_vector/render.py . --for-agent`. This fragment names what to
look at, not a parallel copy of it (E1/E8).

## What changed this session
Migrated Sula's own operating model from prompt-layer discipline to
data/runtime-layer invariants. See the goal `2026-07-25T15-24-14Z--goal-sula-vector-v1-1`
(closed ✓ by its own verifier) and the five decisions refs'd to it. In short:
identity is derived from the filename; nothing loads silently; `note.py` writes
judgments and rejects bad references; `witness.py` + `hooks/install.py` capture
evidence mechanically on any substrate; three lanes (judgment/evidence/direction)
organise every view; `supersedes`/`closes` make the append-only graph resolvable;
`--view doctor` guards integrity and exits 1 on problems; boot is two steps again;
all five host files point at AGENTS.md.

## How to resume (any model, any device)
1. Read AGENTS.md, then run `render . --for-agent`. That is the whole boot.
2. `render . --view doctor` must exit 0 before you claim anything done (D5).
3. Record judgments with `note.py` (never hand-write a fragment). Do not narrate
   files you produced — `witness.py` already has them, with hashes.
4. Supersede a past judgment with `--supersedes <id>`; close a direction with
   `--closes <id>`. Append, never edit (B1/E3).

## Known state / open edges
- Legacy Sula 0.18.x surface (scripts/sula.py 928KB, .sula/, STATUS.md,
  docs/change-records/) still sits at the repo root, now banner-marked "do not
  act on this". It has NOT been moved to legacy/ or a tag — that was flagged as
  the next step and deliberately left for explicit confirmation, since it touches
  the repo root. `scripts/sula.py doctor` still runs and will emit its own
  legacy intents; ignore them, they are the old world.
- The `.github/workflows/ci.yml` now has two jobs: `vector` (authoritative) and
  `legacy` (historical). VERSION file still reads 0.18.15 (legacy artifact).
- Non-git substrates (Drive/Dropbox) get folder-level witness only, no sha —
  documented as a fidelity tier, not hidden.
- Nothing has been committed. All v1.1 work is in the working tree.
