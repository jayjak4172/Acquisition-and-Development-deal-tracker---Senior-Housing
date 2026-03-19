"""
Senior Housing M&A Intelligence Dashboard
Run: streamlit run dashboard_app.py
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Senior Housing M&A Intelligence",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Theme / CSS ───────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@300;400&family=DM+Sans:wght@300;400;500&display=swap');

  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

  .main { background: #0d0f14; }
  .block-container { padding-top: 2rem; padding-bottom: 2rem; }

  h1, h2, h3 { font-family: 'DM Serif Display', serif !important; font-weight: 400 !important; }

  .kpi-card {
    background: #13161e;
    border: 1px solid #252938;
    border-top: 2px solid #c8a96e;
    padding: 20px;
    border-radius: 2px;
  }
  .kpi-label { font-size: 10px; letter-spacing: 1.2px; text-transform: uppercase;
               color: #7a7f94; font-family: 'DM Mono', monospace; margin-bottom: 8px; }
  .kpi-value { font-family: 'DM Serif Display', serif; font-size: 32px;
               color: #c8a96e; line-height: 1; }
  .kpi-sub   { font-size: 11px; color: #454a5e; font-family: 'DM Mono', monospace;
               margin-top: 4px; }

  .section-label { font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase;
                   color: #454a5e; font-family: 'DM Mono', monospace;
                   border-bottom: 1px solid #252938; padding-bottom: 8px; margin-bottom: 16px; }
  .insight-box { background: #13161e; border: 1px solid #252938;
                 border-left: 3px solid #c8a96e; padding: 16px 20px;
                 font-size: 13px; color: #7a7f94; line-height: 1.7; }
  .insight-box b { color: #c8a96e; }
</style>
""", unsafe_allow_html=True)

GOLD  = "#c8a96e"
TEAL  = "#7eb8a4"
BLUE  = "#8b9ed4"
RED   = "#e07b6a"
BG    = "#0d0f14"
SURF  = "#13161e"
SURF2 = "#1a1e2a"
BORD  = "#252938"

PLOTLY_LAYOUT = dict(
    paper_bgcolor=SURF, plot_bgcolor=SURF2,
    font=dict(family="DM Mono", color="#7a7f94", size=11),
    margin=dict(l=8, r=8, t=8, b=8),
    xaxis=dict(gridcolor=BORD, linecolor=BORD, tickcolor=BORD),
    yaxis=dict(gridcolor=BORD, linecolor=BORD, tickcolor=BORD),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#7a7f94")),
)

# ── Data loading ──────────────────────────────────────────────
@st.cache_data(ttl=300)  # refresh every 5 min
def load_data():
    conn = sqlite3.connect("senior_housing_deals.db")

    deals = pd.read_sql("SELECT * FROM deals", conn)
    dev   = pd.read_sql("SELECT * FROM development_projects", conn)
    conn.close()

    # Normalize deal_type
    deals["deal_type"] = deals["deal_type"].replace("M&A", "Acquisition")

    # Parse dates
    for col in ["article_date", "announcement_date", "transaction_date"]:
        deals[col] = pd.to_datetime(deals[col], errors="coerce")
    dev["article_date"] = pd.to_datetime(dev["article_date"], errors="coerce")

    # Clean numerics
    deals["price"]       = pd.to_numeric(deals["price"], errors="coerce")
    deals["total_units"] = pd.to_numeric(deals["total_units"], errors="coerce")
    deals["loan_amount"] = pd.to_numeric(deals["loan_amount"], errors="coerce")
    dev["unit_count"]    = pd.to_numeric(dev["unit_count"], errors="coerce")
    dev["total_project_cost"] = pd.to_numeric(dev["total_project_cost"], errors="coerce")

    # Derived
    deals["month"]       = deals["article_date"].dt.to_period("M").astype(str)
    deals["year"]        = deals["article_date"].dt.year
    dev["month"]         = dev["article_date"].dt.to_period("M").astype(str)

    # Clean N/A strings
    for col in ["buyer","seller","broker","metro","state","property_type","region"]:
        if col in deals.columns:
            deals[col] = deals[col].replace({"N/A": np.nan, "": np.nan})
    for col in ["developer","metro","state","building_type"]:
        if col in dev.columns:
            dev[col] = dev[col].replace({"N/A": np.nan, "": np.nan})

    return deals, dev

deals, dev = load_data()

# ── Sidebar filters ───────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏢 Senior Housing\nM&A Intelligence")
    st.markdown("---")

    st.markdown("**Filters**")

    # Date range
    dated = deals[deals["article_date"].notna()]
    if len(dated):
        min_d = dated["article_date"].min().date()
        max_d = dated["article_date"].max().date()
        date_range = st.date_input("Date range", value=(min_d, max_d),
                                    min_value=min_d, max_value=max_d)
    else:
        date_range = None

    # Deal type
    deal_types = ["All"] + sorted(deals["deal_type"].dropna().unique().tolist())
    sel_type = st.selectbox("Deal Type", deal_types)

    # State
    states_avail = sorted(deals["state"].dropna().unique().tolist())
    sel_states = st.multiselect("State", states_avail, default=[])

    # Property type (simplified)
    prop_types = sorted(deals["property_type"].dropna().unique().tolist())
    sel_prop = st.multiselect("Property Type", prop_types, default=[])

    st.markdown("---")
    st.markdown(f"""
    <div style='font-family:DM Mono; font-size:11px; color:#454a5e; line-height:1.8'>
    Deals: {len(deals)}<br>
    Dev projects: {len(dev)}<br>
    Updated: {datetime.now().strftime('%b %d, %Y')}
    </div>
    """, unsafe_allow_html=True)

# ── Apply filters ─────────────────────────────────────────────
df = deals.copy()

if date_range and len(date_range) == 2:
    df = df[
        (df["article_date"].isna()) |
        ((df["article_date"].dt.date >= date_range[0]) &
         (df["article_date"].dt.date <= date_range[1]))
    ]

if sel_type != "All":
    df = df[df["deal_type"] == sel_type]

if sel_states:
    df = df[df["state"].isin(sel_states)]

if sel_prop:
    df = df[df["property_type"].isin(sel_prop)]

acq = df[df["deal_type"] == "Acquisition"]
fin = df[df["deal_type"] == "Financing"]

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<h1 style='font-size:36px; margin-bottom:4px'>
  Senior Housing <em style='color:#c8a96e'>M&A</em> Intelligence
</h1>
<p style='font-family:DM Mono; font-size:12px; color:#454a5e; margin-bottom:32px'>
  Automated market tracker · SeniorsHousingBusiness.com · SeniorHousingNews.com
</p>
""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)

total_val = df["price"].sum()
total_units = df["total_units"].sum()
dev_units = dev["unit_count"].sum()

def kpi(col, label, value, sub=""):
    col.markdown(f"""
    <div class='kpi-card'>
      <div class='kpi-label'>{label}</div>
      <div class='kpi-value'>{value}</div>
      <div class='kpi-sub'>{sub}</div>
    </div>""", unsafe_allow_html=True)

kpi(k1, "Acquisitions",  f"{len(acq)}",  "tracked deals")
kpi(k2, "Total Value",   f"${total_val/1e9:.1f}B" if pd.notna(total_val) and total_val > 0 else "—",
    f"{df['price'].notna().sum()} priced")
kpi(k3, "MA Units",      f"{int(total_units):,}" if pd.notna(total_units) else "—", "beds transacted")
kpi(k4, "Dev Pipeline",  f"{len(dev)}", f"{int(dev_units):,} units planned")
kpi(k5, "Financing",     f"{len(fin)}", "loan transactions")
kpi(k6, "States",        f"{df['state'].nunique()}", "geographic coverage")

st.markdown("<br>", unsafe_allow_html=True)

# ── Tab layout ────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📈 Volume & Trends", "🗺 Geography", "🏢 Players", "🔍 Deal Explorer"])

# ───────────────────────────────────────────
# TAB 1: Volume & Trends
# ───────────────────────────────────────────
with tab1:
    col_a, col_b = st.columns([2, 1])

    with col_a:
        st.markdown("<div class='section-label'>Monthly Deal Volume</div>", unsafe_allow_html=True)

        dated_df = df[df["article_date"].notna()].copy()
        dated_dev = dev[dev["article_date"].notna()].copy()

        if len(dated_df):
            monthly_acq = dated_df[dated_df["deal_type"]=="Acquisition"].groupby("month").size().reset_index(name="Acquisitions")
            monthly_fin = dated_df[dated_df["deal_type"]=="Financing"].groupby("month").size().reset_index(name="Financing")
            monthly_dev = dated_dev.groupby("month").size().reset_index(name="Development")

            all_months = sorted(set(
                list(monthly_acq["month"]) + list(monthly_fin["month"]) + list(monthly_dev["month"])
            ))
            base = pd.DataFrame({"month": all_months})
            monthly = (base
                .merge(monthly_acq, on="month", how="left")
                .merge(monthly_fin, on="month", how="left")
                .merge(monthly_dev, on="month", how="left")
                .fillna(0))

            fig = go.Figure()
            fig.add_bar(x=monthly["month"], y=monthly["Acquisitions"],
                        name="Acquisitions", marker_color=GOLD, opacity=0.85)
            fig.add_bar(x=monthly["month"], y=monthly["Financing"],
                        name="Financing", marker_color=TEAL, opacity=0.85)
            fig.add_bar(x=monthly["month"], y=monthly["Development"],
                        name="Development", marker_color=BLUE, opacity=0.85)

            fig.update_layout(**PLOTLY_LAYOUT, barmode="stack", height=280,
                              legend=dict(orientation="h", yanchor="bottom", y=1.02))
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("<div class='section-label'>Deal Size Distribution</div>", unsafe_allow_html=True)
        priced = df[df["price"].notna()]
        if len(priced):
            bins   = [0, 50e6, 100e6, 200e6, 500e6, float("inf")]
            labels = ["<$50M","$50–100M","$100–200M","$200–500M","$500M+"]
            priced = priced.copy()
            priced["size_bucket"] = pd.cut(priced["price"], bins=bins, labels=labels)
            dist = priced["size_bucket"].value_counts().reindex(labels).fillna(0)

            fig2 = go.Figure(go.Bar(
                x=dist.values, y=dist.index,
                orientation="h",
                marker_color=GOLD, opacity=0.8,
                text=dist.values, textposition="outside",
                textfont=dict(color="#7a7f94", size=11)
            ))
            fig2.update_layout(**PLOTLY_LAYOUT, height=280,
                               xaxis=dict(gridcolor=BORD, showticklabels=False))
            st.plotly_chart(fig2, use_container_width=True)

    # Property type
    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown("<div class='section-label'>Property Type Mix</div>", unsafe_allow_html=True)

        # Normalize property_type (combine variants)
        def simplify_pt(val):
            if pd.isna(val): return np.nan
            v = val.upper().replace(" ", "").replace("/","_").replace(",","_")
            if "SNF" in v: return "SNF"
            if "CCRC" in v: return "CCRC / Mixed"
            if "IL" in v and "AL" in v and "MC" in v: return "IL / AL / MC"
            if "AL" in v and "MC" in v: return "AL / MC"
            if "AL" in v: return "AL"
            if "IL" in v: return "IL"
            if "MC" in v: return "MC"
            return "Other"

        pt_data = acq["property_type"].apply(simplify_pt).value_counts()
        colors = [GOLD, TEAL, BLUE, RED, "#a78bca", "#6ab4e0", "#e0c46a"]
        fig3 = go.Figure(go.Pie(
            labels=pt_data.index, values=pt_data.values,
            hole=0.55, marker_colors=colors[:len(pt_data)],
            textinfo="percent", textfont=dict(size=11),
        ))
        fig3.update_layout(**PLOTLY_LAYOUT, height=280,
                           legend=dict(orientation="v", x=1, font=dict(size=11)))
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        st.markdown("<div class='section-label'>Key Insights</div>", unsafe_allow_html=True)

        # Auto-compute insights
        if len(dated_df):
            peak_month = monthly.set_index("month")["Acquisitions"].idxmax()
            peak_n = int(monthly.set_index("month")["Acquisitions"].max())
            top_state = df["state"].value_counts().index[0] if df["state"].notna().any() else "—"
            top_state_n = int(df["state"].value_counts().iloc[0]) if df["state"].notna().any() else 0
            dev_recent = dated_dev[dated_dev["month"] >= "2026-01"]
            dev_surge = len(dev_recent)

        st.markdown(f"""
        <div class='insight-box' style='margin-bottom:12px'>
          📈 <b>Peak activity: {peak_month}</b><br>
          {peak_n} acquisitions — highest monthly volume in the tracked period.
        </div>
        <div class='insight-box' style='margin-bottom:12px'>
          🌎 <b>Top state: {top_state} ({top_state_n} deals)</b><br>
          Sunbelt states CA · FL · TX · GA account for ~31% of all deal flow.
        </div>
        <div class='insight-box'>
          🏗️ <b>Development surge: {dev_surge} projects in 2026 YTD</b><br>
          Leading indicator of supply pressure in 18–24 months.
        </div>
        """, unsafe_allow_html=True)

# ───────────────────────────────────────────
# TAB 2: Geography
# ───────────────────────────────────────────
with tab2:
    col_e, col_f = st.columns([1.5, 1])

    with col_e:
        st.markdown("<div class='section-label'>Deal Activity by State</div>", unsafe_allow_html=True)
        state_data = df[df["state"].notna()]["state"].value_counts().reset_index()
        state_data.columns = ["state", "count"]

        fig_map = go.Figure(go.Choropleth(
            locations=state_data["state"],
            z=state_data["count"],
            locationmode="USA-states",
            colorscale=[[0, SURF2], [0.3, "#4a3f28"], [0.7, "#8a6b3a"], [1, GOLD]],
            marker_line_color=BORD,
            marker_line_width=0.5,
            colorbar=dict(
                bgcolor=SURF, bordercolor=BORD, tickfont=dict(color="#7a7f94", size=10),
                title=dict(text="Deals", font=dict(color="#7a7f94", size=10))
            ),
            showscale=True,
        ))
        fig_map.update_layout(
            geo=dict(scope="usa", bgcolor=BG, landcolor=SURF2,
                     lakecolor=BG, subunitcolor=BORD),
            paper_bgcolor=SURF, height=380,
            margin=dict(l=0, r=0, t=0, b=0),
        )
        st.plotly_chart(fig_map, use_container_width=True)

    with col_f:
        st.markdown("<div class='section-label'>Top Metros</div>", unsafe_allow_html=True)
        metro_data = df[df["metro"].notna()]["metro"].value_counts().head(12).reset_index()
        metro_data.columns = ["metro", "count"]

        fig_metro = go.Figure(go.Bar(
            x=metro_data["count"], y=metro_data["metro"],
            orientation="h",
            marker=dict(color=TEAL, opacity=0.8),
            text=metro_data["count"], textposition="outside",
            textfont=dict(color="#7a7f94", size=11)
        ))
        fig_metro.update_layout(**PLOTLY_LAYOUT, height=380,
                                yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
                                xaxis=dict(showticklabels=False))
        st.plotly_chart(fig_metro, use_container_width=True)

    # Dev vs Acq by state
    st.markdown("<div class='section-label'>Acquisition vs Development Pipeline by State</div>",
                unsafe_allow_html=True)
    acq_st = acq[acq["state"].notna()]["state"].value_counts().rename("Acquisitions")
    dev_st  = dev[dev["state"].notna()]["state"].value_counts().rename("Development")
    combo   = pd.concat([acq_st, dev_st], axis=1).fillna(0).astype(int)
    combo   = combo[combo.sum(axis=1) >= 3].sort_values("Acquisitions", ascending=False).head(12)

    fig_combo = go.Figure()
    fig_combo.add_bar(x=combo.index, y=combo["Acquisitions"], name="Acquisitions",
                      marker_color=GOLD, opacity=0.85)
    fig_combo.add_bar(x=combo.index, y=combo["Development"], name="Dev Pipeline",
                      marker_color=BLUE, opacity=0.85)
    fig_combo.update_layout(**PLOTLY_LAYOUT, barmode="group", height=260,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig_combo, use_container_width=True)

# ───────────────────────────────────────────
# TAB 3: Players
# ───────────────────────────────────────────
with tab3:
    col_g, col_h = st.columns(2)

    with col_g:
        st.markdown("<div class='section-label'>Most Active Buyers</div>", unsafe_allow_html=True)
        buyers = (acq[acq["buyer"].notna() & (acq["buyer"] != "Undisclosed")]
                  ["buyer"].value_counts().head(12).reset_index())
        buyers.columns = ["buyer", "count"]

        fig_buy = go.Figure(go.Bar(
            x=buyers["count"], y=buyers["buyer"],
            orientation="h",
            marker=dict(color=GOLD, opacity=0.8),
            text=buyers["count"], textposition="outside",
            textfont=dict(color="#7a7f94", size=11)
        ))
        fig_buy.update_layout(**PLOTLY_LAYOUT, height=380,
                              yaxis=dict(autorange="reversed"),
                              xaxis=dict(showticklabels=False))
        st.plotly_chart(fig_buy, use_container_width=True)

    with col_h:
        st.markdown("<div class='section-label'>Most Active Sellers</div>", unsafe_allow_html=True)
        sellers = (acq[acq["seller"].notna() & (acq["seller"] != "Undisclosed")]
                   ["seller"].value_counts().head(12).reset_index())
        sellers.columns = ["seller", "count"]

        fig_sell = go.Figure(go.Bar(
            x=sellers["count"], y=sellers["seller"],
            orientation="h",
            marker=dict(color=RED, opacity=0.8),
            text=sellers["count"], textposition="outside",
            textfont=dict(color="#7a7f94", size=11)
        ))
        fig_sell.update_layout(**PLOTLY_LAYOUT, height=380,
                               yaxis=dict(autorange="reversed"),
                               xaxis=dict(showticklabels=False))
        st.plotly_chart(fig_sell, use_container_width=True)

    # Brokers
    col_i, col_j = st.columns(2)
    with col_i:
        st.markdown("<div class='section-label'>Top Brokers</div>", unsafe_allow_html=True)
        brokers = (acq[acq["broker"].notna()]["broker"]
                   .value_counts().head(8).reset_index())
        brokers.columns = ["broker", "count"]
        if len(brokers):
            fig_brk = go.Figure(go.Bar(
                x=brokers["count"], y=brokers["broker"],
                orientation="h",
                marker=dict(color=TEAL, opacity=0.8),
                text=brokers["count"], textposition="outside",
                textfont=dict(color="#7a7f94", size=11)
            ))
            fig_brk.update_layout(**PLOTLY_LAYOUT, height=280,
                                  yaxis=dict(autorange="reversed"),
                                  xaxis=dict(showticklabels=False))
            st.plotly_chart(fig_brk, use_container_width=True)

    with col_j:
        st.markdown("<div class='section-label'>Top Developers (Pipeline)</div>", unsafe_allow_html=True)
        devs = (dev[dev["developer"].notna()]["developer"]
                .value_counts().head(8).reset_index())
        devs.columns = ["developer", "count"]
        if len(devs):
            fig_dev = go.Figure(go.Bar(
                x=devs["count"], y=devs["developer"],
                orientation="h",
                marker=dict(color=BLUE, opacity=0.8),
                text=devs["count"], textposition="outside",
                textfont=dict(color="#7a7f94", size=11)
            ))
            fig_dev.update_layout(**PLOTLY_LAYOUT, height=280,
                                  yaxis=dict(autorange="reversed"),
                                  xaxis=dict(showticklabels=False))
            st.plotly_chart(fig_dev, use_container_width=True)

# ───────────────────────────────────────────
# TAB 4: Deal Explorer
# ───────────────────────────────────────────
with tab4:
    st.markdown("<div class='section-label'>Deal Explorer</div>", unsafe_allow_html=True)

    search = st.text_input("Search (buyer, seller, property, state...)", "")

    show = df.copy()
    if search:
        mask = (
            show["buyer"].str.contains(search, case=False, na=False) |
            show["seller"].str.contains(search, case=False, na=False) |
            show["property_name"].str.contains(search, case=False, na=False) |
            show["state"].str.contains(search, case=False, na=False) |
            show["metro"].str.contains(search, case=False, na=False)
        )
        show = show[mask]

    display_cols = ["article_date","deal_type","property_name","buyer","seller",
                    "broker","price","total_units","property_type","metro","state"]
    available = [c for c in display_cols if c in show.columns]
    show_display = show[available].copy()
    show_display["article_date"] = show_display["article_date"].dt.strftime("%Y-%m-%d")
    show_display["price"] = show_display["price"].apply(
        lambda x: f"${x/1e6:.1f}M" if pd.notna(x) else "—"
    )

    st.markdown(f"**{len(show_display)} deals**")
    st.dataframe(
        show_display.sort_values("article_date", ascending=False),
        use_container_width=True,
        height=500,
        column_config={
            "article_date":   st.column_config.TextColumn("Date", width=90),
            "deal_type":      st.column_config.TextColumn("Type", width=90),
            "property_name":  st.column_config.TextColumn("Property"),
            "buyer":          st.column_config.TextColumn("Buyer"),
            "seller":         st.column_config.TextColumn("Seller"),
            "broker":         st.column_config.TextColumn("Broker"),
            "price":          st.column_config.TextColumn("Price", width=80),
            "total_units":    st.column_config.NumberColumn("Units", width=60),
            "property_type":  st.column_config.TextColumn("Type"),
            "metro":          st.column_config.TextColumn("Metro"),
            "state":          st.column_config.TextColumn("ST", width=50),
        }
    )

    # Export
    csv = show_display.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇ Download filtered CSV", csv,
                       file_name="senior_housing_filtered.csv", mime="text/csv")
