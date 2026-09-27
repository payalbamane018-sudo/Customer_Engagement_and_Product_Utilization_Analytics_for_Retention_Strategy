# Customer Engagement & Product Utilization Analytics for Retention Strategy

Quantitative analysis of a 10,000-customer European retail bank dataset, evaluating retention through customer **behavior and relationship depth** rather than demographics or balance alone. Includes a 5-stage analytical pipeline, a Streamlit monitoring dashboard, and formal report deliverables.

## Table of Contents
- [Background](#background)
- [Problem Statement](#problem-statement)
- [Objectives](#objectives)
- [KPI Framework](#kpi-framework)
- [Repository Structure](#repository-structure)
- [Methodology](#methodology)
- [Key Findings](#key-findings)
- [Dashboard](#dashboard)
- [Getting Started](#getting-started)
- [Reports](#reports)
- [Limitations](#limitations)
- [License](#license)

## Background

Banks increasingly recognize that customer behavior and engagement — not just demographics — determine long-term retention. Customers may appear financially strong (high balance or salary) but still churn due to low engagement, limited product adoption, or weak relationship depth with the bank. This project evaluates retention through that behavioral lens to support cross-sell strategy, loyalty programs, and engagement-driven retention initiatives.

## Problem Statement

Despite having data on customer engagement and product usage, banks often lack:
- Quantitative insight into which behaviors drive retention
- Clarity on whether product depth reduces churn
- Evidence on whether high balances alone ensure loyalty

## Objectives

**Primary**
- Evaluate the relationship between engagement and churn
- Measure retention impact of product count and product mix
- Identify disengaged yet high-value customers

**Secondary**
- Support engagement-driven retention strategies
- Improve product bundling decisions
- Reduce silent churn among premium customers

## KPI Framework

| KPI | Description |
|---|---|
| Engagement Retention Ratio | Active vs. inactive churn comparison |
| Product Depth Index | Products used vs. loyalty |
| High-Balance Disengagement Rate | Premium churn risk |
| Credit Card Stickiness Score | Card ownership retention impact |
| Relationship Strength Index (RSI) | Combined engagement & product score |

## Repository Structure

```
.
├── European_Bank.csv                          # Source dataset (10,000 customers, 14 fields)
│
├── step1_data_validation.py                   # Data ingestion & validation
├── step1_validation_summary.csv
│
├── step2_engagement_classification.py         # Engagement profile segmentation
├── step2_engagement_profiles.csv              # Full dataset + EngagementProfile column
├── step2_engagement_summary.csv
│
├── step3_product_utilization.py               # Product depth vs. churn analysis
├── step3_churn_by_products.csv
├── step3_single_vs_multi.csv
├── step3_depth_engagement_crosstab.csv
│
├── step4_financial_engagement.py              # Balance/salary vs. engagement analysis
├── step4_balance_activity_crosstab.csv
├── step4_salary_balance_mismatch.csv
├── step4_atrisk_premium_targets.csv            # Actionable outreach list
├── step4_full_flags.csv
│
├── step5_retention_strength.py                # Relationship Strength Index (RSI)
├── step5_rsi_by_score.csv
├── step5_rsi_tier_summary.csv
├── step5_stability_by_geography.csv
├── step5_stability_by_gender.csv
├── step5_stability_by_ageband.csv
├── step5_customer_rsi_scores.csv
│
├── retention_dashboard.py                     # Streamlit monitoring dashboard
├── requirements.txt
│
├── Retention_Strategy_Final_Report.docx       # Business-facing final report
├── Retention_Research_Report.docx             # Academic-style research report
│
└── README.md
```

## Methodology

1. **Data Ingestion & Validation** — completeness, duplication, and binary-field integrity checks.
2. **Engagement Classification** — 4 mutually exclusive profiles: *Inactive High-Balance*, *Inactive Disengaged*, *Active Low-Product*, *Active Engaged*.
3. **Product Utilization Analysis** — churn rate by product count; single- vs. multi-product retention; product depth vs. churn relationship.
4. **Financial Commitment vs. Engagement Analysis** — balance vs. activity cross-analysis; salary-balance mismatch detection; at-risk premium customer identification.
5. **Retention Strength Assessment** — Relationship Strength Index (RSI, 0–6) combining activity, a non-linear product score, and card ownership; stability-checked across Geography, Gender, and Age.

Each step is a standalone, runnable Python script (`pandas`) that reads `European_Bank.csv` and writes its results to CSV.

## Key Findings

- **Engagement beats wealth as a churn predictor.** Active members churn at ~14.3% vs. ~26.9% for inactive members — a pattern that holds at every balance and salary level tested.
- **Product depth is non-linear.** 2 products is a genuine retention sweet spot (7.6% churn); 3–4 products is a severe distress signal (83–100% churn), not a loyalty bonus. Correlation between raw product count and churn is nearly flat (r ≈ -0.05) precisely because the relationship is a spike, not a line.
- **The composite RSI outperforms any single variable.** RSI produces a monotonic churn gradient from 92% (score 0) to 5% (score 6), with a clean action threshold at **RSI ≥ 4** (churn < 15%).
- **Balance does not protect against disengagement.** Inactive High-Balance and At-Risk Premium segments both churn at 30%+ despite being the bank's most valuable accounts on paper. 133 at-risk premium customers are still retained and form a prioritized outreach list (`step4_atrisk_premium_targets.csv`).
- **RSI is not equally reliable everywhere.** Germany churns higher than France/Spain at every RSI tier, and churn rises with age within every tier — both need a risk overlay on top of RSI.

## Dashboard

A Streamlit app operationalizes the analysis for ongoing monitoring, with 4 modules and sidebar filters (activity status, product count, balance/salary range, geography):

1. Engagement vs. Churn Overview
2. Product Utilization Impact Analysis
3. High-Value Disengaged Customer Detector (with CSV export of the target list)
4. Retention Strength Scoring Panels

## Getting Started

```bash
# Clone the repo
git clone <your-repo-url>
cd <your-repo-name>

# Install dependencies
pip install -r requirements.txt

# Run the individual analysis steps (optional — outputs already included)
python step1_data_validation.py
python step2_engagement_classification.py
python step3_product_utilization.py
python step4_financial_engagement.py
python step5_retention_strength.py

# Launch the dashboard
streamlit run retention_dashboard.py
```

`European_Bank.csv` must be in the working directory (or uploaded via the dashboard's sidebar uploader).

## Reports

- **`Retention_Strategy_Final_Report.docx`** — business-facing report: executive summary, KPI results, findings, and strategic recommendations.
- **`Retention_Research_Report.docx`** — academic-style report: abstract, hypotheses (H1–H4), methodology, results, discussion, and limitations.

## Limitations

- Cross-sectional data (single time point) — causal direction cannot be established.
- `IsActiveMember` is a coarse binary proxy for engagement; no transaction- or login-level data was available.
- Geography- and age-related churn effects are identified but not explained by this dataset.
- No predictive model or hold-out validation was performed; this is an explanatory/diagnostic study, not a churn-prediction model.

## License

Add a license of your choice (e.g., MIT) before making this repository public, especially if `European_Bank.csv` contains data that is not yours to redistribute.
