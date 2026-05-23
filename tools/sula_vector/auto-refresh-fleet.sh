#!/usr/bin/env bash
# auto-refresh-fleet.sh — auto-update every Sula vector project on this device.
#
# Discovers projects by scanning for AGENTS.md files containing the
# <!-- sula-vector --> sentinel under a given root (default: $HOME).
# For each, invokes the project's own auto-update-from-canonical.py skill.
#
# Designed for cron:
#   0 3 * * *  /path/to/sula-vector/tools/sula_vector/auto-refresh-fleet.sh
#
# Idempotent: silent on no-op (Tier C7). Resilient to transient network
# failures (skill exits 0 on unreachable canonical).
#
# Usage:
#   auto-refresh-fleet.sh                       # default scan root: $HOME
#   auto-refresh-fleet.sh --root /some/path     # scan under given path
#   auto-refresh-fleet.sh --dry-run             # report what would happen
#   auto-refresh-fleet.sh --quiet               # cron mode (silent on no-op)

set -uo pipefail

ROOT="$HOME"
EXTRA_ARGS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)    ROOT="$2"; shift 2;;
    --dry-run) EXTRA_ARGS="$EXTRA_ARGS --dry-run"; shift;;
    --quiet)   EXTRA_ARGS="$EXTRA_ARGS --quiet"; shift;;
    -h|--help) sed -n '2,17p' "$0" | sed 's/^# //'; exit 0;;
    *) echo "unknown arg: $1" >&2; exit 1;;
  esac
done

# Discover Sula vector projects: AGENTS.md with the sentinel
declare -a PROJECTS
while IFS= read -r agents; do
  proj=$(dirname "$agents")
  skill="$proj/tools/sula_vector/skills/auto-update-from-canonical.py"
  if [[ -f "$skill" ]]; then
    PROJECTS+=("$proj")
  fi
done < <(grep -rl --include=AGENTS.md "<!-- sula-vector -->" "$ROOT" 2>/dev/null \
         | grep -v '/\.git/' \
         | grep -v '/pre-fix-backups/' \
         | grep -v '/uploads/' \
         | grep -v '/archive/' \
         | grep -v '/sula-public-0\.' \
         | grep -v '/sula-public-canonical/')

if [[ ${#PROJECTS[@]} -eq 0 ]]; then
  echo "no Sula vector projects found under $ROOT (looking for AGENTS.md with sentinel)"
  exit 0
fi

[[ "$EXTRA_ARGS" != *"--quiet"* ]] && echo "scanning ${#PROJECTS[@]} project(s) under $ROOT ..."

UPDATED=0
ERRORS=0
for proj in "${PROJECTS[@]}"; do
  skill="$proj/tools/sula_vector/skills/auto-update-from-canonical.py"
  if python3 "$skill" --project-root "$proj" $EXTRA_ARGS; then
    if ls "$proj"/fragments/*--operation-auto-updated-from-canonical.md >/dev/null 2>&1; then
      latest=$(ls -t "$proj"/fragments/*--operation-auto-updated-from-canonical.md 2>/dev/null | head -1)
      latest_mtime=$(stat -c %Y "$latest" 2>/dev/null || stat -f %m "$latest" 2>/dev/null)
      now_mtime=$(date +%s)
      if [[ -n "$latest_mtime" && $((now_mtime - latest_mtime)) -lt 60 ]]; then
        UPDATED=$((UPDATED + 1))
      fi
    fi
  else
    ERRORS=$((ERRORS + 1))
  fi
done

[[ "$EXTRA_ARGS" != *"--quiet"* || $UPDATED -gt 0 || $ERRORS -gt 0 ]] && \
  echo "fleet auto-refresh: ${#PROJECTS[@]} project(s), updated=$UPDATED, errors=$ERRORS"
