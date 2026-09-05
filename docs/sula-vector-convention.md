# Sula Vector Convention

> **A project's truth is an ordered folder of small typed text fragments.
> Every view (status, progress, AI context, governance report, edit decision list)
> is a pure function of that folder.**
>
> No daemon. No kernel directory. No cache as truth. No central type registry.
> The same shape works for code projects, governance projects, client-service
> projects, and creative projects (e.g. video edits).

Convention version: `1.2`

v1.1 adds three things and invalidates no v1.0 fragment: **derived identity**
(id and time come from the filename, never from hand-written frontmatter),
**three lanes** (a render-time projection of every fragment into judgment /
evidence / direction), and **mechanical evidence** (the `witness` skill
captures what changed instead of asking an agent to describe it).

v1.2 adds **reliable observation and focused reading**: atomic no-replace
publication for every built-in writer, full-content capture hashing, relation
validation, content-bound verification, and an optional task-focus reading
view. See [Reliable observation and focused reading (1.2)](#reliable-observation-and-focused-reading-12).

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
filename is filesystem-safe. Convention 1.2 also accepts microseconds, e.g.
`2026-09-05T00-00-00.123456Z--decision-<unique-suffix>.md`. Readers normalize
whole and fractional seconds when ordering; plain lexical sorting across both
formats is insufficient. Captures follow explicit parent links when clocks differ.

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

### Identity is derived, not declared (v1.1)

| field  | source of truth                                                     |
| ------ | ------------------------------------------------------------------- |
| `id`   | **the filename stem** — always                                       |
| `time` | **parsed from the filename** — always                                |
| `kind` | frontmatter; the only field that must be authored                    |

`id` and `time` may still appear in frontmatter (every v1.0 fragment has
them). They are then treated as a redundant copy: render ignores them for
identity and reports any disagreement as a `header-disagreement` problem. A
fragment can therefore never carry a wrong id or a wrong timestamp.

A fragment is **never silently dropped**. A file missing `kind`, or with an
unparsable filename, still loads and surfaces through `--view doctor`. Silent
loss is the one failure an append-only store cannot recover from.

Use `note.py` rather than writing files by hand — it derives identity from the
clock and refuses unknown `refs` / `closes` / `supersedes` targets, so a
dangling reference cannot be created in the first place.

`kind` is a free-form string. The convention does **not** enumerate kinds
centrally. Projects add new kinds whenever they need them. Render functions
operate generically by filtering on `kind` strings supplied at query time.

### Three lanes (v1.1)

Every fragment projects into exactly one lane. The lane is computed from
`kind` at render time (override with an explicit `lane:` field). This is a
projection for readers, not a validated enumeration — B3 and E4 still hold.

| lane        | question    | metaphor | typical kinds                                              |
| ----------- | ----------- | -------- | ---------------------------------------------------------- |
| `judgment`  | **why**     | 方向     | `decision`, `correction`, `principle`, `assessment`, `annotation`, `preference`, `pitfall` |
| `evidence`  | **what**    | 位置     | `witness`, `fact`, `verification-fact`, `artifact`, `release`, `operation` |
| `direction` | **where to**| 去向     | `intent`, `goal`                                            |

The division carries the operating rule: **a human or agent supplies judgment;
the runtime supplies evidence.** Anything mechanical (a file appeared, a commit
landed, a hash changed) must not be narrated by hand — see *Mechanical
evidence* below.

### Supersession, closure, explanation (v1.1)

Optional list fields make the append-only graph resolvable:

| field         | meaning                                                             |
| ------------- | ------------------------------------------------------------------- |
| `supersedes`  | ids of judgments this fragment replaces; render hides them from `--for-agent` and shows the trail in `--view effective` |
| `closes`      | ids of directions this fragment closes; closed directions leave the open list |
| `explains`    | ids of witnessed changes this judgment accounts for                 |
| `explained_by`| ids of judgments a capture found in its own window; written by `witness`, never by hand |

All three are explicit only. Referencing a fragment in `refs` never implies
replacing, closing, or explaining it, so context links stay free of side
effects.

Explanation is two-directional for one reason: a judgment cannot name a capture
that has not happened yet, and a capture cannot name a judgment written after it
fired. Whichever side knows, states it. What neither side claims is a real
omission — see *Judgment has no mechanical source* below.

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
| `governs`      | paths a judgment is about; witnessed removal of all of them surfaces it in `--view decay` |
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

| view              | what it returns                                                       |
| ----------------- | --------------------------------------------------------------------- |
| `list`            | all fragments matching the filter, sorted by `time`                   |
| `digest`          | judgments in force, open directions, recent evidence, pinned threads — the default agent context |
| `journal`         | day by day: what was decided, what was produced (the human/company view) |
| `effective`       | judgments in force plus the retired ones and what superseded them     |
| `doctor`          | structural integrity of the vector; exit code 1 when problems exist   |
| `progress`        | directions matched against evidence via `refs`                        |
| `goals`           | goals + their verification status                                     |
| `principles`      | Tier A–E currently in force                                           |
| `unexplained`     | witnessed change that no judgment claims                              |
| `decay`           | judgments in force whose `governs` subject the evidence says is gone  |
| `thread`          | turns in a single thread, time-ordered                                |
| `family`          | artifact family with members and latest entry per `artifact_role`     |
| `changes-summary` | what was appended in a window (used for the turn-mark)                |

All filters are open: `--kind`, `--lane`, `--since`, `--until`, `--tag`,
`--ref`, `--thread`, `--family`. New views are added by writing a new function;
they never require a new on-disk format.

### `--view doctor`

Doctor is a pure function of the fragments — no state, no network, no writes.
It reports: `no-frontmatter`, `missing-kind`, `unparsable-filename`,
`unparsable-time`, `header-disagreement`, `duplicate-id`, `dangling-ref`,
`goal-without-verifier`, `unexplained-change`. Exit code is 1 when anything is
found, so the same command works as a CI gate and as a goal verifier
(`verifier_ref: shell: python3 tools/sula_vector/render.py . --view doctor`).

The last two codes are invariant violations rather than malformed files: a goal
without a verifier is a wish (B9), and a witnessed change nothing claims has no
why anywhere (B8). Both are things only an author can supply, which is exactly
why the gate and not the notice is the right place for them.

A dangling reference is treated as acknowledged when some fragment records it
in a `broken_ref` field — the append-only repair path, since the broken
fragment itself can never be edited (B1, E3). `broken_ref` takes one id or a
list, so a project that inherited hundreds of bad references from hand-written
fragments settles them in one append:

```bash
python3 tools/sula_vector/render.py . --view doctor --json \
  | python3 -c "import json,sys;print(','.join(sorted({p['detail'][3:] for p in json.load(sys.stdin)['problems'] if p['code']=='dangling-ref'})))"
python3 tools/sula_vector/note.py . --kind correction --broken-ref <the ids> "<what was lost>"
```

`--broken-ref` is the one write flag `note.py` does not validate: those ids are
broken precisely because nothing carries them.

---

---

## Mechanical evidence (v1.1)

Asking an agent to remember to write down what it did is a prompt-layer
enforcement of a data-layer invariant: it fails silently and unobservably.
The `witness` skill removes the discretion.

```bash
python3 tools/sula_vector/skills/witness.py --project-root .
```

It scans the project folder, compares against the last witnessed state, and
appends one `kind: witness` fragment recording the delta — path, content hash,
size for every added, changed, and removed file. On a git repository it also
records `commit` and `branch` and lists the commits since the previous witness,
which gives sha-level traceability for free. Newly appeared documents
(`.pdf`, `.docx`, `.xlsx`, `.pptx`, `.pages`, `.key`, …) additionally get one
`kind: artifact` fragment each with a `pointer`, so they show up in
`--view journal`.

Two properties matter:

- **No state directory.** The previous state is not cached anywhere; it is
  folded out of the prior witness fragments, each of which carries only its own
  delta. Truth stays in `fragments/` (B2, B4, E1, E2).
- **Silent when nothing changed.** Running it twice appends nothing (C7).

Ignore patterns come from the defaults plus any fragment carrying a
`witness_ignore` field — configuration is itself a fragment, so it obeys B2.

### Judgment has no mechanical source

Witness closes half of the asymmetry, not all of it:

| lane | mechanical source | mechanical end |
| --- | --- | --- |
| `evidence` | `witness` | not needed; evidence only recedes into the past |
| `direction` | authored | `verifier_ref` (B9) |
| `judgment` | **authored — nothing can supply it** | `governs` decay, else supersession by hand |

The supply of *why* is not mechanizable and must not be faked. Generating it
from commit messages or chat transcripts would put a machine's inference into
the one lane that exists to hold deliberate thought — E1 in a new costume, and
worse than an empty lane because it reads as if someone had thought.

What is mechanizable is the **demand**:

- **Absence is counted.** A witnessed change that neither side claims is an
  `unexplained-change` in `--view doctor`, so the done-gate (D5) stays shut
  until the why lands. Explicit pairing is what makes this survive: any rule of
  the form "some judgment came after the change" is discharged by the next
  unrelated append, and the omission evaporates instead of being inherited.
- **Obsolescence is surfaced.** A judgment with `governs` retires the moment the
  evidence lane reports its subject removed. Without it, judgment is the only
  lane with no ending: it accumulates until boot weight inverts and most of what
  an agent reads at boot describes a system that no longer exists.

Neither mechanism writes a judgment. They make its absence and its decay
expensive, which is the most a convention can honestly do.

### A verifier is required, not proven

B9 makes a goal carry a verifier. Nothing checks that the verifier tests the
claim, and in general nothing can: whether a command proves a `done_when` is not
decidable from the fragments.

One subclass is decidable, because it is a fact about the fragments rather than
about the code: **the same verifier standing behind several unrelated goals
cannot discriminate any of them.** It passes for reasons that have nothing to do
with a particular `done_when`, so the resulting ✓ carries less than it appears
to. `--view goals` marks every goal that shares its verifier, and `--for-agent`
lists the *satisfied* ones — those are where a hollow ✓ is already being relied
on.

This never gates. Two goals may legitimately assert the same condition. The
notice asks a question; judging the answer stays with the reader, the same
boundary the trust model draws.

### Capture triggers

```bash
python3 tools/sula_vector/hooks/install.py --project-root .
```

The installer wires whichever mechanical trigger the substrate already
provides, and nothing else:

| substrate | trigger installed |
| --------- | ----------------- |
| git repository | `.git/hooks/post-commit` |
| Kiro CLI | `.kiro/agents/sula.json` — `agentSpawn` injects the boot, `stop` runs the finish gate (written, not activated) |
| Kiro IDE | `.kiro/hooks/sula-witness.kiro.hook` |
| Drive / Dropbox / plain folder | launchd timer on macOS, else the cron line to paste |

Sula still starts and schedules nothing itself (B7, E5). Every trigger belongs
to a system that already exists.

---

## Worked example: a company, not a codebase

A client-service folder on Drive. No git, no code, no build.

```bash
mkdir -p acme/fragments
cp -r tools/sula_vector acme/tools/sula_vector
cp tools/sula_vector/AGENTS.md acme/AGENTS.md
cp tools/sula_vector/principles/*.md acme/fragments/
```

Work happens the way it already happens — someone writes a proposal, someone
exports a quote sheet:

```bash
# a judgment: why, in one append
python3 acme/tools/sula_vector/note.py acme --kind decision \
  --title "对 Acme 采用月度交付节奏" --tags acme cadence "理由：匹配他们的采购周期。"

# the evidence: mechanical, no narration
python3 acme/tools/sula_vector/skills/witness.py --project-root acme \
  --label "Acme 提案与报价定稿"
```

```
$ python3 acme/tools/sula_vector/render.py acme --view journal
## 2026-07-25
  ◆ decision: 对 Acme 采用月度交付节奏
  · artifact: acme-提案-v1.pdf  [客户资料/acme-提案-v1.pdf]
  · artifact: acme-报价.xlsx  [客户资料/acme-报价.xlsx]
  · witness: Acme 提案与报价定稿
```

Later, the proposal is revised and the quote sheet withdrawn. Nobody records
that by hand:

```
$ python3 acme/tools/sula_vector/skills/witness.py --project-root acme
[witness] + witness  2026-07-25T11-15-35Z--witness.md  (+0 ~1 -1, 0 commit(s))
$ python3 acme/tools/sula_vector/skills/witness.py --project-root acme
[witness] no change
```

Any LLM handed the `acme/` folder now boots into the same context, on any
device, with no install and no network.

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
It is standard library only and demonstrates every standard view. Reimplement
it in any language; given the same `(fragments, conventions)`, the rendered
view is byte-stable.

The write path is `tools/sula_vector/note.py` (judgment) and
`tools/sula_vector/skills/witness.py` (evidence). Both are optional: a fragment
is just a text file, and a project stays valid if no Sula tooling exists on the
device.

---

## Versioning the convention

Bump the convention version when the fragment filename grammar requires a new
reader, or a previously valid fragment would no longer parse. Bumps are rare. Adding a recommended kind, a new view, or a
new optional field is **not** a bump — projects add those locally without
coordination.

Current convention version: `1.2` (2026-09-05). Existing v1.0/v1.1 fragments
remain readable. New writers use microseconds and unique filename suffixes;
update readers before sharing these new fragments. Existence and semantic
validation of explanation links is now enforced consistently in every view.

See `tools/sula_vector/RELEASE-NOTES.md` for release notes, verification
evidence, and the adoption guide.

## Reliable observation and focused reading (1.2)

Writers publish a fully written staging file with an atomic, no-replace hard
link. Staging files are temporary non-fragments; there is no state directory.
Unsupported filesystems fail explicitly. Migration preserves deterministic
legacy IDs and skips an existing destination without replacing it.

Capture streams full SHA-256 over every included regular file. Each new witness
records `hash_method`, `capture_ignore`, `coverage`, `capture_format: 2`, and
`capture_parents`. Multiple heads or missing ancestors prevent completion.
After synchronization, explicit `--reconcile` appends a full `snapshot: true`
with all observed heads as parents. It asserts the current local tree, not that
remote synchronization has occurred.

`finish.py` observes files, runs doctor, and scans again for intervening edits.
Doctor remains a pure fragment check. File observation, structural validity,
and task-specific acceptance are separate statements.

A `verification-fact` may carry `verified_tree_digest` and `verification_scope`.
The verifier checks the same inputs before and after the command and records
`verified_command`. Readers compare against the latest coherent witnessed tree:
`current`, `stale`, `unknown`, `failed`, or `unbound` for historical results
without a binding. The latest verification determines satisfaction unless a
direction was explicitly closed. No file digest proves an external service's
state or the correctness of a verifier.

Display selectors operate after relation resolution. `--until` bounds the
historical graph before resolution. A task focus is an optional reading view
after full boot: principles, `scope: global`, open directions and risks remain
visible; selected rationale and outgoing evidence links are included. It is not
a new source of truth. `review_after` is evaluated against recorded activity;
`review_when` is a business condition for the reader. Both require explicit
restatement or supersession to change a judgment's authority.
