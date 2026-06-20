# Security

Report vulnerabilities privately to the maintainers. Do not open public issues for undisclosed security bugs.

Do not commit secrets; `detect-secrets` runs in pre-commit.

## Local database

`data/cache.db` contains **plaintext** DIDs and handles. It is gitignored. Use full-disk encryption on research machines. Do not copy the database to shared drives without explicit approval.
