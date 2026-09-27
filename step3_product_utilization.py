"""
Step 3: Product Utilization Analysis
Project: Customer Engagement & Product Utilization Analytics for Retention Strategy
"""

import pandas as pd

# ---- Load dataset ----
df = pd.read_csv('European_Bank.csv')

# ---- Churn rate by number of products ----
churn_by_products = df.groupby('NumOfProducts').agg(
    CustomerCount=('CustomerId', 'count'),
    ChurnRatePct=('Exited', lambda x: round(x.mean() * 100, 2)),
    RetentionRatePct=('Exited', lambda x: round((1 - x.mean()) * 100, 2))
).reset_index()
print("=== Churn Rate by NumOfProducts ===")
print(churn_by_products.to_string(index=False))

# ---- Single-product vs multi-product retention ----
df['ProductGroup'] = df['NumOfProducts'].apply(
    lambda x: 'Single-Product (1)' if x == 1 else 'Multi-Product (2+)'
)
single_vs_multi = df.groupby('ProductGroup').agg(
    CustomerCount=('CustomerId', 'count'),
    ChurnRatePct=('Exited', lambda x: round(x.mean() * 100, 2)),
    RetentionRatePct=('Exited', lambda x: round((1 - x.mean()) * 100, 2))
).reset_index()
print("\n=== Single vs Multi-Product ===")
print(single_vs_multi.to_string(index=False))

# ---- Product depth vs churn relationship (linear correlation) ----
corr = df['NumOfProducts'].corr(df['Exited'])
print(f"\n=== Correlation: NumOfProducts vs Exited ===\n{round(corr, 4)}")
print("Note: near-zero/weak linear correlation because the relationship is")
print("NON-MONOTONIC (a 'sweet spot' at 2 products, not a straight line) --")
print("see the crosstab below.")

# ---- Product depth x engagement crosstab (explains the non-monotonic shape) ----
depth_engagement = df.groupby(['NumOfProducts', 'IsActiveMember']).agg(
    CustomerCount=('CustomerId', 'count'),
    ChurnRatePct=('Exited', lambda x: round(x.mean() * 100, 2))
).reset_index()
print("\n=== Product Depth x Active Status vs Churn ===")
print(depth_engagement.to_string(index=False))

# ---- Retention gap summary ----
single_churn = df[df['NumOfProducts'] == 1]['Exited'].mean() * 100
multi_churn = df[df['NumOfProducts'] >= 2]['Exited'].mean() * 100
print(f"\nSingle-product churn: {round(single_churn, 2)}%")
print(f"Multi-product (2+) churn: {round(multi_churn, 2)}%")
print(f"Retention gap (pp): {round(single_churn - multi_churn, 2)}")

# ---- Exports ----
churn_by_products.to_csv('step3_churn_by_products.csv', index=False)
single_vs_multi.to_csv('step3_single_vs_multi.csv', index=False)
depth_engagement.to_csv('step3_depth_engagement_crosstab.csv', index=False)
