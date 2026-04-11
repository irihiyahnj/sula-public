# Sula Philosophy

Sula exists to make high-quality project operations reusable.

## Principles

### One Source Of Truth Per Concern

- repository-specific hard rules stay in the project
- reusable operational patterns live in Sula
- one-off history stays in project change records

### Reuse The System, Not The Accident

Sula should capture durable patterns:

- how a project takes work
- how it decides release risk
- how it keeps traceability
- how AI tools stay aligned

It should not hard-code temporary project quirks as if they were universal.

### Managed Files Must Stay Narrow

If Sula overwrites too much, it becomes dangerous.

If it overwrites too little, it stops being useful.

The right split is:

- Sula manages the operating system
- the project owns its business facts

### Evolution Must Benefit Existing Projects

Sula is only valuable if improvements can be synced back into adopted repositories in a controlled way.

That is why Sula uses:

- a stable manifest
- managed templates
- scaffold starters
- doctor checks

### Profiles Before Premature Generalization

Sula should support project families through profiles.

It should not pretend that one set of architecture docs fits every stack.

The first profile is `react-frontend-erpnext` because it was extracted from real project use.
