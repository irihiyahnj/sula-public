---
id: 2026-05-23T05-45-41Z--correction-chronicle-broken-assessment-ref
time: 2026-05-23T05:45:41Z
kind: correction
refs: [2026-05-23T05-42-48Z--chronicle-sula-vector-v1-0-design-genealogy, 2026-05-23T05-38-31Z--assessment-sula-vector-1-0-self-evaluation]
tags: [audit, bug-fix, demonstrate-trust-model]
author: jing
supersedes_field: refs
broken_ref: 2026-05-23T05-37-XX--assessment-sula-vector-1-0-self-evaluation
correct_ref: 2026-05-23T05-38-31Z--assessment-sula-vector-1-0-self-evaluation
---
The chronicle fragment 2026-05-23T05-42-48Z--chronicle-sula-vector-v1-0-design-genealogy
contains a broken reference in its refs frontmatter:

  broken: 2026-05-23T05-37-XX--assessment-sula-vector-1-0-self-evaluation
  correct: 2026-05-23T05-38-31Z--assessment-sula-vector-1-0-self-evaluation

The bug was introduced by an unsubstituted placeholder during fragment authoring.
Per Tier B1, the chronicle cannot be edited or deleted. This correction fragment
records the truth: any reader following refs from the chronicle should treat the
correct id above as the assessment fragment.

This very correction is also a live demonstration of the v1.0 trust model the
operator was asking about: when a fragment claims something that turns out to be
wrong (here, a typo'd ref; in principle, a false "passed: true" or other fabricated
claim), the convention does not allow silent fixing — instead it requires an
append-only correction whose refs make both the broken claim and the fix
permanently visible. Audit is by reading; integrity is by visibility.
