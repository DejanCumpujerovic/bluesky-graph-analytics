# ADR 004: Leiden over Louvain

Status: Accepted

## Context

Community detection needs well-connected communities and a global quality score (modularity Q).

## Decision

Use **Leiden** (`leidenalg.RBConfigurationVertexPartition`, `seed=42`) on the overlap-weighted follower–follower projection. Reject partitions with global Q &lt; 0.3 (`modularity_min`).

## Consequences

- Better connected communities than Louvain in practice.
- Extra dependency (`leidenalg`, `igraph`).
- Visualization uses FR layout in MVP (not ForceAtlas2) for stability.
