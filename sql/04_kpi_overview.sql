-- =====================================================================
-- 04_kpi_overview.sql – Fő mutatók évenként, éves változással
-- =====================================================================

WITH yearly AS (
    SELECT
        order_year,
        COUNT(DISTINCT order_id)     AS orders,
        COUNT(DISTINCT customer_id)  AS active_customers,
        SUM(net_revenue)             AS revenue,
        SUM(gross_margin)            AS gross_margin
    FROM v_sales_lines
    GROUP BY order_year
)
SELECT
    order_year                                       AS ev,
    orders                                           AS rendelesek,
    active_customers                                 AS aktiv_vevok,
    ROUND(revenue / 1e6, 1)                          AS arbevetel_mFt,
    ROUND(revenue / orders)                          AS atlagos_kosarertek_Ft,
    ROUND(100.0 * gross_margin / revenue, 1)         AS arres_szazalek,
    ROUND(100.0 * (revenue / LAG(revenue) OVER (ORDER BY order_year) - 1), 1)
                                                     AS arbevetel_valtozas_szazalek
FROM yearly
ORDER BY order_year;
