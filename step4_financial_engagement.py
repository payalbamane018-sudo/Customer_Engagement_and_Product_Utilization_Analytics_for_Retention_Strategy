"""
Step 4: Financial Commitment vs Engagement Analysis
Project: Customer Engagement & Product Utilization Analytics for Retention Strategy
"""

import pandas as pd

# ---- Load dataset ----
df = pd.read_csv('European_Bank.csv')

# ============================================================
# 1. BALANCE vs ACTIVITY CROSS-ANALYSIS
# ============================================================
# Balance has a large zero-balance cluster (~36% of customers), so tiers
# are built off NON-ZERO balances to avoid distorted quartiles.
nonzero = df[df['Balance'] > 0]['Balance']
p50 = nonzero.quantile(0.50)
p75 = nonzero.quantile(0.75)


def balance_tier(bal):
    if bal == 0:
        return 'Zero Balance'
    elif bal <= p50:
        return 'Low Balance'
    elif bal <= p75:
        return 'Medium Balance'
    else:
        return 'High Balance'


df['BalanceTier'] = df['Balance'].apply(balance_tier)
tier_order = ['Zero Balance', 'Low Balance', 'Medium Balance', 'High Balance']

cross = df.groupby(['BalanceTier', 'IsActiveMember']).agg(
    CustomerCount=('CustomerId', 'count'),
    ChurnRatePct=('Exited', lambda x: round(x.mean() * 100, 2)),
    AvgSalary=('EstimatedSalary', lambda x: round(x.mean(), 2))
).reset_index()
cross['BalanceTier'] = pd.Categorical(cross['BalanceTier'], categories=tier_order, ordered=True)
cross = cross.sort_values(['BalanceTier', 'IsActiveMember'])
print("=== Balance Tier x Activity Status ===")
print(cross.to_string(index=False))

# ============================================================
# 2. SALARY-BALANCE MISMATCH DETECTION
# ============================================================
balance_rank_map = {'Zero Balance': 0, 'Low Balance': 1, 'Medium Balance': 2, 'High Balance': 3}
df['BalanceRank'] = df['BalanceTier'].map(balance_rank_map)
df['SalaryRank'] = pd.qcut(df['EstimatedSalary'], 4, labels=[0, 1, 2, 3]).astype(int)

df['MismatchScore'] = df['SalaryRank'] - df['BalanceRank']


def mismatch_label(score):
    if score >= 2:
        return 'High Salary / Low Balance (Wallet-Share Risk)'
    elif score <= -2:
        return 'High Balance / Low Salary (Unusual Profile)'
    else:
        return 'Aligned'


df['MismatchFlag'] = df['MismatchScore'].apply(mismatch_label)

mismatch_summary = df.groupby('MismatchFlag').agg(
    CustomerCount=('CustomerId', 'count'),
    ChurnRatePct=('Exited', lambda x: round(x.mean() * 100, 2)),
    AvgBalance=('Balance', lambda x: round(x.mean(), 2)),
    AvgSalary=('EstimatedSalary', lambda x: round(x.mean(), 2))
).reset_index().sort_values('ChurnRatePct', ascending=False)
print("\n=== Salary-Balance Mismatch Summary ===")
print(mismatch_summary.to_string(index=False))

# ============================================================
# 3. AT-RISK PREMIUM CUSTOMERS
# ============================================================
# Premium = top-quartile salary AND High Balance tier
df['IsPremium'] = (df['SalaryRank'] == 3) & (df['BalanceTier'] == 'High Balance')
df['AtRiskPremium'] = df['IsPremium'] & (df['IsActiveMember'] == 0)

print(f"\nTotal Premium customers (top-quartile salary + high balance): {df['IsPremium'].sum()}")
print(f"At-Risk Premium (Premium + Inactive): {df['AtRiskPremium'].sum()}")

atrisk_churn = df[df['AtRiskPremium']]['Exited'].mean() * 100
premium_active_churn = df[(df['IsPremium']) & (df['IsActiveMember'] == 1)]['Exited'].mean() * 100
print(f"Churn rate - At-Risk Premium (inactive): {round(atrisk_churn, 2)}%")
print(f"Churn rate - Premium but Active: {round(premium_active_churn, 2)}%")

# Actionable target list: at-risk premium customers who HAVEN'T churned yet
target_list = df[(df['AtRiskPremium']) & (df['Exited'] == 0)][
    ['CustomerId', 'Surname', 'Geography', 'Age', 'Balance', 'EstimatedSalary',
     'NumOfProducts', 'HasCrCard', 'IsActiveMember']
].sort_values('Balance', ascending=False)
print(f"\nActionable target list (at-risk premium, still retained): {len(target_list)} customers")

# ---- Exports ----
cross.to_csv('step4_balance_activity_crosstab.csv', index=False)
mismatch_summary.to_csv('step4_salary_balance_mismatch.csv', index=False)
target_list.to_csv('step4_atrisk_premium_targets.csv', index=False)
df[['CustomerId', 'BalanceTier', 'SalaryRank', 'MismatchFlag', 'IsPremium', 'AtRiskPremium']].to_csv(
    'step4_full_flags.csv', index=False)
