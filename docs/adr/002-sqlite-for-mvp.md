# ADR 002: SQLite for MVP

Status: Accepted

## Context

Phase 1 is a single-researcher MVP with one crawl at a time and local reproducibility.

## Decision

Use **SQLite** via `aiosqlite` + SQLAlchemy async. Schema: `runs`, `profiles(did, run_id)`, `follows`, `deletion_requests`.

## Consequences

- Zero external DB setup for reviewers.
- Concurrent writers limited; acceptable for MVP.
- Postgres migration path reserved for Phase 2.
