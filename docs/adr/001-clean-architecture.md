# ADR 001: Clean Architecture (four layers)

Status: Accepted

## Context

Phase 1 needs clear boundaries between domain rules, use cases, infrastructure, and UI.

## Decision

Use four layers under `src/bluesky_graph_analytics/`:

1. **Domain** — pure models, graph algorithms, metrics (no I/O).
2. **Application** — services, ports, DTOs, orchestration.
3. **Infrastructure** — SQLite, atproto client, pseudonymization.
4. **Interfaces** — Typer CLI and Streamlit (read-only dashboard).

Dependency rule: domain ← application ← infrastructure/interfaces. Composition root wires concrete adapters.

## Consequences

- Testable domain without DB or network.
- Slightly more boilerplate than a single-package script.
- CLI name is `bga` (Bluesky Graph Analytics), not `beleske`.
