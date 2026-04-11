# Sula Smoke Test Checklist

Apply the global checks plus the impacted module checks.

## Global

- [ ] application shell opens
- [ ] login and session behavior are sane
- [ ] primary navigation loads
- [ ] no obvious fatal API or runtime errors

## Impacted Flows

- [ ] changed feature path is manually exercised
- [ ] error state is checked
- [ ] permission or role boundaries are checked if relevant

## Deployment-Specific

- [ ] production path `/` is correct
- [ ] production URL is reachable: `https://github.com/irihiyahnj/sula`
- [ ] deployment workflow reference is correct: `.github/workflows/ci.yml`
