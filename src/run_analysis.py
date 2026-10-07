"""
Teljes elemzési folyamat egy lépésben:

1. SQLite adatbázis létrehozása a sémából (sql/01_schema.sql)
2. A nyers CSV-k betöltése (data/raw/*.csv)
3. Az elemzési nézet létrehozása (sql/02_views.sql)
4. Az elemző lekérdezések futtatása (sql/03_*.sql ... sql/11_*.sql),
   az eredmények mentése a results/ mappába CSV-ként

Futtatás:  python src/run_analysis.py
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"
RAW_DIR = ROOT / "data" / "raw"
RESULTS_DIR = ROOT / "results"
DB_PATH = ROOT / "data" / "sales.db"

# betöltési sorrend: előbb a törzsadatok, utána a rájuk hivatkozó táblák
TABLES = ["customers", "products", "sales_orders", "order_items",
          "deliveries", "invoices"]


def build_database(con: sqlite3.Connection) -> None:
    con.executescript((SQL_DIR / "01_schema.sql").read_text(encoding="utf-8"))
    for table in TABLES:
        df = pd.read_csv(RAW_DIR / f"{table}.csv")
        df.to_sql(table, con, if_exists="append", index=False)
    con.executescript((SQL_DIR / "02_views.sql").read_text(encoding="utf-8"))
    con.commit()


def run_queries(con: sqlite3.Connection) -> dict[str, pd.DataFrame]:
    RESULTS_DIR.mkdir(exist_ok=True)
    results = {}
    for path in sorted(SQL_DIR.glob("*.sql")):
        if path.name in ("01_schema.sql", "02_views.sql"):
            continue
        df = pd.read_sql_query(path.read_text(encoding="utf-8"), con)
        name = path.stem
        df.to_csv(RESULTS_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")
        results[name] = df
        print(f"\n=== {name} ===")
        print(df.to_string(index=False))
    return results


def main() -> int:
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    build_database(con)
    results = run_queries(con)
    con.close()

    # az adatminőségi ellenőrzéseken nem lehet hiba
    errors = results["03_data_quality"]["hibas_sorok"].sum()
    if errors:
        print(f"\nFIGYELEM: {errors} adatminőségi hiba!")
        return 1
    print("\nAdatminőség: minden ellenőrzés rendben (0 hiba).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
