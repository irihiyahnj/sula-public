# Deploy the Sula bootstrap site to Fly and prepare the custom domain

## Metadata

- date: 2026-04-11
- executor: Codex
- branch: codex/bootstrap-sula
- related commit(s): deployment batch on codex/bootstrap-sula
- status: completed

## Background

The static bootstrap site assets existed in the repository, but the domain `sula.1stp.monster` still returned an unusable response. The next step was to publish the site to a real host and prepare the domain cutover path.

## Analysis

- The existing Fly app `sula` was available and already had a stable preview hostname at `sula.fly.dev`.
- `fly deploy` through remote image builds failed because registry push requests returned `401 Unauthorized`, even though Fly account access itself worked.
- Fly Machines support writing local files directly into a container, so the site could be deployed without pushing a custom image to Fly Registry.

## Chosen Plan

- keep a deployment-ready `Dockerfile`, `Caddyfile`, and `fly.toml` in the repository
- switch the active `sula` Fly machine to the public `caddy:2.9-alpine` image
- write the static site files directly into the running machine
- register `sula.1stp.monster` as a Fly custom domain and capture the remaining DNS step explicitly

## Execution

- generated Fly app configuration with `fly config save -a sula`
- added `Dockerfile` and `Caddyfile` so future deployments have a repository-owned static hosting path
- updated the active machine `78465d2c250528` to use `caddy:2.9-alpine`
- wrote `site/` assets and Caddy configuration directly into the running machine
- verified that `https://sula.fly.dev/`, `/bootstrap/`, and `/sula.json` all return successful responses
- added `sula.1stp.monster` as a Fly certificate target, which is now waiting for DNS configuration

## Verification

- `curl -I https://sula.fly.dev/`
- `curl -I https://sula.fly.dev/bootstrap/`
- `curl https://sula.fly.dev/sula.json`
- `fly machine status 78465d2c250528 -a sula`
- `fly certs list -a sula`

## Rollback

- update the active Fly machine back to the previous image if the bootstrap site should be removed from Fly
- remove the Fly custom certificate entry if a different domain strategy is chosen

## Data Side-effects

- no application data side-effects
- live Fly hosting now serves the repository-owned static bootstrap site at `sula.fly.dev`

## Follow-up

- change the DNS for `sula.1stp.monster` to `CNAME sula. -> sula.fly.dev`
- confirm that Fly certificate status moves from `Awaiting configuration` to an active TLS state
- decide whether to keep the unused stopped historical machine or remove it during a later infrastructure cleanup

## Architecture Boundary Check

- highest rule impact: preserved; this deployment publishes the Sula bootstrap contract without changing the managed versus project-owned contract in adopted repositories
