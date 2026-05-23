---
id: 2026-05-23T05-14-14Z--goal-build-scheduler-and-dispatcher-skills
time: 2026-05-23T05:14:14Z
kind: goal
refs: [2026-05-23T05-14-14Z--decision-skills-extension-model]
done_when: scheduler.py and llm-dispatcher.py exist under tools/sula_vector/skills/ and pass py_compile
verifier_ref: shell:python3 -m py_compile tools/sula_vector/skills/scheduler.py tools/sula_vector/skills/llm-dispatcher.py
tags: [skills, codex-superpowers]
author: jing
---
Add two more reference skills so the Codex superpowers contract is
demonstrably complete:

- scheduler.py: read kind:intent fragments with cadence; emit a fresh intent
  when the interval has elapsed since the most recent occurrence.
- llm-dispatcher.py: read kind:intent fragments with executor_command; pipe
  the body to the configured shell command; append a kind:turn fragment
  with stdout/stderr and refs back to the intent.

Acceptance: both scripts compile clean and verifier-shell.py against this
goal closes it with PASS.
