"""
Step 2: Engagement Classification
Project: Customer Engagement & Product Utilization Analytics for Retention Strategy

Creates 4 mutually exclusive engagement profiles:
  1. Inactive High-Balance   -> IsActiveMember=0 AND Balance >= 75th percentile
  2. Active Engaged          -> IsActiveMember=1 AND NumOfProducts >= 2
  3. Active Low-Product      -> IsActiveMember=1 AND NumOfProducts == 1
  4. Inactive Disengaged     -> IsActiveMember=0 AND Balance below threshold
     (Inactive High-Balance is checked first so premium at-risk customers
      are not buried inside the general "Inactive Disengaged" bucket.)
"""

import pandas as pd

# ---- Load dataset ----
df = pd.read_csv('European_Bank.csv')

# ---- Define high-balance threshold (top quartile of Balance) ----
high_balance_threshold = df['Balance'].quantile(0.75)
print("High-balance threshold (75th pct):", round(high_balance_threshold, 2))


def classify(row):
    if row['IsActiveMember'] == 0 and row['Balance'] >= high_balance_threshold:
        return 'Inactive High-Balance'
    elif row['IsActiveMember'] == 1 and row['NumOfProducts'] >= 2:
        return 'Active Engaged'
    elif row['IsActiveMember'] == 1 and row['NumOfProducts'] == 1:
        return 'Active Low-Product'
    else:  # IsActiveMember == 0 and Balance < threshold
        return 'Inactive Disengaged'


df['EngagementProfile'] = df.apply(classify, axis=1)

# ---- Segment counts ----
print("\n=== Segment Counts ===")
print(df['EngagementProfile'].value_counts())

print("\n=== Segment Counts (%) ===")
print((df['EngagementProfile'].value_counts(normalize=True) * 100).round(2))

# ---- Churn rate by segment ----
print("\n=== Churn Rate by Segment ===")
churn_by_segment = (
    df.groupby('EngagementProfile')['Exited']
    .mean().mul(100).round(2).sort_values(ascending=False)
)
print(churn_by_segment)

# ---- Profile characteristics ----
print("\n=== Avg Balance / Products / Salary by Segment ===")
print(df.groupby('EngagementProfile')[['Balance', 'NumOfProducts', 'EstimatedSalary']].mean().round(2))

# ---- Export full profiled dataset ----
df.to_csv('step2_engagement_profiles.csv', index=False)

# ---- Export summary table ----
summary = df.groupby('EngagementProfile').agg(
    CustomerCount=('CustomerId', 'count'),
    ChurnRatePct=('Exited', lambda x: round(x.mean() * 100, 2)),
    AvgBalance=('Balance', lambda x: round(x.mean(), 2)),
    AvgProducts=('NumOfProducts', lambda x: round(x.mean(), 2)),
    AvgSalary=('EstimatedSalary', lambda x: round(x.mean(), 2))
).reset_index().sort_values('ChurnRatePct', ascending=False)

summary.to_csv('step2_engagement_summary.csv', index=False)

print("\n=== SUMMARY TABLE ===")
print(summary.to_string(index=False))
