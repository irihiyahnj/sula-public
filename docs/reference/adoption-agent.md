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
- `site/launch/index.html`
- `site/bootstrap/index.html`
- `site/sula.json`

## Existing Consumers

If a target repository already has `.sula/project.toml`, Sula should treat it as an existing consumer instead of a fresh adoption target.

That means the default review path becomes:

1. inspect the existing manifest and lockfile
2. run `doctor --strict`
3. preview `sync --dry-run`
4. report consumer state, blockers, warnings, and likely next steps

The report should explicitly say that the repository is already under Sula management.

Software integrations should prefer the JSON form so they can consume adoption reports and apply results without scraping prose.

## Tool Resolution

If the target repository does not include a local `scripts/sula.py`, the adoption agent should not stop at “CLI missing”.

Instead it should:

1. read `site/sula.json` or the hosted `/sula.json`
2. resolve the canonical Sula launcher or source from the declared URLs
3. prefer `site/launch/bootstrap.py` when no vendored local source exists
4. report an explicit source-availability blocker only after repository inspection is complete

This keeps the protocol anchored to a canonical source repository without requiring every target repository to vendor Sula locally.

## CLI Flow

Human-first guided onboarding:

```bash
python3 scripts/sula.py onboard --project-root /path/to/project
```

URL-first launcher path:

```bash
python3 launch/bootstrap.py --project-root /path/to/project
```

Low-level inspect and report:

```bash
python3 scripts/sula.py adopt --project-root /path/to/project
python3 scripts/sula.py adopt --project-root /path/to/project --json
```

Apply after approval:

```bash
python3 scripts/sula.py adopt --project-root /path/to/project --approve
python3 scripts/sula.py adopt --project-root /path/to/project --approve --json
```

## What The Report Must Cover

- recommended profile
- whether `generic-project` was selected as a safe fallback
- detected project facts
- selected projection mode
- visible projection files that will be created
- visible projection files that will be overwritten
- scaffold files that will be created
- scaffold files that will be preserved
- kernel files that will be created under `.sula/`
- blockers and warnings

## What Apply Must Do

- create the manifest and lockfile
- create or refresh the `.sula/` kernel state
- render the visible files required by the current projection mode
- preserve existing scaffold truth where appropriate
- create the initial adoption traceability
- validate the result
- tell the user how to use Sula afterward
