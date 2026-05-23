---
id: 2026-05-23T06-05-07Z--operation-public-release-v1-0
time: 2026-05-23T06:05:07Z
kind: operation
refs: [2026-05-23T05-33-46Z--release-sula-vector-1-0-ga, 2026-05-23T05-59-09Z--decision-each-project-self-contained]
tags: [public-release, github, v1-0]
author: jing
remote: https://github.com/irihiyahnj/sula-public.git
branch: main
tag: sula-vector-v1.0.0
commit: 1adc220
---
Sula Vector v1.0 GA published to public Git remote.

Repo:   https://github.com/irihiyahnj/sula-public
Branch: main (advanced from 658dc2c → 1adc220)
Tag:    sula-vector-v1.0.0 (eb7306d)

Adoption from this point:

  # New project
  git clone https://github.com/irihiyahnj/sula-public.git
  mkdir -p my-project/fragments
  cp -r sula-public/tools/sula_vector/ my-project/tools/sula_vector/
  cp sula-public/tools/sula_vector/AGENTS.md my-project/AGENTS.md
  cp sula-public/tools/sula_vector/principles/*.md my-project/fragments/
  python3 my-project/tools/sula_vector/render.py my-project --for-agent

  # Legacy 0.18.x project
  git clone https://github.com/irihiyahnj/sula-public.git
  python3 sula-public/tools/sula_vector/migrate.py --project-root /path/to/legacy-project

What this commit contains:
- 532 files changed, 17959 insertions, 21427 deletions
- Top-level README rewritten as v1.0 announcement (legacy 0.18.x preserved inline)
- New: tools/sula_vector/ (renderer, migrator, skills, AGENTS template, tests, RELEASE-NOTES)
- New: docs/sula-vector-convention.md (authoritative spec)
- New: fragments/ (Sula's own project memory, 340+ fragments)
- New: examples/{okoktoto,client-service-gdrive,field-ops-generic}/{fragments/,tools/}
- AGENTS.md adds host operating protocol section
- .gitignore expanded to exclude legacy .sula/ runtime state files (events,
  indexes, objects, sources, exports, projections, adapters, memory-digest)

Legacy Sula 0.18.x runtime (scripts/sula.py, .sula/) preserved untouched in
the repo. Recommended path forward is v1.0.

Convention frozen at v1.0 for all v1.x releases. Each project that adopts
gets its own self-contained tools/sula_vector/ — there is no shared central
runtime, by design.
