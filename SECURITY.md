# Security Policy

## Reporting A Vulnerability

If you believe you found a security issue in Sula, do not open a public issue with exploit details.

Until a dedicated security contact is published, report the problem privately through a trusted maintainer channel and include:

- affected version or commit
- reproduction steps
- expected impact
- whether the issue affects only Sula Core or also adopted repositories

## Scope

Security issues may include:

- secrets or credentials committed into the repository
- template behavior that could cause adopted repositories to expose credentials or unsafe instructions
- path handling, file overwrite, or command execution bugs in `scripts/sula.py`
- governance mistakes that could cause unsafe automated rollout into adopted repositories

## Response Expectations

- triage the report
- confirm impact
- prepare a fix or mitigation
- document any required rollout action for adopted repositories

## Non-security Issues

Use normal issues for bugs, docs mistakes, or adoption ergonomics problems that do not have security impact.
