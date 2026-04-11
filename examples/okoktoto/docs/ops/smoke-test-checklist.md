# OKOKTOTO v5 Smoke Test Checklist

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

- [ ] production path `/app/` is correct
- [ ] production URL is reachable: `https://chn.okoktoto.com/app/`
- [ ] deployment workflow reference is correct: `.github/workflows/deploy-okoktoto-v5.yml`
