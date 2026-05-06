# Sula 0.15.1 Session Report and STATUS Overflow Mechanism

## Metadata

- date: 2026-05-02
- kind: plan
- project: Sula
- workflow pack: operating-system
- workflow slot: design
- storage provider: local-fs
- document genre: proposal
- document bundle: problem-solution-workplan-raci

## Summary

Design and implement the `sula report` command and companion mechanisms so that every AI session can write its work summary back into STATUS.md, historical entries overflow to an archive to keep STATUS.md concise, and a new AI window can read the digest and immediately understand the project's current state without losing access to older context.

## Executive Summary

Sula's design intent is that STATUS.md serves as the project-owned truth source that any AI can read and immediately understand. The intended flow is: AI works → updates STATUS.md → Sula generates memory-digest.md → new AI window reads digest and knows the current state.

Today, this chain breaks at the first step: there is no command for an AI to write its session summary back into STATUS.md. The AI must manually edit STATUS.md, remember the template fields, and decide what to write — none of which is guided or validated by Sula. Furthermore, STATUS.md has no overflow mechanism, so over months of active work the Summary section would grow unboundedly, making the file harder to read for new AI windows.

This plan proposes a lightweight `sula report` command that accepts a session summary from the AI, writes it into STATUS.md in date-grouped form, automatically archives older entries when a threshold is exceeded, regenerates memory-digest.md, and outputs a structured brief that the AI can show to the user. Companion changes include Summary freshness validation in `sula check`, working tree dirtiness tolerance for runtime state, and consideration of whether memory-digest.md should be committed.

## Objectives And Scope

| Item | Details |
| --- | --- |
| Business objective | Make Sula a true zero-memory handoff system: any AI window at any time can read STATUS.md (or memory-digest.md) and know what the project is, what just happened, and what to do next. |
| In scope | `sula report` command; date-grouped Summary structure with automatic overflow archiving to `docs/ops/status-archive.md`; Summary freshness advisory in `sula check`; working tree dirtiness tolerance for runtime state files; `memory-digest.md` commit policy evaluation; change record auto-creation from report payload. |
| Out of scope | Rewriting existing 0.1.0-0.15.0 Summary entries into date groups (they stay as-is under `### 0.15.0 and earlier`); semantic analysis of git commits; automatic report generation without AI-provided summary text; changing the Handoff contract structure. |

## Current State And Constraints

### Current Flow

```
AI session works → (manual edit STATUS.md or nothing)
                → Sula reads STATUS.md
                → generates memory-digest.md (gitignored)
                → .sula/state/current.md (tracked)
                → sula check validates structure, not content freshness
```

### Observed Gaps (from 2026-05-02 session)

1. **No write-back command**: The 12 commits we made (committing 0.15.0, fixing gitignore, adding `git commit: any` sentinel, syncing canaries) were not recorded in STATUS.md Summary or Recent Decisions until we manually edited both files. A new AI window reading STATUS.md before our manual fix would not know any of this work happened.

2. **Summary structure is flat**: All 43 historical entries are in one list. There is no way to distinguish "what happened today" from "what happened in 0.1.0". Our fix added `### 2026-05-02` and `### 0.15.0 and earlier` sub-sections as a prototype of the date-grouped structure.

3. **memory-digest.md is gitignored**: `**/.sula/memory-digest.md` is in `.gitignore`, so a fresh `git clone` has no digest. The new AI must read CLAUDE.md, discover it needs to run `memory digest`, and do so before it can understand the project. This adds friction to the handoff flow.

4. **Working tree dirtiness self-inflicted**: Running `sula check` creates automation events that dirty the working tree (even though those files are now gitignored), and the working tree validation reports "dirty" against STATUS.md's claim of "clean".

5. **No freshness validation**: `sula check` validates STATUS.md structure (handoff fields present, git commit matches, etc.) but does not check whether the Summary content is stale — e.g., whether there are git commits newer than the last Summary date entry.

### Constraints

- STATUS.md must remain under ~200 lines for new-AI readability.
- The split between centrally managed OS files and project-owned truth must be preserved: `sula report` writes to project-owned files (STATUS.md, change records), not only to kernel state.
- The Handoff section format is already validated by `check` and `doctor --strict`. Any changes to Handoff fields must maintain backward compatibility.
- Automation events (`[automation]`) remain gitignored runtime state and are not project-owned truth. The report command bridges the gap by reading them and writing meaningful summaries to project-owned files.
- The template-based document design rules apply: this plan follows the `problem-solution-workplan-raci` bundle, and the implementation should use `sula workflow scaffold` for any new plan/spec/review documents.

## Proposed Approach

### 1. New Command: `sula report`

```
python3 scripts/sula.py report --project-root . \
  --summary "Fixed gitignore for runtime state. Added 'any' sentinel." \
  [--create-change-record] \
  [--archive-older-than 90d] \
  [--json]
```

#### Input

| Field | Required | Description |
| --- | --- | --- |
| `--summary` | yes | Human-readable summary of what was done this session. Multi-line supported. |
| `--create-change-record` | no | If set, also create a `docs/change-records/YYYY-MM-DD-{slug}.md` from the summary. |
| `--archive-older-than` | no | Override the default archive threshold (default: 90 days or configurable in manifest). |
| `--title` | no | Short title for the change record (used only with `--create-change-record`). |
| `--json` | no | Emit machine-readable output envelope. |

#### Behavior

1. Read the current STATUS.md.
2. Parse the Summary section, identifying existing date groups.
3. If a date group for today already exists, append to it. Otherwise, create a new `### YYYY-MM-DD` sub-section at the top of Summary.
4. Write the `--summary` text as bullet points under today's date group.
5. Update Handoff `verification date` to today.
6. If `--create-change-record` is set, scaffold a change record from a template (or from `--title` + `--summary`), write it to `docs/change-records/`, and update CHANGE-RECORDS.md index.
7. Update Handoff `latest record` and `start here` to point to the new change record (if created) or keep existing values.
8. Run the archive check: if any date group is older than the threshold, move its entries to `docs/ops/status-archive.md` under a dated section, and remove them from STATUS.md. If `docs/ops/status-archive.md` does not exist, create it with a header.
9. Regenerate `.sula/memory-digest.md` and `.sula/state/current.md`.
10. Record a `report.created` automation event.
11. Output:
    - Human-readable brief: "STATUS.md updated with N new entries under YYYY-MM-DD. Archived M old entries. Change record: path/to/record.md. Digest regenerated."
    - JSON envelope with the same data plus the new STATUS.md line count, archive path, and change record path.

#### Manifest Configuration (new optional section)

```toml
[status]
summary_max_date_groups = 5      # keep at most N date groups in Summary before archiving
summary_archive_days = 90        # auto-archive groups older than N days
summary_max_lines_per_group = 10 # warn if a single date group exceeds N lines
archive_path = "docs/ops/status-archive.md"  # where overflow goes
```

Defaults keep STATUS.md Summary at roughly 5 date groups * ~8 lines each + header/footer = ~60 lines for Summary, leaving room for Health, Focus, Blockers, Decisions, Handoff within the 200-line target.

### 2. Date-Grouped Summary Structure

STATUS.md Summary adopts a consistent structure:

```markdown
## Summary

### 2026-05-02

- Committed 0.15.0 release (118 files, +9742/-1038 lines)...
- Added `**/.sula/state/automation/*` to `.gitignore`...
- Added `git commit: any` sentinel to doctor validation...
- Verified all 4 canaries pass release readiness...

### 2026-05-01

- ... (0.15.0 features)

### 0.15.0 and earlier

- ... (historical milestones, kept as one collapsed group)
```

`### 0.15.0 and earlier` is a special group: it is never auto-archived (it represents the project's foundational capabilities). It can be manually trimmed during major version releases.

### 3. Archive Mechanism: `docs/ops/status-archive.md`

Already referenced in the Sula docs map (`docs/ops/status-archive.md`). The file currently exists and contains overflow from the `Current Focus` and `Blocker` sections (managed by `memory digest --archive`).

Extend it to also hold historical Summary entries:

```markdown
# Status Archive

## Archived Summary Entries

### 2026-04-22

- Strengthened handoff contract and Git upgrade flow...
- ...

### 2026-04-18

- ...
```

`sula query` already indexes `docs/ops/status-archive.md` through the source registry and kernel object extraction. No changes needed to the query path — historical entries become searchable automatically.

### 4. Summary Freshness Advisory in `sula check`

Add a new check to the `check` command:

```
If there are git commits newer than the most recent Summary date group:
  → advisory (not error): "STATUS.md Summary may be stale: N commits since last Summary entry (YYYY-MM-DD). Run `sula report` to update."
```

This is an advisory, not a hard error, because:
- Summary updates are project-owned (the AI/human decides what to write).
- There may be legitimate reasons to not record every commit (e.g., fixup commits, merge commits).
- `sula check` should not fail on a project-owned content decision, but should notify.

### 5. Working Tree Dirtiness Tolerance

Modify the `git working tree` validation in `doctor` and `check` to exclude files matched by `.gitignore` patterns when comparing against STATUS.md's declared state.

Implementation: after `detect_git_worktree_state` returns "dirty", run `git status --porcelain` and filter out lines matching `.gitignore` patterns (or, more simply, filter out paths under `.sula/state/automation/` and `.sula/state/orchestration/`).

Alternative: change `detect_git_worktree_state` to use `git diff --name-only` (which respects `.gitignore`) instead of `git status --porcelain`.

### 6. memory-digest.md Commit Policy

Two options:

| Option | Pros | Cons |
| --- | --- | --- |
| **A: Keep gitignored** | No diff noise from regenerated timestamps. | Fresh clone has no digest; new AI must run `memory digest` first. |
| **B: Remove from .gitignore, commit it** | Fresh clone immediately has digest. New AI reads it directly. | Regenerated timestamp on every `sula report` creates a diff that must be committed. |

**Recommendation**: Option B, with a modification — remove the `generated on` timestamp from memory-digest.md (keep only the content), and have `sula report` regenerate and stage it. This way the digest is always committed and up to date, without timestamp churn.

If the timestamp is needed for debugging, store it in `.sula/state/last-digest.json` (gitignored) instead of in the digest file itself.

### 7. Complete Target Flow

```
AI session works
  → AI calls `sula report --summary "..." [--create-change-record]`
  → STATUS.md Summary updated (date-grouped)
  → Old entries auto-archived to docs/ops/status-archive.md (if threshold exceeded)
  → Change record created (if requested)
  → memory-digest.md regenerated (committed, no timestamp)
  → AI shows brief to user: "STATUS.md updated. Check: ok. Archive: 3 entries moved."
  → AI commits STATUS.md + digest + change records
  → sula check passes (Summary fresh, structure valid, working tree clean)

New AI window opens
  → reads memory-digest.md (committed, always present)
  → sees latest Summary entries at the top
  → sees Handoff with next action
  → immediately knows current state and what to do
  → if needs history: sula query --q "gitignore" finds archived entries
```

## Milestones And Work Plan

| Milestone | Timing | Owner | Done Definition |
| --- | --- | --- | --- |
| Proposal approval | 2026-05-02 | Sula Core maintainers | This plan approved |
| `sula report` core command | 2026-05-03 | AI executor | `sula report --summary "..." --json` writes to STATUS.md, creates date groups, regenerates digest |
| Archive overflow | 2026-05-03 | AI executor | Date groups older than threshold auto-moved to `docs/ops/status-archive.md`; `[status]` manifest section validated |
| Summary freshness check | 2026-05-04 | AI executor | `sula check` emits advisory when commits exist newer than last Summary date |
| Working tree tolerance | 2026-05-04 | AI executor | `doctor` and `check` exclude gitignored paths from working tree dirtiness comparison |
| memory-digest.md commit policy | 2026-05-04 | AI executor | Digest regenerated without timestamp; removed from `.gitignore`; `sula report` stages it |
| Change record auto-creation | 2026-05-04 | AI executor | `--create-change-record` scaffolds from template and updates CHANGE-RECORDS.md |
| Integration test + canary | 2026-05-05 | AI executor | New tests for `sula report`; all 4 canaries pass; `sula release readiness` passes |
| Docs and CHANGELOG | 2026-05-05 | AI executor | README updated; CHANGELOG 0.15.1 entry; `docs/reference/` updated |

## Responsibility Matrix

| Work Package | Responsible R | Accountable A | Consulted C | Informed I |
| --- | --- | --- | --- | --- |
| Finalize proposal | Claude Code | Sula Core maintainers | — | — |
| `sula report` implementation | Claude Code / Codex | Sula Core maintainers | — | — |
| Archive + freshness + worktree | Claude Code / Codex | Sula Core maintainers | — | — |
| Tests + canary verification | Claude Code / Codex | Sula Core maintainers | — | — |
| Docs + release | Claude Code / Codex | Sula Core maintainers | — | Adopted projects |

## Risks And Decisions

### Risks

- **Summary format migration**: Existing adopted projects may have custom Summary formats. `sula report` should detect non-date-grouped Summaries and either convert them or add a `### YYYY-MM-DD` group without touching the existing flat list.
- **Archive file conflicts**: If `docs/ops/status-archive.md` already has content (from Current Focus/Blocker overflow), the new Summary archive sections must not collide with existing sections.
- **Digest commit churn**: If timestamps are removed from memory-digest.md but other generated fields remain, there may still be diff noise. The digest should be content-stable when the source documents haven't changed.

### Open Decisions

1. **`--create-change-record` default**: Should it be opt-in (flag required) or opt-out (default on, `--no-change-record` to skip)? Recommendation: opt-in for 0.15.1, gather feedback, potentially change default in 0.16.0.
2. **Archive threshold default**: 90 days or 30 days? Recommendation: 90 days for Sula Core (conservative), configurable per project in `[status]` manifest.
3. **`### 0.15.0 and earlier` group**: Should it be renamed to `### Version history` for clarity? Or kept as-is to preserve the release boundary? Recommendation: keep as-is; it serves as a natural separator between "current era" and "foundational history."
4. **memory-digest.md timestamp removal**: Is the `generated on` timestamp used by any downstream consumer? If not, remove it. If yes, move it to `.sula/state/last-digest.json`.

## Architecture Boundary Check

- highest rule impact: none. `sula report` writes to project-owned files (STATUS.md, change records, archive). The kernel continues to read from those files. The managed/project-owned split is preserved.
- New managed files: none. `[status]` manifest section is optional, defaults are safe for all existing projects.
- Sync impact: existing adopted projects remain compatible. They gain the `sula report` command and `[status]` manifest section on next sync. Projects that do not configure `[status]` use safe defaults (5 date groups, 90-day archive, `docs/ops/status-archive.md`).
