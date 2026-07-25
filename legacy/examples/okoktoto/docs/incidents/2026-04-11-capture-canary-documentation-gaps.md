# Capture canary documentation gaps

## Metadata

- date: 2026-04-11
- executor: Codex
- branch: codex/bootstrap-sula
- status: resolved

## Summary

Tracked the missing project-memory coverage discovered during the canary uplift.

## Impact

- before the uplift, the example could not verify whether single-project memory scaffolds and checks behaved correctly
- this created blind spots for future sync changes

## Timeline

- 2026-04-11: identified that the example only contained a manifest and README
- 2026-04-11: rendered the full Sula operating-system layer into the example
- 2026-04-11: added canary records and generated the first digest

## Root Cause

- the original example was intentionally lightweight and did not yet exercise Sula's memory contract

## Resolution

- promoted the example into a memory-aware canary
- added strict-doctor target files and durable memory records

## Follow-up

- keep the example aligned with doctor and digest behavior
- use the canary during future memory-related Sula releases
