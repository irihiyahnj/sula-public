# OKOKTOTO Example

This example shows how Sula represents the current OKOKTOTO v5 repository as a reusable profile consumer.

Key file:

- [`.sula/project.toml`](.sula/project.toml)

This example now also acts as the in-repo canary for Sula's single-project memory features.

Canary memory assets:

- [STATUS.md](STATUS.md)
- [CHANGE-RECORDS.md](CHANGE-RECORDS.md)
- [docs/change-records/](docs/change-records)
- [docs/releases/](docs/releases)
- [docs/incidents/](docs/incidents)
- [.sula/memory-digest.md](.sula/memory-digest.md)

The real project still keeps its own business truth and detailed history in its own repository. This example exists to verify that Sula Core can render, validate, and summarize a memory-aware project safely.
