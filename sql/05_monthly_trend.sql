-- =====================================================================
-- 05_monthly_trend.sql – Havi árbevétel, előző év azonos hónapjához mért
-- változás (YoY) és éven belüli kumulált árbevétel
-- Ablakfüggvények: LAG, SUM() OVER (PARTITION BY ...)
-- =====================================================================

WITH monthly AS (
    SELECT
        order_month,
        order_year,
        SUM(net_revenue) AS revenue
    FROM v_sales_lines
    GROUP BY order_month, order_year
)
SELECT
    order_month                                          AS honap,
    ROUND(revenue / 1e6, 1)                              AS arbevetel_mFt,
    ROUND(LAG(revenue, 12) OVER (ORDER BY order_month) / 1e6, 1)
                                                         AS elozo_ev_mFt,
    ROUND(100.0 * (revenue / LAG(revenue, 12) OVER (ORDER BY order_month) - 1), 1)
                                                         AS yoy_valtozas_szazalek,
    ROUND(SUM(revenue) OVER (PARTITION BY order_year ORDER BY order_month) / 1e6, 1)
                                                         AS eves_kumulalt_mFt
FROM monthly
ORDER BY order_month;
