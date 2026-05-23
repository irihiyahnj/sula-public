---
id: 2026-05-23T05-54-53Z--operation-fleet-upgrade-to-v1-0
time: 2026-05-23T05:54:53Z
kind: operation
refs: [2026-05-23T05-33-46Z--release-sula-vector-1-0-ga, 2026-05-23T05-54-53Z--correction-agents-md-relative-path-bug]
tags: [fleet, bulk-migration, v1-0-rollout]
author: jing
projects_migrated: 12
projects_already_vector: 2
total_projects: 14
---
Bulk fleet upgrade: every Sula-adopted project on this device migrated to
Sula Vector v1.0 (or confirmed already-vector via idempotence).

Newly migrated this operation:
- /home/jing/Project/projectdev/madcut                                    64 fragments
- /home/jing/Project/projectdev/medflow/app                              222 fragments
- /home/jing/Project/projectdev/medflow/app3                             573 fragments
- /home/jing/Project/projectdev/medflow/medcut                          1444 fragments
- /home/jing/Project/projectdev/okoktoto                                 122 fragments
- /home/jing/Project/projectdev/okoktoto/bot/okoktoto-bot                 21 fragments
- /home/jing/Project/projectdev/okoktoto-v6                              161 fragments
- /home/jing/Project/projectdev/opensula                                  33 fragments
- /home/jing/Project/projectdev/sula/examples/okoktoto                    35 fragments
- /home/jing/Project/projectdev/sula/examples/client-service-gdrive       37 fragments
- /home/jing/Project/projectdev/sula/examples/field-ops-generic           37 fragments
- /home/jing/Project/医院/2026/昆明同仁医院                       127 fragments

Already-vector (idempotent re-run = 0 net change):
- /home/jing/Project/projectdev/sula                                     ~340 fragments
- /home/jing/Project/projectdev/1terminal                                  28 fragments

Excluded as frozen historical / sandbox copies (not migrated):
- /home/jing/Project/archive/*                  (frozen released artifacts)
- /home/jing/Project/projectdev/sula-public-*   (released version snapshots)
- /home/jing/Project/projectdev/.opensula-workspaces/*  (sandbox runs)
- /home/jing/.aoi/                              (not a project)

Path bug discovered and corrected mid-operation: see the correction fragment
listed in refs. AGENTS.md on Sula self and 1terminal repaired; new migrations
produced correctly from then on.

Verification:
- 34/34 unittest tests pass after migrate.py path fix
- byte-stable replay confirmed on 4 sample projects (madcut, medflow/medcut,
  opensula, 昆明同仁医院)
- migrate.py idempotent (Sula self + 1terminal third-run = no-op)
