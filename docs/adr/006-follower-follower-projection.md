# ADR 006: Follower–follower projection for communities

Status: Accepted

## Context

Seed–follower bipartite graphs are sparse for community algorithms tuned for dense projections.

## Decision

Build a **follower–follower** graph: edge between followers A and B if they follow overlapping seeds; weight = `compute_overlap(S(A), S(B))` (shared `overlap.py` with similarity layer).

## Consequences

- Communities reflect co-audience structure, not seed similarity directly.
- Overlap threshold and `min_overlap_seeds` gate noise edges.
