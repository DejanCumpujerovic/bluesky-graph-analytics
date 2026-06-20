# Methodology

Phase 1 (MVP) delivers three analysis layers on a 1-hop Bluesky follower graph from seed profiles.

## Data collection

- Seeds from `config/seed_profiles.yaml`; invalid seeds logged to `data/raw/seed_skipped.csv`.
- One hop: followers of each valid seed, paginated via atproto `getFollowers`.
- Profiles stored per run `(did, run_id)`; follows keyed by `snapshot_id`.

## Layer 1 — Similarity

Profile–profile metrics on shared follower sets: **Jaccard**, **Adamic–Adar**, **Overlap** (shared `compute_overlap`). Pairs below dynamic `min_overlap` are dropped. Outputs: per-metric parquet (plaintext DIDs in DB-backed pipeline), pseudonymized `top_pairs.csv`, `metric_correlation.csv` (Spearman, Kendall, RBO@50).

## Layer 2 — Communities

**Leiden** on overlap-weighted follower–follower projection. NLP: English descriptions only (langdetect ≥0.90); c-TF-IDF-style top-10 terms per community. Global modularity Q; MVP gate Q ≥ 0.3.

## Layer 3 — Link prediction

Directed heuristics (CN, AA, Jaccard on in-neighbors), **Node2Vec** + logistic regression (Hadamard features). **Random 90/10 split** — see ADR 005. Metrics: AUC, P@k, R@k, MAP for k ∈ {10, 50, 100}.

## Reproducibility

`random_seed=42` in config; `output_sha256` over result artifacts; `git_commit_hash` on each run.

## Ethics

See [ETHICS.md](ETHICS.md). Pseudonymized exports only for sharing; deletion workflow in CLI.
