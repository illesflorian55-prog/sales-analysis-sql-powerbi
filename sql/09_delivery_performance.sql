-- =====================================================================
-- 09_delivery_performance.sql – Határidőre teljesített kiszállítások
-- aránya (OTD, on-time delivery) régiónként
-- =====================================================================

SELECT
    c.region                                                       AS regio,
    COUNT(*)                                                       AS kiszallitasok,
    ROUND(100.0 * AVG(d.delivery_date <= d.planned_date), 1)       AS hataridore_szazalek,
    ROUND(AVG(MAX(julianday(d.delivery_date) - julianday(d.planned_date), 0)), 2)
                                                                   AS atlagos_keses_nap,
    ROUND(AVG(julianday(d.delivery_date) - julianday(o.order_date)), 1)
                                                                   AS atlagos_atfutas_nap
FROM deliveries   d
JOIN sales_orders o ON o.order_id = d.order_id
JOIN customers    c ON c.customer_id = o.customer_id
GROUP BY c.region
ORDER BY hataridore_szazalek;
