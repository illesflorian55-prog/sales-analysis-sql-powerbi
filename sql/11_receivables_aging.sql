-- =====================================================================
-- 11_receivables_aging.sql – Nyitott vevői követelések korosítása
-- a vizsgált időszak végén (2025-12-31)
-- =====================================================================

WITH open_items AS (
    SELECT
        v.invoice_id,
        julianday('2025-12-31') - julianday(v.due_date) AS days_overdue,
        (SELECT SUM(quantity * unit_price * (1 - discount_pct))
         FROM order_items i WHERE i.order_id = v.order_id) AS amount
    FROM invoices v
    WHERE v.payment_date IS NULL
),
bucketed AS (
    SELECT
        CASE
            WHEN days_overdue <= 0  THEN '1. Nem lejárt'
            WHEN days_overdue <= 30 THEN '2. 1–30 napja lejárt'
            WHEN days_overdue <= 60 THEN '3. 31–60 napja lejárt'
            ELSE                         '4. 60 napon túl lejárt'
        END AS bucket,
        amount
    FROM open_items
)
SELECT
    bucket                                                      AS korosztaly,
    COUNT(*)                                                    AS szamlak,
    ROUND(SUM(amount) / 1e6, 1)                                 AS osszeg_mFt,
    ROUND(100.0 * SUM(amount) / SUM(SUM(amount)) OVER (), 1)    AS aranya_szazalek
FROM bucketed
GROUP BY bucket
ORDER BY bucket;
