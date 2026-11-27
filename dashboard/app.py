from __future__ import annotations

import gzip
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# AIRTEL | REVENUE INTELLIGENCE
# Compact, executive-style, single-screen Streamlit dashboard
# ============================================================

st.set_page_config(
    page_title="Airtel | Revenue Intelligence",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- Theme -----------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

    :root {
      --bg: #080d18;
      --panel: #111b2b;
      --panel-2: #152238;
      --line: rgba(173, 193, 220, .13);
      --text: #edf4ff;
      --muted: #8ea1bd;
      --red: #ff526b;
      --cyan: #55d6d2;
      --violet: #9c8cff;
      --gold: #f2c879;
    }

    html, body, [class*="css"] {
      font-family: 'DM Sans', sans-serif;
    }
    .stApp {
      background:
        radial-gradient(ellipse at 8% 0%, rgba(255,82,107,.14), transparent 29%),
        radial-gradient(ellipse at 90% 10%, rgba(85,214,210,.10), transparent 27%),
        linear-gradient(135deg, #080d18 0%, #0b1423 55%, #111326 100%);
      color: var(--text);
      height: 100vh;
      overflow: hidden;
    }
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"] {
      height: 100vh !important;
      overflow: hidden !important;
    }
    [data-testid="stMainBlockContainer"] {
      max-width: 100% !important;
      padding: .8rem 1.35rem .5rem !important;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"] { right: 1rem; }
    footer { visibility: hidden; }

    /* Sidebar */
    [data-testid="stSidebar"] {
      background: linear-gradient(180deg, #0d1728 0%, #11172a 100%);
      border-right: 1px solid var(--line);
      min-width: 245px !important;
      max-width: 245px !important;
    }
    [data-testid="stSidebar"] * { color: #e8f0ff; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
      color: var(--muted);
      font-size: 11px;
    }
    [data-testid="stSidebar"] label {
      color: #b9c9df !important;
      font-size: 10px !important;
      font-weight: 700 !important;
      letter-spacing: .7px;
      text-transform: uppercase;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
      background: #17243a !important;
      border: 1px solid rgba(173,193,220,.17) !important;
      border-radius: 10px !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] * { color: #f1f6ff !important; }
    [data-testid="stSidebar"] hr { border-color: var(--line); }

    /* Header */
    .topline {
      display:flex; align-items:center; justify-content:space-between;
      margin: 0 0 9px 0;
    }
    .brand {
      display:flex; align-items:center; gap:10px;
    }
    .brand-symbol {
      width:35px; height:35px; border-radius:11px;
      display:flex; align-items:center; justify-content:center;
      color:#fff; font-size:20px; font-weight:800;
      background:linear-gradient(145deg,#ff526b,#c9274e);
      box-shadow:0 7px 22px rgba(255,82,107,.25);
    }
    .brand-name {
      color:#fff; font-family:Manrope,sans-serif;
      font-size:21px; font-weight:800; letter-spacing:-1px;
    }
    .brand-sub {
      color:#8ea1bd; font-size:8px; letter-spacing:1.8px;
      margin-top:-2px; font-weight:700;
    }
    .header-right {
      color:#9aacc5; font-size:9px; letter-spacing:1.5px;
      text-align:right; font-weight:700;
    }
    .page-title {
      font-family:Manrope,sans-serif; font-size:20px;
      font-weight:800; color:#f3f7ff; letter-spacing:-.6px;
      margin: 2px 0 0 0;
    }
    .page-subtitle {
      color:#91a4c0; font-size:10px; margin-top:1px;
    }
    .live {
      display:inline-flex; align-items:center; gap:7px;
      border:1px solid rgba(85,214,210,.25);
      background:rgba(85,214,210,.07); color:#9ce9e3;
      border-radius:20px; padding:6px 10px;
      font-size:8px; letter-spacing:1.1px; font-weight:700;
    }
    .live-dot {
      width:6px;height:6px;border-radius:50%;background:#55d6d2;
      box-shadow:0 0 9px #55d6d2;
    }

    /* KPI tiles */
    div[data-testid="stHorizontalBlock"] { gap: .65rem; }
    .kpi {
      min-height:70px; padding:11px 14px 9px;
      border-radius:15px;
      background:linear-gradient(145deg,rgba(23,37,59,.97),rgba(15,26,43,.97));
      border:1px solid var(--line);
      border-left:2px solid var(--accent, #ff526b);
      box-shadow:0 9px 25px rgba(0,0,0,.12);
    }
    .kpi-label {
      color:#91a4c0; font-size:8px; font-weight:700;
      letter-spacing:1.2px; text-transform:uppercase;
    }
    .kpi-value {
      color:#f4f7ff; font-family:Manrope,sans-serif;
      font-size:22px; font-weight:800; letter-spacing:-.7px;
      margin-top:4px; line-height:1.1;
    }
    .kpi-note { color:#8295b1; font-size:8px; margin-top:3px; }

    /* Chart cards */
    .chart-head {
      display:flex; justify-content:space-between; align-items:center;
      margin: 7px 0 2px;
    }
    .chart-title {
      color:#eaf1ff; font-family:Manrope,sans-serif;
      font-size:11px; font-weight:800; letter-spacing:.1px;
    }
    .chart-tag {
      color:#8ea1bd; font-size:7px; letter-spacing:1px;
      border:1px solid var(--line); border-radius:20px;
      padding:3px 7px; text-transform:uppercase;
    }
    .chart-caption {
      color:#8498b5; font-size:8px; margin-bottom:0;
    }
    div[data-testid="stPlotlyChart"] {
      background:linear-gradient(145deg,rgba(18,30,49,.95),rgba(13,23,39,.95));
      border:1px solid var(--line);
      border-radius:16px;
      padding:5px 5px 0;
      box-shadow:0 10px 26px rgba(0,0,0,.12);
    }
    div[data-testid="stTabs"] { margin-top:3px; }
    div[data-testid="stTabs"] button {
      color:#a9bad2 !important; font-size:10px !important;
      font-weight:700 !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
      color:#ff7185 !important; border-bottom-color:#ff526b !important;
    }
    div[data-testid="stSelectbox"] label,
    div[data-testid="stDateInput"] label {
      color:#9eb0c9 !important; font-size:9px !important;
    }
    div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
      background:#142139 !important; border:1px solid var(--line) !important;
      border-radius:9px !important; min-height:32px;
    }
    div[data-testid="stSelectbox"] * { color:#eef4ff !important; }
    div[data-testid="stAlert"] { border-radius:12px; }
    .footnote {
      color:#667b99; font-size:8px; text-align:right;
      letter-spacing:.8px; margin-top:4px;
    }

    /* Keep this app intentionally fixed to the viewport. */
    @media (max-height: 800px) {
      [data-testid="stMainBlockContainer"] { padding-top:.45rem !important; }
      .kpi { min-height:62px; padding:8px 11px; }
      .kpi-value { font-size:19px; }
      .page-title { font-size:18px; }
      div[data-testid="stPlotlyChart"] { padding:2px; }
    }
    @media (max-width: 1100px) {
      [data-testid="stAppViewContainer"],
      [data-testid="stMain"],
      [data-testid="stMainBlockContainer"] {
        overflow:auto !important;
      }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------- Database ---------------------------
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent

DB_CANDIDATES = [
    PROJECT_ROOT / "data" / "raw" / "airtel.db",
    PROJECT_ROOT / "data" / "raw" / "airtel.db.gz",
    PROJECT_ROOT / "data" / "airtel.db",
    PROJECT_ROOT / "data" / "airtel.db.gz",
    APP_DIR / "data" / "raw" / "airtel.db",
    APP_DIR / "data" / "raw" / "airtel.db.gz",
    Path.cwd() / "data" / "raw" / "airtel.db",
    Path.cwd() / "data" / "raw" / "airtel.db.gz",
]

def locate_database() -> Path | None:
    for candidate in DB_CANDIDATES:
        if candidate.exists() and candidate.suffix == ".db":
            return candidate
        if candidate.exists() and candidate.suffix == ".gz":
            output = PROJECT_ROOT / "data" / "raw" / "airtel.db"
            output.parent.mkdir(parents=True, exist_ok=True)
            try:
                with gzip.open(candidate, "rb") as src, output.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                return output
            except (OSError, EOFError):
                # Fall back to a temporary extraction if the project folder is read-only.
                try:
                    temp_db = Path(tempfile.gettempdir()) / "airtel_dashboard.db"
                    with gzip.open(candidate, "rb") as src, temp_db.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                    return temp_db
                except (OSError, EOFError):
                    continue
    return None

DB_PATH = locate_database()

@st.cache_data(show_spinner="Loading Airtel data...")
def load_data(db_path: str):
    connection = sqlite3.connect(db_path)
    try:
        recharges = pd.read_sql_query(
            """
            SELECT r.recharge_id, r.customer_id, r.recharge_date, r.amount_inr,
                   r.plan_id, r.channel, r.txn_type,
                   c.connection_type, c.circle_id, ci.circle_name, ci.region,
                   p.plan_name, p.plan_type
            FROM recharges r
            LEFT JOIN customers c ON r.customer_id = c.customer_id
            LEFT JOIN circles ci ON c.circle_id = ci.circle_id
            LEFT JOIN plans p ON r.plan_id = p.plan_id
            WHERE r.recharge_date >= '2025-01-01'
              AND r.recharge_date < '2025-07-01'
            """, connection
        )
        features = pd.read_sql_query(
            """
            SELECT customer_id, circle_name, region, plan_name, plan_type,
                   connection_type, age_band, gender, device_type,
                   stated_arpu, actual_arpu_6m, arpu_gap,
                   recharge_total_6m, recharge_count, complaint_count
            FROM customer_features
            """, connection
        )
    finally:
        connection.close()

    recharges["recharge_date"] = pd.to_datetime(recharges["recharge_date"], errors="coerce")
    recharges["month"] = recharges["recharge_date"].dt.to_period("M").dt.to_timestamp()
    numeric_columns = [
        "amount_inr", "stated_arpu", "actual_arpu_6m",
        "arpu_gap", "recharge_total_6m", "recharge_count", "complaint_count"
    ]
    for frame in (recharges, features):
        for column in numeric_columns:
            if column in frame.columns:
                frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return recharges, features

def money(value: float) -> str:
    return f"₹{value:,.0f}"

def kpi(label: str, value: str, note: str, accent: str):
    st.markdown(
        f"""
        <div class="kpi" style="--accent:{accent}">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def card_heading(title: str, tag: str, caption: str):
    st.markdown(
        f"""
        <div class="chart-head">
          <div class="chart-title">{title}</div>
          <div class="chart-tag">{tag}</div>
        </div>
        <div class="chart-caption">{caption}</div>
        """,
        unsafe_allow_html=True,
    )

def style_figure(fig, height=245):
    fig.update_layout(
        height=height,
        margin=dict(l=12, r=12, t=25, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", size=9, color="#c8d5e8"),
        colorway=["#ff526b", "#55d6d2", "#9c8cff", "#f2c879", "#6ca8ff"],
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1, font=dict(size=8, color="#aebed4")
        ),
        hoverlabel=dict(bgcolor="#17243a", font_color="#ffffff"),
    )
    fig.update_xaxes(
        showgrid=False, zeroline=False,
        linecolor="rgba(173,193,220,.16)",
        tickfont=dict(color="#91a5c1", size=8),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor="rgba(173,193,220,.10)",
        zeroline=False, tickfont=dict(color="#91a5c1", size=8),
    )
    return fig

def show_chart(fig, height=245):
    st.plotly_chart(
        style_figure(fig, height),
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
    )

def safe_group(df: pd.DataFrame, dimension: str, measure: str):
    result = df.groupby(dimension, dropna=True, as_index=False)[measure].sum()
    result[dimension] = result[dimension].astype(str)
    return result.sort_values(measure, ascending=False)

def treemap_chart(df, dimension, measure, title=None):
    data = safe_group(df, dimension, measure).head(14)
    if data.empty:
        st.info("No matching data.")
        return
    fig = px.treemap(
        data, path=[dimension], values=measure, color=measure,
        color_continuous_scale=["#17354a", "#287f87", "#55d6d2", "#ff7185"],
    )
    fig.update_traces(
        textfont=dict(size=10, color="#ffffff"),
        marker=dict(line=dict(color="#0c1727", width=2)),
        hovertemplate="%{label}<br>Value: %{value:,.0f}<extra></extra>",
    )
    show_chart(fig)

def sunburst_chart(df, path, measure):
    clean = df.dropna(subset=path).copy()
    if clean.empty:
        st.info("No matching data.")
        return
    grouped = clean.groupby(path, as_index=False)[measure].sum()
    fig = px.sunburst(
        grouped, path=path, values=measure, color=measure,
        color_continuous_scale=["#15253c", "#6556a9", "#9c8cff", "#ff7185"],
    )
    fig.update_traces(textfont=dict(size=9, color="white"))
    show_chart(fig)

def polar_chart(df, dimension, measure):
    data = safe_group(df, dimension, measure).head(10)
    if data.empty:
        st.info("No matching data.")
        return
    fig = px.bar_polar(
        data, r=measure, theta=dimension, color=measure,
        color_continuous_scale=["#1d5264", "#55d6d2", "#ff7185"],
    )
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(gridcolor="rgba(173,193,220,.14)", tickfont=dict(size=7, color="#91a5c1")),
            angularaxis=dict(gridcolor="rgba(173,193,220,.14)", tickfont=dict(size=8, color="#c8d5e8")),
        )
    )
    show_chart(fig)

def radar_chart(df, dimension, measure):
    data = safe_group(df, dimension, measure).head(8)
    if data.empty:
        st.info("No matching data.")
        return
    # Normalize to make categories with different scales easier to compare.
    maximum = data[measure].max()
    data["score"] = data[measure] / maximum * 100 if maximum else 0
    theta = data[dimension].tolist()
    radius = data["score"].tolist()
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=radius + radius[:1],
        theta=theta + theta[:1],
        fill="toself",
        fillcolor="rgba(156,140,255,.20)",
        line=dict(color="#9c8cff", width=2),
        name="Relative index",
        hovertemplate="%{theta}<br>Index: %{r:.1f}<extra></extra>",
    ))
    fig.update_layout(
        showlegend=False,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(range=[0, 100], gridcolor="rgba(173,193,220,.15)", tickfont=dict(size=7, color="#91a5c1")),
            angularaxis=dict(gridcolor="rgba(173,193,220,.15)", tickfont=dict(size=8, color="#c8d5e8")),
        ),
    )
    show_chart(fig)

def heatmap_chart(df, row, column, measure):
    data = df.dropna(subset=[row, column]).copy()
    if data.empty:
        st.info("No matching data.")
        return
    pivot = data.pivot_table(
        index=row, columns=column, values=measure, aggfunc="sum", fill_value=0
    )
    pivot = pivot.iloc[:12, :10]
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[str(v) for v in pivot.columns],
        y=[str(v) for v in pivot.index],
        colorscale=[[0, "#14243a"], [.45, "#287f87"], [1, "#ff7185"]],
        colorbar=dict(thickness=7, tickfont=dict(size=7, color="#91a5c1")),
        hovertemplate="%{y} / %{x}<br>Value: %{z:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        xaxis=dict(side="bottom", tickfont=dict(size=8)),
        yaxis=dict(autorange="reversed", tickfont=dict(size=8)),
    )
    show_chart(fig)

def waterfall_chart(df, dimension, measure):
    data = safe_group(df, dimension, measure).head(10).sort_values(measure, ascending=True)
    if data.empty:
        st.info("No matching data.")
        return
    # Category contributions are shown as sequential increments, not a time-series total.
    fig = go.Figure(go.Waterfall(
        orientation="v",
        x=data[dimension],
        y=data[measure],
        measure=["relative"] * len(data),
        connector={"line": {"color": "rgba(173,193,220,.30)", "width": 1}},
        increasing={"marker": {"color": "#55d6d2"}},
        decreasing={"marker": {"color": "#ff526b"}},
        text=[f"{v:,.0f}" for v in data[measure]],
        textposition="outside",
    ))
    fig.update_layout(showlegend=False)
    show_chart(fig)

def bubble_chart(df, dimension, x_measure, y_measure, size_measure):
    data = df.dropna(subset=[dimension, x_measure, y_measure]).copy()
    if data.empty:
        st.info("No matching data.")
        return
    grouped = data.groupby(dimension, as_index=False).agg(
        x=(x_measure, "mean"),
        y=(y_measure, "mean"),
        size=(size_measure, "sum"),
    ).head(18)
    fig = px.scatter(
        grouped, x="x", y="y", size="size", color=dimension,
        hover_name=dimension, size_max=38,
        color_discrete_sequence=["#ff7185", "#55d6d2", "#9c8cff", "#f2c879", "#6ca8ff"],
    )
    fig.update_traces(marker=dict(opacity=.82, line=dict(width=1, color="rgba(255,255,255,.4)")))
    fig.update_layout(
        xaxis_title=x_measure.replace("_", " ").title(),
        yaxis_title=y_measure.replace("_", " ").title(),
        legend=dict(font=dict(size=7)),
    )
    show_chart(fig)

# -------------------------- Load data ---------------------------
if DB_PATH is None or not DB_PATH.exists():
    st.error(
        "Database not found. Place airtel.db or airtel.db.gz inside "
        "airtel-telecom-analytics/data/raw/ and restart the app."
    )
    st.code("airtel-telecom-analytics/\\n  dashboard/app.py\\n  data/raw/airtel.db.gz")
    st.stop()

try:
    recharges, features = load_data(str(DB_PATH))
except Exception as error:
    st.error("Could not load the Airtel database. Check that the database contains the expected tables and columns.")
    st.exception(error)
    st.stop()

if recharges.empty or features.empty:
    st.warning("The database loaded, but the selected date range or required tables contain no records.")
    st.stop()

# ---------------------------- Sidebar ---------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="brand" style="margin:3px 0 18px">
          <div class="brand-symbol">a</div>
          <div>
            <div class="brand-name">airtel</div>
            <div class="brand-sub">REVENUE INTELLIGENCE</div>
          </div>
        </div>
        <div style="color:#55d6d2;font-size:8px;font-weight:800;letter-spacing:1.5px;margin-bottom:8px">
          CONTROL CENTRE
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("**DASHBOARD PAGES**")
    st.caption("Use the two tabs at the top of the dashboard to switch views.")
    st.markdown("---")
    st.markdown("**GLOBAL FILTERS**")
    region_values = ["All regions"] + sorted(features["region"].dropna().astype(str).unique().tolist())
    connection_values = ["All connections"] + sorted(features["connection_type"].dropna().astype(str).unique().tolist())
    plan_values = ["All plan types"] + sorted(features["plan_type"].dropna().astype(str).unique().tolist())
    selected_region = st.selectbox("Operating region", region_values)
    selected_connection = st.selectbox("Connection segment", connection_values)
    selected_plan = st.selectbox("Plan category", plan_values)
    st.markdown("---")
    st.caption("Reporting period")
    st.markdown("**JAN — JUN 2025**")
    st.caption("Source: Airtel analytical SQLite database")
    if st.button("Reset all filters", use_container_width=True):
        st.rerun()

# Apply consistent global filters to both datasets.
if selected_region != "All regions":
    features = features[features["region"].astype(str) == selected_region].copy()
    recharges = recharges[recharges["region"].astype(str) == selected_region].copy()
if selected_connection != "All connections":
    features = features[features["connection_type"].astype(str) == selected_connection].copy()
    recharges = recharges[recharges["connection_type"].astype(str) == selected_connection].copy()
if selected_plan != "All plan types":
    features = features[features["plan_type"].astype(str) == selected_plan].copy()
    recharges = recharges[recharges["plan_type"].astype(str) == selected_plan].copy()

# ------------------------- Dashboard tabs -----------------------
tab_overview, tab_diagnostics = st.tabs(["◉  Executive overview", "◎  Revenue diagnostics"])

with tab_overview:
    page_title = "Executive overview"
    page_subtitle = "A concise view of revenue momentum, customer value and portfolio composition."
    # ------------------------- Header and KPIs -----------------------
    st.markdown(
        """
        <div class="topline">
          <div class="brand">
            <div class="brand-symbol">a</div>
            <div>
              <div class="brand-name">airtel <span style="font-weight:500;color:#8ea1bd">/ intelligence</span></div>
              <div class="brand-sub">TELECOM FINANCE & CUSTOMER ANALYTICS</div>
            </div>
          </div>
          <div class="live"><span class="live-dot"></span> DATA CONNECTED &nbsp; • &nbsp; H1 2025</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="page-title">{page_title}</div><div class="page-subtitle">{page_subtitle}</div>',
        unsafe_allow_html=True,
    )

    received = float(recharges["amount_inr"].fillna(0).sum())
    transactions = int(recharges["recharge_id"].nunique())
    subscribers = int(features["customer_id"].nunique())
    avg_arpu = float(features["actual_arpu_6m"].mean()) if not features.empty else 0
    complaints = int(features["complaint_count"].fillna(0).sum()) if "complaint_count" in features else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi("Subscriber base", f"{subscribers:,}", "Unique customers in filtered view", "#55d6d2")
    with k2:
        kpi("Recharge revenue", f"₹{received/1e7:.2f} Cr", "Jan–Jun 2025 transaction value", "#ff526b")
    with k3:
        kpi("Transactions", f"{transactions:,}", "Successful recharge records", "#9c8cff")
    with k4:
        kpi("Average actual ARPU", money(avg_arpu), f"{complaints:,} recorded complaints", "#f2c879")

    # -------------------------- Chart views -------------------------

    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        card_heading("Revenue composition", "TREEMAP", "Which plans contribute most to actual ARPU?")
        treemap_chart(features, "plan_name", "actual_arpu_6m")

    with col2:
        card_heading("Regional revenue signature", "POLAR", "A radial comparison of regional contribution.")
        polar_chart(features, "region", "actual_arpu_6m")

    with col3:
        card_heading("Customer value profile", "RADAR INDEX", "Relative revenue index across plan categories.")
        radar_chart(features, "plan_type", "actual_arpu_6m")

    col4, col5, col6 = st.columns(3, gap="medium")
    with col4:
        card_heading("Revenue by month", "AREA CONTOUR", "Monthly recharge value and transaction density.")
        monthly = recharges.groupby("month", as_index=False).agg(
            revenue=("amount_inr", "sum"),
            transactions=("recharge_id", "nunique"),
        )
        if monthly.empty:
            st.info("No monthly recharge data.")
        else:
            fig = px.area(
                monthly, x="month", y="revenue",
                color_discrete_sequence=["#55d6d2"],
            )
            fig.update_traces(
                line=dict(width=2, color="#55d6d2"),
                fillcolor="rgba(85,214,210,.16)",
                hovertemplate="%{x|%b %Y}<br>Revenue: ₹%{y:,.0f}<extra></extra>",
            )
            show_chart(fig, 205)

    with col5:
        card_heading("Channel mix hierarchy", "SUNBURST", "Channel and transaction type contribution.")
        sunburst_chart(recharges, ["channel", "txn_type"], "amount_inr")

    with col6:
        card_heading("Region × connection matrix", "HEATMAP", "Revenue concentration across segments.")
        heatmap_chart(features, "region", "connection_type", "actual_arpu_6m")


with tab_diagnostics:
    page_title = "Revenue diagnostics"
    page_subtitle = "Explore channel quality, regional concentration and customer value patterns."
    # ------------------------- Header and KPIs -----------------------
    st.markdown(
        """
        <div class="topline">
          <div class="brand">
            <div class="brand-symbol">a</div>
            <div>
              <div class="brand-name">airtel <span style="font-weight:500;color:#8ea1bd">/ intelligence</span></div>
              <div class="brand-sub">TELECOM FINANCE & CUSTOMER ANALYTICS</div>
            </div>
          </div>
          <div class="live"><span class="live-dot"></span> DATA CONNECTED &nbsp; • &nbsp; H1 2025</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="page-title">{page_title}</div><div class="page-subtitle">{page_subtitle}</div>',
        unsafe_allow_html=True,
    )

    received = float(recharges["amount_inr"].fillna(0).sum())
    transactions = int(recharges["recharge_id"].nunique())
    subscribers = int(features["customer_id"].nunique())
    avg_arpu = float(features["actual_arpu_6m"].mean()) if not features.empty else 0
    complaints = int(features["complaint_count"].fillna(0).sum()) if "complaint_count" in features else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi("Subscriber base", f"{subscribers:,}", "Unique customers in filtered view", "#55d6d2")
    with k2:
        kpi("Recharge revenue", f"₹{received/1e7:.2f} Cr", "Jan–Jun 2025 transaction value", "#ff526b")
    with k3:
        kpi("Transactions", f"{transactions:,}", "Successful recharge records", "#9c8cff")
    with k4:
        kpi("Average actual ARPU", money(avg_arpu), f"{complaints:,} recorded complaints", "#f2c879")

    # -------------------------- Chart views -------------------------

    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        card_heading("Revenue contribution bridge", "WATERFALL", "Contribution by recharge channel.")
        waterfall_chart(recharges, "channel", "amount_inr")

    with col2:
        card_heading("Plan portfolio hierarchy", "ICICLE", "Explore plan category and plan-level value.")
        hierarchy = features.dropna(subset=["plan_type", "plan_name"]).groupby(
            ["plan_type", "plan_name"], as_index=False
        )["actual_arpu_6m"].sum()
        if hierarchy.empty:
            st.info("No plan hierarchy data.")
        else:
            fig = px.icicle(
                hierarchy, path=["plan_type", "plan_name"], values="actual_arpu_6m",
                color="actual_arpu_6m",
                color_continuous_scale=["#14243a", "#6556a9", "#9c8cff", "#ff7185"],
            )
            fig.update_traces(textfont=dict(size=9, color="white"))
            show_chart(fig)

    with col3:
        card_heading("ARPU vs recharge behaviour", "BUBBLE", "Average ARPU against recharge frequency.")
        bubble_chart(
            features, "plan_type", "actual_arpu_6m",
            "recharge_count", "recharge_total_6m"
        )

    col4, col5, col6 = st.columns(3, gap="medium")
    with col4:
        card_heading("ARPU gap distribution", "VIOLIN", "Distribution of stated-to-actual ARPU gap.")
        violin = features.dropna(subset=["plan_type", "arpu_gap"]).copy()
        if violin.empty:
            st.info("No ARPU gap data.")
        else:
            fig = px.violin(
                violin, x="plan_type", y="arpu_gap", color="plan_type",
                box=True, points="outliers",
                color_discrete_sequence=["#55d6d2", "#9c8cff", "#ff7185", "#f2c879"],
            )
            fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="ARPU gap (₹)")
            show_chart(fig, 205)

    with col5:
        card_heading("Recharge amount distribution", "DENSITY", "Where transaction values cluster.")
        amount_data = recharges.dropna(subset=["amount_inr"])
        if amount_data.empty:
            st.info("No transaction amount data.")
        else:
            fig = px.violin(
                amount_data, y="amount_inr", x="txn_type",
                color="txn_type", box=False, points=False,
                color_discrete_sequence=["#ff7185", "#55d6d2", "#9c8cff", "#f2c879"],
            )
            fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Recharge amount (₹)")
            show_chart(fig, 205)

    with col6:
        card_heading("Customer spend concentration", "DECILE CURVE", "Cumulative recharge value by spend rank.")
        spend = features[["customer_id", "recharge_total_6m"]].dropna().copy()
        if spend.empty:
            st.info("No customer spend data.")
        else:
            spend = spend.sort_values("recharge_total_6m", ascending=False).reset_index(drop=True)
            spend["customer_share"] = (spend.index + 1) / len(spend) * 100
            total_spend = spend["recharge_total_6m"].sum()
            spend["revenue_share"] = spend["recharge_total_6m"].cumsum() / total_spend * 100 if total_spend else 0
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=spend["customer_share"], y=spend["revenue_share"],
                mode="lines", line=dict(color="#ff7185", width=2.5),
                fill="tozeroy", fillcolor="rgba(255,113,133,.12)",
                hovertemplate="Customer share: %{x:.1f}%<br>Revenue share: %{y:.1f}%<extra></extra>",
            ))
            fig.add_trace(go.Scatter(
                x=[0, 100], y=[0, 100], mode="lines",
                line=dict(color="rgba(173,193,220,.4)", dash="dash", width=1),
                hoverinfo="skip",
            ))
            fig.update_layout(
                showlegend=False, xaxis_title="Cumulative customer share (%)",
                yaxis_title="Cumulative revenue share (%)",
            )
            show_chart(fig, 205)


st.markdown(
    '<div class="footnote">AIRTEL REVENUE INTELLIGENCE &nbsp; / &nbsp; INTERNAL ANALYTICS VIEW &nbsp; / &nbsp; SOURCE: SQLITE</div>',
    unsafe_allow_html=True,
)
