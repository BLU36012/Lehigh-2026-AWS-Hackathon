"""Stage 1: stream the three machine-readable files and pull out only the rows
matching the curated shoppable-service list. Writes newline-delimited JSON to
the scratch dir so the SQLite build never has to touch the multi-hundred-MB
source files again."""
import csv, json, os, re, sys, collections

csv.field_size_limit(10 ** 9)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
LVHN = sys.argv[2]
SLHN = sys.argv[3:]  # name=path pairs

def load_targets():
    hcpcs, drg = {}, {}
    with open(os.path.join(HERE, "shoppable_services.csv"), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["code_type"] == "MS-DRG":
                drg[r["code"].lstrip("0")] = r["code"]
            else:
                hcpcs[r["code"].upper()] = r["code"]
    return hcpcs, drg

HCPCS, DRG = load_targets()

def norm_drg(v):
    return (v or "").strip().lstrip("0")

BASE = re.compile(r"^[A-Z0-9]{5}")

def split_codes(raw):
    """LVHN packs several codes into one field and glues modifiers onto the
    code itself (``G0307; G0307QW``, ``44392SG``). Yield (base, modifier)."""
    for tok in (raw or "").replace(",", ";").split(";"):
        tok = tok.strip().upper()
        if not tok:
            continue
        m = BASE.match(tok)
        if m:
            yield m.group(0), tok[5:] or None
        else:
            yield tok, None

def num(v):
    v = (v or "").strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None

stats = collections.Counter()
payers = collections.defaultdict(collections.Counter)

def emit(w, rec):
    w.write(json.dumps(rec, separators=(",", ":")) + "\n")
    stats[rec["hospital"]] += 1

# ---------------- LVHN: vendor-flattened layout, no preamble ----------------
def parse_lvhn(path, w):
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            stats["lvhn_scanned"] += 1
            svc = stype = modifier = None
            for base, mod in split_codes(row.get("code_HCPCS")):
                if base in HCPCS:
                    svc, stype, modifier = HCPCS[base], "HCPCS", mod
                    break
            if not svc:
                drg = norm_drg(row.get("code_MS-DRG"))
                if drg in DRG:
                    svc, stype = DRG[drg], "MS-DRG"
            if not svc:
                continue
            payers["LVHN"][row["payer_name"]] += 1
            emit(w, {
                "hospital": "LVH-ALL",
                "service_code": svc, "service_type": stype,
                "description": (row.get("description") or "").strip().strip('"'),
                "setting": row.get("setting") or None,
                "modifier": modifier,
                "billing_class": None,          # not published by LVHN
                "rev_code": row.get("code_RC") or None,
                "cdm": row.get("code_CDM") or None,
                "drug_unit": row.get("drug_unit") or None,
                "drug_unit_type": row.get("drug_unit_type") or None,
                "gross": num(row.get("gross_charge")),
                "cash": num(row.get("discounted_cash")),
                "min_neg": num(row.get("min_negotiated")),
                "max_neg": num(row.get("max_negotiated")),
                "payer": (row.get("payer_name") or "").strip(),
                "plan": (row.get("plan_name") or "").strip(),
                "methodology": row.get("methodology") or None,
                "neg_dollar": num(row.get("negotiated_dollar")),
                "neg_pct": num(row.get("negotiated_percentage")),
                "neg_algorithm": row.get("negotiated_algorithm") or None,
                "est_amount": num(row.get("median_amount")),
                "notes": row.get("additional_generic_notes") or None,
            })

# ---------------- SLHN: canonical CMS v3.0 tall layout, 2-row preamble -------
def parse_slhn(hosp_id, path, w):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        next(rd); next(rd)                      # metadata header + metadata values
        hdr = next(rd)
        for row in csv.DictReader(f, fieldnames=hdr):
            stats["slhn_scanned"] += 1
            svc = stype = None
            rev = cdm = None
            for i in "1234":
                c = (row.get(f"code|{i}") or "").strip()
                t = (row.get(f"code|{i}|type") or "").strip().upper()
                if not c:
                    continue
                if t == "RC":
                    rev = c
                elif t == "CDM":
                    cdm = c
                if svc:
                    continue
                if t in ("CPT", "HCPCS"):
                    for base, _mod in split_codes(c):
                        if base in HCPCS:
                            svc, stype = HCPCS[base], "HCPCS"
                            break
                elif t == "MS-DRG" and norm_drg(c) in DRG:
                    svc, stype = DRG[norm_drg(c)], "MS-DRG"
            if not svc:
                continue
            payers[hosp_id][row["payer_name"]] += 1
            emit(w, {
                "hospital": hosp_id,
                "service_code": svc, "service_type": stype,
                "description": (row.get("description") or "").strip(),
                "setting": row.get("setting") or None,
                "modifier": (row.get("modifiers") or "").strip() or None,
                "billing_class": row.get("billing_class") or None,
                "rev_code": rev, "cdm": cdm,
                "drug_unit": row.get("drug_unit_of_measurement") or None,
                "drug_unit_type": row.get("drug_type_of_measurement") or None,
                "gross": num(row.get("standard_charge|gross")),
                "cash": num(row.get("standard_charge|discounted_cash")),
                "min_neg": num(row.get("standard_charge|min")),
                "max_neg": num(row.get("standard_charge|max")),
                "payer": (row.get("payer_name") or "").strip(),
                "plan": (row.get("plan_name") or "").strip(),
                "methodology": row.get("standard_charge|methodology") or None,
                "neg_dollar": num(row.get("standard_charge|negotiated_dollar")),
                "neg_pct": num(row.get("standard_charge|negotiated_percentage")),
                "neg_algorithm": row.get("standard_charge|negotiated_algorithm") or None,
                "est_amount": num(row.get("median_amount")),
                "notes": row.get("additional_generic_notes") or None,
            })

with open(OUT, "w", encoding="utf-8") as w:
    parse_lvhn(LVHN, w)
    for spec in SLHN:
        hid, path = spec.split("=", 1)
        parse_slhn(hid, path, w)

print(json.dumps({"stats": stats, "payers": {k: v.most_common() for k, v in payers.items()}}, indent=1))
