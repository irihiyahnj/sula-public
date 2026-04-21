# Sula Public Export

- generated_on: 2026-04-21T16:43:02Z
- source_tree: tracked files exported from the private source repository
- file_count: 295
- public_release_strategy: fresh-public-repo

This export intentionally omits git history so maintainers can create a fresh public repository from a clean tracked-file tree.

## Suggested Initialization

1. create a new empty public repository
2. copy this exported tree into that repository root
3. set an explicit public-safe git identity before the first commit
4. run `git init`, `git add .`, and create the initial public commit
5. update `site/sula.json` so `source_repository_url` and `source_ref` point at that published public repository
