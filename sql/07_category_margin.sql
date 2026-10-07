-- =====================================================================
-- 07_category_margin.sql – Termékkategóriák árbevétele és jövedelmezősége
-- =====================================================================

SELECT
    category                                                AS kategoria,
    ROUND(SUM(net_revenue) / 1e6, 1)                        AS arbevetel_mFt,
    ROUND(100.0 * SUM(net_revenue) / SUM(SUM(net_revenue)) OVER (), 1)
                                                            AS arbevetel_reszesedes_szazalek,
    ROUND(SUM(gross_margin) / 1e6, 1)                       AS arres_mFt,
    ROUND(100.0 * SUM(gross_margin) / SUM(net_revenue), 1)  AS arres_szazalek,
    RANK() OVER (ORDER BY SUM(gross_margin) DESC)           AS arres_rang
FROM v_sales_lines
GROUP BY category
ORDER BY arbevetel_mFt DESC;
