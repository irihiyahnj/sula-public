---
id: 2026-05-23T05-54-53Z--correction-agents-md-relative-path-bug
time: 2026-05-23T05:54:53Z
kind: correction
refs: [2026-05-23T05-25-40Z--decision-enshrine-host-operating-protocol]
tags: [audit, bug-fix, path-fix]
author: jing
broken_behavior: AGENTS.md migration suffix used relative path 'tools/sula_vector/render.py' which only resolved correctly inside Sula's own repo
correct_behavior: migrate.py now substitutes the absolute path of Path(__file__).resolve().parent at install time
---
The host operating protocol previously installed the path 'tools/sula_vector/render.py'
as a relative path. Inside Sula's own repository this happens to resolve, but in any
external project (1terminal, medflow, okoktoto, etc.) the path was broken because
those projects do not contain tools/sula_vector/.

Fixed in migrate.py: install_agents_template now embeds the absolute path of
the canonical Sula tools directory (resolved from Path(__file__).resolve().parent)
into the suffix and into the template substitution. AGENTS.md files in Sula self
and 1terminal were repaired manually since they were generated before this fix.

Idempotence preserved: the sentinel <!-- sula-vector --> still marks already-migrated
files. To repair any future stale path, replace the sentinel block.

This correction itself was discovered during the bulk fleet upgrade (see the
operation fragment appended in the same turn).
