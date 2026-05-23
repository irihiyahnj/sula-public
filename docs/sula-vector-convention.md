# Sula Vector Convention

> **A project's truth is an ordered folder of small typed text fragments.
> Every view (status, progress, AI context, governance report, edit decision list)
> is a pure function of that folder.**
>
> No daemon. No kernel directory. No cache as truth. No central type registry.
> The same shape works for code projects, governance projects, client-service
> projects, and creative projects (e.g. video edits).

Convention version: `1.0`

---

## The one-line model

```
project_view  =  render(fragments, conventions)
```

`fragments` is a folder of text files. `conventions` is this document. `render`
is a pure function. Everything else (status digests, progress reports, AI
context blocks, project memory, agent handoffs) is derived and disposable.

This is the same shape as MadCut's render-as-pure-function:
`EDL = render(transcript, intelligence, master, instructions[])`. Sula is the
generalization to arbitrary project domains.

---

## Workspace shape

Any folder that holds fragments is a **Sula vector**. Typical layout:

```
<project-root>/
├── AGENTS.md          ← copy of (or pointer to) this convention
└── fragments/         ← every fragment is one file here, append-only
    ├── 2026-05-23T04-21-56Z--decision-monthly-cadence.md
    ├── 2026-05-23T04-30-12Z--fact-contract-signed.md
    └── …
```

The substrate is whatever the project already uses:

- **Code project** — folder lives in git; commits hold the history
- **Company management / client service** — folder syncs through Drive, Dropbox, SharePoint
- **Personal project** — plain local folder
- **Mixed teams** — any combination, because fragments are independent files

A Sula vector is portable: copy the folder to any device, hand it to any LLM,
run `render`, and the agent has full project context. Nothing else needs to
travel with it.

---

## Fragment file

### Filename

```
<ISO-8601-time-Z>--<short-slug>.md
```

Example: `2026-05-23T04-21-56Z--decision-monthly-cadence.md`

The timestamp is the canonical creation time. `:` is replaced by `-` so the
filename is filesystem-safe and `ls` returns chronological order without any
tool.

### File body

```
---
id: 2026-05-23T04-21-56Z--decision-monthly-cadence
time: 2026-05-23T04:21:56Z
kind: decision
refs: [2026-04-12T10-00-00Z--fact-contract-signed]
tags: [hospital-acme, cadence]
---
Decided: monthly delivery cadence for hospital-acme.
Rationale: matches their procurement cycle and intake report rhythm.
```

### Required fields

| field  | meaning                                                              |
| ------ | -------------------------------------------------------------------- |
| `id`   | stable unique identifier (filename stem is the recommended default)  |
| `time` | ISO-8601 UTC timestamp; the canonical sort key                       |
| `kind` | a short string describing the role of this fragment                  |

`kind` is a free-form string. The convention does **not** enumerate kinds
centrally. Projects add new kinds whenever they need them. Render functions
operate generically by filtering on `kind` strings supplied at query time.

### Common optional fields

| field          | meaning                                                                                  |
| -------------- | ---------------------------------------------------------------------------------------- |
| `refs`         | list of other fragment ids (or symbolic refs like `family:<key>`, `thread:<id>`)         |
| `tags`         | free-form labels                                                                         |
| `thread_id`    | groups conversational turns into a durable thread                                        |
| `family_key`   | groups artifact siblings (provider-native + workspace-source + exported derivatives)     |
| `artifact_role`| role inside a family (`workspace-source`, `provider-native-source`, `exported-derivative`) |
| `pointer`      | URL or relative path to an external artifact (PDF, deck, sheet, code path, video)        |
| `done_when`    | machine-readable success condition for goals/intents                                     |
| `verifier_ref` | id of a fragment (or skill/test/recipe) that proves `done_when`                          |
| `passed`       | `true`/`false` on a `verification-fact` fragment                                         |
| `cadence`      | for recurring intents (`every-30m`, `daily`, etc.)                                       |
| `interrupt`    | `true` for steering: runners read latest intent before continuing                        |
| `after`        | id of a run/intent that this fragment should follow (queuing)                            |
| `pinned`       | `true` to mark this thread as pinned (surfaces in the digest)                            |
| `author`       | who appended this fragment (human, agent name, system)                                   |

---

## Recommended starter kinds

Common across domains. Treat as starters, not as a closed schema.

| kind                 | purpose                                                            |
| -------------------- | ------------------------------------------------------------------ |
| `intent`             | a desired direction or action                                      |
| `decision`           | a chosen option with rationale                                     |
| `fact`               | something that happened or was observed                            |
| `artifact`           | a deliverable (with `pointer`)                                     |
| `annotation`         | comment/markup on another fragment (uses `refs`)                   |
| `turn`               | a conversation turn (uses `thread_id`)                             |
| `goal`               | a long-running intent with `done_when` and `verifier_ref`          |
| `verification-fact`  | output of a verifier (test, benchmark, manual sign-off)            |
| `skill`              | a reusable workflow recipe                                         |
| `preference`         | persistent agent memory (likes/dislikes, defaults)                 |
| `pitfall`            | known issue to remember                                            |

Domain-specific kinds (`milestone`, `regulatory-approval`, `edit-instruction`,
`rendered-cut`, `ticket`, `incident`, `release`, …) are added by writing them.
The render function does not need to know them in advance.

---

## How relationships emerge

Relationships are not stored in a central index. They live in `refs` on
individual fragments and are joined at render time:

- Project progress = match `intent`/`goal` fragments against `verification-fact`/`fact` fragments via `refs`
- Conversation thread = group all fragments by `thread_id`
- Artifact family freshness = group by `family_key`, take latest per `artifact_role`
- Goal status = `goal` plus its `verification-fact` fragments via `refs`
- Steering = newest `intent` with `interrupt: true` for the active task

There is no separate "relations table" to keep in sync. There is only the
fragment graph and a render call.

This is the same property as MadCut: given the same `(fragments, conventions)`,
every view is byte-stable. Nothing depends on history of who rendered what
when.

---

## Standard views

The reference renderer exposes a small set of named views. Each view is a
deterministic function of the fragments and a query.

| view       | what it returns                                                              |
| ---------- | ---------------------------------------------------------------------------- |
| `list`     | all fragments matching the filter, sorted by `time`                          |
| `digest`   | recent decisions, open intents/goals, recent facts, pinned threads' last turn — the default agent context |
| `progress` | intents/goals matched against evidence facts via `refs`                      |
| `thread`   | turns in a single thread, time-ordered                                       |
| `family`   | artifact family with members and latest entry per `artifact_role`            |
| `goals`    | goals + their verification status                                            |

All filters are open: `--kind`, `--since`, `--until`, `--tag`, `--ref`,
`--thread`, `--family`. New views are added by writing a new function; they
never require a new on-disk format.

---

## Agent boot contract

Any LLM, on any device, joining a Sula vector for the first time does exactly
two things:

1. Read `AGENTS.md` (this document or a project-specific subset).
2. Run `render --for-agent` over the fragment folder.

Step 2 produces a compact text block: project line, recent decisions, open
intents/goals, recent facts, pinned threads' last turn. The agent has full
operational context from this single read.

Every subsequent agent action is one operation: **append a new fragment**. The
agent never edits past fragments and never maintains hidden state. When the
agent stops, the next agent — even on a different model and a different device
— resumes by repeating the same two-step boot.

This is what makes a Sula vector a vector in the strict sense: it points
somewhere (the folder), it carries direction (time-ordered fragments), and it
composes (multiple vectors merge by union of fragments).

---

## Agent superpowers, expressed in this convention

Each capability is a fragment kind plus an optional adapter. No new
dimension is required.

| Capability                           | fragment realisation                                                       |
| ------------------------------------ | -------------------------------------------------------------------------- |
| Durable threads                      | `kind: turn` with shared `thread_id`                                       |
| Pinned threads                       | a turn fragment with `pinned: true` (surfaces in digest)                   |
| Voice input                          | transcribed body in a `kind: intent` or `kind: turn` fragment              |
| Steering                             | `kind: intent` with `interrupt: true`; runner re-reads latest before each step |
| Queuing                              | `kind: intent` with `after: <run-or-intent-id>`                            |
| Browser / chrome / computer / MCP    | adapters that read `intent`, write `fact` and `artifact` fragments         |
| Skills                               | `kind: skill`, body holds the recipe                                       |
| Mobile                               | same vector; whichever device can write to the substrate writes a fragment |
| Scheduled automations                | `kind: intent` with `cadence: every-30m`; the scheduler is just an adapter |
| Thread automations                   | scheduled intent scoped to a `thread_id`                                   |
| Goals with verifiers                 | `kind: goal` with `done_when` and `verifier_ref`; `kind: verification-fact` with `passed: true` closes it |
| Side-panel artifacts                 | `kind: artifact` with `pointer`                                            |
| Annotations                          | `kind: annotation` with `refs`                                             |
| Shared memory / Obsidian-style vault | the fragment folder itself                                                 |
| Memories (preferences, pitfalls)     | `kind: preference`, `kind: pitfall`                                        |

---

## Substrate and concurrency

Sula does not handle storage, sync, or concurrency. The substrate does.

| substrate                           | what it gives                                                       |
| ----------------------------------- | ------------------------------------------------------------------- |
| **git**                             | content-addressed history, signing, branching, merge, distributed clone |
| **Google Drive / Dropbox / OneDrive** | live multi-user sync with per-file granularity                      |
| **plain local folder**              | trivial portability                                                 |
| **any combination**                 | works because fragments are independent files                       |

Multiple agents and multiple devices appending in parallel produce multiple new
files. Filesystem semantics resolve concurrency. Sula does not invent locking,
transactions, or consensus.

---

## What is explicitly outside Sula

These are deliberately **not** part of the convention:

- a daemon or long-running process
- a kernel directory of derived state (`.sula/state`, `.sula/objects`, `.sula/indexes`, etc.)
- a central catalog or registry kept in sync with fragments
- a runtime that must be installed before reading the vector
- enumerated `kind` types
- bundled scheduling, orchestration, or fleet-management subsystems
- a versioning protocol projects must follow to "upgrade Sula"

A Sula vector remains valid even if no Sula tooling exists on the device.
Anyone can re-implement `render` in any language.

---

## Built-in principles (Tier A through E)

Sula vector ships five tiers of principles as `kind: principle` fragments.
Every adoption copies them into its `fragments/` folder. `render --for-agent`
prepends the full Tier A–E text to every agent boot. Together with
invariant **B6** (any LLM, any device, two-step boot), this guarantees that
every session in any project starts with the principles fully visible.

### Tier A — Highest rule

> A project's truth is an ordered, append-only folder of typed fragments.
> Every view is `render(fragments, conventions)`.
> No mutation. No implicit state. No truth outside this convention.
>
> If anything else conflicts with this rule, this rule wins.

### Tier B — Invariants (must hold at all times)

- **B1.** No mutation. Append-only. Past fragments are immutable.
- **B2.** No implicit state. Anything that affects render output must be a named fragment.
- **B3.** `kind` is a free-form string. No central enumeration of kinds. New scenarios add strings, not dimensions.
- **B4.** No daemon, no kernel directory, no cache-as-truth, no central catalog.
- **B5.** Given the same `(fragments, conventions)`, the rendered view is byte-stable.
- **B6.** Any LLM, any device, two-step boot: read AGENTS.md, run `render --for-agent`. Anything more required is a leak.
- **B7.** The substrate (git / Drive / filesystem) handles storage and concurrency. Sula does not invent its own.
- **B8.** Important context must land in fragments. Conversation transcripts alone do not count as durable memory.
- **B9.** Goals must carry a verifier. Ambition without verification is a wish, not a goal.

### Tier C — Aesthetics

- **C1.** 找到本质的维度，在那一层解决问题。极简和高级感不是目标，是维度找对了的结果。
- **C2.** 不搏斗，站上去。代码量骤降、问题消失（不是被处理，是不存在了）才是对的层。
- **C3.** 几何 > 尺寸。文件远超参考线 = 去看几何，不要拿剪刀。
- **C4.** 越过界限。常规的不要参考。
- **C5.** 极简交互：每一次变化 = 追加一个片段；不超过一个动作。
- **C6.** 隐喻贯穿一切。在 Sula 这一层，隐喻是“矢量与流”。
- **C7.** 不要 churn。没有有意义的变化就不追加片段。

### Tier D — Implementation discipline

- **D1.** Standard library only when reasonable. No mandatory third-party dependencies.
- **D2.** Zero comments unless WHY is non-obvious (hidden constraint, workaround, non-obvious invariant).
- **D3.** No TODO, no placeholder functions, no half-implementations.
- **D4.** No backwards-compatibility shims. Change the code directly.
- **D5.** No claim of done without verification. Build / tests / byte-stable replay must pass where applicable.

### Tier E — Anti-patterns (delete on sight)

- **E1.** Storing derived views as truth (status snapshots, indexes, catalogs as primary).
- **E2.** Adding a new state directory beside `fragments/`.
- **E3.** Editing or deleting past fragments. Even "cleanup" or "merge" — append a new fragment that refs the old instead.
- **E4.** Centralizing the `kind` enumeration or central kind validation.
- **E5.** Inventing a new substrate / runtime / daemon when an existing one already solves it.
- **E6.** Wrapping fragments in a SaaS-shaped registry / orchestration / API surface.
- **E7.** Splitting a file purely to satisfy a line count.
- **E8.** Leaving decisions and context in chat transcripts only, never landed in fragments.
- **E9.** Declaring a goal without a verifier.

## Enforcement

The principles are enforced through the convention itself, not through a
runtime daemon. Three layers, each one a check that the next agent boot will
hit:

1. **Principles ship as fragments.** Every adoption copies the canonical
   `kind: principle` fragments from `tools/sula_vector/principles/` into its
   own `fragments/` folder. They obey the same append-only rule as everything
   else.
2. **`render --for-agent` always prepends Tier A through E.** No SDK, no
   daemon, no install step. Every LLM session in any project starts by
   reading them.
3. **`render --view principles`** lets humans and CI inspect the current set
   on demand and diff against the canonical set.

A principle is changed by appending a `kind: decision` fragment whose `refs`
include the principle's id and whose body explains the supersession. The
supersession trail remains visible in every subsequent render.

## Skills (Superpowers)

The convention deliberately keeps the core minimal: one folder of fragments
plus one render function. New capabilities — verifiers, voice transcription,
browser automation, scheduled refreshes, code-task dispatchers, anything an
agent might want to add — live **outside** the core, as **skills**.

A skill is a small, independent program that:

1. Takes `--project-root <path>` as its argument.
2. Reads fragments from `<project-root>/fragments/`.
3. Filters to fragments it cares about (by `kind`, `refs`, `tags`).
4. Does its work.
5. Appends new fragments back.
6. Exits.

Skills must obey every Tier B invariant. Skills must not introduce a state
directory, daemon, central registry, or SaaS-shaped wrapper. The "registry"
of available skills is `ls tools/sula_vector/skills/` — no manifest, no
plugin descriptor, no version negotiation.

Skills are invoked by whichever scheduler your substrate already provides
(cron, file-watchers, git hooks, agents, humans). Sula does not start,
schedule, or supervise skills — that is correctly the substrate's job (B7).

A reference skill ships at `tools/sula_vector/skills/verifier-shell.py`
(runs shell-command goal verifiers and emits `verification-fact` fragments).
The full skills contract is in `tools/sula_vector/skills/README.md`.

Adding a new skill is one action: drop a script into the skills folder.
Removing one is one action: delete it. No project changes are required.
This is the architectural lever that lets the core stay at ~1000 lines
while the surrounding ecosystem grows arbitrarily.

## Optional: turn-mark for user visibility

The convention itself is silent (C5, C7). A host LLM (Kiro / Claude / Codex
/ etc.) MAY surface a small one-line mark to its user at the end of any turn
in which it appended fragments. The mark is generated from the existing
`--since` filter:

```
$ python3 tools/sula_vector/render.py . --view changes-summary --since <session-start-ISO>
[sula] +4 (3 decision, 1 goal)
```

If nothing was appended this turn, the mark is `[sula] no changes` and the
host should not display it (C7).

The session-start timestamp is **host-local** state, not Sula state. Sula
remains stateless. Hosts that want this visibility track their own session
boundary and call `--view changes-summary --since ...` once per turn.

This pattern is principle-compatible:
- B2 (no implicit state): the timestamp lives in the host, not in Sula
- C5 (minimal interaction): one render call, one line out
- C7 (no churn): silent when nothing happened

## Reference renderer

A pure-Python reference implementation lives at `tools/sula_vector/render.py`.
It is standard library only, under 500 lines, and demonstrates every
standard view. Reimplement it in any language; given the same `(fragments,
conventions)`, the rendered view is byte-stable.

---

## Versioning the convention

Bump the convention version only when a previously-valid fragment file would
no longer parse. Bumps are rare. Adding a recommended kind, a new view, or a
new optional field is **not** a bump — projects add those locally without
coordination.

Current convention version: `1.0` (GA, ship-frozen 2026-05-23).

See `tools/sula_vector/RELEASE-NOTES.md` for the v1.0 release notes,
verification evidence, and the adoption guide.
