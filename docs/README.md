# Documentation

This folder contains living documentation for setup, API usage, and operational behavior.

## Documents
- `api_usage.md`: API base paths, planned endpoint map, request patterns, and examples.
- `runbook.md`: local runbook, split rules, settle-up behavior, idempotency expectations, and concurrency/consistency notes.

## Notes on Implementation State
- The repository currently contains scaffolding for the API modules and routes.
- Financial domain behavior described in these docs reflects MVP contract expectations from the project plan and task list.
- As implementation lands, examples and guarantees should be tightened to match actual endpoint contracts in `shared/api/openapi.yaml`.
