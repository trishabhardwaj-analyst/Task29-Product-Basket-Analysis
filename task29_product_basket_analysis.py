"""
Task 29 — Product Basket Analysis
Veda Technology | Data Analytics Track

Primary dataset: UCI Online Retail II
Source: https://archive.ics.uci.edu/dataset/502/online+retail+ii

The script:
1. Loads Online Retail II from Excel.
2. Normalizes column names.
3. Removes cancelled/returned transactions and invalid quantities.
4. Uses Invoice/Order ID as the basket identifier.
5. De-duplicates products within each order.
6. Generates unordered product pairs (no self-pairs, no A+B / B+A duplication).
7. Calculates pair count and support.
8. Produces recommendation text.
9. Saves CSV outputs and PNG charts.

Usage:
    pip install -r requirements.txt
    python task29_product_basket_analysis.py

Put online_retail_II.xlsx in data/ or change DATA_FILE below.
If the file is absent, the script prints the UCI source and exits cleanly.
"""

from pathlib import Path
from itertools import combinations
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("data/online_retail_II.xlsx")
OUTPUT_DIR = Path("outputs")
TOP_N = 50
MIN_PAIR_COUNT = 5


def load_online_retail(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}\n"
            "Download Online Retail II from UCI:\n"
            "https://archive.ics.uci.edu/dataset/502/online+retail+ii"
        )

    # Online Retail II is commonly distributed as two Excel sheets.
    xls = pd.ExcelFile(path)
    frames = []
    for sheet in xls.sheet_names:
        part = pd.read_excel(path, sheet_name=sheet)
        frames.append(part)

    df = pd.concat(frames, ignore_index=True)
    return df


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for c in df.columns:
        key = str(c).strip().lower().replace("_", " ").replace("-", " ")
        key = " ".join(key.split())
        if key in {"invoiceno", "invoice", "invoice no", "order id", "orderid"}:
            rename[c] = "Invoice"
        elif key in {"stockcode", "stock code", "product code"}:
            rename[c] = "StockCode"
        elif key in {"description", "product", "product name"}:
            rename[c] = "Description"
        elif key == "quantity":
            rename[c] = "Quantity"
        elif key in {"invoicedate", "invoice date", "order date"}:
            rename[c] = "InvoiceDate"
        elif key in {"price", "unitprice", "unit price"}:
            rename[c] = "Price"
        elif key in {"customer id", "customerid", "customer"}:
            rename[c] = "CustomerID"
        elif key == "country":
            rename[c] = "Country"
    return df.rename(columns=rename)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    required = ["Invoice", "StockCode", "Description", "Quantity"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    out = df.copy()
    out["Invoice"] = out["Invoice"].astype(str).str.strip()
    out["StockCode"] = out["StockCode"].astype(str).str.strip()
    out["Description"] = (
        out["Description"].astype(str).str.strip().str.upper().str.replace(r"\s+", " ", regex=True)
    )
    out["Quantity"] = pd.to_numeric(out["Quantity"], errors="coerce")

    # Remove cancelled/credit invoices and non-positive quantities.
    out = out[out["Invoice"].notna()]
    out = out[~out["Invoice"].str.upper().str.startswith("C")]
    out = out[out["Quantity"] > 0]
    out = out[out["Description"].notna()]
    out = out[out["StockCode"].notna()]
    return out


def make_pair_table(df: pd.DataFrame) -> pd.DataFrame:
    # One product occurrence per invoice is enough for basket analysis.
    basket_rows = (
        df[["Invoice", "StockCode", "Description"]]
        .drop_duplicates(["Invoice", "StockCode"])
        .sort_values(["Invoice", "StockCode"])
    )

    label_map = (
        basket_rows.groupby("StockCode")["Description"]
        .agg(lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0])
        .to_dict()
    )

    pair_counter = Counter()
    invoice_count = basket_rows["Invoice"].nunique()

    for _, group in basket_rows.groupby("Invoice", sort=False):
        items = sorted(set(group["StockCode"]))
        if len(items) < 2:
            continue
        pair_counter.update(combinations(items, 2))

    rows = []
    for (a, b), count in pair_counter.items():
        if count < MIN_PAIR_COUNT:
            continue
        rows.append({
            "Product_A_Code": a,
            "Product_B_Code": b,
            "Product_A": label_map.get(a, a),
            "Product_B": label_map.get(b, b),
            "Pair_Count": count,
            "Support": count / invoice_count if invoice_count else 0,
            "Recommendation": (
                f"Customers who buy {label_map.get(a, a)} often also buy "
                f"{label_map.get(b, b)}. Consider cross-selling or bundling them."
            ),
        })

    result = pd.DataFrame(rows)
    if result.empty:
        return result

    return result.sort_values(
        ["Pair_Count", "Support"], ascending=[False, False]
    ).reset_index(drop=True)


def save_outputs(df, pairs):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df.head(100).to_csv(OUTPUT_DIR / "cleaned_transaction_sample.csv", index=False)
    pairs.head(TOP_N).to_csv(OUTPUT_DIR / "top_product_pairs.csv", index=False)

    product_freq = (
        df.drop_duplicates(["Invoice", "StockCode"])
          .groupby("Description")
          .size()
          .sort_values(ascending=False)
          .head(20)
          .reset_index(name="Invoice_Count")
    )
    product_freq.to_csv(OUTPUT_DIR / "top_products.csv", index=False)

    # Chart: top products
    plot_df = product_freq.head(10).sort_values("Invoice_Count")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(plot_df["Description"], plot_df["Invoice_Count"])
    ax.set_title("Top Products by Number of Invoices")
    ax.set_xlabel("Number of invoices")
    ax.set_ylabel("Product")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "top_products.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    # Chart: top pairs
    if not pairs.empty:
        plot_pairs = pairs.head(10).sort_values("Pair_Count")
        labels = [
            f"{a} + {b}" for a, b in
            zip(plot_pairs["Product_A"], plot_pairs["Product_B"])
        ]
        fig, ax = plt.subplots(figsize=(11, 6))
        ax.barh(labels, plot_pairs["Pair_Count"])
        ax.set_title("Top Product Pairs by Co-occurrence")
        ax.set_xlabel("Orders containing both products")
        ax.set_ylabel("Product pair")
        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / "top_product_pairs.png", dpi=180, bbox_inches="tight")
        plt.close(fig)


def main():
    raw = load_online_retail(DATA_FILE)
    clean = clean_data(raw)
    pairs = make_pair_table(clean)
    save_outputs(clean, pairs)

    print("Task 29 completed.")
    print(f"Raw rows: {len(raw):,}")
    print(f"Clean rows: {len(clean):,}")
    print(f"Unique invoices: {clean['Invoice'].nunique():,}")
    print(f"Unique products: {clean['StockCode'].nunique():,}")
    print(f"Pair rows retained: {len(pairs):,}")
    print("\\nTop product pairs:")
    print(pairs.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
