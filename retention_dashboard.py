"""
Customer Engagement & Product Utilization Analytics for Retention Strategy
Streamlit Dashboard

Run with:
    pip install streamlit pandas plotly
    streamlit run retention_dashboard.py

Place 'European_Bank.csv' in the same folder as this script, or upload it
via the sidebar when the app starts.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Retention Strategy Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# DATA LOADING
# ============================================================
@st.cache_data
def load_data(file):
    return pd.read_csv(file)


st.sidebar.title("📊 Retention Dashboard")
uploaded = st.sidebar.file_uploader("Upload European_Bank.csv", type="csv")

if uploaded is not None:
    df = load_data(uploaded)
elif __import__("os").path.exists("European_Bank.csv"):
    df = load_data("European_Bank.csv")
else:
    st.warning("Upload 'European_Bank.csv' in the sidebar to begin.")
    st.stop()


# ============================================================
# FEATURE ENGINEERING (Steps 2 & 5 logic)
# ============================================================
@st.cache_data
def engineer_features(data):
    d = data.copy()

    # High-balance threshold (75th percentile) -> Step 2 engagement profiles
    high_balance_threshold = d['Balance'].quantile(0.75)

    def classify(row):
        if row['IsActiveMember'] == 0 and row['Balance'] >= high_balance_threshold:
            return 'Inactive High-Balance'
        elif row['IsActiveMember'] == 1 and row['NumOfProducts'] >= 2:
            return 'Active Engaged'
        elif row['IsActiveMember'] == 1 and row['NumOfProducts'] == 1:
            return 'Active Low-Product'
        else:
            return 'Inactive Disengaged'

    d['EngagementProfile'] = d.apply(classify, axis=1)

    # Relationship Strength Index -> Step 5 (2 products = sweet spot, 3+ = red flag)
    def product_score(n):
        if n == 1:
            return 1
        elif n == 2:
            return 3
        else:
            return 0

    d['ActivityScore'] = d['IsActiveMember'] * 2
    d['ProductScore'] = d['NumOfProducts'].apply(product_score)
    d['CardScore'] = d['HasCrCard'] * 1
    d['RSI'] = d['ActivityScore'] + d['ProductScore'] + d['CardScore']

    def rsi_tier(score):
        if score >= 4:
            return 'Sticky Customer'
        elif score >= 2:
            return 'Moderate Relationship'
        else:
            return 'At-Risk Customer'

    d['RSITier'] = d['RSI'].apply(rsi_tier)
    return d, high_balance_threshold


df, HIGH_BALANCE_THRESHOLD = engineer_features(df)

# ============================================================
# SIDEBAR FILTERS
# ============================================================
st.sidebar.header("Filters")

activity_filter = st.sidebar.multiselect(
    "Engagement / Activity status",
    options=["Active", "Inactive"],
    default=["Active", "Inactive"]
)

product_range = st.sidebar.slider(
    "Number of products",
    min_value=int(df['NumOfProducts'].min()),
    max_value=int(df['NumOfProducts'].max()),
    value=(int(df['NumOfProducts'].min()), int(df['NumOfProducts'].max()))
)

balance_range = st.sidebar.slider(
    "Balance range ($)",
    min_value=float(df['Balance'].min()),
    max_value=float(df['Balance'].max()),
    value=(float(df['Balance'].min()), float(df['Balance'].max())),
    step=1000.0
)

salary_range = st.sidebar.slider(
    "Estimated salary range ($)",
    min_value=float(df['EstimatedSalary'].min()),
    max_value=float(df['EstimatedSalary'].max()),
    value=(float(df['EstimatedSalary'].min()), float(df['EstimatedSalary'].max())),
    step=1000.0
)

geo_filter = st.sidebar.multiselect(
    "Geography",
    options=sorted(df['Geography'].unique()),
    default=sorted(df['Geography'].unique())
)

# ---- Apply filters ----
active_map = {"Active": 1, "Inactive": 0}
active_vals = [active_map[a] for a in activity_filter] if activity_filter else [0, 1]

fdf = df[
    (df['IsActiveMember'].isin(active_vals)) &
    (df['NumOfProducts'].between(product_range[0], product_range[1])) &
    (df['Balance'].between(balance_range[0], balance_range[1])) &
    (df['EstimatedSalary'].between(salary_range[0], salary_range[1])) &
    (df['Geography'].isin(geo_filter))
]

st.sidebar.markdown(f"**Filtered customers:** {len(fdf):,} / {len(df):,}")

if len(fdf) == 0:
    st.error("No customers match the current filter combination. Widen the filters.")
    st.stop()

# ============================================================
# HEADER / TOP-LINE KPIs
# ============================================================
st.title("Customer Engagement & Product Utilization Analytics")
st.caption("Retention Strategy Dashboard — filtered view based on sidebar selections")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Customers (filtered)", f"{len(fdf):,}")
k2.metric("Churn Rate", f"{fdf['Exited'].mean() * 100:.1f}%")
k3.metric("Active Member Rate", f"{fdf['IsActiveMember'].mean() * 100:.1f}%")
k4.metric("Avg. Products / Customer", f"{fdf['NumOfProducts'].mean():.2f}")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs([
    "🔎 Engagement vs Churn",
    "📦 Product Utilization",
    "💰 High-Value Disengaged Detector",
    "🧲 Retention Strength Scoring"
])

# ============================================================
# TAB 1: ENGAGEMENT VS CHURN OVERVIEW
# ============================================================
with tab1:
    st.subheader("Engagement vs Churn Overview")

    c1, c2 = st.columns(2)

    with c1:
        activity_churn = fdf.groupby('IsActiveMember')['Exited'].mean().mul(100).round(2)
        activity_churn.index = ['Inactive', 'Active']
        fig1 = px.bar(
            x=activity_churn.index, y=activity_churn.values,
            labels={'x': 'Activity Status', 'y': 'Churn Rate (%)'},
            title="Churn Rate: Active vs Inactive",
            color=activity_churn.index,
            color_discrete_map={'Active': '#2E7D32', 'Inactive': '#C62828'}
        )
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        profile_summary = fdf.groupby('EngagementProfile').agg(
            Customers=('CustomerId', 'count'),
            ChurnRate=('Exited', lambda x: round(x.mean() * 100, 2))
        ).reset_index().sort_values('ChurnRate', ascending=False)
        fig2 = px.bar(
            profile_summary, x='EngagementProfile', y='ChurnRate',
            text='Customers',
            title="Churn Rate by Engagement Profile",
            labels={'ChurnRate': 'Churn Rate (%)', 'EngagementProfile': ''},
            color='ChurnRate', color_continuous_scale='Reds'
        )
        fig2.update_traces(texttemplate='n=%{text}', textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**Engagement Profile Detail**")
    st.dataframe(profile_summary, use_container_width=True, hide_index=True)

# ============================================================
# TAB 2: PRODUCT UTILIZATION IMPACT ANALYSIS
# ============================================================
with tab2:
    st.subheader("Product Utilization Impact Analysis")

    c1, c2 = st.columns(2)

    with c1:
        prod_churn = fdf.groupby('NumOfProducts').agg(
            Customers=('CustomerId', 'count'),
            ChurnRate=('Exited', lambda x: round(x.mean() * 100, 2))
        ).reset_index()
        fig3 = px.bar(
            prod_churn, x='NumOfProducts', y='ChurnRate', text='Customers',
            title="Churn Rate by Number of Products",
            labels={'ChurnRate': 'Churn Rate (%)', 'NumOfProducts': 'Products Held'},
            color='ChurnRate', color_continuous_scale='RdYlGn_r'
        )
        fig3.update_traces(texttemplate='n=%{text}', textposition='outside')
        st.plotly_chart(fig3, use_container_width=True)
        st.caption("⚠️ 3–4 products is a distress signal in this dataset, not a loyalty bonus — "
                   "2 products is the retention sweet spot.")

    with c2:
        fdf_local = fdf.copy()
        fdf_local['ProductGroup'] = fdf_local['NumOfProducts'].apply(
            lambda x: 'Single-Product (1)' if x == 1 else 'Multi-Product (2+)'
        )
        svm = fdf_local.groupby('ProductGroup')['Exited'].mean().mul(100).round(2)
        fig4 = px.bar(
            x=svm.index, y=svm.values,
            labels={'x': '', 'y': 'Churn Rate (%)'},
            title="Single-Product vs Multi-Product Churn",
            color=svm.index
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("**Product Depth x Activity Status**")
    depth_activity = fdf.groupby(['NumOfProducts', 'IsActiveMember']).agg(
        Customers=('CustomerId', 'count'),
        ChurnRate=('Exited', lambda x: round(x.mean() * 100, 2))
    ).reset_index()
    depth_activity['IsActiveMember'] = depth_activity['IsActiveMember'].map({0: 'Inactive', 1: 'Active'})
    st.dataframe(depth_activity, use_container_width=True, hide_index=True)

# ============================================================
# TAB 3: HIGH-VALUE DISENGAGED CUSTOMER DETECTOR
# ============================================================
with tab3:
    st.subheader("High-Value Disengaged Customer Detector")
    st.caption("Uses the Balance / Salary sliders in the sidebar to define 'high-value', "
               "crossed with inactive status, to surface premium silent-churn risk.")

    hv1, hv2 = st.columns(2)
    with hv1:
        min_balance_hv = st.number_input(
            "Minimum balance to count as 'high-value' ($)",
            min_value=0.0, max_value=float(df['Balance'].max()),
            value=float(HIGH_BALANCE_THRESHOLD), step=1000.0
        )
    with hv2:
        min_salary_hv = st.number_input(
            "Minimum salary to count as 'high-value' ($)",
            min_value=0.0, max_value=float(df['EstimatedSalary'].max()),
            value=float(df['EstimatedSalary'].quantile(0.75)), step=1000.0
        )

    detected = fdf[
        (fdf['IsActiveMember'] == 0) &
        (fdf['Balance'] >= min_balance_hv) &
        (fdf['EstimatedSalary'] >= min_salary_hv)
    ].copy()

    d1, d2, d3 = st.columns(3)
    d1.metric("High-Value Disengaged Customers", f"{len(detected):,}")
    d2.metric("Churn Rate (this group)", f"{detected['Exited'].mean()*100:.1f}%" if len(detected) else "N/A")
    d3.metric("Not Yet Churned (target list)", f"{(detected['Exited']==0).sum():,}")

    st.markdown("**Target list — high-value, disengaged, still retained (act on these first)**")
    target_list = detected[detected['Exited'] == 0][
        ['CustomerId', 'Surname', 'Geography', 'Age', 'Balance',
         'EstimatedSalary', 'NumOfProducts', 'HasCrCard', 'RSITier']
    ].sort_values('Balance', ascending=False)

    st.dataframe(target_list, use_container_width=True, hide_index=True)

    csv_export = target_list.to_csv(index=False).encode('utf-8')
    st.download_button(
        "⬇️ Download target list as CSV",
        data=csv_export,
        file_name="high_value_disengaged_targets.csv",
        mime="text/csv"
    )

# ============================================================
# TAB 4: RETENTION STRENGTH SCORING PANELS
# ============================================================
with tab4:
    st.subheader("Retention Strength Scoring (RSI)")
    st.caption("RSI = Activity score (0/2) + Product score (1/3/0) + Card score (0/1), range 0–6.")

    c1, c2 = st.columns(2)

    with c1:
        rsi_by_score = fdf.groupby('RSI').agg(
            Customers=('CustomerId', 'count'),
            ChurnRate=('Exited', lambda x: round(x.mean() * 100, 2))
        ).reset_index()
        fig5 = px.line(
            rsi_by_score, x='RSI', y='ChurnRate', markers=True,
            title="Churn Rate by RSI Score (0-6)",
            labels={'ChurnRate': 'Churn Rate (%)', 'RSI': 'Relationship Strength Index'}
        )
        st.plotly_chart(fig5, use_container_width=True)

    with c2:
        tier_order = ['At-Risk Customer', 'Moderate Relationship', 'Sticky Customer']
        tier_summary = fdf.groupby('RSITier').agg(
            Customers=('CustomerId', 'count'),
            ChurnRate=('Exited', lambda x: round(x.mean() * 100, 2))
        ).reindex(tier_order).reset_index()
        fig6 = px.bar(
            tier_summary, x='RSITier', y='ChurnRate', text='Customers',
            title="Churn Rate by RSI Tier",
            labels={'ChurnRate': 'Churn Rate (%)', 'RSITier': ''},
            color='RSITier',
            color_discrete_map={
                'At-Risk Customer': '#C62828',
                'Moderate Relationship': '#F9A825',
                'Sticky Customer': '#2E7D32'
            }
        )
        fig6.update_traces(texttemplate='n=%{text}', textposition='outside')
        st.plotly_chart(fig6, use_container_width=True)

    st.markdown("**RSI Tier Summary Table**")
    st.dataframe(tier_summary, use_container_width=True, hide_index=True)

    st.markdown("**Stability check — churn rate by tier across Geography** "
                "(large spread = engagement score alone doesn't explain that group)")
    stab_geo = fdf.groupby(['RSITier', 'Geography'])['Exited'].mean().mul(100).round(2).unstack()
    stab_geo = stab_geo.reindex(tier_order)
    st.dataframe(stab_geo, use_container_width=True)

st.divider()
st.caption("Customer Engagement & Product Utilization Analytics for Retention Strategy — internal dashboard")
