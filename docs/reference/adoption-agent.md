# Sula Adoption Agent

Sula should feel like an adoption agent, not a checklist.

## User Experience Goal

The default user request should be as short as:

`Please adopt Sula into this repository.`

Sula then handles the rest in two phases:

1. inspect and report
2. apply after approval

## CLI Flow

Inspect and report:

```bash
python3 scripts/sula.py adopt --project-root /path/to/project
```

Apply after approval:

```bash
python3 scripts/sula.py adopt --project-root /path/to/project --approve
```

## What The Report Must Cover

- recommended profile
- detected project facts
- managed files that will be created
- managed files that will be overwritten
- scaffold files that will be created
- scaffold files that will be preserved
- blockers and warnings

## What Apply Must Do

- create the manifest and lockfile
- render managed files
- preserve existing scaffold truth where appropriate
- create the initial adoption traceability
- validate the result
- tell the user how to use Sula afterward
