# Architecture

Bluesky Graph Analytics follows **Clean Architecture** with four layers:

| Layer | Package | Responsibility |
|-------|---------|----------------|
| **Interfaces** | `interfaces/` | CLI (Typer), Streamlit pages |
| **Application** | `application/` | Use cases, DTOs, ports |
| **Domain** | `domain/` | Entities, strategies, pure logic |
| **Infrastructure** | `infrastructure/` | atproto ACL, SQLAlchemy, observability |

Wiring lives in `composition_root.py` (manual DI).

See `docs/adr/` for architecture decision records.
