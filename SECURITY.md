# Security policy

Please report suspected vulnerabilities privately to the repository owner rather than opening a public issue containing exploit details.

The portfolio edition keeps credentials in environment variables, requires explicit production authentication configuration, signs session cookies, validates CSRF tokens on state-changing forms, and limits repeated login failures. Tests use mocks and do not call paid APIs.

Generated databases and exports are local artifacts and are ignored by Git. Do not commit real catalogs, uploads, logs, API payloads, or credentials.

The remote-image ingestion feature from the private product is intentionally absent. Reintroducing it requires DNS resolution checks, public-IP enforcement on every redirect, response-size limits, strict media validation, and bounded timeouts.
