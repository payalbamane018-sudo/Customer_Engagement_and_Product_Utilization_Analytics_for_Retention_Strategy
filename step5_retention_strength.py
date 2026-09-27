"""
Step 5: Retention Strength Assessment
Project: Customer Engagement & Product Utilization Analytics for Retention Strategy
"""

import pandas as pd

# ---- Load dataset ----
df = pd.read_csv('European_Bank.csv')

# ============================================================
# 1. RELATIONSHIP STRENGTH INDEX (RSI) -> "STICKY CUSTOMER" PROFILES
# ============================================================
# Component scores. Informed by Step 3 finding: 2 products is the retention
# sweet spot; 3+ products is a distress signal, NOT a bonus, so it is
# scored the same as 1 product rather than rewarded further.
def product_score(n):
    if n == 1:
        return 1
    elif n == 2:
        return 3
    else:
        return 0  # 3+ products: red flag, not rewarded


df['ActivityScore'] = df['IsActiveMember'] * 2                    # 0 or 2
df['ProductScore'] = df['NumOfProducts'].apply(product_score)      # 0, 1, or 3
df['CardScore'] = df['HasCrCard'] * 1                               # 0 or 1

df['RSI'] = df['ActivityScore'] + df['ProductScore'] + df['CardScore']  # range 0-6

print("=== Churn Rate by Raw RSI Score (0-6) ===")
rsi_raw = df.groupby('RSI').agg(
    CustomerCount=('CustomerId', 'count'),
    ChurnRatePct=('Exited', lambda x: round(x.mean() * 100, 2))
).reset_index()
print(rsi_raw.to_string(index=False))

# ---- Bucket into Sticky / Moderate / At-Risk tiers ----
def rsi_tier(score):
    if score >= 4:
        return 'Sticky Customer'
    elif score >= 2:
        return 'Moderate Relationship'
    else:
        return 'At-Risk Customer'


df['RSITier'] = df['RSI'].apply(rsi_tier)
tier_order = ['At-Risk Customer', 'Moderate Relationship', 'Sticky Customer']

tier_summary = df.groupby('RSITier').agg(
    CustomerCount=('CustomerId', 'count'),
    ChurnRatePct=('Exited', lambda x: round(x.mean() * 100, 2)),
    AvgBalance=('Balance', lambda x: round(x.mean(), 2)),
    AvgTenure=('Tenure', lambda x: round(x.mean(), 2))
).reset_index()
tier_summary['RSITier'] = pd.Categorical(tier_summary['RSITier'], categories=tier_order, ordered=True)
tier_summary = tier_summary.sort_values('RSITier')
print("\n=== RSI Tier Summary ===")
print(tier_summary.to_string(index=False))

# ============================================================
# 2. CHURN STABILITY ACROSS ENGAGEMENT TIERS
# ============================================================
# Does each tier's churn rate hold steady across Geography, Gender, Age?
df['AgeBand'] = pd.cut(df['Age'], bins=[17, 30, 40, 50, 60, 100],
                        labels=['18-30', '31-40', '41-50', '51-60', '60+'])

print("\n=== Stability Check: RSI Tier x Geography ===")
stab_geo = df.groupby(['RSITier', 'Geography'])['Exited'].mean().mul(100).round(2).unstack()
stab_geo = stab_geo.reindex(tier_order)
print(stab_geo)
print("\nRange (max-min churn %) across Geography, by tier:")
print((stab_geo.max(axis=1) - stab_geo.min(axis=1)).round(2))

print("\n=== Stability Check: RSI Tier x Gender ===")
stab_gender = df.groupby(['RSITier', 'Gender'])['Exited'].mean().mul(100).round(2).unstack()
stab_gender = stab_gender.reindex(tier_order)
print(stab_gender)

print("\n=== Stability Check: RSI Tier x Age Band ===")
stab_age = df.groupby(['RSITier', 'AgeBand'], observed=True)['Exited'].mean().mul(100).round(2).unstack()
stab_age = stab_age.reindex(tier_order)
print(stab_age)
print("\nRange (max-min churn %) across Age Band, by tier:")
print((stab_age.max(axis=1) - stab_age.min(axis=1)).round(2))

# ============================================================
# 3. ENGAGEMENT THRESHOLDS LINKED TO RETENTION
# ============================================================
print("\n=== Threshold Detection (target: churn < 15%) ===")
threshold_table = rsi_raw.copy()
threshold_table['MeetsRetentionTarget(<15%)'] = threshold_table['ChurnRatePct'] < 15
print(threshold_table.to_string(index=False))

below_15 = threshold_table[threshold_table['ChurnRatePct'] < 15]['RSI'].tolist()
print(f"\nRSI scores with churn < 15%: {below_15}")
print("-> RSI >= 4 is the retention threshold (Sticky Customer tier).")

# ---- Exports ----
rsi_raw.to_csv('step5_rsi_by_score.csv', index=False)
tier_summary.to_csv('step5_rsi_tier_summary.csv', index=False)
stab_geo.to_csv('step5_stability_by_geography.csv')
stab_gender.to_csv('step5_stability_by_gender.csv')
stab_age.to_csv('step5_stability_by_ageband.csv')
df[['CustomerId', 'ActivityScore', 'ProductScore', 'CardScore', 'RSI', 'RSITier']].to_csv(
    'step5_customer_rsi_scores.csv', index=False)
