---
id: 2026-05-23T06-22-58Z--correction-agents-md-legacy-vs-vector-ambiguity
time: 2026-05-23T06:22:58Z
kind: correction
refs: [2026-05-23T05-25-40Z--decision-enshrine-host-operating-protocol, 2026-05-23T05-59-09Z--decision-each-project-self-contained]
tags: [b6-violation, audit, agents-md, structural-fix]
author: jing
broken_behavior: "migrate.py appended the Sula Vector host protocol to the END of pre-existing AGENTS.md files; legacy 0.18.x rules above the sentinel still read as authoritative to LLMs"
correct_behavior: "a top-of-file <!-- sula-vector-priority --> notice now declares the post-sentinel Vector protocol authoritative and marks any pre-sentinel rules as superseded"
---
A live LLM session in 1terminal exposed a B6 violation: the LLM read the
project's AGENTS.md top-down and treated 49 lines of legacy 0.18.x rules
("must run scripts/sula.py check", "treat SULA CHECK OK as completion gate",
"keep machine-owned kernel state under .sula/") as currently active, in
parallel with the Sula Vector protocol below the sentinel. It also asked
permission to run render --for-agent at session start instead of just doing
it as the protocol prescribes.

Root cause is structural, not behavioural: migrate.py appended the new
protocol to the BOTTOM of pre-existing AGENTS.md files. There was no
top-of-file marker telling readers "everything below the sentinel
supersedes everything above". A reading LLM saw two equally-formatted
authority blocks and got confused.

Fix:

1. migrate.py install_agents_template now also prepends a
   <!-- sula-vector-priority --> notice at the very top of any AGENTS.md
   it touches. The notice points at the sentinel block below and marks
   pre-sentinel rules as legacy/superseded. Sentinel-protected idempotence
   is preserved.

2. Bulk fleet repair: re-ran migrate.py on all 14 projects on this device.
   All 14 AGENTS.md files now have the priority notice at line 1.
   migrate.py status reported "priority-prepended" for all of them
   (verified before/after by grep).

3. README.md adds a new "Updating an already-adopted project" section
   documenting that migrate.py IS the update path. A one-line wrapper
   tools/sula_vector/update-from-canonical.sh ships for operators who
   want to refresh from the GitHub canonical source.

This is the second AGENTS.md correction shipped (first was the
relative-vs-absolute path bug at fragments/2026-05-23T05-54-53Z--correction-agents-md-relative-path-bug.md).
Both demonstrate the v1.0 trust model: real bugs found in deployed vectors
get fixed by appending corrections + applying structural fixes, with the
trail permanently visible.

Behavioural addendum (not a Sula bug, just a note): when a host LLM reads
AGENTS.md and sees "At session start: run render --for-agent", it should
JUST RUN IT, not ask permission. Asking for permission for explicitly-
prescribed protocol steps is a small failure of B6 boot semantics. This
correction's text and the priority notice should make the precedence
clear enough that future LLMs do not need to ask.
