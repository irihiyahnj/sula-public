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

### The Kernel Must Stay Separate From Visible Projections

If Sula rewrites too much visible surface by default, it becomes dangerous.

If it exposes too little structure, it stops being useful.

The right split is:

- Sula owns the `.sula/` kernel
- visible governance files stay optional projection packs
- the project owns its business facts

### Evolution Must Benefit Existing Projects

Sula is only valuable if improvements can be synced back into adopted repositories in a controlled way.

That is why Sula uses:

- a stable manifest
- a namespaced kernel
- optional projection packs
- scaffold starters
- doctor and check gates

### Profiles Before Premature Generalization

Sula should support project families through profiles.

It should not pretend that one set of architecture docs fits every stack.

The first profile is `react-frontend-erpnext` because it was extracted from real project use.
