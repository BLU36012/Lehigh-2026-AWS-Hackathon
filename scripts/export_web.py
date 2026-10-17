"""Stage 3: export a compact JSON bundle for the web front end."""
import json, os, sqlite3, statistics, sys

DB, ZIPS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

COORDS = {   # geocoded via OpenStreetMap Nominatim
    "LVH-ALL":  (40.5651728, -75.5220282),
    "SLH-BETH": (40.6092805, -75.3931974),
    "SLH-ALLE": (40.5952668, -75.4933804),
}

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

hospitals = []
for r in db.execute("""SELECT h.*, n.network_name FROM hospital h
                       JOIN network n ON n.network_id = h.network_id"""):
    lat, lon = COORDS[r["hospital_id"]]
    hospitals.append({
        "id": r["hospital_id"], "name": r["hospital_name"], "campus": r["campus"],
        "network": r["network_name"], "net": r["network_id"],
        "addr": f'{r["street"]}, {r["city"]}, {r["state"]} {r["zip"]}',
        "lat": lat, "lon": lon, "campuses": r["covers_campuses"],
        "updated": r["last_updated_on"],
    })

services = [dict(code=r["service_code"], type=r["code_type"],
                 name=r["service_name"], cat=r["category"])
            for r in db.execute(
                "SELECT * FROM service ORDER BY category, service_name")]

payers = []
for r in db.execute("""SELECT p.payer_name AS n,
                              GROUP_CONCAT(DISTINCT h.network_id) AS nets
                       FROM payer p
                       JOIN plan pl    ON pl.payer_id = p.payer_id
                       JOIN hospital h ON h.hospital_id = pl.hospital_id
                       GROUP BY p.payer_name ORDER BY p.payer_name"""):
    payers.append({"n": r["n"], "nets": sorted(r["nets"].split(","))})

# prices["<code>|<payer>"]["<hospital>"] = {lo, mid, hi, n, setting, plans:[...]}
prices = {}
rows = db.execute("""
    SELECT service_code, payer_name, hospital_id, plan_name, setting,
           methodology, negotiated_dollar, cash_price
    FROM v_rate WHERE negotiated_dollar IS NOT NULL""").fetchall()

bucket = {}
for r in rows:
    bucket.setdefault((r["service_code"], r["payer_name"], r["hospital_id"]),
                      []).append(r)

for (code, payer, hosp), rs in bucket.items():
    vals = sorted(x["negotiated_dollar"] for x in rs)
    plans = {}
    for x in rs:
        plans.setdefault(x["plan_name"], []).append(x["negotiated_dollar"])
    cash = [x["cash_price"] for x in rs if x["cash_price"] is not None]
    entry = {
        "lo": round(vals[0], 2),
        "mid": round(statistics.median(vals), 2),
        "hi": round(vals[-1], 2),
        "n": len(vals),
        "set": rs[0]["setting"],
        "meth": rs[0]["methodology"],
        "plans": sorted(
            ({"p": k, "lo": round(min(v), 2), "hi": round(max(v), 2)}
             for k, v in plans.items()), key=lambda d: d["lo"]),
    }
    if cash:
        entry["cash"] = round(min(cash), 2)
    prices.setdefault(f"{code}|{payer}", {})[hosp] = entry

bundle = {
    "hospitals": hospitals,
    "services": services,
    "payers": payers,
    "prices": prices,
    "zips": json.load(open(ZIPS)),
}
json.dump(bundle, open(OUT, "w"), separators=(",", ":"))
print(f"hospitals={len(hospitals)} services={len(services)} payers={len(payers)} "
      f"price_keys={len(prices)} zips={len(bundle['zips'])}")
print(f"{OUT}: {os.path.getsize(OUT)/1024:.0f} KB")
