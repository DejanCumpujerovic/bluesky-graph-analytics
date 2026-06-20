# ADR 005: Random split for link prediction (MVP)

Status: Accepted

## Context

Temporal train/test splits need multiple snapshots; MVP has one snapshot per run.

## Decision

Use **random stratified 90/10** split per seed for link prediction. Surface explicit warning in UI and `methodology_warning.txt` that AUC may be inflated 5–15% vs temporal split.

## Consequences

- Comparable to literature that reports random splits.
- Phase 2 will add temporal evaluation when multi-snapshot timelines exist.
