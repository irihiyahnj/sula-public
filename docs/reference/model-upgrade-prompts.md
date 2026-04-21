# Model-facing Sula Upgrade Prompts

## Purpose

Use these prompts when you want a large model to upgrade an already-adopted project to a published Sula release with minimal operator explanation.

These prompts assume:

- Sula already has a published canonical Git source
- the target project is already under Sula management
- the model should inspect old managed files and current `.sula/` state before deciding what to change
- the model should finish at the stable-release bar, not stop at partial sync

Current canonical release for these prompts:

- launch contract: `https://sula.1stp.monster/launch/`
- public source: `https://github.com/irihiyahnj/sula-public.git`
- stable tag: `v0.14.0`

## Recommended Prompt Set

Keep three prompt variants and reuse them consistently:

1. standard upgrade
2. strict audit upgrade
3. batch fleet upgrade

This is enough for most real use. More variants usually create drift instead of clarity.

## Chinese Prompts

### 1. Standard Upgrade

```text
请按 Sula 发布升级协议处理当前项目：先读取 https://sula.1stp.monster/launch/ ，再使用 Sula v0.14.0 的公开发布源 https://github.com/irihiyahnj/sula-public.git 对当前仓库执行完整升级。你需要先检查旧文件和现有 .sula 状态，识别所有与最新稳定版不一致的内容，再完成 sync、memory digest、doctor --strict、check，并在结束时报告变更、遗留风险、是否已达到稳定版要求，以及后续使用方式。
```

### 2. Strict Audit Upgrade

```text
请按 Sula 严格升级审计协议处理当前项目：先读取 https://sula.1stp.monster/launch/ ，再基于 Sula v0.14.0 发布源 https://github.com/irihiyahnj/sula-public.git 对当前仓库进行一次完整的升级审计。你必须遍历旧的 managed files、docs、.sula 状态和 release/check 相关文件，找出所有不符合最新稳定版规范的地方；然后执行升级、修复必要问题、重建派生状态，并最终确认 doctor --strict 和 check 是否通过，哪些地方已达标，哪些地方仍需人工决策。
```

### 3. Batch Fleet Upgrade

```text
请按 Sula 批量升级协议处理这一批项目：先读取 https://sula.1stp.monster/launch/ ，并以 Sula v0.14.0 发布源 https://github.com/irihiyahnj/sula-public.git 作为唯一升级基线。对每个项目都先检查旧文件、现有 .sula 状态和与稳定版规范的差异，再执行完整升级与验证流程；每个项目最后都要输出升级结果、失败点、遗留风险、是否达到稳定版要求，以及是否还需要继续处理 staged memory 或旧 release 文档问题。
```

## English Prompts

### 1. Standard Upgrade

```text
Please handle this repository using the Sula release-upgrade protocol: first read https://sula.1stp.monster/launch/ , then use the published Sula v0.14.0 source at https://github.com/irihiyahnj/sula-public.git to perform a complete upgrade of the current repository. Inspect old managed files and the current .sula state first, identify every place that is out of line with the latest stable release, then complete sync, memory digest, doctor --strict, and check. At the end, report the changes, residual risks, whether the repository now meets the stable-release bar, and how the team should use it afterwards.
```

### 2. Strict Audit Upgrade

```text
Please handle this repository using the Sula strict upgrade-audit protocol: first read https://sula.1stp.monster/launch/ , then use the published Sula v0.14.0 source at https://github.com/irihiyahnj/sula-public.git to perform a full upgrade audit of the current repository. You must inspect old managed files, docs, .sula state, and release/check-related files, identify every place that does not match the latest stable-release standard, then execute the upgrade, repair necessary issues, rebuild derived state, and finally confirm whether doctor --strict and check pass, which areas are now compliant, and which areas still require human decisions.
```

### 3. Batch Fleet Upgrade

```text
Please handle this project fleet using the Sula batch-upgrade protocol: first read https://sula.1stp.monster/launch/ , and use the published Sula v0.14.0 source at https://github.com/irihiyahnj/sula-public.git as the only upgrade baseline. For each project, inspect old files, current .sula state, and differences from the stable-release standard before making changes, then complete the full upgrade and verification flow. Each project must end with a report of upgrade results, failure points, residual risks, whether it meets the stable-release bar, and whether staged memory or old release-document issues still need follow-up.
```

## One-line Versions

Use these when the model already understands the Sula operating style and you want the shortest viable instruction.

### Chinese

```text
请读取 https://sula.1stp.monster/launch/ ，并基于 https://github.com/irihiyahnj/sula-public.git 的 Sula v0.14.0 发布源，把当前项目完整升级到最新稳定规范，遍历旧文件与 .sula 状态，修复不一致项，直到 doctor --strict 和 check 达到稳定版要求，再汇报结果。
```

### English

```text
Please read https://sula.1stp.monster/launch/ and use the Sula v0.14.0 release at https://github.com/irihiyahnj/sula-public.git to fully upgrade this project to the latest stable standard, inspect old files and current .sula state, fix every mismatch, and continue until doctor --strict and check meet the stable-release bar, then report the result.
```

## Selection Rules

- use `standard upgrade` for most already-adopted projects
- use `strict audit upgrade` for projects with older drift, messy docs, or uncertain release hygiene
- use `batch fleet upgrade` when you are managing many repositories under one rollout
- use the one-line versions only when the model already has enough context to infer the rest of the workflow correctly

## Expected End State

No matter which prompt variant you use, the model should converge on the same minimum bar:

- the project is upgraded from the published Git release, not from an arbitrary mutable local checkout
- old managed files and current `.sula/` state have been inspected before changes are finalized
- derived state has been rebuilt
- `doctor --strict` passes
- `check` passes
- residual risks and manual decisions are reported explicitly
