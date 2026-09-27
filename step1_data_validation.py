"""
Step 1: Data Ingestion & Validation
Project: Customer Engagement & Product Utilization Analytics for Retention Strategy
"""

import pandas as pd

# ---- Load dataset ----
df = pd.read_csv('European_Bank.csv')

rows = []
rows.append(("Total Rows", len(df)))
rows.append(("Total Columns", df.shape[1]))
rows.append(("Unique CustomerId", df['CustomerId'].nunique()))
rows.append(("Duplicate CustomerId Rows", int(df['CustomerId'].duplicated().sum())))
rows.append(("Full Duplicate Rows", int(df.duplicated().sum())))
rows.append(("Total Missing Values (all columns)", int(df.isnull().sum().sum())))

# ---- Binary field validation ----
for col in ['HasCrCard', 'IsActiveMember', 'Exited']:
    vals = sorted(df[col].unique().tolist())
    counts = df[col].value_counts().to_dict()
    rows.append((f"{col} - Unique Values", str(vals)))
    rows.append((f"{col} - Count = 1", counts.get(1, 0)))
    rows.append((f"{col} - Count = 0", counts.get(0, 0)))

# ---- Product field distribution ----
for k, v in df['NumOfProducts'].value_counts().sort_index().items():
    rows.append((f"NumOfProducts = {k}", v))

# ---- Categorical distributions ----
for k, v in df['Geography'].value_counts().items():
    rows.append((f"Geography - {k}", v))

for k, v in df['Gender'].value_counts().items():
    rows.append((f"Gender - {k}", v))

# ---- Numeric field ranges ----
desc = df[['CreditScore', 'Age', 'Tenure', 'Balance', 'EstimatedSalary']].describe()
for col in desc.columns:
    for stat in desc.index:
        rows.append((f"{col} - {stat}", round(desc.loc[stat, col], 2)))

# ---- Additional checks ----
rows.append(("Customers with Balance = 0", int((df['Balance'] == 0).sum())))
rows.append(("Churn Rate (%)", round(df['Exited'].mean() * 100, 2)))
rows.append(("Active Member Rate (%)", round(df['IsActiveMember'].mean() * 100, 2)))

# ---- Build summary and export ----
summary_df = pd.DataFrame(rows, columns=["Metric", "Value"])
summary_df.to_csv('step1_validation_summary.csv', index=False)

print(summary_df.to_string(index=False))
