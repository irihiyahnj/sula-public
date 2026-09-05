## Summary

- what changed
- why it changed

## Verification

- [ ] `python3 -m unittest discover -s tools/sula_vector/tests -v`
- [ ] `python3 tools/sula_vector/skills/finish.py --project-root .`
- [ ] `python3 tools/sula_vector/render.py . --for-agent > /dev/null`
- [ ] `python3 tools/sula_vector/render.py tools/sula_vector/example --view doctor`
- [ ] other project-specific verification is described below

## Sync Impact

- [ ] no adopted-project sync impact
- [ ] sync impact is described below

## Traceability

- [ ] fragments/ contains a judgment explaining this change (`note.py`)
- [ ] mechanical capture was witnessed and doctor stays clean (`skills/witness.py`)

## Notes

Describe any rollout caveats, follow-up work, or explicit non-goals.
