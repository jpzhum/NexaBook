# Publication allowlist

This document records the classification made before assembling the portfolio edition.

| Source component | Classification | Public-edition treatment |
| --- | --- | --- |
| FastAPI/Jinja2 application shape | REIMPLEMENT | Small, independent web/API layer using only generic book workflows |
| Google Books and Open Library providers | REIMPLEMENT | Public API adapters with timeouts and normalized outputs |
| OpenAI metadata fallback | REIMPLEMENT | Strict JSON contract, bounded input, validation and graceful failure |
| Metadata resolution pipeline | REIMPLEMENT | Generic ordered enrichment without customer rules |
| SQLite persistence | REIMPLEMENT | New schema; empty database is generated locally |
| CSV/XLSX export | REIMPLEMENT | Generic portfolio schema, not a marketplace/customer layout |
| Authentication | SANITIZE / REIMPLEMENT | Environment-only credentials, signed session, CSRF and login throttling |
| Environment variable names | SAFE | Empty values and documented defaults only |
| Tests | REIMPLEMENT | Isolated temporary databases, mocks and synthetic records |
| Production databases, caches and events | EXCLUDE | Never copied |
| Backups, uploads, exports and spreadsheets | EXCLUDE | Never copied |
| Customer/provider lists and codes | EXCLUDE | Replaced with unrelated synthetic examples |
| Pricing, taxonomy and description rules | EXCLUDE | Potentially customer-specific business logic |
| Marketplace-specific export layout | EXCLUDE | Replaced by a generic export contract |
| Internal reports and operational manuals | EXCLUDE | Derived from the private implementation |
| Original logo and production assets | OWNER REVIEW REQUIRED / EXCLUDE | Not included pending ownership review |
| Render configuration, domain and service metadata | EXCLUDE | Portfolio edition is deployment-independent |

No file under the private repository's `data/`, `outputs/`, or `.git/` directories is part of this edition.
