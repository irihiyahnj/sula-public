# Formal Document Design Principles

This file defines how formal planning, proposal, report, process, and training documents should be structured in `OKOKTOTO v5`.

## Core Rules

- classify the document genre before drafting
- use the document's native professional structure, not screenshots or image-only layouts
- keep the editable source file as the project-owned truth
- prefer `markdown` for source documents unless the genre clearly needs tabular source data
- materialize derived `.docx`, `.html`, or `.xlsx` deliverables only when needed
- register derived deliverables in the artifact catalog when `register_derived_artifacts = true`

## Formal Genres

### Schedule

- default bundle: `monthly-gantt-dual-actions-raci`
- default sections:
  - Monthly Overview
  - Role-split Gantt
  - Counterparty Action Table
  - Internal Action Table
  - Responsibility Matrix

### Proposal

- default bundle: `problem-solution-workplan-raci`
- default sections:
  - Executive Summary
  - Objectives And Scope
  - Current State And Constraints
  - Proposed Approach
  - Milestones And Work Plan
  - Responsibility Matrix
  - Risks And Decisions

### Report

- default bundle: `executive-findings-actions`
- default sections:
  - Executive Summary
  - Background And Scope
  - Method And Evidence
  - Key Findings
  - Progress And Risks
  - Decisions And Requests
  - Next Actions

### Process

- default bundle: `purpose-workflow-controls-records`
- default sections:
  - Purpose And Scope
  - Roles And Inputs
  - Workflow Steps
  - Controls And Exceptions
  - Artifacts And Records
  - Metrics And Review

### Training

- default bundle: `outcomes-agenda-delivery-assessment-followup`
- default sections:
  - Audience And Outcomes
  - Agenda Overview
  - Preparation And Materials
  - Session Plan
  - Exercises And Assessment
  - Follow-up And Records

## Source-First Delivery Rule

1. maintain the source file first
2. materialize the provider-ready deliverable second
3. register the source and the derived deliverable in the Sula artifact catalog
4. keep provider-native files traceable through `derived_from` and provider metadata

## Anti-patterns

- delivering a screenshot where a table or structured section should exist
- replacing a schedule with a raw spreadsheet dump and no narrative structure
- editing only the derived `.docx` or `.xlsx` while leaving the source stale
- creating provider-native deliverables without registering them back into Sula
