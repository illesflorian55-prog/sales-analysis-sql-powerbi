-- =====================================================================
-- 03_data_quality.sql – Adatminőségi ellenőrzések
-- Minden sornak 0 hibát kell mutatnia, mielőtt az elemzéseknek hiszünk.
-- =====================================================================

SELECT 'Rendelés ismeretlen vevővel' AS ellenorzes, COUNT(*) AS hibas_sorok
FROM sales_orders o
LEFT JOIN customers c ON c.customer_id = o.customer_id
WHERE c.customer_id IS NULL

UNION ALL
SELECT 'Tétel ismeretlen termékkel', COUNT(*)
FROM order_items i
LEFT JOIN products p ON p.product_id = i.product_id
WHERE p.product_id IS NULL

UNION ALL
SELECT 'Rendelés tétel nélkül', COUNT(*)
FROM sales_orders o
WHERE NOT EXISTS (SELECT 1 FROM order_items i WHERE i.order_id = o.order_id)

UNION ALL
SELECT 'Teljesített rendelés számla nélkül', COUNT(*)
FROM sales_orders o
LEFT JOIN invoices v ON v.order_id = o.order_id
WHERE o.status = 'Teljesített' AND v.invoice_id IS NULL

UNION ALL
SELECT 'Törölt rendelés kiszállítással', COUNT(*)
FROM sales_orders o
JOIN deliveries d ON d.order_id = o.order_id
WHERE o.status = 'Törölt'

UNION ALL
SELECT 'Kiszállítás a rendelés előtt', COUNT(*)
FROM deliveries d
JOIN sales_orders o ON o.order_id = d.order_id
WHERE d.delivery_date < o.order_date

UNION ALL
SELECT 'Negatív árrésű tétel', COUNT(*)
FROM order_items
WHERE unit_price * (1 - discount_pct) < unit_cost;
