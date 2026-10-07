-- =====================================================================
-- 06_customer_abc.sql – Vevők ABC-elemzése (Pareto-elv)
-- A: a forgalom első 80%-át adó vevők, B: a következő 15%, C: a maradék 5%
-- Ablakfüggvény: kumulált részarány árbevétel szerint csökkenő sorrendben
-- =====================================================================

WITH customer_revenue AS (
    SELECT
        customer_id,
        customer_name,
        segment,
        SUM(net_revenue) AS revenue
    FROM v_sales_lines
    GROUP BY customer_id, customer_name, segment
),
ranked AS (
    SELECT
        *,
        SUM(revenue) OVER (ORDER BY revenue DESC
                           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
            / SUM(revenue) OVER () AS cumulative_share
    FROM customer_revenue
),
classified AS (
    SELECT
        *,
        CASE
            WHEN cumulative_share - revenue / SUM(revenue) OVER () < 0.80 THEN 'A'
            WHEN cumulative_share - revenue / SUM(revenue) OVER () < 0.95 THEN 'B'
            ELSE 'C'
        END AS abc_class
    FROM ranked
)
SELECT
    abc_class                                                  AS osztaly,
    COUNT(*)                                                   AS vevok_szama,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)         AS vevok_aranya_szazalek,
    ROUND(SUM(revenue) / 1e6, 1)                               AS arbevetel_mFt,
    ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 1) AS arbevetel_aranya_szazalek
FROM classified
GROUP BY abc_class
ORDER BY abc_class;
