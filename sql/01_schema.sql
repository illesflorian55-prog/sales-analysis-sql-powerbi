-- =====================================================================
-- 01_schema.sql – Adatbázisséma (SQLite)
-- Order-to-cash folyamat: vevői rendelés -> kiszállítás -> számla -> fizetés
-- =====================================================================

DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS deliveries;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS sales_orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

-- Vevőtörzs
CREATE TABLE customers (
    customer_id         TEXT PRIMARY KEY,
    customer_name       TEXT NOT NULL,
    segment             TEXT NOT NULL,          -- Nagyvállalat / KKV / Közszféra
    region              TEXT NOT NULL,
    payment_terms_days  INTEGER NOT NULL,       -- fizetési határidő napokban
    customer_since      DATE NOT NULL
);

-- Anyagtörzs
CREATE TABLE products (
    product_id    TEXT PRIMARY KEY,
    product_name  TEXT NOT NULL,
    category      TEXT NOT NULL,
    unit_price    REAL NOT NULL,                -- listaár (Ft, nettó)
    unit_cost     REAL NOT NULL                 -- beszerzési ár (Ft, nettó)
);

-- Vevői rendelés fejléce (SAP SD: VA01)
CREATE TABLE sales_orders (
    order_id       TEXT PRIMARY KEY,
    customer_id    TEXT NOT NULL REFERENCES customers (customer_id),
    order_date     DATE NOT NULL,
    sales_channel  TEXT NOT NULL,               -- Webshop / Értékesítő / EDI
    status         TEXT NOT NULL                -- Teljesített / Törölt
);

-- Rendelési tételek
CREATE TABLE order_items (
    order_id      TEXT NOT NULL REFERENCES sales_orders (order_id),
    line_no       INTEGER NOT NULL,
    product_id    TEXT NOT NULL REFERENCES products (product_id),
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    unit_price    REAL NOT NULL,                -- rendeléskori ár
    unit_cost     REAL NOT NULL,
    discount_pct  REAL NOT NULL DEFAULT 0 CHECK (discount_pct BETWEEN 0 AND 1),
    PRIMARY KEY (order_id, line_no)
);

-- Kiszállítás (SAP SD: VL01N)
CREATE TABLE deliveries (
    delivery_id    TEXT PRIMARY KEY,
    order_id       TEXT NOT NULL UNIQUE REFERENCES sales_orders (order_id),
    planned_date   DATE NOT NULL,
    delivery_date  DATE NOT NULL
);

-- Számla és kiegyenlítés (SAP SD: VF01, FI: beérkező fizetés)
CREATE TABLE invoices (
    invoice_id    TEXT PRIMARY KEY,
    order_id      TEXT NOT NULL UNIQUE REFERENCES sales_orders (order_id),
    invoice_date  DATE NOT NULL,
    due_date      DATE NOT NULL,
    payment_date  DATE                          -- NULL = még nyitott tétel
);

CREATE INDEX idx_orders_customer ON sales_orders (customer_id);
CREATE INDEX idx_orders_date     ON sales_orders (order_date);
CREATE INDEX idx_items_product   ON order_items (product_id);
