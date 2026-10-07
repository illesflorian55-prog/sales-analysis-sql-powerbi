-- =====================================================================
-- 10_payment_behaviour.sql – Fizetési fegyelem szegmensenként
-- Order-to-cash átfutás: a rendeléstől a pénz beérkezéséig eltelt napok
-- =====================================================================

WITH invoice_values AS (
    SELECT order_id, SUM(quantity * unit_price * (1 - discount_pct)) AS amount
    FROM order_items
    GROUP BY order_id
)
SELECT
    c.segment                                                         AS szegmens,
    COUNT(*)                                                          AS kifizetett_szamlak,
    ROUND(100.0 * AVG(v.payment_date > v.due_date), 1)                AS kesve_fizetett_szazalek,
    ROUND(AVG(julianday(v.payment_date) - julianday(v.invoice_date)), 1)
                                                                      AS atlagos_fizetesi_ido_nap,
    ROUND(AVG(julianday(v.payment_date) - julianday(o.order_date)), 1)
                                                                      AS order_to_cash_nap,
    ROUND(SUM(iv.amount * (julianday(v.payment_date) - julianday(v.invoice_date)))
          / SUM(iv.amount), 1)                                        AS ertekkel_sulyozott_fizetesi_ido_nap
FROM invoices       v
JOIN sales_orders   o  ON o.order_id = v.order_id
JOIN customers      c  ON c.customer_id = o.customer_id
JOIN invoice_values iv ON iv.order_id = v.order_id
WHERE v.payment_date IS NOT NULL
GROUP BY c.segment
ORDER BY kesve_fizetett_szazalek DESC;
