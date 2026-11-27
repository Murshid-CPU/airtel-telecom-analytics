# Airtel Telecom Analytics - Domain B: Revenue
# Save as: dashboard/app.py
# Run from project root: python -m streamlit run dashboard/app.py

from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import linregress

st.set_page_config(
    page_title="Airtel Telecom Analytics | Revenue",
    page_icon="📶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- Theme -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {font-family: Inter, sans-serif;}
.stApp {background:#f4f8fc;}
[data-testid="stSidebar"] {background:#fff;border-right:1px solid #dce7f2;}
.top-banner {
  background:linear-gradient(105deg,#eaf5ff,#d7edff);
  border:1px solid #c4e1f7;border-radius:18px;padding:17px 22px;
  text-align:center;margin-bottom:10px;
}
.top-banner h1 {color:#102f52;font-size:27px;font-weight:800;margin:0;}
.top-banner p {color:#58718a;margin:5px 0 0;font-size:13px;}
.airtel-word {color:#e32636;font-size:29px;font-weight:800;letter-spacing:-1px;}
.section-title {font-size:19px;font-weight:750;color:#173b65;margin:8px 0 12px;}
.metric-card {
  background:white;border:1px solid #d5e5f2;border-radius:15px;
  padding:15px 17px;min-height:112px;box-shadow:0 2px 8px #16466b0b;
}
.metric-label {font-size:12px;color:#58718a;font-weight:700;text-transform:uppercase;}
.metric-value {font-size:27px;color:#102f52;font-weight:800;margin-top:7px;}
.metric-help {font-size:11px;color:#71869b;margin-top:2px;}
.info-strip {
  background:#eaf5ff;border:1px solid #cde5f8;border-radius:12px;
  color:#294b69;padding:11px 15px;text-align:center;margin:7px 0 15px;
}
div[data-testid="stPlotlyChart"] {
  background:white;border:1px solid #d8e6f1;border-radius:14px;padding:7px;
}
.small-muted {font-size:11px;color:#72869a;}
</style>
""", unsafe_allow_html=True)

BLUE = "#1687cf"
DARK_BLUE = "#075b9a"
LIGHT_BLUE = "#75c8f2"
PALETTE = [DARK_BLUE, BLUE, LIGHT_BLUE, "#8ab6d8", "#c2e2f5", "#e32636"]

# ----------------------------- Load data -----------------------------
@st.cache_data(show_spinner="Loading Airtel datasets...")
def load_data():
    # This file is dashboard/app.py; datasets are in ../data/raw/
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data" / "raw"

    required = ["recharges.csv", "customers.csv", "plans.csv", "circles.csv"]
    missing = [f for f in required if not (data_dir / f).exists()]
    if missing:
        raise FileNotFoundError(
            "Missing dataset(s): " + ", ".join(missing) +
            f". Expected folder: {data_dir}"
        )

    recharges = pd.read_csv(data_dir / "recharges.csv", parse_dates=["recharge_date"])
    customers = pd.read_csv(
        data_dir / "customers.csv",
        parse_dates=["activation_date", "churn_date"]
    )
    plans = pd.read_csv(data_dir / "plans.csv")
    circles = pd.read_csv(data_dir / "circles.csv")

    # Add customer connection, circle and region details to every transaction.
    tx = recharges.merge(
        customers[[
            "customer_id", "connection_type", "circle_id", "arpu_inr",
            "is_churned", "activation_date"
        ]],
        on="customer_id", how="left"
    )
    tx = tx.merge(circles[["circle_id", "circle_name", "region"]], on="circle_id", how="left")
    tx = tx.merge(
        plans[["plan_id", "plan_name", "plan_type", "price_inr", "is_5g"]],
        on="plan_id", how="left", suffixes=("", "_plan")
    )
    tx["recharge_date"] = pd.to_datetime(tx["recharge_date"], errors="coerce")
    tx["amount_inr"] = pd.to_numeric(tx["amount_inr"], errors="coerce").fillna(0)
    tx["month"] = tx["recharge_date"].dt.to_period("M").dt.to_timestamp()
    tx["month_label"] = tx["month"].dt.strftime("%b %Y")
    customers["arpu_inr"] = pd.to_numeric(customers["arpu_inr"], errors="coerce")
    return tx, customers, plans, circles

try:
    tx_all, customers_all, plans, circles = load_data()
except Exception as exc:
    st.error("Unable to load the Airtel datasets.")
    st.code(str(exc))
    st.info(
        "Expected structure: project-root/data/raw/recharges.csv, "
        "customers.csv, plans.csv and circles.csv. Save this script as dashboard/app.py."
    )
    st.stop()

# ----------------------------- Helpers -----------------------------
def money_inr(value):
    value = float(value or 0)
    if abs(value) >= 10_000_000:
        return f"₹{value / 10_000_000:,.2f} Cr"
    if abs(value) >= 100_000:
        return f"₹{value / 100_000:,.2f} L"
    return f"₹{value:,.0f}"

def metric_card(label, value, note):
    st.markdown(
        f"""<div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-help">{note}</div>
        </div>""",
        unsafe_allow_html=True
    )

def chart_style(fig, height=320):
    fig.update_layout(
        height=height,
        margin=dict(l=12, r=12, t=52, b=12),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter, sans-serif", color="#29445e", size=11),
        title=dict(x=0.02, xanchor="left", font=dict(size=15, color="#173b65")),
        legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"),
    )
    fig.update_xaxes(showgrid=False, linecolor="#c3d2df")
    fig.update_yaxes(showgrid=True, gridcolor="#e8eff5", zeroline=False)
    return fig

def empty_chart_message(message="No records match the selected filters."):
    st.info(message)

# ----------------------------- Header -----------------------------
st.markdown("""
<div class="top-banner">
  <h1>📶 Airtel Telecom Analytics – Domain B: Revenue</h1>
  <p>Revenue intelligence dashboard | Actual project datasets</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------- Sidebar filters -----------------------------
with st.sidebar:
    st.markdown('<div class="airtel-word">airtel</div>', unsafe_allow_html=True)
    st.caption("TELECOM ANALYTICS")
    st.divider()
    st.subheader("Dashboard Filters")

    min_date = tx_all["recharge_date"].min().date()
    max_date = tx_all["recharge_date"].max().date()
    default_start = max(min_date, pd.Timestamp("2025-01-01").date())
    default_end = max_date

    date_range = st.date_input(
        "Recharge date range",
        value=(default_start, default_end),
        min_value=min_date,
        max_value=max_date,
    )
    connection_options = ["All"] + sorted(tx_all["connection_type"].dropna().astype(str).unique())
    selected_connection = st.selectbox("Connection Type", connection_options)

    region_options = ["All"] + sorted(tx_all["region"].dropna().astype(str).unique())
    selected_region = st.selectbox("Region", region_options)

    plan_options = ["All"] + sorted(tx_all["plan_type"].dropna().astype(str).unique())
    selected_plan_type = st.selectbox("Plan Type", plan_options)

    channel_options = ["All"] + sorted(tx_all["channel"].dropna().astype(str).unique())
    selected_channel = st.selectbox("Recharge Channel", channel_options)

    st.divider()
    st.caption("Dataset date coverage")
    st.write(f"{min_date:%d %b %Y} – {max_date:%d %b %Y}")
    if st.button("Reset filters", use_container_width=True):
        st.rerun()

if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.warning("Please select both a start date and an end date.")
    st.stop()

start_date, end_date = date_range
if start_date > end_date:
    st.error("Start date must be before end date.")
    st.stop()

# Apply selected filters to transaction-level data.
mask = tx_all["recharge_date"].dt.date.between(start_date, end_date)
if selected_connection != "All":
    mask &= tx_all["connection_type"].eq(selected_connection)
if selected_region != "All":
    mask &= tx_all["region"].eq(selected_region)
if selected_plan_type != "All":
    mask &= tx_all["plan_type"].eq(selected_plan_type)
if selected_channel != "All":
    mask &= tx_all["channel"].eq(selected_channel)

tx = tx_all.loc[mask].copy()
filtered_customer_ids = tx["customer_id"].dropna().unique()
customer_view = customers_all[customers_all["customer_id"].isin(filtered_customer_ids)].copy()

# ----------------------------- Tabs -----------------------------
overview_tab, detail_tab, data_tab = st.tabs([
    "📊  1. Overview", "🔎  2. Detail", "📁  3. Data Explorer"
])

with overview_tab:
    st.markdown(
        '<div class="info-strip">Understand received revenue, monthly patterns, plan performance and regional comparisons.</div>',
        unsafe_allow_html=True
    )
    st.markdown('<div class="section-title">Revenue at a glance</div>', unsafe_allow_html=True)

    total_revenue = tx["amount_inr"].sum()
    transaction_count = len(tx)
    unique_subscribers = tx["customer_id"].nunique()
    avg_revenue_per_txn = total_revenue / transaction_count if transaction_count else 0
    arpu = customer_view["arpu_inr"].mean() if not customer_view.empty else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        metric_card("Total Received Revenue", money_inr(total_revenue), "Sum of transaction amount")
    with k2:
        metric_card("Transactions", f"{transaction_count:,}", "Recharge and bill-payment records")
    with k3:
        metric_card("Unique Subscribers", f"{unique_subscribers:,}", "Customers with transactions in filter")
    with k4:
        metric_card("Average Customer ARPU", money_inr(arpu), "Mean customer ARPU in INR")

    st.markdown('<div class="section-title">Revenue performance</div>', unsafe_allow_html=True)
    monthly = (
        tx.groupby("month", as_index=False)
          .agg(revenue_inr=("amount_inr", "sum"), transactions=("recharge_id", "count"))
          .sort_values("month")
    )
    if not monthly.empty:
        fig = px.line(
            monthly, x="month", y="revenue_inr", markers=True,
            title="Monthly Revenue Trend",
            labels={"month": "Month", "revenue_inr": "Revenue (₹)"},
        )
        fig.update_traces(line=dict(color=BLUE, width=3), marker=dict(size=8),
                          hovertemplate="%{x|%b %Y}<br>Revenue: ₹%{y:,.0f}<extra></extra>")
        fig.update_yaxes(tickprefix="₹", tickformat=",.0f")
        st.plotly_chart(chart_style(fig, 350), use_container_width=True)

        # Linear regression p-value is calculated from the selected monthly totals.
        if len(monthly) >= 3 and monthly["revenue_inr"].nunique() > 1:
            x = np.arange(len(monthly))
            test = linregress(x, monthly["revenue_inr"].to_numpy())
            direction = "Increasing" if test.slope > 0 else "Decreasing" if test.slope < 0 else "No clear change"
            st.caption(
                f"Monthly revenue linear-trend test: p-value = {test.pvalue:.4f} | "
                f"Direction: {direction}. This is a trend test, not a causal test."
            )
        else:
            st.caption("Trend test needs at least three months with changing revenue.")
    else:
        empty_chart_message()

    left, right = st.columns(2)
    with left:
        by_plan = tx.groupby("plan_type", as_index=False)["amount_inr"].sum().sort_values("amount_inr", ascending=False)
        if not by_plan.empty:
            fig = px.bar(
                by_plan, x="plan_type", y="amount_inr", color="plan_type",
                title="Revenue by Connection Plan",
                labels={"plan_type": "Plan Type", "amount_inr": "Revenue (₹)"},
                color_discrete_sequence=[DARK_BLUE, LIGHT_BLUE, BLUE],
            )
            fig.update_traces(texttemplate="₹%{y:,.0f}", textposition="outside")
            fig.update_layout(showlegend=False)
            fig.update_yaxes(tickprefix="₹", tickformat=",.0f")
            st.plotly_chart(chart_style(fig, 330), use_container_width=True)
        else:
            empty_chart_message()

    with right:
        sub_share = (
            customer_view.groupby("connection_type")["customer_id"].nunique()
            .reset_index(name="subscribers")
        )
        if not sub_share.empty:
            fig = px.pie(
                sub_share, names="connection_type", values="subscribers",
                hole=0.58, title="Subscriber Share",
                color_discrete_sequence=[DARK_BLUE, LIGHT_BLUE, BLUE],
            )
            fig.update_traces(textinfo="percent+label")
            st.plotly_chart(chart_style(fig, 330), use_container_width=True)
        else:
            empty_chart_message()

    left, right = st.columns(2)
    with left:
        by_region = tx.groupby("region", as_index=False)["amount_inr"].sum().sort_values("amount_inr", ascending=False)
        if not by_region.empty:
            fig = px.bar(
                by_region, x="region", y="amount_inr", title="Revenue by Region",
                labels={"region": "Region", "amount_inr": "Revenue (₹)"},
                color="region", color_discrete_sequence=PALETTE,
            )
            fig.update_layout(showlegend=False)
            fig.update_yaxes(tickprefix="₹", tickformat=",.0f")
            st.plotly_chart(chart_style(fig, 320), use_container_width=True)
        else:
            empty_chart_message()

    with right:
        by_channel = tx.groupby("channel", as_index=False)["amount_inr"].sum().sort_values("amount_inr", ascending=False)
        if not by_channel.empty:
            fig = px.bar(
                by_channel, x="channel", y="amount_inr", title="Revenue by Recharge Channel",
                labels={"channel": "Channel", "amount_inr": "Revenue (₹)"},
                color_discrete_sequence=[BLUE],
            )
            fig.update_yaxes(tickprefix="₹", tickformat=",.0f")
            st.plotly_chart(chart_style(fig, 320), use_container_width=True)
        else:
            empty_chart_message()

with detail_tab:
    st.markdown(
        '<div class="info-strip">Explore plan-specific revenue, subscriber metrics and regional performance.</div>',
        unsafe_allow_html=True
    )
    plan_choices = sorted(tx["plan_type"].dropna().unique().tolist())
    detail_plan = st.selectbox(
        "Select plan type",
        ["All"] + plan_choices,
        index=0,
        key="detail_plan_selector",
    )
    detail_tx = tx.copy()
    if detail_plan != "All":
        detail_tx = detail_tx[detail_tx["plan_type"] == detail_plan]

    detail_ids = detail_tx["customer_id"].dropna().unique()
    detail_customers = customers_all[customers_all["customer_id"].isin(detail_ids)]
    detail_revenue = detail_tx["amount_inr"].sum()
    detail_subscribers = detail_tx["customer_id"].nunique()
    detail_arpu = detail_customers["arpu_inr"].mean() if not detail_customers.empty else 0

    st.markdown(f'<div class="section-title">{detail_plan} Plan Summary</div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    with a:
        metric_card("Subscribers", f"{detail_subscribers:,}", "Unique customers with transactions")
    with b:
        metric_card("Received Revenue", money_inr(detail_revenue), "Selected plan and filters")
    with c:
        metric_card("Average ARPU", money_inr(detail_arpu), "Mean customer ARPU (INR)")

    col1, col2 = st.columns([1.2, 1])
    with col1:
        plan_month = (
            detail_tx.groupby("month", as_index=False)["amount_inr"].sum()
            .sort_values("month")
        )
        if not plan_month.empty:
            fig = px.line(
                plan_month, x="month", y="amount_inr", markers=True,
                title=f"Revenue Trend – {detail_plan}",
                labels={"month": "Month", "amount_inr": "Revenue (₹)"},
            )
            fig.update_traces(line=dict(color=BLUE, width=3), marker=dict(size=8))
            fig.update_yaxes(tickprefix="₹", tickformat=",.0f")
            st.plotly_chart(chart_style(fig, 320), use_container_width=True)
        else:
            empty_chart_message()

    with col2:
        plan_region = detail_tx.groupby("circle_name", as_index=False)["amount_inr"].sum()
        plan_region = plan_region.sort_values("amount_inr", ascending=False).head(10)
        if not plan_region.empty:
            fig = px.bar(
                plan_region, x="circle_name", y="amount_inr",
                title=f"Revenue by Circle – {detail_plan}",
                labels={"circle_name": "Telecom Circle", "amount_inr": "Revenue (₹)"},
                color_discrete_sequence=[BLUE],
            )
            fig.update_xaxes(tickangle=-35)
            fig.update_yaxes(tickprefix="₹", tickformat=",.0f")
            st.plotly_chart(chart_style(fig, 320), use_container_width=True)
        else:
            empty_chart_message()

    compare = (
        tx.groupby(["month", "connection_type"], as_index=False)["amount_inr"].sum()
        .sort_values("month")
    )
    if not compare.empty:
        fig = px.bar(
            compare, x="month", y="amount_inr", color="connection_type",
            barmode="group", title="Comparison: Prepaid vs Postpaid",
            labels={"month": "Month", "amount_inr": "Revenue (₹)", "connection_type": "Connection"},
            color_discrete_map={"Prepaid": DARK_BLUE, "Postpaid": LIGHT_BLUE},
        )
        fig.update_yaxes(tickprefix="₹", tickformat=",.0f")
        st.plotly_chart(chart_style(fig, 350), use_container_width=True)
    else:
        empty_chart_message()

    plan_table = (
        detail_tx.groupby(["plan_name", "plan_type"], as_index=False)
        .agg(revenue_inr=("amount_inr", "sum"),
             transactions=("recharge_id", "count"),
             subscribers=("customer_id", "nunique"))
        .sort_values("revenue_inr", ascending=False)
    )
    st.markdown("#### Plan performance table")
    if not plan_table.empty:
        st.dataframe(
            plan_table.rename(columns={
                "plan_name": "Plan", "plan_type": "Plan Type",
                "revenue_inr": "Revenue (INR)", "transactions": "Transactions",
                "subscribers": "Unique Subscribers",
            }),
            use_container_width=True, hide_index=True
        )
    else:
        empty_chart_message()

with data_tab:
    st.markdown(
        '<div class="info-strip">Inspect the filtered transaction records and download the data used in this dashboard.</div>',
        unsafe_allow_html=True
    )
    st.markdown('<div class="section-title">Filtered dataset summary</div>', unsafe_allow_html=True)
    st.write(f"Showing **{len(tx):,}** transaction records.")
    display_cols = [
        "recharge_id", "customer_id", "recharge_date", "amount_inr",
        "plan_name", "plan_type", "connection_type", "circle_name",
        "region", "channel", "txn_type"
    ]
    available_cols = [col for col in display_cols if col in tx.columns]
    st.dataframe(
        tx[available_cols].sort_values("recharge_date", ascending=False).head(5000),
        use_container_width=True, hide_index=True
    )
    csv_data = tx[available_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download filtered transactions as CSV",
        data=csv_data,
        file_name="airtel_filtered_revenue_data.csv",
        mime="text/csv",
    )

st.markdown("---")
st.markdown(
    '<div class="small-muted">Airtel Telecom Analytics • Domain B: Revenue | '
    'Revenue is calculated as the sum of amount_inr from the selected transaction records. '
    'ARPU is the mean arpu_inr of unique customers represented in the filtered transactions. '
    'This dashboard analyses the supplied project datasets.</div>',
    unsafe_allow_html=True
)
