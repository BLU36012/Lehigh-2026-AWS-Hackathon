-- Example queries against data/lehigh_valley_prices.db
--   sqlite3 data/lehigh_valley_prices.db ".read sql/example_queries.sql"

-- 1. What is in here?
SELECT n.network_name, h.hospital_id, h.campus, h.last_updated_on,
       COUNT(DISTINCT ci.service_code) AS services,
       COUNT(r.rate_id)                AS rates
FROM hospital h
JOIN network n          ON n.network_id = h.network_id
JOIN charge_item ci     ON ci.hospital_id = h.hospital_id
JOIN negotiated_rate r  ON r.item_id = ci.item_id
GROUP BY h.hospital_id;

-- 2. Same payer, same service, both networks: who negotiated harder?
SELECT service_code, service_name, payer_name,
       ROUND(AVG(CASE WHEN hospital_id = 'LVH-ALL'  THEN negotiated_dollar END), 2) AS lvhn,
       ROUND(AVG(CASE WHEN hospital_id = 'SLH-BETH' THEN negotiated_dollar END), 2) AS stlukes_bethlehem
FROM v_rate
WHERE negotiated_dollar IS NOT NULL
GROUP BY service_code, payer_name
HAVING lvhn IS NOT NULL AND stlukes_bethlehem IS NOT NULL
ORDER BY ABS(lvhn - stlukes_bethlehem) DESC
LIMIT 25;

-- 3. Widest payer spread for one service at one hospital
--    (how much the same MRI costs depending only on your insurance card)
SELECT hospital_id, service_code, service_name,
       COUNT(*)                          AS rates,
       ROUND(MIN(negotiated_dollar), 2)  AS cheapest,
       ROUND(MAX(negotiated_dollar), 2)  AS dearest,
       ROUND(MAX(negotiated_dollar) / NULLIF(MIN(negotiated_dollar), 0), 1) AS spread_x
FROM v_rate
WHERE negotiated_dollar > 0
GROUP BY hospital_id, service_code
HAVING rates >= 5
ORDER BY spread_x DESC
LIMIT 20;

-- 4. Inpatient DRG comparison across the two networks
SELECT * FROM v_network_gap
WHERE code_type = 'MS-DRG'
ORDER BY lvhn_minus_stlukes DESC;

-- 5. Cheapest option per service, for the 13 payers both networks contract with
SELECT v.service_code, v.service_name, v.payer_name,
       v.hospital_id, ROUND(MIN(v.negotiated_dollar), 2) AS best_rate
FROM v_rate v
WHERE v.negotiated_dollar > 0
  AND v.payer_name IN (
      SELECT p.payer_name FROM payer p
      JOIN plan pl    ON pl.payer_id = p.payer_id
      JOIN hospital h ON h.hospital_id = pl.hospital_id
      GROUP BY p.payer_name
      HAVING COUNT(DISTINCT h.network_id) = 2)
GROUP BY v.service_code, v.payer_name
ORDER BY v.service_code, v.payer_name
LIMIT 40;

-- 6. Rates that are not a dollar amount (percent-of-charges / algorithm)
SELECT hospital_id, methodology, COUNT(*) AS n
FROM v_rate
WHERE negotiated_dollar IS NULL
GROUP BY hospital_id, methodology;

-- 7. Payer name normalization audit
SELECT p.payer_name AS canonical, a.hospital_id, a.raw_name
FROM payer_alias a
JOIN payer p ON p.payer_id = a.payer_id
ORDER BY canonical, a.hospital_id;
