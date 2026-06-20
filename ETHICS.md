# Ethics

- Collect only what is required for stated research goals.
- Store **plaintext DIDs** under `data/processed/` and `data/results/` locally.
- Share only **pseudonymized** exports from `data/anonymized/`.
- Honor deletion requests via `DeletionService` / `deletion_requests` table.

## Deletion workflow

1. `bga deletion add --did did:plc:xxxx --reason "user request"`
2. `bga deletion add --handle user.bsky.social --reason "user request"`
3. Manual SQL insert into `deletion_requests` (subject_did, requested_at, reason) for emergencies

Process queued requests: `bga deletion process` (transactional erase from `follows` and `profiles`).

List pending: `bga deletion list --pending`
