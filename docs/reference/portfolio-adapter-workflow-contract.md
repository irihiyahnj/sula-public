# Sula Portfolio, Adapter, and Workflow Contract

This document defines how Sula should scale from one adopted repository to a multi-project workspace that may mix code projects, Google Drive projects, and future providers such as Feishu.

## Core Rule

Google Drive, Git, local filesystem, and future providers are adapters.

They are not project types and must not change the core Sula object model.

## Layers

### Core

Sula Core owns:

- project identity
- state snapshot
- events
- objects
- indexes
- query
- adoption, sync, doctor, and remove flows

### Adapter

Adapters connect Core to storage or provider-specific metadata:

- `local-fs`
- `repo`
- `google-drive`
- future `feishu-drive`

### Workflow Pack

Workflow packs define how a project routes artifacts and stages work:

- `generic-project`
- `client-service`
- `video-production`
- `software-delivery`
- `operating-system`

### Portfolio

Portfolio is the multi-project layer:

- project registry
- aggregate status
- cross-project query
- workspace grouping

## User-Facing Contract

Sula should act like a guided operator, not a memory test.

That means:

- users should connect a project and answer missing questions instead of memorizing Sula commands or file-routing rules
- adapters and workflow packs should supply enough metadata for setup flows to explain what will be managed
- the configured result should be inspectable afterward as a clear promise: which files go where, which state is tracked, and how the project can be queried

## Manifest Sections

Projects may declare:

- `[workflow]`
- `[storage]`
- `[portfolio]`

These sections extend project metadata without changing the core managed/scaffold split.

## Storage Adapter Contract

Storage adapters should expose:

- `provider`
- `sync_mode`
- `workspace_root`
- `provider_root_url`
- `provider_root_id`

For `google-drive` today, the supported mode is `local-sync`, where a Drive-synced local directory acts as the project root or workspace root.

Future direct API mode may enrich metadata, but must not become mandatory for Core.

`workspace_root` is a runtime access path for the current machine. It is not the durable cross-device identity of provider-backed artifacts.

## Workflow Pack Contract

Workflow packs should define:

- pack id
- valid slots
- default slot mapping per artifact kind
- stage vocabulary

Artifact routing should depend on the workflow pack, not on the storage adapter.

Example:

- `agreement` -> `contracts`
- `invoice` -> `finance`
- `shot-list` -> `production`

## Artifact Contract

Artifacts are first-class project objects.

Sula should track:

- id
- kind
- title
- slot
- path
- summary
- date
- workflow pack
- storage provider metadata

Artifacts should be stored in `.sula/artifacts/catalog.json` as Sula-managed operating metadata, while the actual file remains project-owned truth.

For provider-backed workspaces, artifact identity should reconcile provider metadata and project-relative location before falling back to one machine's absolute path.

See [provider-backed-artifact-identity.md](provider-backed-artifact-identity.md) for the target cross-device identity model.

## Portfolio Registry Contract

Portfolio registry entries should include:

- project name
- project slug
- root path
- profile
- workflow pack and stage
- storage provider
- workspace / portfolio id
- owner
- summary
- health
- last activity

The portfolio registry is allowed to be local machine state or live in a synced workspace. It should not be required to live in Git.

## Machine Interface Contract

The CLI should be usable by humans and by software.

Commands that matter for software integration should support `--json`:

- `onboard`
- `init`
- `adopt`
- `sync`
- `doctor`
- `status`
- `query`
- `artifact`
- `record new`
- `memory digest`
- `remove`
- `portfolio`

This lets chat tools, local agents, and future GUI integrations treat Sula as a local control protocol instead of scraping plain text.
