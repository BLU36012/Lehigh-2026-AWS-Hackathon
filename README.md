# Lehigh-2026-AWS-Hackathon

## Data

`data/lehigh_valley_prices.db` — a small SQLite database of negotiated
hospital prices for Lehigh Valley Health Network and St. Luke's University
Health Network, built from their CMS machine-readable standard-charge files.

76 shoppable services · 26 payers · 6,856 negotiated rates · 708 KB.

See **[DATA.md](DATA.md)** for the schema, provenance, caveats, and rebuild
steps, and [sql/example_queries.sql](sql/example_queries.sql) to get started.

```bash
sqlite3 data/lehigh_valley_prices.db ".read sql/example_queries.sql"
```
