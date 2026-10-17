# Lehigh Valley hospital price database

A small SQLite database comparing what **Lehigh Valley Health Network** and
**St. Luke's University Health Network** have negotiated with insurers for a
curated set of 76 common shoppable services.

`data/lehigh_valley_prices.db` — 708 KB, 6,856 negotiated rates.

It is a deliberate subset. The three source files are 1.17 GB of CSV and
5.4 million rows; this keeps the ~0.1% that supports head-to-head price
comparison and throws away the chargemaster long tail.

## Contents

| | |
|---|---|
| Hospitals | 3 (LVH all-campuses, St. Luke's Bethlehem, St. Luke's Allentown) |
| Services | 76 (57 HCPCS/CPT, 19 MS-DRG) across 15 categories |
| Services priced by **both** networks | 68 |
| Payers | 26 canonical, **13 contracted with both networks** |
| Plans | 105 |
| Charge items | 400 |
| Negotiated rates | 6,856 (6,820 dollar-denominated) |

Methodologies present: fee schedule (4,840), case rate (1,018),
percent of total billed charges (940), per diem (38), other (20).

## Sources

All three are CMS 45 CFR 180.50 machine-readable standard-charge files, v3.0.0.

| Hospital | Published | Source file |
|---|---|---|
| Lehigh Valley Hospital | 2026-07-01 | `231689692-1164400131_lehigh-valley-hospital_standardcharges.csv` (582 MB, 1.70 M rows) |
| St. Luke's Hospital – Bethlehem Campus | 2026-02-26 | `23-1352213_stlukeshospitalbethlehemcampus_standardcharges.csv` (302 MB, 1.29 M rows) |
| St. Luke's Hospital – Allentown Campus | 2026-02-26 | `23-1352213_stlukeshospitalallentowncampus_standardcharges.csv` (286 MB, 1.28 M rows) |

The St. Luke's files come from
<https://www.slhn.org/billing/patient-billing/price-transparency>.

The two networks publish in different shapes, which the loader reconciles:

- **St. Luke's** uses the canonical CMS tall layout — a two-row metadata
  preamble, then `code|1..4` with parallel `code|N|type` columns, and a
  separate `modifiers` column.
- **LVHN** uses a vendor-flattened layout with one column per code system and
  no preamble. Critically, it **glues modifiers onto the code itself** and packs
  several codes into one field: `44392SG`, `G0307; G0307QW`. Matching on the
  exact code string finds only a third of the services; the loader splits on
  `;` and takes the leading five characters as the base code.

## Schema

```
network ──< hospital ──< charge_item >── service
                 │            │
                 │            └──< negotiated_rate >── plan >── payer
                 └──< payer_alias ────────────────────────────────┘
```

- **`charge_item`** — one priced line: a service as a hospital bills it, with
  setting, modifier, revenue code, local description, and the
  gross / cash / min / max standard charges.
- **`negotiated_rate`** — one payer-specific rate against a charge item, as a
  dollar amount, a percentage, or a contractual algorithm.
- **`payer_alias`** — audit trail for payer normalization, so LVHN's `IBC` and
  St. Luke's `Independence Blue Cross` roll into one `payer` row and you can
  see exactly which raw strings were merged.

Three views do most of the work:

| View | Grain |
|---|---|
| `v_rate` | fully denormalized rate line — start here |
| `v_service_price` | hospital × service min / avg / max |
| `v_network_gap` | LVHN vs St. Luke's average, side by side |

## Caveats that matter before you draw conclusions

1. **LVHN publishes no gross charge for coded services.** Its file is strictly
   partitioned: rows carrying a HCPCS or MS-DRG code never carry a gross
   charge, which appears only on chargemaster-description rows. So
   `gross_charge` and `cash_price` are NULL for all LVHN items and populated
   for about 62% of St. Luke's. **Compare on `negotiated_dollar`, not gross.**
2. **LVHN does not publish `billing_class`.** St. Luke's rows are all
   `facility`. Some LVHN rates are professional-only, which is the likely
   explanation where LVHN looks implausibly cheap (e.g. CPT 49505 hernia
   repair, 19120 breast lesion excision). Treat large negative gaps with
   suspicion.
3. **LVHN files one MRF for eight locations** (Cedar Crest, Muhlenberg,
   Hecktown Oaks, Reilly Children's, 17th Street, Carbon, and the two
   Coordinated Health sites) with no per-campus breakdown. `LVH-ALL` is the
   network's blended rate; the two St. Luke's rows are single campuses.
4. **The files are five months apart** (July vs February 2026).
5. **`plan_name` is not normalized** — LVHN's `ALL PRODUCTS` and St. Luke's
   `Commercial` are not the same thing. Join on payer, not plan.
6. **Two St. Luke's campuses are near-identical** in this subset; they appear
   to share a fee schedule. Don't read campus variation into it.
7. Services were matched on base code only. Modifier-bearing LVHN lines
   (`66984LT`, `66984RT`, `66984SG`) collapse to the same service but remain
   distinct `charge_item` rows — aggregate accordingly.

## Rebuilding

```bash
# 1. fetch the two St. Luke's files (~590 MB)
curl -o slhn_bethlehem.csv "https://www.slhn.org/-/media/sluhn/billing/pdf/standard-charges/23-1352213_stlukeshospitalbethlehemcampus_standardcharges.ashx"
curl -o slhn_allentown.csv "https://www.slhn.org/-/media/sluhn/billing/pdf/standard-charges/23-1352213_stlukeshospitalallentowncampus_standardcharges.ashx"

# 2. stream all three files, keep only the curated services (~6 min)
python scripts/extract_subset.py staged.jsonl \
    /path/to/231689692-1164400131_lehigh-valley-hospital_standardcharges.csv \
    SLH-BETH=slhn_bethlehem.csv \
    SLH-ALLE=slhn_allentown.csv

# 3. load into SQLite (~1 s)
python scripts/build_db.py staged.jsonl data/lehigh_valley_prices.db
```

Standard library only, no dependencies.

To widen or narrow the subset, edit `scripts/shoppable_services.csv`
(`code, code_type, category, service_name`) and re-run both steps.

## Querying

```bash
sqlite3 data/lehigh_valley_prices.db ".read sql/example_queries.sql"
```

`sql/example_queries.sql` has seven worked examples: same-payer head-to-head
comparison, payer spread within one hospital, DRG comparison, cheapest option
per service, and the payer-normalization audit.

```sql
SELECT service_name, payer_name, hospital_id, negotiated_dollar
FROM v_rate
WHERE service_code = '72148'        -- MRI lumbar spine without contrast
ORDER BY negotiated_dollar;
```
