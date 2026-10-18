# Lehigh-2026-AWS-Hackathon

Compare what Lehigh Valley Health Network and St. Luke's have negotiated with
insurers for common procedures — the prices both networks are legally required
to publish, and which nobody can read in their raw form.

## Start here
Website: https://d110is5v4ymqks.cloudfront.net
| | |
|---|---|
| **[DATA.md](DATA.md)** | The database: schema, provenance, caveats, rebuild steps |
| **[DEPLOY.md](DEPLOY.md)** | Step-by-step AWS deployment with the CLI |
| `data/lehigh_valley_prices.db` | SQLite, 708 KB, 6,856 negotiated rates |
| `web/index.html` | The front end |
| `infra/template.yaml` | S3 + CloudFront + API Gateway + Lambda + DynamoDB |

## Query the data locally

```bash
sqlite3 data/lehigh_valley_prices.db ".read sql/example_queries.sql"
```

From Java (JDBC driver is in `lib/`):

```bash
javac -cp "lib/sqlite-jdbc-3.53.2.1.jar" -d out src/datamanager.java
java  -cp "out;lib/sqlite-jdbc-3.53.2.1.jar" DataManager 72148
```

## Pipeline

```
MRF CSVs (1.2 GB)
  └─ scripts/extract_subset.py   filter to the curated service list
       └─ scripts/build_db.py    → data/lehigh_valley_prices.db
            └─ scripts/export_web.py  → web/prices.json
                 ├─ scripts/build_site.py   → dist/   (static hosting)
                 └─ scripts/load_dynamo.py  → DynamoDB (API)
```

Standard library only, except `boto3` for the DynamoDB step.
