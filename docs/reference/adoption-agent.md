# Sula Adoption Agent

Sula should feel like an adoption agent, not a checklist.

## User Experience Goal

The default user request should be as short as:

`Please take over this repository using the Sula bootstrap protocol: first read https://sula.1stp.monster/, inspect the repo and produce an adoption report, wait for my approval, then adopt it and report the changes, risks, and how to use it.`

Chinese equivalent:

`请按 Sula bootstrap 协议接管当前仓库：先读取 https://sula.1stp.monster/ 的说明，inspect 并输出 adoption report，等我批准后再 adopt，完成后汇报变更、风险和使用方式。`

Sula then handles the rest in two phases:

1. inspect and report
2. apply after approval

The public-facing copies of this contract should live in:

- `site/index.html`
- `site/bootstrap/index.html`
- `site/sula.json`

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
