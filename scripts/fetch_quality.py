"""Fetch CMS Care Compare quality data for the hospitals in the subset.

    python scripts/fetch_quality.py

Writes scripts/cms_quality.json so the build is reproducible without hitting
CMS every time. Re-run to refresh.

Source: CMS Provider Data Catalog, "Hospital General Information" (xubh-q36u).
Each hospital is matched by CMS Certification Number (CCN), not by name.
"""
import json, os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "cms_quality.json")

# Hospital in our subset -> CMS CCN. St. Luke's Allentown has no separate CCN
# in Care Compare, so it is deliberately unrated rather than given Bethlehem's.
CCN = {
    "LVH-ALL":  "390133",   # LEHIGH VALLEY HOSPITAL (Cedar Crest)
    "SLH-BETH": "390049",   # ST LUKES HOSPITAL (Bethlehem)
    "SLH-ALLE": None,
}

URL = ("https://data.cms.gov/provider-data/api/1/datastore/query/xubh-q36u/0"
       "?limit=400&conditions[0][property]=state&conditions[0][value]=PA"
       "&conditions[0][operator]==")


def num(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def group(row, prefix, total_key):
    """Turn CMS's better/same/worse counts into a 0-100 subscore.

    A measure scored 'better than national average' counts 1, 'no different'
    counts 0.5, 'worse' counts 0. That is the most defensible reading of what
    CMS actually publishes; it is not a CMS-endorsed composite.
    """
    better = num(row.get("count_of_%s_measures_better" % prefix))
    same = num(row.get("count_of_%s_measures_no_different" % prefix))
    worse = num(row.get("count_of_%s_measures_worse" % prefix))
    total = num(row.get(total_key))
    if None in (better, same, worse) or not total:
        return None
    return {
        "score": round(100.0 * (better + 0.5 * same) / total, 1),
        "better": better, "same": same, "worse": worse, "measures": total,
    }


print("fetching CMS Hospital General Information ...")
with urllib.request.urlopen(URL.replace("[", "%5B").replace("]", "%5D"),
                            timeout=90) as r:
    rows = json.load(r).get("results", [])
print("  %d PA hospitals" % len(rows))

by_ccn = {r["facility_id"]: r for r in rows}
out = {}

for hospital_id, ccn in CCN.items():
    if not ccn:
        out[hospital_id] = {
            "rated": False,
            "note": ("CMS Care Compare does not publish a separate rating for "
                     "this campus; it has no CCN of its own in the dataset."),
        }
        print("  %-9s not rated by CMS" % hospital_id)
        continue

    row = by_ccn.get(ccn)
    if not row:
        raise SystemExit("CCN %s not found in the CMS response" % ccn)

    stars = num(row.get("hospital_overall_rating"))
    out[hospital_id] = {
        "rated": True,
        "ccn": ccn,
        "cms_name": row.get("facility_name"),
        "stars": stars,
        "ownership": row.get("hospital_ownership"),
        "type": row.get("hospital_type"),
        "emergency": row.get("emergency_services"),
        "birthing_friendly": row.get("meets_criteria_for_birthing_friendly_designation") == "Y",
        "safety": group(row, "safety", "count_of_facility_safety_measures"),
        "mortality": group(row, "mort", "count_of_facility_mort_measures"),
        "readmission": group(row, "readm", "count_of_facility_readm_measures"),
    }
    print("  %-9s CCN %s  %s stars  %s" % (hospital_id, ccn, stars,
                                           row.get("facility_name")))

json.dump(out, open(OUT, "w"), indent=1)
print("wrote %s" % OUT)
