# Task 29 — Product Basket Analysis

## Veda Technology — Data Analytics Internship

### Objective

Find products that are frequently purchased together using association-style analysis.

---

## Dataset

Online Retail II dataset from the UCI Machine Learning Repository.

Dataset:
https://archive.ics.uci.edu/dataset/502/online+retail+ii

The dataset contains transactional records from a UK-based online retailer.

---

## Tools Used

- Python
- Pandas
- Matplotlib
- OpenPyXL

---

## Methodology

1. Load the Online Retail II dataset.
2. Combine the available Excel sheets.
3. Clean transaction data.
4. Remove cancelled invoices.
5. Remove invalid quantities.
6. Use Invoice ID as the basket identifier.
7. Group products by invoice.
8. Remove duplicate products within an invoice.
9. Generate unique product pairs.
10. Exclude self-pairs.
11. Count pair co-occurrences.
12. Calculate support.
13. Sort product pairs by frequency.
14. Generate cross-selling recommendations.

---

## Market Basket Analysis

Market Basket Analysis identifies products that are frequently purchased together.

For example:

Customer purchases:

```text
Product A
Product B
Product C
