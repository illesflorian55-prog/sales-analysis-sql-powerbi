-- =====================================================================
-- 02_views.sql – Elemzési nézet
-- Egy sor = egy teljesített rendelési tétel, minden elemzéshez szükséges
-- dimenzióval és számított mutatóval. A többi lekérdezés erre épül.
-- =====================================================================

DROP VIEW IF EXISTS v_sales_lines;

CREATE VIEW v_sales_lines AS
SELECT
    o.order_id,
    o.order_date,
    CAST(strftime('%Y', o.order_date) AS INTEGER)       AS order_year,
    strftime('%Y-%m', o.order_date)                     AS order_month,
    o.sales_channel,
    c.customer_id,
    c.customer_name,
    c.segment,
    c.region,
    p.product_id,
    p.product_name,
    p.category,
    i.quantity,
    -- nettó árbevétel = mennyiség x ár x (1 - kedvezmény)
    i.quantity * i.unit_price * (1 - i.discount_pct)    AS net_revenue,
    i.quantity * i.unit_cost                            AS cost,
    i.quantity * i.unit_price * (1 - i.discount_pct)
        - i.quantity * i.unit_cost                      AS gross_margin
FROM sales_orders AS o
JOIN order_items  AS i ON i.order_id = o.order_id
JOIN customers    AS c ON c.customer_id = o.customer_id
JOIN products     AS p ON p.product_id = i.product_id
WHERE o.status = 'Teljesített';
