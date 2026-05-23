---
id: 2026-05-23T05-42-48Z--chronicle-sula-vector-v1-0-design-genealogy
time: 2026-05-23T05:42:48Z
kind: chronicle
refs: [2026-05-23T05-33-46Z--release-sula-vector-1-0-ga, 2026-05-23T05-37-XX--assessment-sula-vector-1-0-self-evaluation, 2026-05-23T05-14-14Z--decision-adopt-sula-vector-convention, 2026-05-23T05-14-14Z--decision-enshrine-tier-a-e-principles, 2026-05-23T05-14-14Z--decision-skills-extension-model]
tags: [genealogy, design-rationale, how-we-got-here, recoverable-context]
author: jing
---
Design genealogy of Sula Vector v1.0, condensed from the 2026-05-23 working session.
Recorded so that any future LLM, in any session, can recover not only WHAT was decided
but the SHAPE of reasoning that led there.

## Stages

S1. **Concern raised.** Operator observed Sula 0.18.x had drifted: a 945 KB single-file
    sula.py, 12 parallel state directories, 30+ subcommands. Symptoms suggested
    wrong-layer accumulation rather than wrong-feature accumulation.

S2. **MADCUT principles applied.** Read cinema-principle.md and render-as-pure-function.md
    in /home/jing/Project/projectdev/madcut. Distilled: find the essential dimension;
    don't fight, stand on top; geometry > size; cross the boundary; render-as-pure-function.

S3. **First uplift attempt — REJECTED.** Proposal: events.jsonl + render(events, policy)
    + adapter framework. Self-test failed Tier A: still inventing a new substrate;
    still 5+ co-equal concepts; was a refactor with vocabulary swap, not dimension
    shift.

S4. **Second uplift attempt — REJECTED.** Proposal: stand on git + markdown.
    Operator's reframe ("could it apply to non-code projects, e.g. company governance,
    client services?") exposed the hidden code-centric anchor. git is one substrate
    among many; choosing it as THE substrate is still wrong-layer.

S5. **Third uplift — ACCEPTED.** Proposal: a project = an ordered, append-only folder
    of typed text fragments; every view is render(fragments, conventions). Substrate
    is whatever the project already uses (git, Drive, Dropbox, local). Tested by
    folding Codex superpowers + four project-type domains; no new dimension required.

S6. **Tier A–E enshrined.** Five principle tiers (highest rule, invariants, aesthetics,
    discipline, anti-patterns) ship as kind:principle fragments. render --for-agent
    prepends them. Self-similar enforcement: principles obey the same convention they
    define.

S7. **Skills extension model.** Codex superpowers (durable threads, voice, steering,
    queuing, goals/verifiers, automations, MCP, browser/computer-use, side-panel
    artifacts) all became independent ~100-line scripts under skills/. Core
    render.py never grows when capabilities are added. Removability via rm.

S8. **Migration tool.** migrate.py: idempotent (3rd run = 0 net change), reads only
    legacy sources, writes only into fragments/, never touches .sula/ or STATUS.md.
    Demonstrated on two real adopted projects: Sula self (327 fragments), 1terminal
    (28 fragments). byte-stable across runs.

S9. **Three reference skills.** verifier-shell (closes goals via shell command),
    scheduler (fires cadence-tick when recurring intent's interval elapses),
    llm-dispatcher (pipes intent body to a configured executor command). All
    end-to-end exercised on real fragments.

S10. **User-visible turn-mark.** Rich multi-line --view changes-summary block:
     "[sula] +N this turn:" followed by one line per appended fragment with kind +
     summary, ✓/✗ for verification-fact. Silent on empty turns (C7).

S11. **Host operating protocol.** Written into AGENTS.md of every adopting project:
     at session start read --for-agent; throughout turn append fragments; at end of
     turn surface changes-summary. Sentinel-marked for idempotence. From the next
     session, any LLM that reads AGENTS.md executes the protocol.

S12. **v1.0 GA shipped.** 34 stdlib unittest tests pass in 1.6s; both vectors
     byte-stable; all 3 skills exercised; convention frozen for v1.x. RELEASE-NOTES.md
     written. Total tooling surface ~2895 lines, no third-party dependencies.

S13. **Self-assessment.** High-level by dimensional standards (right layer, minimal
     primitives, complexity collapsed); minimal by engineering standards (no ML, no
     algorithms, no distributed system). Two metrics disagree on purpose. Current
     value > investment cost; potential value >> current value, depending on adoption.

## Reasoning that did NOT make the cut

- **E10 anti-pattern "don't recreate 945KB single file": REJECTED.** At the right
  dimension this problem does not exist; listing it would be defending at the wrong
  layer (C2). Operator caught this and refused.

- **Cleanup tool to delete legacy .sula/: REJECTED.** Legacy files are inert; cleaning
  them is one human commit, not a Sula runtime concern. Building a tool would be
  E5 + C2 violation.

- **Auto-bootstrapping every host LLM session from inside Sula: REJECTED.** That is
  host-side concern (B7). Sula's role is to provide AGENTS.md instructions; whether
  the host follows them is the host's contract, not Sula's enforcement.

## What survives chat erasure

EVERY operational fact: Tier A–E principles, host protocol in AGENTS.md, render and
migrate tools, three skills, test suite, release fragment, assessment, this chronicle.
A fresh LLM on a fresh device can recover the system fully by reading AGENTS.md and
running render --for-agent.

## What does not survive

The dialogue's exact pacing and phrasings; specific tactical micro-decisions (e.g.
"demo on okoktoto before 1terminal") that did not produce durable artefacts. These
were correctly omitted by C7.

## Outcome

v1.0 is a frozen artefact plus a reproducible method. Adoption realises the value;
the artefact alone proves the method works.
