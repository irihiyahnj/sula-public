# Sula

> A pure-function project operating system for AI-native teams.
> Cross-LLM, cross-device, byte-stable, principle-enforced.

**Sula Vector v1.1** — capture as invariant, errors made unrepresentable.
Convention backwards-compatible with v1.0 (2026-05-23 GA).

A project's truth is an ordered, append-only folder of typed text fragments.
Every view (status, progress, AI context, audit trail) is `render(fragments,
conventions)`. No daemon, no kernel directory, no cache-as-truth. The same
shape works for code projects, governance projects, client-service projects,
and creative projects.

---

## Quick adoption

### New project

```bash
git clone https://github.com/irihiyahnj/sula-vector.git
mkdir -p my-project/fragments
cp -r sula-vector/tools/sula_vector/ my-project/tools/sula_vector/
cp sula-vector/tools/sula_vector/AGENTS.md my-project/AGENTS.md
cp sula-vector/tools/sula_vector/principles/*.md my-project/fragments/
cd my-project
python3 tools/sula_vector/render.py . --for-agent
```

That's the entire onboarding. Output of the last command is the boot context
every future agent (any LLM) reads.

### Legacy Sula 0.18.x project

```bash
git clone https://github.com/irihiyahnj/sula-vector.git
python3 sula-vector/tools/sula_vector/migrate.py --project-root /path/to/legacy-project
```

Idempotent. Leaves legacy `.sula/`, `STATUS.md`, and `docs/change-records/`
untouched (preserved for rollback). Each project becomes self-contained with
its own `tools/sula_vector/`.

### Updating an already-adopted project

`migrate.py` is also the **update** path. Re-running it on a project that has
already been migrated does the right thing:

- refreshes `tools/sula_vector/render.py` and skills to the canonical version
- adds any missing AGENTS.md sentinels (e.g. the priority notice)
- never duplicates existing fragments (sentinel/content idempotence throughout)

A one-line wrapper for the common case (refresh from GitHub):

```bash
sula-vector/tools/sula_vector/update-from-canonical.sh \
  --project-root /path/to/your-project
```

This is operator-level (not a per-project skill). Each project decides when
to update — there is no automatic central push. If you want a project to
stay on its current tooling version, simply do not run the update.

---

## What v1.0 gives any project

1. **Cross-LLM continuity** — same project context works with Claude, Codex, Kiro, Gemini, any future model. Switch cost = 0.
2. **Cross-device portability** — folder syncs through git, Drive, Dropbox, or local; any device that reads text files is a workspace.
3. **Append-only project memory** — every decision, fact, goal preserved forever; supersession via refs, never deletion.
4. **Mechanical goal closure** — `done_when` + `verifier_ref` + skill = automatic closure. No human asking "is it done?".
5. **Tier A–E principles enforced at every boot** — no drift in design standards.
6. **Zero install for new agents** — hand a folder path. No SDK, no daemon, no Python package required.
7. **Domain-agnostic** — code, governance, client services, creative work — same `render(fragments, conventions)`.
8. **byte-stable replay** — reproducible views; auditable.
9. **Skill ecosystem** — agent superpowers (durable threads, voice, browser, automation, verifiers) drop in as ~100-line scripts. Core never grows.
10. **Visible turn-mark** — multi-line `[sula] +N this turn:` block at end of any turn that appended fragments.
11. **No technical-debt accumulation** — append-only means no maintenance burden.
12. **Free fork/branch** — copy the folder = full project history; subset = a derivative.

---

## The one-line model

```
project_view  =  render(fragments, conventions)
```

`fragments` is a folder of text files. `conventions` is the spec (ship-frozen at v1.0). `render` is a pure function. Everything else is derived and disposable.

This is the same shape as MadCut's `EDL = render(transcript, intelligence, master, instructions[])` — generalised to arbitrary project domains.

---

## Tier A–E principles (enforced at every agent boot)

The full principle set ships as `kind: principle` fragments inside every
adopting project. `render --for-agent` prepends them to every boot.

### Tier A — Highest rule

> A project's truth is an ordered, append-only folder of typed fragments.
> Every view is `render(fragments, conventions)`. No mutation, no implicit
> state, no truth outside this convention. If anything else conflicts with
> this rule, this rule wins.

### Tier B — Invariants (B1–B9)

Append-only · No implicit state · `kind` is open · No daemon/kernel/cache-as-truth · byte-stable replay · Two-step boot for any LLM · Substrate handles concurrency · Important context lands in fragments · Goals must carry a verifier.

### Tier C — Aesthetics (C1–C7)

找到本质的维度 · 不搏斗站上去 · 几何 > 尺寸 · 越过界限 · 极简交互 · 隐喻贯穿 · 不要 churn.

### Tier D — Implementation discipline (D1–D5)

Standard library only · Zero comments unless WHY non-obvious · No TODO/placeholders/half-implementations · No backwards-compatibility shims · No "done" without verification.

### Tier E — Anti-patterns (E1–E9)

Storing derived as truth · State directories beside `fragments/` · Editing past fragments · Centralising `kind` enum · Inventing new substrate · SaaS-shape wrappers · Splits to satisfy line counts · Chat-only context · Goals without verifier.

Full text: [`docs/sula-vector-convention.md`](docs/sula-vector-convention.md) and [`tools/sula_vector/principles/`](tools/sula_vector/principles/).

---

## Skills (the extension model)

Skills are independent scripts under `tools/sula_vector/skills/`. Each takes
`--project-root <path>`, reads fragments, does work, appends new fragments,
exits. The "registry" is `ls skills/` — no manifest, no plugin descriptor,
no SDK.

Reference skills:

| Skill | Role |
| ----- | ---- |
| `witness.py` | Mechanical evidence on any substrate: diffs the project folder against state folded from prior witness fragments, records path + content hash per changed file (plus commits on git), emits `kind: artifact` per new document. Silent when nothing changed. |
| `verifier-shell.py` | Closes goals via shell-command verifier; emits `kind: verification-fact`. |
| `scheduler.py` | Fires `kind: cadence-tick` when a recurring intent's interval has elapsed. |
| `llm-dispatcher.py` | Routes `kind: intent` fragments with `executor_command` to a configured shell executor; captures stdout into a `kind: turn`. |

`witness.py` is what makes capture an invariant rather than a habit — wire it
once with `hooks/install.py` (git `post-commit`, Kiro `agentStop`, or cron).
Record judgments with `note.py`, which derives id/time from the clock and
refuses dangling references or goals without verifiers.

Skills contract: [`tools/sula_vector/skills/README.md`](tools/sula_vector/skills/README.md).

Every agent superpower (durable threads, voice, steering, queuing, goals,
automations, browser/computer-use, MCP, side-panel artifacts) implements as
a skill of this shape. The core renderer never grows.

---

## Trust model

Sula does not, and cannot, prevent a fragment from making a false claim.
What it does is structural:

1. Append-only — false claims cannot be deleted (B1).
2. byte-stable replay — claim/counter-claim trail is reproducible (B5).
3. refs graph — claims, evidence, disputes, corrections all reference each other (open `kind`).
4. Substrate handles concurrency (B7).

Together: any deception leaves a permanent trace. Readers traverse the refs
graph and judge for themselves. **Trust is a property of the reader, not of
the convention.** Identity signing, evidence-density audits, dispute
resolution — all layer on as future skills, never as core enforcement.

See [`fragments/2026-05-23T05-50-10Z--decision-trust-is-reader-side.md`](fragments/2026-05-23T05-50-10Z--decision-trust-is-reader-side.md) for the full crystallised meta-principle.

---

## Repository layout

```
AGENTS.md                      ← authoritative host operating protocol
CLAUDE.md CODEX.md GEMINI.md   ← thin pointers to AGENTS.md
README.md                      ← this file
docs/
  sula-vector-convention.md    ← authoritative convention spec (v1.1)
tools/
  sula_vector/                 ← canonical tooling. Each adopting project
                                 receives its own copy of this folder.
    render.py                  ← pure-function renderer (digest, journal,
                                 effective, doctor, goals, …)
    note.py                    ← append a judgment; id/time derived, refs checked
    migrate.py                 ← idempotent legacy → vector migrator
    AGENTS.md                  ← host operating protocol template
    RELEASE-NOTES.md
    principles/                ← canonical Tier A–E principle fragments
    hooks/install.py           ← wire witness to git / Kiro / cron
    skills/                    ← witness, verifier-shell, scheduler, llm-dispatcher
    tests/                     ← stdlib unittest suite (65 tests)
fragments/                     ← Sula's own project memory as a Sula vector
                                 (370+ fragments — decisions, releases,
                                 corrections, the v1.0 GA and v1.1 events)
legacy/                        ← Sula 0.18.x runtime, archived for reference:
                                 scripts/sula.py, .sula/, STATUS.md, tests/,
                                 CHANGELOG.md, docs/change-records/, examples/, …
```

The entire legacy Sula 0.18.x runtime now lives under `legacy/`, kept for
history and rollback. Nothing at the repository root except `legacy/` predates
the vector convention. The recommended path forward is Sula Vector v1.1.

---

## Verification evidence (Tier D5)

| Check | Result |
| ----- | ------ |
| Test suite (`tools.sula_vector.tests.test_sula_vector`) | **65/65 PASS** |
| `render.py --view doctor` on Sula's own vector | ✓ 0 problems, 375 fragments |
| Standard library only | ✓ no third-party deps |
| `render.py` byte-stable replay (Sula self) | ✓ |
| `render.py` byte-stable replay (1terminal) | ✓ |
| `migrate.py` 3rd-run idempotence | ✓ 0 net change |
| All 3 reference skills exercised end-to-end on real fragments | ✓ |
| Tier A–E principles installed and surfaced at every boot | ✓ |
| Host operating protocol installed in AGENTS.md | ✓ |
| Real-world adoption | 14 projects on this device migrated to v1.0 |
| Project portability test (move folder, re-run boot) | ✓ |

---

## Convention freeze and semantic versioning

- **v1.x** — convention frozen. Any fragment file written against v1.0 continues to parse, and keeps the same meaning, across all v1.x releases. The freeze covers fragment validity and semantics, not the exact bytes of a rendered view: a view that loses live state is a defect and gets fixed.
- **v1.x.y minor** — may add new views, new recommended kinds, new skills, new optional frontmatter fields. Never invalidates existing fragments.
- **v2.0** — only if a previously-valid fragment file would no longer parse. No current plan.

---

## Documentation

| Document | Purpose |
| -------- | ------- |
| [`docs/sula-vector-convention.md`](docs/sula-vector-convention.md) | Authoritative convention spec — read first. |
| [`tools/sula_vector/RELEASE-NOTES.md`](tools/sula_vector/RELEASE-NOTES.md) | v1.1 and v1.0 release notes, verification evidence, adoption guide. |
| [`tools/sula_vector/AGENTS.md`](tools/sula_vector/AGENTS.md) | Host operating protocol template. |
| [`tools/sula_vector/skills/README.md`](tools/sula_vector/skills/README.md) | Skills contract. |
| [`tools/sula_vector/principles/README.md`](tools/sula_vector/principles/README.md) | Principles adoption guide. |
| [`fragments/`](fragments/) | Sula's own project memory in vector form (chronicle, decisions, releases). |

---

## Legacy Sula 0.18.x

The earlier Sula runtime (945 KB single Python file `scripts/sula.py`, 12
parallel state directories under `.sula/`, 30+ subcommands) is archived under
`legacy/` as historical reference:

- [`legacy/CHANGELOG.md`](legacy/CHANGELOG.md) — release history through 0.18.14
- [`legacy/docs/release-process.md`](legacy/docs/release-process.md) — legacy release flow
- [`legacy/docs/change-records/`](legacy/docs/change-records/) — legacy change records

Existing 0.18.x adopted projects can migrate to the vector via:

```bash
python3 tools/sula_vector/migrate.py --project-root /path/to/legacy-project
```

The migrator is idempotent and never touches a project's own legacy `.sula/`,
`STATUS.md`, or `docs/change-records/`.

---

## Project governance

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [SECURITY.md](SECURITY.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
