-- Lehigh Valley hospital price-transparency subset
-- Source: CMS 45 CFR 180.50 machine-readable standard-charge files (v3.0.0)
PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS v_network_gap;
DROP VIEW  IF EXISTS v_service_price;
DROP VIEW  IF EXISTS v_rate;
DROP TABLE IF EXISTS negotiated_rate;
DROP TABLE IF EXISTS charge_item;
DROP TABLE IF EXISTS plan;
DROP TABLE IF EXISTS payer_alias;
DROP TABLE IF EXISTS payer;
DROP TABLE IF EXISTS service;
DROP TABLE IF EXISTS hospital;
DROP TABLE IF EXISTS network;

CREATE TABLE network (
    network_id   TEXT PRIMARY KEY,
    network_name TEXT NOT NULL,
    parent_org   TEXT
);

CREATE TABLE hospital (
    hospital_id     TEXT PRIMARY KEY,
    network_id      TEXT NOT NULL REFERENCES network(network_id),
    hospital_name   TEXT NOT NULL,
    campus          TEXT,
    street          TEXT,
    city            TEXT,
    state           TEXT,
    zip             TEXT,
    ein             TEXT,
    primary_npi     TEXT,
    mrf_version     TEXT,
    last_updated_on TEXT,          -- ISO date the source file was published
    source_file     TEXT,
    covers_campuses INTEGER NOT NULL DEFAULT 1,  -- LVHN files one MRF for 8 sites
    notes           TEXT
);

-- Curated subset definition: the shoppable services this database covers.
CREATE TABLE service (
    service_code TEXT NOT NULL,
    code_type    TEXT NOT NULL CHECK (code_type IN ('HCPCS', 'MS-DRG')),
    category     TEXT NOT NULL,
    service_name TEXT NOT NULL,
    PRIMARY KEY (service_code, code_type)
);

-- Canonical payer identity, so LVHN's "IBC" and St. Luke's
-- "Independence Blue Cross" roll up to one row.
CREATE TABLE payer (
    payer_id   INTEGER PRIMARY KEY,
    payer_name TEXT NOT NULL UNIQUE
);

-- Audit trail for that normalization: every raw string -> canonical payer.
CREATE TABLE payer_alias (
    raw_name    TEXT NOT NULL,
    hospital_id TEXT NOT NULL REFERENCES hospital(hospital_id),
    payer_id    INTEGER NOT NULL REFERENCES payer(payer_id),
    PRIMARY KEY (raw_name, hospital_id)
);

CREATE TABLE plan (
    plan_id     INTEGER PRIMARY KEY,
    payer_id    INTEGER NOT NULL REFERENCES payer(payer_id),
    hospital_id TEXT    NOT NULL REFERENCES hospital(hospital_id),
    plan_name   TEXT    NOT NULL,
    UNIQUE (payer_id, hospital_id, plan_name)
);

-- One priced line: a service as a given hospital bills it.
CREATE TABLE charge_item (
    item_id           INTEGER PRIMARY KEY,
    hospital_id       TEXT NOT NULL REFERENCES hospital(hospital_id),
    service_code      TEXT NOT NULL,
    code_type         TEXT NOT NULL,
    modifier          TEXT,          -- HCPCS modifier, when the source carries one
    setting           TEXT CHECK (setting IN ('inpatient', 'outpatient', 'both')),
    billing_class     TEXT,          -- facility / professional; NULL = not published
    rev_code          TEXT,
    cdm               TEXT,
    local_description TEXT,
    gross_charge      REAL,          -- chargemaster list price
    cash_price        REAL,          -- discounted cash price
    min_negotiated    REAL,
    max_negotiated    REAL,
    FOREIGN KEY (service_code, code_type) REFERENCES service(service_code, code_type)
);

-- One payer-specific negotiated rate against a charge_item.
CREATE TABLE negotiated_rate (
    rate_id               INTEGER PRIMARY KEY,
    item_id               INTEGER NOT NULL REFERENCES charge_item(item_id),
    plan_id               INTEGER NOT NULL REFERENCES plan(plan_id),
    methodology           TEXT,
    negotiated_dollar     REAL,
    negotiated_percentage REAL,
    negotiated_algorithm  TEXT,
    estimated_amount      REAL,
    notes                 TEXT
);

CREATE INDEX idx_item_service  ON charge_item (service_code, code_type);
CREATE INDEX idx_item_hospital ON charge_item (hospital_id);
CREATE INDEX idx_rate_item     ON negotiated_rate (item_id);
CREATE INDEX idx_rate_plan     ON negotiated_rate (plan_id);
CREATE INDEX idx_plan_payer    ON plan (payer_id);

-- ---------------------------------------------------------------- views ---

-- Fully denormalized rate line: the table most analysis should start from.
CREATE VIEW v_rate AS
SELECT n.network_name,
       h.hospital_id,
       h.hospital_name,
       s.category,
       s.service_code,
       s.code_type,
       s.service_name,
       ci.setting,
       ci.billing_class,
       ci.modifier,
       ci.local_description,
       p.payer_name,
       pl.plan_name,
       r.methodology,
       r.negotiated_dollar,
       r.negotiated_percentage,
       r.negotiated_algorithm,
       ci.gross_charge,
       ci.cash_price,
       ci.min_negotiated,
       ci.max_negotiated
FROM negotiated_rate r
JOIN charge_item ci ON ci.item_id = r.item_id
JOIN hospital   h  ON h.hospital_id = ci.hospital_id
JOIN network    n  ON n.network_id = h.network_id
JOIN service    s  ON s.service_code = ci.service_code AND s.code_type = ci.code_type
JOIN plan       pl ON pl.plan_id = r.plan_id
JOIN payer      p  ON p.payer_id = pl.payer_id;

-- Per hospital x service price summary over dollar-denominated rates.
CREATE VIEW v_service_price AS
SELECT network_name,
       hospital_id,
       hospital_name,
       category,
       service_code,
       code_type,
       service_name,
       COUNT(negotiated_dollar)                AS rate_count,
       COUNT(DISTINCT payer_name)              AS payer_count,
       ROUND(MIN(negotiated_dollar), 2)        AS min_rate,
       ROUND(AVG(negotiated_dollar), 2)        AS avg_rate,
       ROUND(MAX(negotiated_dollar), 2)        AS max_rate
FROM v_rate
WHERE negotiated_dollar IS NOT NULL
GROUP BY hospital_id, service_code, code_type;

-- Head-to-head: LVHN vs St. Luke's average negotiated dollar per service.
CREATE VIEW v_network_gap AS
SELECT s.category,
       s.service_code,
       s.code_type,
       s.service_name,
       ROUND(AVG(CASE WHEN v.network_name LIKE 'Lehigh%'   THEN v.negotiated_dollar END), 2) AS lvhn_avg,
       ROUND(AVG(CASE WHEN v.network_name LIKE 'St. Luke%' THEN v.negotiated_dollar END), 2) AS stlukes_avg,
       ROUND(AVG(CASE WHEN v.network_name LIKE 'Lehigh%'   THEN v.negotiated_dollar END)
           - AVG(CASE WHEN v.network_name LIKE 'St. Luke%' THEN v.negotiated_dollar END), 2) AS lvhn_minus_stlukes
FROM service s
JOIN v_rate v ON v.service_code = s.service_code AND v.code_type = s.code_type
WHERE v.negotiated_dollar IS NOT NULL
GROUP BY s.service_code, s.code_type
HAVING lvhn_avg IS NOT NULL AND stlukes_avg IS NOT NULL;
