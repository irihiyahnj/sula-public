# Sula Vector tooling

Project memory is an append-only `fragments/` folder. Render reads it; tools
publish complete new fragments. Python standard library only.

## Start and finish a session

```bash
python3 tools/sula_vector/render.py . --for-agent
python3 tools/sula_vector/note.py . --kind decision --title "Chosen approach" "Why this approach"
python3 tools/sula_vector/skills/finish.py --project-root .
```

`finish` captures files, runs doctor, then scans again to detect changes after
capture. Its success describes that observation, not future edits. Plain
`render --view doctor` checks recorded fragments without reading project files.

## Read a task's context

```bash
python3 tools/sula_vector/render.py . --for-agent --focus "contract"
python3 tools/sula_vector/render.py . --view goals --kind goal
python3 tools/sula_vector/render.py . --view effective --tag delivery
```

Use focus after the full boot. It selects matching text, tags, subjects and
outgoing evidence links. It keeps principles, judgments explicitly marked
`scope: global`, open directions and risk notices. It includes the selected
judgments' rationale; it never changes which judgments remain in force.

Mark a business review condition with `--field review_when="contract renewed"`
or `--field review_after=2026-12-01`. Date review uses the latest recorded
activity, keeping replay deterministic. Supersede or restate a judgment after
review; a review notice does not retire it automatically.

All display filters preserve the full evidence graph. `--until` explicitly
selects a historical graph; `--since` limits displayed objects only.

## Verify a file version

```bash
python3 tools/sula_vector/note.py . --kind goal --title "Validate delivery" \
  --done-when "Delivery checks pass" --verifier "shell: python3 checks.py" \
  --verify-path delivery --verify-path checks.py "Validate the delivery folder"
python3 tools/sula_vector/skills/verifier-shell.py --project-root .
python3 tools/sula_vector/render.py . --view goals
```

By default verification covers every captured file. Repeat `--verify-path` to
select relative files/directories, including all inputs and dependencies the
check relies on. The verifier hashes before and after the command. Changing
its inputs invalidates the result. Later captured changes mark old results
`stale`; old results without a binding are shown as `unbound`. External services
and runtime environments are not covered by file hashes.

## Storage and sync

Convention 1.2 accepts both second and microsecond timestamps. New fragment
names carry random suffixes. `append.py` stages a complete file inside
`fragments/`, flushes it, and uses an atomic no-replace hard link to publish it.
A `.tmp` left by a killed process is not a fragment. An unsupported filesystem
fails explicitly; it must not silently fall back to an overwriting write.

`witness` streams SHA-256 for every included regular file, including large
media. Ignore patterns and excluded symlinks are recorded as coverage. Read or
mid-read mutation errors stop capture. The first capture after upgrading old
fingerprints refreshes the stored hashes, so it may list unchanged-content files.

New captures name their parents. Missing ancestors and concurrent capture
branches fail doctor rather than silently choosing a tree. After fully syncing
the project files and fragments, merge the observed branches with:

```bash
python3 tools/sula_vector/skills/witness.py --project-root . --reconcile
python3 tools/sula_vector/skills/finish.py --project-root .
```

Reconciliation records the current local tree as a complete snapshot. It does
not perform synchronization or decide which device's files should win.

The updater copies `append.py`, `capture.py`, `migrate.py` and all skills as one
tooling set. Update every writer/reader before it consumes convention 1.2
fragments. Existing fragments are never rewritten.
