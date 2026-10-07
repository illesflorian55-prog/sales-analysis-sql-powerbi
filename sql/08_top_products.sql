-- =====================================================================
-- 08_top_products.sql – A 3 legnagyobb árbevételű termék kategóriánként
-- Ablakfüggvény: ROW_NUMBER() OVER (PARTITION BY ...)
-- =====================================================================

WITH product_sales AS (
    SELECT
        category,
        product_name,
        SUM(quantity)     AS units,
        SUM(net_revenue)  AS revenue,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY SUM(net_revenue) DESC) AS rn
    FROM v_sales_lines
    GROUP BY category, product_name
)
SELECT
    category               AS kategoria,
    rn                     AS helyezes,
    product_name           AS termek,
    units                  AS eladott_db,
    ROUND(revenue / 1e6, 1) AS arbevetel_mFt
FROM product_sales
WHERE rn <= 3
ORDER BY category, rn;
