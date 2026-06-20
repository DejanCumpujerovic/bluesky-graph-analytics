# ADR 008: Composite primary key (did, run_id) on profiles

Status: Accepted

## Context

Re-running collection on the same snapshot must not overwrite historical profile rows from prior runs.

## Decision

`profiles` primary key is **`(did, run_id)`** with FK to `runs.id`. Follows keyed by `snapshot_id` for cross-run queries on the active snapshot.

## Consequences

- Storage grows with re-runs; `force_resnapshot` archives and clears snapshot data.
- Queries always scoped by `run_id` or `snapshot_id` as appropriate.
