# Power BI riport – felépítési útmutató

Ez az útmutató leírja, hogyan épül fel a projekt Power BI riportja a `data/raw/` mappa CSV-fájljaiból: az adatmodell, a DAX-mértékek és a riportoldalak.

## 1. Adatok betöltése

**Kezdőlap → Adatok lekérése → Szöveg/CSV**, majd a `data/raw/` mappa hat fájlja:

| Fájl | Tábla szerepe |
|---|---|
| `customers.csv` | dimenzió – vevők |
| `products.csv` | dimenzió – termékek |
| `sales_orders.csv` | rendelésfej (a rendelés dátuma, csatorna, státusz) |
| `order_items.csv` | **ténytábla** – rendelési tételek |
| `deliveries.csv` | kiszállítások |
| `invoices.csv` | számlák és kifizetések |

A Power Queryben ellenőrizendő: a dátumoszlopok típusa *Dátum*, a `unit_price`, `unit_cost` és `discount_pct` típusa *Tizedes tört*. A területi beállítás legyen angol (Egyesült Államok), mert a CSV-k tizedespontot használnak.

## 2. Adatmodell (csillagséma)

```
                 customers                  products
                     │ 1                        │ 1
                     │                          │
                     ▼ *                        ▼ *
  Date 1 ──► * sales_orders 1 ──► * order_items
                     │ 1
          ┌──────────┴──────────┐
          ▼ 1                   ▼ 1
      deliveries             invoices
```

Kapcsolatok (*Modellnézet*):

| Innen (1) | Ide (*) | Kulcs |
|---|---|---|
| `customers` | `sales_orders` | `customer_id` |
| `products` | `order_items` | `product_id` |
| `sales_orders` | `order_items` | `order_id` |
| `sales_orders` | `deliveries` | `order_id` (1:1) |
| `sales_orders` | `invoices` | `order_id` (1:1) |
| `Date` | `sales_orders` | `Date[Date]` → `order_date` |

A `Date` dátumtábla DAX-szal (**Modellezés → Új tábla**), majd *Megjelölés dátumtáblaként*:

```dax
Date =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2024, 1, 1 ), DATE ( 2025, 12, 31 ) ),
    "Év", YEAR ( [Date] ),
    "Hónap száma", MONTH ( [Date] ),
    "Hónap", FORMAT ( [Date], "yyyy-mm" ),
    "Negyedév", "Q" & QUARTER ( [Date] )
)
```

Az `order_items` táblába két számított oszlop kerül:

```dax
Net Revenue = order_items[quantity] * order_items[unit_price] * ( 1 - order_items[discount_pct] )
Line Cost   = order_items[quantity] * order_items[unit_cost]
```

## 3. DAX-mértékek

Egy külön `_Measures` táblába gyűjtve:

```dax
-- Árbevétel csak a teljesített rendelésekből
Revenue =
CALCULATE (
    SUM ( order_items[Net Revenue] ),
    sales_orders[status] = "Teljesített"
)

Gross Margin =
[Revenue]
    - CALCULATE ( SUM ( order_items[Line Cost] ), sales_orders[status] = "Teljesített" )

Gross Margin % = DIVIDE ( [Gross Margin], [Revenue] )

Orders =
CALCULATE ( DISTINCTCOUNT ( sales_orders[order_id] ), sales_orders[status] = "Teljesített" )

Average Order Value = DIVIDE ( [Revenue], [Orders] )

-- Előző év azonos időszaka és éves változás
Revenue PY = CALCULATE ( [Revenue], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )

Revenue YoY % = DIVIDE ( [Revenue] - [Revenue PY], [Revenue PY] )

Revenue YTD = TOTALYTD ( [Revenue], 'Date'[Date] )

-- Határidőre szállítás aránya (OTD)
On-Time Delivery % =
DIVIDE (
    COUNTROWS ( FILTER ( deliveries, deliveries[delivery_date] <= deliveries[planned_date] ) ),
    COUNTROWS ( deliveries )
)

-- Késve fizetett számlák aránya
Late Payment % =
DIVIDE (
    COUNTROWS (
        FILTER ( invoices, NOT ISBLANK ( invoices[payment_date] )
                           && invoices[payment_date] > invoices[due_date] )
    ),
    COUNTROWS ( FILTER ( invoices, NOT ISBLANK ( invoices[payment_date] ) ) )
)

-- Átlagos fizetési idő (számlától a kifizetésig, napokban)
Avg Days to Pay =
AVERAGEX (
    FILTER ( invoices, NOT ISBLANK ( invoices[payment_date] ) ),
    DATEDIFF ( invoices[invoice_date], invoices[payment_date], DAY )
)

-- Nyitott (ki nem fizetett) számlák darabszáma
Open Invoices = COUNTROWS ( FILTER ( invoices, ISBLANK ( invoices[payment_date] ) ) )
```

## 4. Riportoldalak

**1. Áttekintés**
- KPI-kártyák: `Revenue`, `Revenue YoY %`, `Gross Margin %`, `Orders`, `Average Order Value`
- Vonaldiagram: `Revenue` és `Revenue PY` havonta (`Date[Hónap]`)
- Szeletelők: `Date[Év]`, `customers[segment]`, `customers[region]`

**2. Vevők és termékek**
- Sávdiagram: `Revenue` és `Gross Margin %` kategóriánként
- Táblázat: top 10 vevő `Revenue` szerint
- Fatérkép: árbevétel szegmens és régió szerint

**3. Logisztika és pénzügy (order-to-cash)**
- Sávdiagram: `On-Time Delivery %` régiónként, 90%-os célvonallal
- Oszlopdiagram: `Late Payment %` és `Avg Days to Pay` szegmensenként
- Kártya: `Open Invoices`

A számok ellenőrizhetők: a mértékeknek ugyanazt kell adniuk, mint a `results/` mappában lévő SQL-eredményeknek (pl. 2025-ös árbevétel 1 363,5 millió Ft, éves változás +11,6%).
