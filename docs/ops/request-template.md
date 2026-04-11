# Sula Request Template

This template reduces back-and-forth. It is not mandatory, but it is the fastest way to get predictable delivery.

## Minimal Input

1. Goal
2. Constraints
3. Acceptance criteria
4. Priority

## Template

```md
## Goal
<what result you want>

## Background
<why this matters now>

## Constraints
- <what cannot be changed>
- <what approaches are not allowed>

## Acceptance Criteria
- <user-visible outcome>
- <admin-visible outcome>
- <failure behavior>

## Related History
- <existing change record / incident / release note if relevant>

## Priority
<P0 / P1 / normal / exploratory>

## Release Expectation
<working branch only / ready for deployment branch / do not deploy>
```

## Default Assumptions

If not specified otherwise:

- implementation is preferred over pure analysis
- working-branch delivery is preferred over silent deployment
- the highest architecture rule still applies
- existing project memory should be reused before creating new rules
