"""Stage 2: load the staged subset into a SQLite database.

    python scripts/build_db.py <staged.jsonl> <out.db>
"""
import csv, json, os, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STAGED, DB = sys.argv[1], sys.argv[2]

NETWORKS = [
    ("LVHN", "Lehigh Valley Health Network", "Jefferson Health"),
    ("SLUHN", "St. Luke's University Health Network", None),
]

HOSPITALS = [
    # id, network, name, campus, street, city, state, zip, ein, npi,
    # version, last_updated, source_file, covers_campuses, notes
    ("LVH-ALL", "LVHN", "Lehigh Valley Hospital", "All licensed locations",
     "1200 S Cedar Crest Blvd", "Allentown", "PA", "18103", "231689692", "1164400131",
     "3.0.0", "2026-07-01",
     "231689692-1164400131_lehigh-valley-hospital_standardcharges.csv", 8,
     "One MRF covers 8 locations (Cedar Crest, Muhlenberg, Hecktown Oaks, Reilly "
     "Children's, 17th Street, Carbon, Coordinated Health Allentown/Bethlehem). "
     "Rates are not broken out by campus. LVHN publishes no gross charge on rows "
     "that carry a HCPCS or MS-DRG code, so gross_charge/cash_price are NULL here."),
    ("SLH-BETH", "SLUHN", "St. Luke's Hospital", "Bethlehem Campus",
     "801 Ostrum St", "Bethlehem", "PA", "18015", "23-1352213", "1508343906",
     "3.0.0", "2026-02-26", "23-1352213_stlukeshospitalbethlehemcampus_standardcharges.csv", 1,
     "Flagship campus. Facility billing class only."),
    ("SLH-ALLE", "SLUHN", "St. Luke's Hospital", "Allentown Campus",
     "1736 Hamilton St", "Allentown", "PA", "18104", "23-1352213", "1326571357",
     "3.0.0", "2026-02-26", "23-1352213_stlukeshospitalallentowncampus_standardcharges.csv", 1,
     "Facility billing class only."),
]

# Raw payer string -> canonical payer. Anything unmapped falls through to a
# title-cased version of the raw string.
PAYER_CANON = {
    "AETNA": "Aetna",
    "AMBETTER": "Ambetter",
    "AMERIHEALTH": "AmeriHealth",
    "AMERIHEALTH CARITAS": "AmeriHealth Caritas",
    "BLUE DISTINCTION": "Blue Distinction",
    "CAPITAL BLUE CROSS": "Capital Blue Cross",
    "CIGNA": "Cigna",
    "COMMUNITY CARE BEHAVIORAL HEALTH": "Community Care Behavioral Health",
    "DEVOTED HEALTH": "Devoted Health",
    "EMBLEM": "EmblemHealth",
    "GATEWAY": "Highmark Wholecare",
    "GEISINGER": "Geisinger",
    "HIGHMARK": "Highmark",
    "HIGHMARK BLUE SHIELD": "Highmark",
    "HIGHMARK WHOLECARE": "Highmark Wholecare",
    "HIGHMARK WHOLECARE/GATEWAY": "Highmark Wholecare",
    "HORIZON BCBS NJ": "Horizon BCBS NJ",
    "HUMANA": "Humana",
    "IBC": "Independence Blue Cross",
    "INDEPENDENCE BLUE CROSS": "Independence Blue Cross",
    "JEFFERSON EMPLOYEES": "Jefferson Employees",
    "JEFFERSON HEALTH PARTNERS": "Jefferson Health Plan",
    "JEFFERSON HEALTH PLAN": "Jefferson Health Plan",
    "KEYSTONE FIRST": "Keystone First",
    "MAGELLAN HEALTHY CHOICES": "Magellan Healthy Choices",
    "MESHOPPEN STONE": "Meshoppen Stone",
    "OPTUM HEALTH": "Optum Health",
    "OSCAR": "Oscar",
    "PA HEALTH & WELLNESS": "PA Health & Wellness",
    "PA HEALTH & WELLNESS (ALLWELL)": "PA Health & Wellness",
    "POPULYTICS": "Populytics",
    "UNITED HEALTHCARE": "UnitedHealthcare",
    "UPMC": "UPMC Health Plan",
    "UPMC HEALTH PLAN": "UPMC Health Plan",
    "VALLEY PREFERRED": "Valley Preferred",
}

def canon(raw):
    return PAYER_CANON.get(raw.strip().upper(), raw.strip().title())

if os.path.exists(DB):
    os.remove(DB)
db = sqlite3.connect(DB)
db.executescript(open(os.path.join(ROOT, "sql", "schema.sql"), encoding="utf-8").read())

db.executemany("INSERT INTO network VALUES (?,?,?)", NETWORKS)
db.executemany("INSERT INTO hospital VALUES (" + ",".join("?" * 15) + ")", HOSPITALS)

with open(os.path.join(HERE, "shoppable_services.csv"), encoding="utf-8-sig") as f:
    db.executemany(
        "INSERT INTO service (service_code, code_type, category, service_name) VALUES (?,?,?,?)",
        [(r["code"], r["code_type"], r["category"], r["service_name"])
         for r in csv.DictReader(f)])

payer_ids, plan_ids, item_ids, aliases = {}, {}, {}, set()

def payer_id(raw):
    name = canon(raw)
    if name not in payer_ids:
        cur = db.execute("INSERT INTO payer (payer_name) VALUES (?)", (name,))
        payer_ids[name] = cur.lastrowid
    return payer_ids[name]

def plan_id(raw_payer, plan_name, hospital_id):
    pid = payer_id(raw_payer)
    key = (pid, hospital_id, plan_name)
    if key not in plan_ids:
        cur = db.execute(
            "INSERT INTO plan (payer_id, hospital_id, plan_name) VALUES (?,?,?)", key)
        plan_ids[key] = cur.lastrowid
    alias = (raw_payer.strip(), hospital_id)
    if alias not in aliases:
        aliases.add(alias)
        db.execute("INSERT INTO payer_alias VALUES (?,?,?)", (*alias, pid))
    return plan_ids[key]

def item_id(rec):
    key = (rec["hospital"], rec["service_code"], rec["service_type"], rec.get("modifier"),
           rec["setting"], rec["billing_class"], rec["rev_code"], rec["cdm"],
           rec["description"])
    if key not in item_ids:
        cur = db.execute(
            "INSERT INTO charge_item (hospital_id, service_code, code_type, modifier, "
            "setting, billing_class, rev_code, cdm, local_description, gross_charge, "
            "cash_price, min_negotiated, max_negotiated) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            key + (rec["gross"], rec["cash"], rec["min_neg"], rec["max_neg"]))
        item_ids[key] = cur.lastrowid
    return item_ids[key]

skipped = 0
with open(STAGED, encoding="utf-8") as f:
    for line in f:
        rec = json.loads(line)
        if not rec["payer"] or not rec["plan"]:
            skipped += 1
            continue
        db.execute(
            "INSERT INTO negotiated_rate (item_id, plan_id, methodology, negotiated_dollar, "
            "negotiated_percentage, negotiated_algorithm, estimated_amount, notes) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (item_id(rec), plan_id(rec["payer"], rec["plan"], rec["hospital"]),
             rec["methodology"], rec["neg_dollar"], rec["neg_pct"],
             rec["neg_algorithm"], rec["est_amount"], rec["notes"]))

db.commit()
db.execute("ANALYZE")
db.commit()

print(f"skipped rows missing payer/plan: {skipped}")
for t in ("network", "hospital", "service", "payer", "payer_alias", "plan",
          "charge_item", "negotiated_rate"):
    print(f"  {t:<17} {db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:>6}")
print(f"\ndb size: {os.path.getsize(DB) / 1024:.0f} KB")
db.close()
