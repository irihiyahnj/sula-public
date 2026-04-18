# Contributing To Sula

Thanks for improving Sula.

## Before You Start

- read [AGENTS.md](AGENTS.md)
- read [README.md](README.md)
- review the current [STATUS.md](STATUS.md) and [CHANGE-RECORDS.md](CHANGE-RECORDS.md)
- keep the split between centrally managed operating-system files and project-owned truth intact

## Development Flow

1. work in a non-`main` branch, usually with the `codex/` prefix
2. keep changes focused and coherent
3. update durable traceability for non-trivial changes
4. consider sync impact on adopted projects before changing managed templates
5. run the relevant verification commands before opening a pull request

## Verification Baseline

For substantial code or template changes, run:

```bash
python3 -m py_compile scripts/sula.py tests/test_sula.py
python3 -m unittest discover -s tests -v
python3 scripts/sula.py doctor --project-root . --strict
python3 scripts/sula.py doctor --project-root examples/okoktoto --strict
python3 scripts/sula.py sync --project-root . --dry-run
python3 scripts/sula.py sync --project-root examples/okoktoto --dry-run
```

## Pull Request Expectations

- explain why the change is needed
- call out sync impact explicitly when managed behavior changes
- mention what was verified
- avoid mixing unrelated cleanup into the same batch

## Public Release Guardrail

Do not assume the repository is ready to be made public just because the working tree is clean. Review [docs/reference/public-release-readiness.md](docs/reference/public-release-readiness.md) before opening the repository or migrating it to a public remote.
