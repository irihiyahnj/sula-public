# Sula Vector

> **Append-only project memory: what was decided, why, and what changed.**
> Cross-LLM, cross-device, byte-stable, principle-enforced. Standard library only.

```
project_view  =  render(fragments, conventions)
```

A project's truth is an ordered, append-only folder of typed text files. Every
view — status, progress, agent boot context, audit trail — is a pure function of
that folder. No daemon, no state directory, no cache-as-truth, no vendor.

The same shape covers a code repository, a company folder of documents on a
sync service, a client-services engagement, and a personal project.

**Current release: v1.2.0** (2026-08-15) · Convention `1.1`, backwards
compatible with v1.0 · [Release notes](tools/sula_vector/RELEASE-NOTES.md)

---

## Table of contents

- [What this is, and what it is not](#what-this-is-and-what-it-is-not)
- [Honest assessment](#honest-assessment)
- [Quick start](#quick-start)
- [Updating an adopted project](#updating-an-adopted-project)
- [The three lanes](#the-three-lanes)
- [Fragment format](#fragment-format)
- [Frontmatter fields](#frontmatter-fields)
- [Views](#views)
- [The done-gate](#the-done-gate)
- [Mechanical capture](#mechanical-capture)
- [Judgment has no mechanical source](#judgment-has-no-mechanical-source)
- [Agent boot contract](#agent-boot-contract)
- [Principles: Tier A–E](#principles-tier-ae)
- [Skills: the extension model](#skills-the-extension-model)
- [Trust model](#trust-model)
- [Substrate and concurrency](#substrate-and-concurrency)
- [What is deliberately outside](#what-is-deliberately-outside)
- [Repository layout](#repository-layout)
- [Verification evidence](#verification-evidence)
- [Versioning](#versioning)
- [Release history](#release-history)
- [Documentation index](#documentation-index)
- [Governance](#governance)

---

## What this is, and what it is not

**It is** a memory and rationale layer. It answers one question your existing
tools cannot: *why is this project in the state it is in, and what is the
evidence?*

**It is not** a project operating system. It does not schedule, assign work,
track effort, resolve dependencies, or coordinate actors. Your substrate (git,
a sync service, a filesystem) and your existing tools keep doing all of that.

Three things become **impossible** rather than merely discouraged:

| | how |
| --- | --- |
| A fragment carrying a wrong id or timestamp | identity is derived from the filename |
| A dangling reference | the write path refuses unknown targets |
| An undetected missing *why* | a witnessed change nothing claims fails the done-gate |

Everything else the convention offers is **assisted discipline**, not a physical
constraint. That distinction is worth keeping in view.

---

## Honest assessment

Written into the homepage on purpose: a project whose thesis is honest records
should not oversell itself.

**What is demonstrated, not claimed:**

- **Cross-model handover works.** A model with no prior exposure to this project booted from the folder in two steps and, in the same session, found a real defect that the project's author, its test suite, and one of its verifiers had all missed.
- **Mechanical capture runs unattended.** On a git substrate the post-commit hook records path- and content-hash-level deltas with no human in the loop, and pairs them with the judgments of its own window.
- **The gate constrains its own authors.** Changing files without recording why fails `--view doctor`, including for the people who wrote the gate.
- **Rot is detectable.** On one adopted project `--view doctor` surfaced several hundred pre-existing structural problems that nothing had reported before.

**Where the value is conditional:**

- **It scales with project lifetime and turnover.** A two-week solo task gains close to nothing. Payoff needs months, multiple models or people, and someone eventually asking why.
- **The ceiling is the author's honesty.** The tooling detects a *missing* why, never a *low-quality* one. What it buys is that absence becomes expensive — not that rationale becomes reliable.
- **Marginal value differs by substrate.** For a code repository, `git log` and pull requests already carry part of the why, so this is an improvement rather than a first. For a folder of documents with no version control, the prior state is zero.
- **Maturity is limited.** The v1.2 mechanisms have little real-world mileage. The bug v1.2 fixes survived three weeks and a green test suite in v1.1.2. Expect v1.2 to have an undiscovered gap of its own.

The code is not the valuable part; it is about 5,200 lines and could be rewritten
in a weekend. The valuable part is the convention plus the fact that its failure
modes were found by running it: a self-healing gap notice, a boot context that
silently truncated live state, an installer that reported success while writing
a file no host read, a verifier weaker than the claim it closed, two copies of a
file list that drifted apart. Each was green in tests first and caught in real
use second.

---

## Quick start

### New project

```bash
git clone https://github.com/irihiyahnj/sula-vector.git
mkdir -p my-project/fragments
cp -r sula-vector/tools/sula_vector my-project/tools/sula_vector
cp sula-vector/tools/sula_vector/AGENTS.md my-project/AGENTS.md
cp sula-vector/tools/sula_vector/principles/*.md my-project/fragments/
python3 my-project/tools/sula_vector/hooks/install.py --project-root my-project
python3 my-project/tools/sula_vector/render.py my-project --for-agent
```

That is the entire onboarding. No install, no network, no daemon, no SDK. The
output of the last command is the boot context every future agent reads.

### Working in it

```bash
# a judgment: why, one append
python3 tools/sula_vector/note.py . --kind decision --title "<one line>" "<why>"

# evidence: mechanical, never narrated by hand
python3 tools/sula_vector/skills/witness.py --project-root .

# before claiming anything is done
python3 tools/sula_vector/render.py . --view doctor   # must exit 0
```

### Migrating a legacy Sula 0.18.x project

```bash
python3 sula-vector/tools/sula_vector/migrate.py --project-root /path/to/project
```

Idempotent. Legacy `.sula/`, `STATUS.md`, `docs/change-records/`,
`docs/releases/` and `docs/incidents/` are read and left untouched.

---

## Updating an adopted project

`migrate.py` is also the update path, and a one-line wrapper drives it from the
canonical repository:

```bash
bash tools/sula_vector/update-from-canonical.sh --project-root <path>
```

An update:

- refreshes every file in `tools/sula_vector/` to the canonical version
- rewrites the `sula-vector` protocol region of `AGENTS.md`, leaving everything the project wrote above it untouched, and leaving a region that does not look like a tool-written protocol alone with a report instead
- projects the host pointers (`CLAUDE.md`, `CODEX.md`, `GEMINI.md`, Cursor rules, Copilot instructions) so every entrypoint boots the same protocol
- never duplicates an existing fragment
- reports whether the resulting vector passes `--view doctor`

**One-time step when updating to v1.2.** Captures recorded before explicit
pairing existed arrive unclaimed, so the done-gate starts shut. Settle them
once:

```bash
bash tools/sula_vector/update-from-canonical.sh --project-root <path> --settle-legacy-captures
```

That appends a single `annotation` claiming those captures as uncollectible
debt, recording how many carry a commit subject and how many carry nothing at
all. It sits behind a flag because the fragment is a judgment, and a judgment
needs an author who chose to make it. Write the claim by hand instead if you
know what those changes were.

Each project decides when to update. There is no central push.

---

## The three lanes

Every fragment projects into exactly one lane at render time. `kind` stays a
free-form string; the lane is a projection for readers, never a validated enum.

| lane | question | who supplies it | typical kinds |
| --- | --- | --- | --- |
| `judgment` | **why** | you, deliberately | `decision`, `correction`, `principle`, `assessment`, `annotation`, `preference`, `pitfall` |
| `evidence` | **what** | the runtime, mechanically | `witness`, `fact`, `verification-fact`, `artifact`, `release`, `operation` |
| `direction` | **where to** | you, with a verifier | `intent`, `goal` |

The division *is* the protocol: **you are responsible for judgment, the runtime
is responsible for evidence.** Mechanical facts are never narrated by hand.

---

## Fragment format

```
fragments/2026-05-23T04-21-56Z--decision-monthly-cadence.md
```

```markdown
---
kind: decision
refs: [2026-04-12T10-00-00Z--fact-contract-signed]
tags: [cadence]
---
Monthly delivery cadence.
Rationale: matches the procurement cycle.
```

`id` and `time` come from the filename, always. Frontmatter copies are treated
as redundant and any disagreement is reported. `kind` is the only field that
must be authored. `:` becomes `-` in filenames so `ls` returns chronological
order with no tool at all.

A fragment is **never silently dropped**. A file with no frontmatter, no `kind`,
or an unparsable name still loads and surfaces in `--view doctor`. Silent loss
is the one failure an append-only store cannot recover from.

---

## Frontmatter fields

All optional except `kind`.

| field | meaning |
| --- | --- |
| `refs` | ids of related fragments, or symbolic refs like `family:<key>` |
| `tags` | free-form labels |
| `summary` | one-line headline used by every view |
| `lane` | override the lane derived from `kind` |
| `supersedes` | ids of judgments this replaces; they leave the boot context, trail visible in `--view effective` |
| `closes` | ids of directions this closes |
| `explains` | ids of witnessed changes this judgment accounts for |
| `explained_by` | ids of judgments a capture found in its own window; written by `witness`, never by hand |
| `governs` | paths a judgment is about; witnessed removal of all of them surfaces it in `--view decay` |
| `broken_ref` | one id or a list that never existed; acknowledges the dangling references pointing at them |
| `done_when` | machine-readable success condition for a direction |
| `verifier_ref` | what proves `done_when`, e.g. `shell: <command>` |
| `passed` | `true`/`false` on a `verification-fact` |
| `pointer` | path or URL of an external artifact |
| `thread_id` / `pinned` | group turns into a durable thread; pin it to the digest |
| `family_key` / `artifact_role` | group artifact siblings and their roles |
| `cadence` / `after` / `interrupt` | recurring, queued, and steering directions |
| `author` | who appended this fragment |
| `witness_ignore` | extra ignore patterns for capture — configuration is itself a fragment |

Supersession, closure and explanation are **explicit only**. Listing something
in `refs` never implies replacing, closing, or explaining it, so context links
stay free of side effects.

---

## Views

Every view is a deterministic function of the fragments and a query.

```bash
python3 tools/sula_vector/render.py . --for-agent            # boot context
python3 tools/sula_vector/render.py . --view journal         # day by day: decided / produced
python3 tools/sula_vector/render.py . --view effective       # judgments in force + retirement trail
python3 tools/sula_vector/render.py . --view goals           # directions + verification status
python3 tools/sula_vector/render.py . --view progress        # directions matched against evidence
python3 tools/sula_vector/render.py . --view unexplained     # witnessed change nothing claims
python3 tools/sula_vector/render.py . --view decay           # judgments whose subject is gone
python3 tools/sula_vector/render.py . --view principles      # Tier A–E in force
python3 tools/sula_vector/render.py . --view doctor          # integrity; exit 1 on problems
python3 tools/sula_vector/render.py . --view thread  --thread <id>
python3 tools/sula_vector/render.py . --view family  --family <key>
python3 tools/sula_vector/render.py . --view changes-summary --since <ISO>
python3 tools/sula_vector/render.py . --lane evidence --view list
```

Filters compose across views: `--kind`, `--lane`, `--since`, `--until`,
`--tag`, `--ref`, `--thread`, `--family`. `--json` on any view. New views are
new functions; none of them ever requires a new on-disk format.

---

## The done-gate

`--view doctor` is a pure function of the fragments — no state, no network, no
writes. Exit code 1 on any problem, so the same command works as a CI gate and
as a goal verifier.

| code | meaning |
| --- | --- |
| `no-frontmatter` | no `---` header block |
| `missing-kind` | `kind` is required |
| `unparsable-filename` | name does not start with `<YYYY-MM-DDTHH-MM-SSZ>--` |
| `unparsable-time` | frontmatter time is malformed and the filename could not supply one |
| `header-disagreement` | frontmatter id/time contradicts the filename |
| `duplicate-id` | two files claim one id |
| `dangling-ref` | points at an id nothing carries, and no fragment acknowledges it |
| `goal-without-verifier` | a wish, not a goal (B9) |
| `unexplained-change` | a witnessed change nothing claims (B8) |

The last two are invariant violations rather than malformed files. Both are
things only an author can supply, which is why the gate — not a notice — is
where they belong.

Repair is append-only, because the offending fragment can never be edited:

```bash
# a dangling reference: acknowledge the ids that never existed, in one append
python3 tools/sula_vector/note.py . --kind correction --broken-ref <id>,<id> "<what was lost>"

# a witnessed change with no why: claim it
python3 tools/sula_vector/note.py . --kind decision --explains <witness-id> "<why>"
```

`--broken-ref` is the one write flag that does **not** validate its targets:
those ids are broken precisely because nothing carries them.

---

## Mechanical capture

```bash
python3 tools/sula_vector/skills/witness.py --project-root .
python3 tools/sula_vector/hooks/install.py  --project-root .   # once
```

`witness` scans the project folder, compares it against the previously witnessed
state, and appends one `witness` fragment recording the delta: path, content
hash and size for every added, changed and removed file. On git it also records
`commit`, `branch`, and the commits since the previous capture. New documents
(`.pdf`, `.docx`, `.xlsx`, `.pptx`, `.pages`, `.key`, …) additionally become one
`artifact` fragment each, so they appear in `--view journal`.

Two properties carry the design:

- **No state directory.** Previous state is folded out of prior witness fragments, each holding only its own delta. Truth stays in `fragments/`.
- **Silent when nothing changed.** Running it twice appends nothing.

The installer wires whichever trigger the substrate already provides, and
nothing else:

| substrate | trigger |
| --- | --- |
| git repository | `.git/hooks/post-commit` |
| Kiro CLI | `.kiro/agents/sula.json` — `agentSpawn` injects the boot, `stop` witnesses the turn (written, not activated) |
| Kiro IDE | `.kiro/hooks/sula-witness.kiro.hook` |
| sync service or plain folder | a launchd timer on macOS, else the cron line to paste |

Sula starts and schedules nothing itself. Every trigger belongs to a system that
already exists.

---

## Judgment has no mechanical source

Capture closes half of an asymmetry, not all of it:

| lane | mechanical source | mechanical end |
| --- | --- | --- |
| `evidence` | `witness` | not needed; evidence only recedes into the past |
| `direction` | authored | `verifier_ref` (B9) |
| `judgment` | **authored — nothing can supply it** | `governs` decay, else supersession by hand |

The supply of *why* is not mechanizable and must not be faked. Generating it
from commit messages or chat transcripts would put a machine's inference into
the one lane that exists to hold deliberate thought — and that reads as if
someone had thought, which is worse than an empty lane.

What *is* mechanizable is the **demand**:

- **Absence is counted.** A witnessed change that neither `explained_by` nor `explains` claims fails the done-gate. Pairing is an explicit fact from whichever side knows it, because any rule of the form "some judgment came after the change" is discharged by the next unrelated append — and then the omission evaporates instead of being inherited.
- **Obsolescence is surfaced.** A judgment with `governs` appears in `--view decay` once the evidence lane reports its subject removed. Without it, judgment is the only lane with no ending, and it accumulates until most of what an agent reads at boot describes a system that no longer exists.
- **A reused verifier is questioned.** B9 requires a verifier, never that the verifier tests the claim; in general that is not decidable from the fragments. One subclass is: the same verifier standing behind several unrelated goals cannot discriminate any of them. `--view goals` marks every sharer and the boot lists the satisfied ones, where a hollow check is already load-bearing.

None of these writes a judgment. They make absence and decay expensive, which is
the most a convention can honestly do.

---

## Agent boot contract

Any LLM, on any device, joining a vector for the first time does exactly two
things:

1. Note the current ISO-8601 UTC time as `session_start`.
2. Run `render --for-agent` and treat the output as authoritative context.

Every subsequent action is one operation: **append a fragment**. The agent never
edits the past and never keeps hidden state. When it stops, the next agent — a
different model on a different machine — resumes by repeating the same two steps.

Optionally, at the end of a turn, the host surfaces the mark:

```bash
python3 tools/sula_vector/render.py . --view changes-summary --since <session_start>
```

```
[sula] +3 this turn:
  + decision    <summary>
  + correction  <summary>
  ✓ verification-fact  PASS  <goal>
```

The session boundary is host-local state, never Sula state. Silent when nothing
was appended.

---

## Principles: Tier A–E

The full set ships as `kind: principle` fragments inside every adopting project,
and `--for-agent` prepends them to every boot. A principle is revised by
appending a judgment that supersedes it; the trail stays visible forever.

### Tier A — Highest rule

> A project's truth is an ordered, append-only folder of typed fragments.
> Every view is `render(fragments, conventions)`.
> No mutation. No implicit state. No truth outside this convention.
>
> If anything else conflicts with this rule, this rule wins.

### Tier B — Invariants

| | |
| --- | --- |
| **B1** | No mutation. Append-only. Past fragments are immutable. |
| **B2** | No implicit state. Anything affecting render output must be a named fragment. |
| **B3** | `kind` is a free-form string. No central enumeration. |
| **B4** | No daemon, no kernel directory, no cache-as-truth, no central catalog. |
| **B5** | Given the same `(fragments, conventions)`, a rendered view is byte-stable. |
| **B6** | Any LLM, any device, two-step boot. Anything more required is a leak. |
| **B7** | The substrate handles storage and concurrency. Sula does not invent its own. |
| **B8** | Important context must land in fragments. Transcripts are not durable memory. |
| **B9** | Goals must carry a verifier. Ambition without verification is a wish. |

### Tier C — Aesthetics

| | |
| --- | --- |
| **C1** | 找到本质的维度，在那一层解决问题。极简和高级感不是目标，是维度找对了的结果。 |
| **C2** | 不搏斗，站上去。代码量骤降、问题消失（不是被处理，是不存在了）才是对的层。 |
| **C3** | 几何 > 尺寸。文件远超参考线 = 去看几何，不要拿剪刀。 |
| **C4** | 越过界限。常规的不要参考。 |
| **C5** | 极简交互：每一次变化 = 追加一个片段；不超过一个动作。 |
| **C6** | 隐喻贯穿一切。在 Sula 这一层，隐喻是「矢量与流」。 |
| **C7** | 不要 churn。没有有意义的变化就不追加片段。 |

### Tier D — Implementation discipline

| | |
| --- | --- |
| **D1** | Standard library only when reasonable. No mandatory third-party dependencies. |
| **D2** | Zero comments unless WHY is non-obvious. |
| **D3** | No TODO, no placeholders, no half-implementations. |
| **D4** | No backwards-compatibility shims. Change the code directly. |
| **D5** | No claim of done without verification. |

### Tier E — Anti-patterns (delete on sight)

| | |
| --- | --- |
| **E1** | Storing derived views as truth. |
| **E2** | Adding a state directory beside `fragments/`. |
| **E3** | Editing or deleting past fragments — even for "cleanup". |
| **E4** | Centralising the `kind` enumeration. |
| **E5** | Inventing a substrate/runtime/daemon when one already solves it. |
| **E6** | Wrapping fragments in a SaaS-shaped registry or API surface. |
| **E7** | Splitting a file purely to satisfy a line count. |
| **E8** | Leaving decisions in chat transcripts only. |
| **E9** | Declaring a goal without a verifier. |

Full text: [`docs/sula-vector-convention.md`](docs/sula-vector-convention.md) ·
[`tools/sula_vector/principles/`](tools/sula_vector/principles/)

---

## Skills: the extension model

A skill is an independent script that takes `--project-root <path>`, reads
fragments, does work, appends fragments, and exits. The registry is
`ls skills/` — no manifest, no plugin descriptor, no SDK, no version
negotiation. Adding one is one action; removing one is one action.

| skill | role |
| --- | --- |
| [`witness.py`](tools/sula_vector/skills/witness.py) | Mechanical evidence on any substrate. Records path + content hash per changed file, commits on git, and an `artifact` per new document. Silent when nothing changed. |
| [`verifier-shell.py`](tools/sula_vector/skills/verifier-shell.py) | Runs shell-command goal verifiers, emits `verification-fact`, closes goals. |
| [`scheduler.py`](tools/sula_vector/skills/scheduler.py) | Emits `cadence-tick` when a recurring direction's interval has elapsed. |
| [`llm-dispatcher.py`](tools/sula_vector/skills/llm-dispatcher.py) | Routes directions carrying `executor_command` to a configured executor, captures stdout as a `turn`. |
| [`auto-update-from-canonical.py`](tools/sula_vector/skills/auto-update-from-canonical.py) | Compares tooling hashes against canonical and updates when they differ. |

Skills are invoked by whatever scheduler the substrate already provides — cron,
launchd, git hooks, agent hooks, or a human. Sula never supervises them.

Every agent capability — durable threads, voice input, steering, queuing, goals
with verifiers, scheduled automations, browser or computer use, MCP adapters,
side-panel artifacts, preferences and pitfalls — expresses as a `kind` plus, at
most, a skill of this shape. The core renderer does not grow when capabilities
are added.

Contract: [`tools/sula_vector/skills/README.md`](tools/sula_vector/skills/README.md)

---

## Trust model

Sula cannot prevent a fragment from making a false claim. What it does is
structural:

1. **Append-only** — a false claim cannot be deleted.
2. **Byte-stable replay** — the claim/counter-claim trail is reproducible.
3. **A refs graph** — claims, evidence, disputes and corrections reference each other.
4. **The substrate handles concurrency** — no invented locking or consensus.

Any deception leaves a permanent trace. Readers traverse the graph and judge for
themselves. **Trust is a property of the reader, not of the convention.**
Identity signing, evidence-density audits and dispute resolution all layer on as
skills, never as core enforcement.

The same boundary applies to verification: the convention can ask whether a
verifier discriminates, and cannot answer whether it is correct.

---

## Substrate and concurrency

| substrate | what it provides |
| --- | --- |
| git | content-addressed history, signing, branching, merge, distributed clones |
| a sync service (Drive, Dropbox, OneDrive, iCloud) | live multi-user sync with per-file granularity |
| a plain local folder | trivial portability |
| any combination | works, because fragments are independent files |

Multiple agents and devices appending in parallel produce multiple new files.
Filesystem semantics resolve it. A vector stays valid even on a machine where no
Sula tooling exists — anyone can re-implement `render` in any language.

---

## What is deliberately outside

- a daemon or long-running process
- a kernel directory of derived state
- a central catalog or registry kept in sync with fragments
- a runtime that must be installed before a vector can be read
- an enumerated set of `kind` values
- bundled scheduling, orchestration or fleet management
- an upgrade protocol projects must follow

---

## Repository layout

```
AGENTS.md                        authoritative host operating protocol
CLAUDE.md CODEX.md GEMINI.md     thin pointers to AGENTS.md
.cursor/rules/ .github/          Cursor rules and Copilot instructions, same pointers
README.md                        this file
docs/
  sula-vector-convention.md      authoritative convention spec
tools/sula_vector/               canonical tooling; each project gets its own copy
  render.py                      pure-function renderer, every view
  note.py                        append a judgment; id/time derived, targets checked
  migrate.py                     idempotent migrator and update path
  update-from-canonical.sh       operator-level wrapper around migrate.py
  AGENTS.md                      host protocol template
  RELEASE-NOTES.md               release history and verification evidence
  principles/                    canonical Tier A–E principle fragments
  hooks/install.py               wire capture to git / Kiro / launchd / cron
  skills/                        witness, verifier-shell, scheduler, dispatcher, updater
  tests/                         stdlib unittest suite
  example/                       a small worked vector: code refactor + client engagement
fragments/                       this project's own memory, kept as a Sula vector
legacy/                          the archived Sula 0.18.x runtime, historical reference
```

Sula keeps its own memory as a Sula vector. Everything in `fragments/` — the
decisions, the corrections of those decisions, the releases, the mechanical
captures — is the project's own working record, readable with the same commands
documented above. It is the largest available worked example, including the
parts that were wrong.

| | |
| --- | --- |
| fragments | 433 |
| by lane | 303 evidence · 123 judgment · 7 direction |
| judgments in force | 54 (65 retired, trail intact) |

---

## Verification evidence

| check | result |
| --- | --- |
| Test suite (`tools.sula_vector.tests.test_sula_vector`) | **113 / 113 PASS** |
| `--view doctor` on this project's own vector | ✓ 0 problems, 433 fragments |
| `--view doctor` on the bundled example vector | ✓ 0 problems |
| Byte-stable replay of `--for-agent` | ✓ |
| Standard library only, Python 3.10–3.12 in CI | ✓ no third-party dependencies |
| `migrate.py` third-run idempotence | ✓ 0 net change |
| Update of an already-adopted project, from a clean clone of this repository | ✓ tooling refreshed, protocol rewritten, project's own text preserved, doctor 0 |
| Every reference skill exercised end-to-end on real fragments | ✓ |
| Tier A–E principles installed and surfaced at every boot | ✓ |
| Real-world adoption | multiple projects across git repositories, synced document folders, and plain folders |
| Portability (move the folder, re-run the boot) | ✓ |

Tooling size: about 5,200 lines including 1,700 lines of tests.

---

## Versioning

- **v1.x** — the convention is frozen. A fragment written against v1.0 keeps parsing and keeps its meaning across every v1.x release. The freeze covers fragment validity and semantics, not the exact bytes of a rendered view: a view that loses live state is a defect and gets fixed.
- **Minor releases** may add views, recommended kinds, skills and optional frontmatter fields. They may also change tool behaviour where that behaviour was wrong — v1.2 changed the exit conditions of `--view doctor`. Read the release notes before updating a project whose CI depends on it.
- **v2.0** would only ship if a previously valid fragment file stopped parsing. There is no current plan.

**No support window is promised.** Long-term support is a development goal, not
a commitment. Pin a tag if you need stability, and update deliberately.

---

## Release history

| version | theme |
| --- | --- |
| **v1.2.0** | The missing why is demanded, and judgment can end. Explicit pairing (`explained_by` / `explains`); `unexplained-change` in the done-gate; `governs` and `--view decay`; a reused verifier is questioned; `broken_ref` takes a list; the update path rewrites stale protocol text. |
| v1.1.3 | Capture wired to hosts that actually read it, after the installer was found reporting success while writing a file no host read. |
| v1.1.2 | The missing why made visible in the turn mark and the boot. Its central claim — that the omission is inherited — turned out to be false, and v1.2 fixes it. |
| v1.1.1 | Boot carries all live state. A single `n=10` cap had been truncating judgments in force. |
| v1.1 | Capture as invariant, errors made unrepresentable: derived identity, three lanes, supersession and closure, mechanical evidence. |
| v1.0 | General availability. Convention frozen; Tier A–E ship as fragments in every adoption. |

Details, including what was wrong and how it was found:
[`tools/sula_vector/RELEASE-NOTES.md`](tools/sula_vector/RELEASE-NOTES.md)

---

## Documentation index

| document | purpose |
| --- | --- |
| [`docs/sula-vector-convention.md`](docs/sula-vector-convention.md) | The authoritative convention spec. Read first. |
| [`AGENTS.md`](AGENTS.md) | The host operating protocol this project runs under. |
| [`tools/sula_vector/AGENTS.md`](tools/sula_vector/AGENTS.md) | The protocol template installed into adopting projects. |
| [`tools/sula_vector/RELEASE-NOTES.md`](tools/sula_vector/RELEASE-NOTES.md) | Release history, verification evidence, migration steps. |
| [`tools/sula_vector/skills/README.md`](tools/sula_vector/skills/README.md) | The skills contract. |
| [`tools/sula_vector/principles/README.md`](tools/sula_vector/principles/README.md) | Principles adoption guide. |
| [`tools/sula_vector/example/`](tools/sula_vector/example/) | A small worked vector demonstrating every lane. |
| [`fragments/`](fragments/) | This project's own memory, in vector form. |
| [`legacy/`](legacy/) | The archived 0.18.x runtime: a 945 KB single-file CLI with twelve parallel state directories and thirty-plus subcommands, kept as historical reference. Superseded; its tests are no longer run in CI, and rollback is by git tag. |

---

## Governance

[CONTRIBUTING.md](CONTRIBUTING.md) ·
[SECURITY.md](SECURITY.md) ·
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) ·
[Issue templates](.github/ISSUE_TEMPLATE/)

Licensing: see the repository's license file if present; otherwise treat the
contents as all rights reserved until one is added.
