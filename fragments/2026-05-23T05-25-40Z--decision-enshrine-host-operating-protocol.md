---
id: 2026-05-23T05-25-40Z--decision-enshrine-host-operating-protocol
time: 2026-05-23T05:25:40Z
kind: decision
refs: [2026-05-23T05-25-40Z--decision-richen-changes-summary-mark, 2026-05-23T05-14-14Z--decision-adopt-sula-vector-convention]
tags: [host-protocol, AGENTS, boot, turn-mark]
author: jing
---
Migrate suffix in AGENTS.md now contains the explicit host operating
protocol:

1. At session start: note ISO time, run render --for-agent, read it.
2. Throughout the turn: append fragments per the convention.
3. At end of turn: if anything was appended, run render --view
   changes-summary --since <session_start> and display the multi-line
   block to the user.

The same protocol shipped to /home/jing/Project/projectdev/sula/AGENTS.md
and /home/jing/Project/projectdev/1terminal/AGENTS.md. Future migrations
via migrate.py emit the same suffix. From the next session onward, any LLM
that reads AGENTS.md will execute the protocol — making "感知" structurally
visible without any ceremony.
