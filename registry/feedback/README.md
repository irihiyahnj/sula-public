# Sula Feedback Registry

This directory is the Sula Core inbox for reusable feedback captured from adopted projects.

## Files

- `catalog.json`: machine-readable queue and decision index
- `inbox/<feedback-id>/`: one ingested feedback bundle plus any later decision record

## Operating Rule

Adopted projects may drift locally when they need an immediate fix, but reusable upstream changes should enter Sula Core through this registry before they are implemented and released.
