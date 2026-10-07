"""
Diagramok készítése a README-hez a lekérdezések eredményeiből.
Előfeltétel: python src/run_analysis.py (létrehozza a results/ mappát és az adatbázist)

Futtatás:  python src/make_charts.py
Kimenet:   images/*.png
"""

import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
IMAGES = ROOT / "images"
DB_PATH = ROOT / "data" / "sales.db"

# színek: egységes, színtévesztők számára is elkülönülő paletta
SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
GRID = "#e4e3df"
BLUE = "#2a78d6"
ORANGE = "#eb6834"

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": GRID,
    "axes.labelcolor": TEXT_2,
    "xtick.color": TEXT_2,
    "ytick.color": TEXT_2,
    "text.color": TEXT,
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "axes.axisbelow": True,
})

MONTHS_HU = ["jan", "febr", "márc", "ápr", "máj", "jún",
             "júl", "aug", "szept", "okt", "nov", "dec"]


def title(ax, main: str, sub: str) -> None:
    ax.set_title(main, loc="left", fontsize=13, fontweight="bold", pad=24)
    ax.text(0, 1.02, sub, transform=ax.transAxes, color=TEXT_2, fontsize=9.5)


def monthly_trend() -> None:
    df = pd.read_csv(RESULTS / "05_monthly_trend.csv")
    df["ev"] = df["honap"].str[:4]
    df["ho"] = df["honap"].str[5:].astype(int)

    fig, ax = plt.subplots(figsize=(9, 4.6))
    for year, color in (("2024", BLUE), ("2025", ORANGE)):
        d = df[df["ev"] == year]
        ax.plot(d["ho"], d["arbevetel_mFt"], color=color, linewidth=2,
                marker="o", markersize=5, label=year)
        last = d.iloc[-1]
        ax.annotate(year, (last["ho"], last["arbevetel_mFt"]), xytext=(8, 0),
                    textcoords="offset points", va="center", color=TEXT,
                    fontweight="bold")
    sept = df[(df["ev"] == "2025") & (df["ho"] == 9)].iloc[0]
    ax.annotate(f"Szeptemberi csúcs: {sept['arbevetel_mFt']:.0f} M Ft",
                (9, sept["arbevetel_mFt"]), xytext=(-12, 0), ha="right", va="center",
                textcoords="offset points", color=TEXT_2, fontsize=9)
    ax.set_xticks(range(1, 13), MONTHS_HU)
    ax.set_xlim(0.6, 12.9)
    ax.set_ylim(0, df["arbevetel_mFt"].max() * 1.15)
    ax.set_ylabel("Nettó árbevétel (millió Ft)")
    ax.legend(frameon=False, loc="lower right", ncol=2)
    title(ax, "Havi árbevétel: 2025 vs. 2024",
          "Éves árbevétel +11,6%; erős szezonalitás: nyári mélypont, szeptemberi csúcs")
    fig.tight_layout()
    fig.savefig(IMAGES / "monthly_revenue.png", dpi=150)
    plt.close(fig)


def category_margin() -> None:
    df = pd.read_csv(RESULTS / "07_category_margin.csv").sort_values("arbevetel_mFt")

    fig, ax = plt.subplots(figsize=(9, 4.4))
    bars = ax.barh(df["kategoria"], df["arbevetel_mFt"], color=BLUE, height=0.6)
    for bar, margin in zip(bars, df["arres_szazalek"]):
        ax.text(bar.get_width() + 8, bar.get_y() + bar.get_height() / 2,
                f"{bar.get_width():.0f} M Ft  |  árrés {margin:.0f}%",
                va="center", color=TEXT, fontsize=9)
    ax.set_xlim(0, df["arbevetel_mFt"].max() * 1.45)
    ax.set_xlabel("Nettó árbevétel 2024–2025 (millió Ft)")
    ax.grid(axis="y", visible=False)
    title(ax, "Árbevétel és árrés kategóriánként",
          "A toner hozza a legtöbb bevételt, de az irodabútor a legtöbb árrést")
    fig.tight_layout()
    fig.savefig(IMAGES / "category_margin.png", dpi=150)
    plt.close(fig)


def customer_pareto() -> None:
    with sqlite3.connect(DB_PATH) as con:
        df = pd.read_sql_query(
            "SELECT customer_id, SUM(net_revenue) AS revenue "
            "FROM v_sales_lines GROUP BY customer_id ORDER BY revenue DESC", con)
    df["cum_customers"] = 100 * (df.index + 1) / len(df)
    df["cum_revenue"] = 100 * df["revenue"].cumsum() / df["revenue"].sum()

    abc = pd.read_csv(RESULTS / "06_customer_abc.csv")
    a_share = abc.loc[abc["osztaly"] == "A", "vevok_aranya_szazalek"].iloc[0]

    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.plot([0, *df["cum_customers"]], [0, *df["cum_revenue"]], color=BLUE, linewidth=2)
    ax.plot([0, 100], [0, 100], color=GRID, linewidth=1.2, linestyle="--")
    ax.axvline(a_share, color=TEXT_2, linewidth=1, linestyle=":")
    ax.axhline(80, color=TEXT_2, linewidth=1, linestyle=":")
    ax.annotate(f"A vevők {a_share:.0f}%-a adja\naz árbevétel 80%-át (A osztály)",
                (a_share, 80), xytext=(14, -48), textcoords="offset points",
                color=TEXT, fontsize=9.5)
    ax.text(62, 52, "egyenletes eloszlás", color=TEXT_2, fontsize=8.5, rotation=24)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 102)
    ax.set_xlabel("Vevők kumulált aránya, árbevétel szerint csökkenő sorrendben (%)")
    ax.set_ylabel("Árbevétel kumulált aránya (%)")
    title(ax, "Vevők ABC-elemzése (Pareto-görbe)",
          "Kis számú kulcsvevőtől függ a forgalom: őket érdemes kiemelten kezelni")
    fig.tight_layout()
    fig.savefig(IMAGES / "customer_pareto.png", dpi=150)
    plt.close(fig)


def delivery_performance() -> None:
    df = pd.read_csv(RESULTS / "09_delivery_performance.csv").sort_values(
        "hataridore_szazalek")

    fig, ax = plt.subplots(figsize=(9, 4.4))
    bars = ax.barh(df["regio"], df["hataridore_szazalek"], color=BLUE, height=0.6)
    for bar in bars:
        ax.text(bar.get_width() - 1.5, bar.get_y() + bar.get_height() / 2,
                f"{bar.get_width():.0f}%", va="center", ha="right", color="white",
                fontsize=9, fontweight="bold")
    ax.axvline(90, color=TEXT_2, linewidth=1, linestyle="--")
    ax.text(90.8, len(df) - 0.55, "90% cél", color=TEXT_2, fontsize=8.5)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Határidőre teljesített kiszállítások aránya (%)")
    ax.grid(axis="y", visible=False)
    title(ax, "Határidőre szállítás (OTD) régiónként",
          "Egyik régió sem éri el a 90%-ot; Észak-Magyarországon minden harmadik szállítás késik")
    fig.tight_layout()
    fig.savefig(IMAGES / "delivery_otd.png", dpi=150)
    plt.close(fig)


def main() -> None:
    IMAGES.mkdir(exist_ok=True)
    monthly_trend()
    category_margin()
    customer_pareto()
    delivery_performance()
    print("Diagramok elkészültek az images/ mappában.")


if __name__ == "__main__":
    main()
