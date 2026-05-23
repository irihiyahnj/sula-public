# Sula Vector v1.0 — Release Notes

**Release date:** 2026-05-23
**Convention version:** 1.0 (ship-frozen)
**Status:** General Availability (GA)

This is the first stable release of Sula Vector. The convention is frozen
for v1.x. Future minor versions add views, kinds, or skills without breaking
existing fragment files.

---

## What v1.0 ships

### Convention (ship-frozen)

- **Tier A** highest rule: `project_view = render(fragments, conventions)`. No mutation, no implicit state.
- **Tier B** invariants (B1–B9): append-only, no daemon, byte-stable replay, two-step boot, substrate handles concurrency, goals require verifiers.
- **Tier C** aesthetics (C1–C7): find the essential dimension; don't fight, stand on top; geometry > size; cross the boundary; minimal interaction; metaphor everywhere; no churn.
- **Tier D** discipline (D1–D5): standard library only; zero comments unless WHY non-obvious; no TODO/placeholders/half-implementations; no backwards-compatibility shims; no "done" without verification.
- **Tier E** anti-patterns (E1–E9): no derived-as-truth; no state directories beside fragments; no editing past fragments; no kind enumeration; no inventing substrate; no SaaS wrappers; no size-based file splits; no chat-only context; no goals without verifiers.

All five tiers ship as `kind: principle` fragments in every adoption.
`render --for-agent` prepends them at every agent boot.

### Reference implementation

| Component | Lines | Role |
|---|---:|---|
| `tools/sula_vector/render.py` | 590 | Pure-function renderer. 8 views: list, digest, progress, thread, family, goals, principles, changes-summary. |
| `tools/sula_vector/migrate.py` | 449 | Idempotent migrator from legacy Sula projects. |
| `tools/sula_vector/skills/verifier-shell.py` | 122 | Goal verifier via shell commands. |
| `tools/sula_vector/skills/scheduler.py` | 145 | Cadence-tick emitter for recurring intents. |
| `tools/sula_vector/skills/llm-dispatcher.py` | 168 | Routes intents to a configured executor command (LLM CLI, API call, etc.). |
| `tools/sula_vector/AGENTS.md` | 99 | Host operating protocol template. |
| `docs/sula-vector-convention.md` | 422 | Authoritative convention spec. |
| `tools/sula_vector/tests/test_sula_vector.py` | 539 | 34-test stdlib unittest suite. |

Total tooling surface: ~2530 lines. Standard library only. No third-party
dependencies. No daemon, no kernel directory, no cache-as-truth.

### Host operating protocol (in AGENTS.md)

1. **At session start** — note ISO time as `session_start`; run `render --for-agent`; treat output as authoritative project context.
2. **Throughout the turn** — append fragments; never edit; no churn.
3. **At end of turn** — run `render --view changes-summary --since <session_start>` and surface the multi-line `[sula]` block to the user.

---

## Verification evidence

| Check | Result |
|---|---|
| Test suite (`tools.sula_vector.tests.test_sula_vector`) | 34/34 PASS, 1.8s |
| `render.py` byte-stable replay (Sula self) | OK, 5849 bytes constant |
| `render.py` byte-stable replay (1terminal) | OK, 4803 bytes constant |
| `migrate.py` idempotence (3rd run = 0 net change) | OK on Sula self (327 fragments) and 1terminal (28 fragments) |
| `verifier-shell.py` end-to-end | Closed real goal; idempotent on second run |
| `scheduler.py` end-to-end | Fired real cadence-tick on backdated intent; skipped fresh intent |
| `llm-dispatcher.py` end-to-end | Dispatched intent with `cat` executor; appended `kind: turn` with body captured; idempotent |
| AGENTS.md host protocol | Installed in Sula self and 1terminal with sentinel; idempotent |

---

## What any project gains by adopting v1.0

1. **Cross-LLM continuity** — same project context works with any model (Kiro, Claude, Codex, Gemini, future models). Switch cost = 0.
2. **Cross-device portability** — folder syncs through git, Drive, Dropbox, or local; any device that reads text files is a workspace.
3. **Append-only project memory** — every decision/fact/goal preserved forever; supersession via refs, never deletion.
4. **Mechanical goal closure** — `done_when` + `verifier_ref` + skill = automatic closure; no human asking "is it done?"
5. **Tier A–E principles enforced at every boot** — no drift in design standards.
6. **Zero install for new agents** — hand a folder path; no SDK, no daemon, no Python package required by readers.
7. **Domain-agnostic** — code projects, governance, client services, creative work — same `render(fragments, conventions)` shape.
8. **byte-stable replay** — reproducible views from the same fragments; auditable.
9. **Skill-based extensibility** — agent superpowers (durable threads, voice, browser, automation) drop in as ~100-line scripts each. Core never grows when capabilities are added.
10. **Visible "感知" via turn-mark** — multi-line `[sula] +N this turn:` block at end of any turn that appended fragments.
11. **No technical-debt accumulation** — append-only means no maintenance burden.
12. **Free fork/branch** — copy the folder = full history; copy a subset = a derivative.

---

## Adoption guide for a new project

```bash
# 1. Make the folder
mkdir -p new-project/fragments

# 2. Drop in AGENTS template + canonical principles
cp /path/to/sula/tools/sula_vector/AGENTS.md   new-project/AGENTS.md
cp /path/to/sula/tools/sula_vector/principles/*.md   new-project/fragments/

# 3. Verify it boots
python3 /path/to/sula/tools/sula_vector/render.py new-project --for-agent
```

That's the entire onboarding. The output of step 3 is what every future
agent (any LLM) reads to gain full project context.

For existing legacy-Sula projects:

```bash
python3 /path/to/sula/tools/sula_vector/migrate.py --project-root /path/to/legacy-project
```

Idempotent. Leaves legacy `.sula/`, `STATUS.md`, and `docs/change-records/`
untouched (preserved for rollback).

---

## Convention freeze and semantic versioning

- **v1.x** — convention is **frozen**. Existing fragment files written against v1.0 will continue to parse and render identically across all v1.x releases.
- **v1.x.y minor releases** may add: new views, new recommended kinds, new skills, new optional frontmatter fields. They will not invalidate existing fragments.
- **v2.0** would only ship if a previously-valid fragment file would no longer parse. There is no current plan for v2.0.

---

## Known limitations (acknowledged, not blockers)

- `llm-dispatcher` ships with a generic shell-executor contract. Wiring to a specific LLM provider (Claude CLI, Codex CLI, OpenAI API, etc.) is the operator's choice — Sula stays provider-agnostic by design.
- The reference renderer's frontmatter parser handles the YAML subset Sula uses (scalars, inline lists, block lists, quoted strings, booleans). Full YAML 1.2 is intentionally not supported; if a project needs it, write fragments with the supported subset.
- No remote sync layer is bundled. Sula uses whatever substrate the project already has (git/Drive/Dropbox/local). This is a feature (B7), not a gap.

---

## Operating Sula Vector going forward

- The convention is finished. **Do not modify it casually.**
- New capabilities are skills. **Add to `tools/sula_vector/skills/`, do not bloat `render.py`.**
- The principles are immutable. **To revise one, append a `kind: decision` whose `refs` includes the principle's id.**
- The substrate handles storage and concurrency. **Sula does not.**

---

## Acknowledgement

This release is the result of a directed dimension-shift exercise: the
predecessor (Sula 0.18.x, ~945 KB single Python file with 12 parallel state
directories) was distilled to its essential dimension — an ordered folder
of typed fragments rendered by a pure function. The same shape covers code
projects, governance projects, client-service projects, and creative
projects. What was 30+ subcommands and a dozen overlapping subsystems is
now one verb (`append`) and one function (`render`).

Three orders of magnitude smaller. Strictly more capable in the dimensions
that matter (cross-LLM, cross-device, byte-stable, principle-enforced). And
it ships with the discipline to keep it that way.

— v1.0
