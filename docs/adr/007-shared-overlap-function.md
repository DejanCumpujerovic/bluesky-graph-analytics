# ADR 007: Shared overlap function

Status: Accepted

## Context

Overlap appears in profile–profile similarity and in projection edge weights; formulas must not diverge.

## Decision

Single function `compute_overlap(set_a, set_b) -> float` in `domain/similarity/overlap.py`:

`overlap(A, B) = |A ∩ B| / min(|A|, |B|)`

Callers pass different sets: neighbor sets (similarity) or seed sets per follower (projection).

## Consequences

- One test suite (Hypothesis) guards the primitive.
- Dynamic `min_overlap` uses `max(MIN_OVERLAP_ABSOLUTE, 0.01 * min(|A|,|B|))`.
