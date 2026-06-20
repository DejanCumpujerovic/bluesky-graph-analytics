# Bluesky Graph Analytics

Analytics and visualization for the Bluesky social graph. **Phase 1** — academic MVP (`v1.0.0` target).

**License:** AGPL-3.0-or-later · **Python:** 3.11+

## Structure

```
src/bluesky_graph_analytics/   # domain → application → infrastructure; interfaces
config/                        # config.yaml, seed_profiles.yaml (+ config.dev.yaml local)
data/                          # raw, processed, results, anonymized, cache.db
alembic/                       # migrations (no create_all in prod)
tests/                         # unit, integration, fixtures
```

See [ARCHITECTURE.md](ARCHITECTURE.md), [ETHICS.md](ETHICS.md), [docs/adr/](docs/adr/).

## Setup

```bash
uv python install 3.11
uv sync --all-extras
alembic upgrade head   # includes 0004 DEO 7 schema (destructive vs pre-0004 DB)
```

## Commands

```bash
uv run bga health
uv run bga version
alembic upgrade head   # includes 0004 DEO 7 schema (destructive vs pre-0004 DB)

# 1-hop collect (seed → followers), curated topic or handles
uv run bga collect --topic example --handle user.bsky.social --snapshot-id snap_2025_q1

# Analysis: community projection + link prediction
uv run bga analyze --run-label my_run --snapshot-id snap_2025_q1

# Export (pseudonymized by default; needs PSEUDONYM_SALT in .env)
uv run bga export --run-label my_run --anonymized

# Deletion workflow (GDPR)
uv run bga deletion add --did did:plc:xxxx --reason "user request"
uv run bga deletion list --pending
uv run bga deletion process

uv run pytest
```

Configuration lives in `config/config.yaml` (nested DEO 6 schema); secrets in `.env` — see `.env.example`.

Set `BLUESKY_HANDLE`, `BLUESKY_APP_PASSWORD` for live crawl. `PSEUDONYM_SALT` ≥ 32 bytes for anonymized exports.

Seed list: `config/seed_profiles.yaml` (50–200 entries for production; set `collection.enforce_mvp_seed_count: true`).

## Development

```bash
pre-commit install
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest --cov=src/bluesky_graph_analytics --cov-fail-under=80
```
