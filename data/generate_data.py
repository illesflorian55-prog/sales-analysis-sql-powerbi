"""
Szintetikus értékesítési (order-to-cash) adatkészlet generálása.

Fiktív cég: Pannon Office Supply Kft. – irodaszer-nagykereskedő, amely
magyarországi vállalati ügyfeleket szolgál ki.

Az adatok NEM valósak: egy rögzített véletlenmaggal (seed) generált,
reprodukálható mintaadatkészlet, amely egy SAP SD-szerű értékesítési
folyamatot modellez: vevői rendelés -> kiszállítás -> számla -> fizetés.

Futtatás:  python data/generate_data.py
Kimenet:   data/raw/*.csv
"""

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
START = date(2024, 1, 1)
END = date(2025, 12, 31)
N_CUSTOMERS = 250
N_ORDERS = 5200

OUT_DIR = Path(__file__).resolve().parent / "raw"
rng = np.random.default_rng(SEED)

# --------------------------------------------------------------------------
# Törzsadatok
# --------------------------------------------------------------------------
REGIONS = {
    # régió: (súly, átlagos szállítási késés napban, tervezett átfutás napban)
    "Budapest": (0.32, 0.4, 1),
    "Pest": (0.14, 0.6, 2),
    "Közép-Dunántúl": (0.10, 0.9, 2),
    "Nyugat-Dunántúl": (0.09, 1.0, 3),
    "Dél-Dunántúl": (0.07, 1.3, 3),
    "Észak-Magyarország": (0.08, 2.0, 3),
    "Észak-Alföld": (0.10, 1.5, 3),
    "Dél-Alföld": (0.10, 1.1, 3),
}

SEGMENTS = {
    # szegmens: (súly, fizetési határidő napban, átlagos fizetési késés, kedvezmény)
    "Nagyvállalat": (0.15, 45, 3, 0.08),
    "KKV": (0.65, 30, 5, 0.03),
    "Közszféra": (0.20, 30, 14, 0.05),
}

CATEGORIES = {
    # kategória: (termékek, árszint Ft, árrés %, szezonális csúcshónapok)
    "Papír és irodaszer": (14, 2500, 0.32, [8, 9, 1]),
    "Nyomtatás és toner": (10, 18000, 0.24, []),
    "IT-kiegészítők": (12, 12000, 0.22, [11, 12]),
    "Irodabútor": (8, 65000, 0.30, [1, 2, 9]),
    "Tisztítószer és higiénia": (8, 3500, 0.35, [3, 10]),
    "Kávé és konyha": (8, 5500, 0.40, [12]),
}

PRODUCT_NAMES = {
    "Papír és irodaszer": [
        "Másolópapír A4 80g (500 lap)", "Másolópapír A3 80g (500 lap)",
        "Spirálfüzet A4 kockás", "Iratrendező 75 mm", "Genotherm A4 (100 db)",
        "Golyóstoll kék (50 db)", "Szövegkiemelő készlet", "Tűzőgép 24/6",
        "Tűzőkapocs 24/6 (1000 db)", "Post-it jegyzettömb (12 db)",
        "Boríték LC/5 (1000 db)", "Irattartó papucs", "Ragasztóroller",
        "Iratmegsemmisítő-papír tasak"],
    "Nyomtatás és toner": [
        "Lézertoner fekete (standard)", "Lézertoner fekete (nagy kapacitású)",
        "Színes toner készlet (CMY)", "Tintapatron fekete", "Tintapatron színes",
        "Dobegység", "Címkenyomtató szalag", "Fotópapír A4 (50 lap)",
        "Nyomtató-karbantartó készlet", "Lézertoner felújított"],
    "IT-kiegészítők": [
        "Vezeték nélküli egér", "Vezeték nélküli billentyűzet", "USB-C dokkoló",
        "Monitor 24\"", "Webkamera Full HD", "Headset zajszűrős",
        "USB pendrive 64 GB", "Külső SSD 1 TB", "HDMI kábel 2 m",
        "Laptoptáska 15,6\"", "Elosztó túlfeszültség-védelemmel",
        "Monitorkar dupla"],
    "Irodabútor": [
        "Ergonomikus irodaszék", "Állítható magasságú íróasztal", "Tárgyalóasztal",
        "Fémszekrény zárható", "Görgős konténer", "Tárgyalószék",
        "Polcos szekrény", "Lábtartó ergonomikus"],
    "Tisztítószer és higiénia": [
        "Kéztörlő papír (20 tekercs)", "Toalettpapír (24 tekercs)",
        "Folyékony szappan 5 l", "Kézfertőtlenítő 5 l", "Felülettisztító 5 l",
        "Szemeteszsák (50 db)", "Mosogatószer 5 l", "Mikroszálas kendő (10 db)"],
    "Kávé és konyha": [
        "Szemes kávé 1 kg", "Kávékapszula (100 db)", "Tea válogatás (100 filter)",
        "Cukor tasakos (1000 db)", "Papírpohár (1000 db)", "Ásványvíz (24 x 0,5 l)",
        "Tejszín kávéhoz (120 db)", "Vízforraló"],
}

FIRST_PARTS = ["Duna", "Tisza", "Alföld", "Bükk", "Mátra", "Balaton", "Pannon",
               "Kárpát", "Zemplén", "Hegyalja", "Rába", "Dráva", "Kőrös", "Sajó"]
SECOND_PARTS = ["Logisztika", "Építő", "Informatika", "Ipari", "Kereskedelmi",
                "Szolgáltató", "Mérnöki", "Agrár", "Egészségügyi", "Oktatási"]
PUBLIC_NAMES = ["Önkormányzat", "Kormányhivatal", "Kórház", "Iskola",
                "Szakképzési Centrum", "Vízmű"]


def make_customers() -> pd.DataFrame:
    regions = list(REGIONS)
    region_w = np.array([REGIONS[r][0] for r in regions])
    segments = list(SEGMENTS)
    segment_w = np.array([SEGMENTS[s][0] for s in segments])

    rows = []
    used = set()
    for i in range(1, N_CUSTOMERS + 1):
        segment = rng.choice(segments, p=segment_w / segment_w.sum())
        region = rng.choice(regions, p=region_w / region_w.sum())
        if segment == "Közszféra":
            base = f"{rng.choice(FIRST_PARTS)}menti {rng.choice(PUBLIC_NAMES)}"
        else:
            suffix = "Zrt." if segment == "Nagyvállalat" else rng.choice(["Kft.", "Bt."])
            base = f"{rng.choice(FIRST_PARTS)} {rng.choice(SECOND_PARTS)} {suffix}"
        name, k = base, 2
        while name in used:  # ütközésnél sorszámot kap a név
            name = f"{base} ({k})"
            k += 1
        used.add(name)
        # kb. 65% régi ügyfél, a többi az időszak alatt szerzett új ügyfél
        if rng.random() < 0.65:
            first_order = date(2019, 1, 1) + timedelta(days=int(rng.integers(0, 1800)))
        else:
            first_order = START + timedelta(days=int(rng.integers(0, 640)))
        rows.append({
            "customer_id": f"C{i:04d}",
            "customer_name": name,
            "segment": segment,
            "region": region,
            "payment_terms_days": SEGMENTS[segment][1],
            "customer_since": first_order.isoformat(),
        })
    return pd.DataFrame(rows)


def make_products() -> pd.DataFrame:
    rows = []
    pid = 1
    for category, (count, price_level, margin, _) in CATEGORIES.items():
        for j in range(1, count + 1):
            price = round(price_level * rng.lognormal(0, 0.45), -1)
            item_margin = np.clip(rng.normal(margin, 0.05), 0.08, 0.6)
            rows.append({
                "product_id": f"P{pid:03d}",
                "product_name": PRODUCT_NAMES[category][j - 1],
                "category": category,
                "unit_price": price,
                "unit_cost": round(price * (1 - item_margin), -1),
            })
            pid += 1
    return pd.DataFrame(rows)


def seasonal_weight(d: date) -> float:
    """Havi szezonalitás + kb. 12%-os éves növekedés."""
    month_factor = {1: 0.95, 2: 0.95, 3: 1.05, 4: 1.0, 5: 1.0, 6: 0.95,
                    7: 0.7, 8: 0.85, 9: 1.3, 10: 1.1, 11: 1.15, 12: 1.0}[d.month]
    growth = 1.12 ** ((d - START).days / 365)
    weekday = 1.0 if d.weekday() < 5 else 0.08
    return month_factor * growth * weekday


def make_orders(customers: pd.DataFrame, products: pd.DataFrame):
    days = [START + timedelta(days=i) for i in range((END - START).days + 1)]
    day_w = np.array([seasonal_weight(d) for d in days])
    order_days = rng.choice(len(days), size=N_ORDERS, p=day_w / day_w.sum())
    order_days.sort()

    # Pareto-szerű vevőaktivitás: kevés vevő adja a forgalom nagy részét
    activity = rng.lognormal(0, 1.1, size=len(customers))
    activity *= np.where(customers["segment"] == "Nagyvállalat", 3.0, 1.0)
    cust_p = activity / activity.sum()

    since = pd.to_datetime(customers["customer_since"]).dt.date.values
    cat_products = {c: products[products["category"] == c] for c in CATEGORIES}
    categories = list(CATEGORIES)

    orders, items, deliveries, invoices = [], [], [], []
    for n, day_idx in enumerate(order_days, start=1):
        order_date = days[day_idx]
        # csak olyan vevő rendelhet, aki már ügyfél
        eligible = since <= order_date
        p = np.where(eligible, cust_p, 0)
        cust = customers.iloc[rng.choice(len(customers), p=p / p.sum())]
        seg = SEGMENTS[cust["segment"]]
        order_id = f"SO{n:06d}"

        status = "Törölt" if rng.random() < 0.03 else "Teljesített"
        orders.append({
            "order_id": order_id,
            "customer_id": cust["customer_id"],
            "order_date": order_date.isoformat(),
            "sales_channel": rng.choice(["Webshop", "Értékesítő", "EDI"],
                                        p=[0.5, 0.35, 0.15]),
            "status": status,
        })

        # rendelési tételek, szezonális kategóriasúlyokkal
        cat_w = np.array([1.6 if order_date.month in CATEGORIES[c][3] else 1.0
                          for c in categories])
        n_lines = int(rng.integers(1, 7))
        chosen = rng.choice(categories, size=n_lines, p=cat_w / cat_w.sum())
        used_products = set()
        line = 0
        for cat in chosen:
            pool = cat_products[cat]
            prod = pool.iloc[int(rng.integers(0, len(pool)))]
            if prod["product_id"] in used_products:
                continue
            used_products.add(prod["product_id"])
            line += 1
            base_qty = 2 if cat == "Irodabútor" else 12
            qty = max(1, int(rng.poisson(base_qty * (2.5 if cust["segment"] == "Nagyvállalat" else 1))))
            discount = round(max(0, rng.normal(seg[3], 0.015)), 3)
            items.append({
                "order_id": order_id,
                "line_no": line,
                "product_id": prod["product_id"],
                "quantity": qty,
                "unit_price": prod["unit_price"],
                "unit_cost": prod["unit_cost"],
                "discount_pct": discount,
            })

        if status == "Törölt":
            continue

        # kiszállítás
        _, mean_delay, lead = REGIONS[cust["region"]]
        planned = order_date + timedelta(days=lead)
        delay = int(rng.poisson(mean_delay)) if rng.random() < 0.35 else 0
        actual = planned + timedelta(days=delay)
        deliveries.append({
            "delivery_id": f"DL{n:06d}",
            "order_id": order_id,
            "planned_date": planned.isoformat(),
            "delivery_date": actual.isoformat(),
        })

        # számla és fizetés
        due = actual + timedelta(days=int(cust["payment_terms_days"]))
        pay_delay = int(rng.gamma(1.2, seg[2])) - int(rng.integers(0, 6))
        payment = due + timedelta(days=pay_delay)
        invoices.append({
            "invoice_id": f"INV{n:06d}",
            "order_id": order_id,
            "invoice_date": actual.isoformat(),
            "due_date": due.isoformat(),
            # a 2025. év végéig ki nem fizetett számlák nyitott tételek
            "payment_date": payment.isoformat() if payment <= END else None,
        })

    return (pd.DataFrame(orders), pd.DataFrame(items),
            pd.DataFrame(deliveries), pd.DataFrame(invoices))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    customers = make_customers()
    products = make_products()
    orders, items, deliveries, invoices = make_orders(customers, products)

    tables = {
        "customers": customers,
        "products": products,
        "sales_orders": orders,
        "order_items": items,
        "deliveries": deliveries,
        "invoices": invoices,
    }
    for name, df in tables.items():
        df.to_csv(OUT_DIR / f"{name}.csv", index=False, encoding="utf-8")
        print(f"{name:<14} {len(df):>6} sor")


if __name__ == "__main__":
    main()
