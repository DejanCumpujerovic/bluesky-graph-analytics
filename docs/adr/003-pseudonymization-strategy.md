# ADR 003: Pseudonymization strategy

Status: Accepted

## Context

GDPR and ethics require limiting identifiability in shared artifacts while keeping reproducible research locally.

## Decision

- **Database**: plaintext DID/handle during collection (operational need).
- **Export & shareable CSV/JSON**: BLAKE2b-based pseudonyms with `PSEUDONYM_SALT` (≥32 bytes).
- **Export manifest**: `pseudonym_salt_fingerprint` (first 16 hex of blake2b8(salt)) — not the salt itself.

## Consequences

- Two exports with same fingerprint are comparable; different salts are not.
- Salt must never be committed or shipped in ZIPs.
