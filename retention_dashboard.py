"""
Customer Engagement & Product Utilization Analytics for Retention Strategy
Streamlit Dashboard

Run with:
    pip install streamlit pandas plotly
    streamlit run retention_dashboard.py

'European_Bank.csv' must be pushed into the same repo/folder as this script
(no in-app upload option — the data source is fixed to the bundled file).
"""

from pathlib import Path

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
# CUSTOM STYLING
# ============================================================
st.markdown("""
<style>
    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {
        background-color: #0F1B2D;
    }
    section[data-testid="stSidebar"] * {
        color: #E8ECF1 !important;
    }
    section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
        background-color: #2E75B6 !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: #2C3E54;
        margin: 0.6rem 0 1rem 0;
    }

    /* Filter section labels */
    .filter-section-label {
        text-transform: uppercase;
        font-size: 0.72rem;
        letter-spacing: 0.08em;
        font-weight: 700;
        color: #7FA8D9 !important;
        margin-top: 0.4rem;
        margin-bottom: 0.2rem;
    }
    .sidebar-brand {
        font-size: 1.35rem;
        font-weight: 800;
        color: #FFFFFF !important;
        margin-bottom: 0;
    }
    .sidebar-subbrand {
        font-size: 0.78rem;
        color: #7FA8D9 !important;
        margin-bottom: 1rem;
    }
    .filter-count-badge {
        background-color: #1B2A3F;
        border: 1px solid #2C3E54;
        border-radius: 8px;
        padding: 10px 14px;
        margin-top: 0.8rem;
        text-align: center;
        font-size: 0.88rem;
    }
    .filter-count-badge b {
        color: #4FD1C5 !important;
        font-size: 1.05rem;
    }

    /* ---- Main area ---- */
    div[data-testid="stMetric"] {
        background-color: #F5F7FA;
        border: 1px solid #E3E8EF;
        border-radius: 10px;
        padding: 14px 16px 10px 16px;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.82rem;
        color: #5B6B82;
    }
    button[data-baseweb="tab"] {
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# DATA LOADING
# ============================================================
@st.cache_data
def load_data(file):
    return pd.read_csv(file)


def find_bank_csv():
    """
    Look for the bank CSV next to this script AND in the current working
    directory (Streamlit Cloud's cwd is not always the repo root), matching
    the filename case-insensitively so 'european_bank.csv' vs
    'European_Bank.csv' on a case-sensitive Linux host still resolves.
    Falls back to the first .csv file found in the repo if no exact-ish
    name match exists.
    """
    search_dirs = [Path(__file__).resolve().parent, Path.cwd()]
    candidates = []
    for d in search_dirs:
        if d.exists():
            candidates.extend(d.rglob("*.csv"))

    # de-duplicate while preserving order
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c.resolve() not in seen:
            seen.add(c.resolve())
            unique_candidates.append(c)

    for c in unique_candidates:
        name = c.name.lower()
        if "european" in name and "bank" in name:
            return c

    return unique_candidates[0] if unique_candidates else None


st.sidebar.markdown('<p class="sidebar-brand">📊 Retention Dashboard</p>', unsafe_allow_html=True)
st.sidebar.markdown('<p class="sidebar-subbrand">Customer Engagement & Product Utilization Analytics</p>', unsafe_allow_html=True)

auto_path = find_bank_csv()
if auto_path is not None:
    df = load_data(auto_path)
else:
    st.error(
        "Couldn't find the bank CSV in this repo. Push 'European_Bank.csv' "
        "into the same folder as this script and redeploy."
    )
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
st.sidebar.markdown("---")
st.sidebar.markdown('<p class="filter-section-label">🎯 Engagement</p>', unsafe_allow_html=True)
activity_filter = st.sidebar.selectbox(
    "Activity status",
    options=["All", "Active", "Inactive"],
    index=0,
    placeholder="Choose an option",
    label_visibility="collapsed"
)

st.sidebar.markdown('<p class="filter-section-label">📦 Product Holdings</p>', unsafe_allow_html=True)
product_range = st.sidebar.slider(
    "Number of products",
    min_value=int(df['NumOfProducts'].min()),
    max_value=int(df['NumOfProducts'].max()),
    value=(int(df['NumOfProducts'].min()), int(df['NumOfProducts'].max())),
    label_visibility="collapsed"
)
st.sidebar.caption(f"Products held: **{product_range[0]} – {product_range[1]}**")

st.sidebar.markdown('<p class="filter-section-label">💰 Financial Profile</p>', unsafe_allow_html=True)
balance_range = st.sidebar.slider(
    "Balance range",
    min_value=float(df['Balance'].min()),
    max_value=float(df['Balance'].max()),
    value=(float(df['Balance'].min()), float(df['Balance'].max())),
    step=1000.0,
    label_visibility="collapsed"
)
st.sidebar.caption(f"Balance: **${balance_range[0]:,.0f} – ${balance_range[1]:,.0f}**")

salary_range = st.sidebar.slider(
    "Estimated salary range",
    min_value=float(df['EstimatedSalary'].min()),
    max_value=float(df['EstimatedSalary'].max()),
    value=(float(df['EstimatedSalary'].min()), float(df['EstimatedSalary'].max())),
    step=1000.0,
    label_visibility="collapsed"
)
st.sidebar.caption(f"Salary: **${salary_range[0]:,.0f} – ${salary_range[1]:,.0f}**")

st.sidebar.markdown('<p class="filter-section-label">🌍 Region</p>', unsafe_allow_html=True)
geo_filter = st.sidebar.selectbox(
    "Geography",
    options=["All"] + sorted(df['Geography'].unique()),
    index=0,
    placeholder="Choose an option",
    label_visibility="collapsed"
)

# ---- Apply filters ----
active_vals = [0, 1] if activity_filter == "All" else [{"Active": 1, "Inactive": 0}[activity_filter]]
geo_vals = df['Geography'].unique().tolist() if geo_filter == "All" else [geo_filter]

fdf = df[
    (df['IsActiveMember'].isin(active_vals)) &
    (df['NumOfProducts'].between(product_range[0], product_range[1])) &
    (df['Balance'].between(balance_range[0], balance_range[1])) &
    (df['EstimatedSalary'].between(salary_range[0], salary_range[1])) &
    (df['Geography'].isin(geo_vals))
]

st.sidebar.markdown(
    f'<div class="filter-count-badge">Showing <b>{len(fdf):,}</b> of {len(df):,} customers</div>',
    unsafe_allow_html=True
)

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
