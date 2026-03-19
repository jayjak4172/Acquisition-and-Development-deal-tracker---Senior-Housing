"""
generate_dashboard.py
DB 읽어서 index.html 자동 생성
실행: python generate_dashboard.py
"""

import sqlite3
import pandas as pd
import numpy as np
import json
from datetime import datetime

# ── Load DB ───────────────────────────────────────────────────
def load_data():
    conn = sqlite3.connect("senior_housing_deals.db")
    deals = pd.read_sql("SELECT * FROM deals", conn)
    dev   = pd.read_sql("SELECT * FROM development_projects", conn)
    conn.close()

    deals["deal_type"]    = deals["deal_type"].replace("M&A", "Acquisition")
    deals["article_date"] = pd.to_datetime(deals["article_date"], errors="coerce")
    dev["article_date"]   = pd.to_datetime(dev["article_date"], errors="coerce")
    deals["price"]        = pd.to_numeric(deals["price"], errors="coerce")
    deals["total_units"]  = pd.to_numeric(deals["total_units"], errors="coerce")
    dev["unit_count"]     = pd.to_numeric(dev["unit_count"], errors="coerce")

    for col in ["buyer","seller","metro","state","property_type"]:
        if col in deals.columns:
            deals[col] = deals[col].replace({"N/A": np.nan, "": np.nan})
    for col in ["developer","metro","state"]:
        if col in dev.columns:
            dev[col] = dev[col].replace({"N/A": np.nan, "": np.nan})

    return deals, dev

# ── Compute chart data ────────────────────────────────────────
def compute(deals, dev):
    acq = deals[deals["deal_type"] == "Acquisition"]

    dated     = deals[deals["article_date"].notna()].copy()
    dated_dev = dev[dev["article_date"].notna()].copy()
    dated["month"]     = dated["article_date"].dt.to_period("M").astype(str)
    dated_dev["month"] = dated_dev["article_date"].dt.to_period("M").astype(str)

    all_months = sorted(set(dated["month"].tolist() + dated_dev["month"].tolist()))
    monthly = []
    for m in all_months:
        a = int((dated[(dated["month"]==m) & (dated["deal_type"]=="Acquisition")].shape[0]))
        f = int((dated[(dated["month"]==m) & (dated["deal_type"]=="Financing")].shape[0]))
        d = int((dated_dev[dated_dev["month"]==m].shape[0]))
        monthly.append({"month": m, "Acquisition": a, "Financing": f, "Development": d})

    buyers_raw = (acq[acq["buyer"].notna() & (acq["buyer"] != "Undisclosed")]
                  ["buyer"].value_counts().head(8))
    buyers = [{"name": k, "count": int(v)} for k, v in buyers_raw.items()]

    metros_raw = deals[deals["metro"].notna()]["metro"].value_counts().head(8)
    metros = [{"metro": k, "count": int(v)} for k, v in metros_raw.items()]

    states_raw = deals[deals["state"].notna()]["state"].value_counts().head(15)
    states = [{"state": k, "count": int(v)} for k, v in states_raw.items()]

    priced = deals[deals["price"].notna()]
    bins   = [0, 50e6, 100e6, 200e6, 500e6, float("inf")]
    labels = ["<$50M", "$50–100M", "$100–200M", "$200–500M", "$500M+"]
    price_dist = []
    for i, label in enumerate(labels):
        n = int(((priced["price"] >= bins[i]) & (priced["price"] < bins[i+1])).sum())
        price_dist.append({"range": label, "count": n})

    def simplify(val):
        if pd.isna(val): return None
        v = val.upper().replace(" ","").replace("/","_").replace(",","_")
        if "SNF" in v: return "SNF"
        if "CCRC" in v: return "CCRC/Mixed"
        if "IL" in v and "AL" in v and "MC" in v: return "IL/AL/MC"
        if "AL" in v and "MC" in v: return "AL/MC"
        if "AL" in v: return "AL"
        if "IL" in v: return "IL"
        if "MC" in v: return "MC"
        return "Other"

    pt_raw = acq["property_type"].apply(simplify).dropna().value_counts().head(6)
    property_types = [{"type": k, "count": int(v)} for k, v in pt_raw.items()]

    # KPIs
    total_val   = deals["price"].sum()
    total_units = deals["total_units"].sum()
    dev_units   = dev["unit_count"].sum()
    priced_n    = int(deals["price"].notna().sum())

    peak_row    = max(monthly, key=lambda x: x["Acquisition"]) if monthly else {}
    peak_month  = peak_row.get("month", "—")
    peak_n      = peak_row.get("Acquisition", 0)

    sunbelt_states = ["CA", "FL", "TX", "GA"]
    sunbelt_n   = sum(s["count"] for s in states if s["state"] in sunbelt_states)
    sunbelt_pct = round(sunbelt_n / len(deals) * 100) if len(deals) else 0

    top_metro   = metros[0]["metro"] if metros else "—"
    top_metro_n = metros[0]["count"] if metros else 0

    dev_2026    = int(dated_dev[dated_dev["month"] >= "2026-01"].shape[0]) if len(dated_dev) else 0

    min_date = dated["article_date"].min().strftime("%b %Y") if len(dated) else "—"
    max_date = dated["article_date"].max().strftime("%b %Y") if len(dated) else "—"

    return {
        "chart": {
            "monthly": monthly,
            "buyers": buyers,
            "metros": metros,
            "states": states,
            "price_dist": price_dist,
            "property_types": property_types,
        },
        "kpi": {
            "acq":        int((deals["deal_type"]=="Acquisition").sum()),
            "fin":        int((deals["deal_type"]=="Financing").sum()),
            "total_value": f"${total_val/1e9:.1f}B" if pd.notna(total_val) and total_val > 0 else "—",
            "priced_n":   priced_n,
            "total_units": f"{int(total_units):,}" if pd.notna(total_units) else "—",
            "dev_projects": len(dev),
            "dev_units":  f"{int(dev_units):,}" if pd.notna(dev_units) else "—",
            "states":     int(deals["state"].nunique()),
            "total_deals": len(deals),
            "date_range": f"{min_date} — {max_date}",
            "updated":    datetime.now().strftime("%B %d, %Y"),
            "peak_month": peak_month,
            "peak_n":     peak_n,
            "sunbelt_n":  sunbelt_n,
            "sunbelt_pct": sunbelt_pct,
            "top_metro":  top_metro,
            "top_metro_n": top_metro_n,
            "dev_2026":   dev_2026,
        }
    }

# ── Generate HTML ─────────────────────────────────────────────
def generate(data):
    k = data["kpi"]
    c = data["chart"]
    data_json = json.dumps(c, ensure_ascii=False, indent=2)

    # Peak month short form e.g. "2025-12" → "Dec '25"
    def fmt_month(m):
        try:
            return datetime.strptime(m, "%Y-%m").strftime("%b '%y")
        except:
            return m

    peak_short = fmt_month(k["peak_month"])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Senior Housing M&A Intelligence · Market Tracker</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #0d0f14; --surface: #13161e; --surface2: #1a1e2a;
    --border: #252938; --accent: #c8a96e; --accent2: #7eb8a4;
    --accent3: #e07b6a; --text: #e8e6e0; --text-muted: #7a7f94;
    --text-dim: #454a5e; --acq: #c8a96e; --fin: #7eb8a4; --dev: #8b9ed4;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: var(--bg); color: var(--text);
    font-family: 'DM Sans', sans-serif; font-weight: 300;
    min-height: 100vh; padding: 48px 40px;
    max-width: 1280px; margin: 0 auto;
  }}
  header {{
    display: flex; justify-content: space-between; align-items: flex-end;
    margin-bottom: 48px; padding-bottom: 24px;
    border-bottom: 1px solid var(--border);
  }}
  .header-left h1 {{
    font-family: 'DM Serif Display', serif; font-size: 32px; font-weight: 400;
    letter-spacing: -0.5px; color: var(--text); line-height: 1.1;
  }}
  .header-left h1 em {{ font-style: italic; color: var(--accent); }}
  .header-left p {{
    margin-top: 6px; font-size: 13px; color: var(--text-muted);
    font-family: 'DM Mono', monospace; font-weight: 300; letter-spacing: 0.5px;
  }}
  .header-right {{
    text-align: right; font-family: 'DM Mono', monospace;
    font-size: 11px; color: var(--text-dim); line-height: 1.8;
  }}
  .badge {{
    display: inline-block; background: var(--accent); color: var(--bg);
    font-size: 9px; font-weight: 500; letter-spacing: 1.5px;
    padding: 3px 8px; text-transform: uppercase; margin-bottom: 8px;
  }}
  .kpi-row {{
    display: grid; grid-template-columns: repeat(6, 1fr);
    gap: 1px; background: var(--border);
    margin-bottom: 32px; border: 1px solid var(--border);
  }}
  .kpi {{
    background: var(--surface); padding: 24px 20px;
    position: relative; overflow: hidden;
  }}
  .kpi::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 2px; background: var(--accent); opacity: 0; transition: opacity 0.3s;
  }}
  .kpi:hover::before {{ opacity: 1; }}
  .kpi-label {{
    font-size: 10px; letter-spacing: 1.2px; text-transform: uppercase;
    color: var(--text-muted); font-family: 'DM Mono', monospace; margin-bottom: 10px;
  }}
  .kpi-value {{
    font-family: 'DM Serif Display', serif; font-size: 28px;
    color: var(--text); line-height: 1;
  }}
  .kpi-sub {{ font-size: 11px; color: var(--text-dim); margin-top: 4px; font-family: 'DM Mono', monospace; }}
  .kpi-value.gold {{ color: var(--accent); }}
  .kpi-value.teal {{ color: var(--accent2); }}
  .kpi-value.blue {{ color: var(--dev); }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }}
  .grid-3 {{ display: grid; grid-template-columns: 1.5fr 1fr 1fr; gap: 16px; margin-bottom: 16px; }}
  .grid-full {{ margin-bottom: 16px; }}
  .panel {{
    background: var(--surface); border: 1px solid var(--border); padding: 28px;
  }}
  .panel-header {{
    display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;
  }}
  .panel-title {{
    font-family: 'DM Serif Display', serif; font-size: 16px;
    font-weight: 400; color: var(--text); letter-spacing: -0.2px;
  }}
  .panel-meta {{ font-family: 'DM Mono', monospace; font-size: 10px; color: var(--text-dim); }}
  .bar-list {{ display: flex; flex-direction: column; gap: 10px; }}
  .bar-item {{ display: flex; align-items: center; gap: 12px; }}
  .bar-label {{
    font-size: 12px; color: var(--text-muted); width: 130px; flex-shrink: 0;
    font-family: 'DM Mono', monospace; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
  }}
  .bar-track {{ flex: 1; height: 6px; background: var(--surface2); }}
  .bar-fill {{ height: 100%; background: var(--accent); transition: width 1s cubic-bezier(0.16,1,0.3,1); }}
  .bar-fill.teal {{ background: var(--accent2); }}
  .bar-count {{
    font-family: 'DM Mono', monospace; font-size: 12px;
    color: var(--text); width: 24px; text-align: right; flex-shrink: 0;
  }}
  .state-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }}
  .state-tile {{
    background: var(--surface2); border: 1px solid var(--border);
    padding: 12px 10px; text-align: center; transition: border-color 0.2s;
  }}
  .state-tile:hover {{ border-color: var(--accent); }}
  .state-abbr {{ font-family: 'DM Mono', monospace; font-size: 14px; font-weight: 500; color: var(--text); }}
  .state-count {{ font-family: 'DM Serif Display', serif; font-size: 20px; color: var(--accent); line-height: 1.2; }}
  .state-label {{ font-size: 9px; color: var(--text-dim); letter-spacing: 0.5px; text-transform: uppercase; }}
  .price-bars {{ display: flex; align-items: flex-end; gap: 8px; height: 120px; }}
  .price-col {{
    flex: 1; display: flex; flex-direction: column;
    align-items: center; gap: 6px; height: 100%; justify-content: flex-end;
  }}
  .price-bar {{ width: 100%; background: var(--accent); opacity: 0.7; transition: opacity 0.2s; }}
  .price-bar:hover {{ opacity: 1; }}
  .price-n {{ font-family: 'DM Serif Display', serif; font-size: 18px; color: var(--text); line-height: 1; }}
  .price-range {{ font-family: 'DM Mono', monospace; font-size: 9px; color: var(--text-dim); text-align: center; }}
  .insight-row {{
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 1px; background: var(--border);
    border: 1px solid var(--border); margin-bottom: 16px;
  }}
  .insight {{ background: var(--surface); padding: 20px 24px; }}
  .insight-icon {{ font-size: 18px; margin-bottom: 8px; }}
  .insight-text {{ font-size: 13px; color: var(--text-muted); line-height: 1.6; }}
  .insight-text strong {{ color: var(--accent); font-weight: 500; }}
  footer {{
    margin-top: 48px; padding-top: 24px;
    border-top: 1px solid var(--border);
    display: flex; justify-content: space-between; align-items: center;
  }}
  footer p {{ font-family: 'DM Mono', monospace; font-size: 11px; color: var(--text-dim); line-height: 1.8; }}
  .legend {{ display: flex; gap: 20px; }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; font-family: 'DM Mono', monospace; font-size: 11px; color: var(--text-muted); }}
  .legend-dot {{ width: 8px; height: 8px; border-radius: 50%; }}
  .dot-acq {{ background: var(--acq); }} .dot-fin {{ background: var(--fin); }} .dot-dev {{ background: var(--dev); }}
  canvas {{ max-height: 220px; }}
</style>
</head>
<body>

<header>
  <div class="header-left">
    <div class="badge">Live Intelligence</div>
    <h1>Senior Housing <em>M&A</em> Tracker</h1>
    <p>Automated pipeline · SeniorsHousingBusiness.com · SeniorHousingNews.com</p>
  </div>
  <div class="header-right">
    <div>{k['total_deals']} M&A Deals · {k['dev_projects']} Development Projects</div>
    <div>{k['date_range']}</div>
    <div>Updated {k['updated']}</div>
  </div>
</header>

<div class="kpi-row">
  <div class="kpi">
    <div class="kpi-label">Acquisitions</div>
    <div class="kpi-value gold">{k['acq']}</div>
    <div class="kpi-sub">tracked deals</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Total Value</div>
    <div class="kpi-value">{k['total_value']}</div>
    <div class="kpi-sub">{k['priced_n']} priced deals</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">MA Units</div>
    <div class="kpi-value">{k['total_units']}</div>
    <div class="kpi-sub">beds transacted</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Dev Pipeline</div>
    <div class="kpi-value blue">{k['dev_projects']}</div>
    <div class="kpi-sub">{k['dev_units']} units planned</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Financing</div>
    <div class="kpi-value teal">{k['fin']}</div>
    <div class="kpi-sub">loan transactions</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">States</div>
    <div class="kpi-value">{k['states']}</div>
    <div class="kpi-sub">geographic coverage</div>
  </div>
</div>

<div class="grid-full">
  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">Deal Volume — Monthly Trend</div>
      <div class="legend">
        <div class="legend-item"><div class="legend-dot dot-acq"></div>Acquisitions</div>
        <div class="legend-item"><div class="legend-dot dot-fin"></div>Financing</div>
        <div class="legend-item"><div class="legend-dot dot-dev"></div>Development</div>
      </div>
    </div>
    <div class="chart-wrap"><canvas id="volumeChart"></canvas></div>
  </div>
</div>

<div class="grid-3">
  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">Most Active Buyers</div>
      <div class="panel-meta">excl. undisclosed</div>
    </div>
    <div class="bar-list" id="buyers-list"></div>
  </div>
  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">Top Metros</div>
      <div class="panel-meta">deal count</div>
    </div>
    <div class="bar-list" id="metros-list"></div>
  </div>
  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">Deal Size Distribution</div>
      <div class="panel-meta">{k['priced_n']} priced deals</div>
    </div>
    <div class="price-bars" id="price-bars"></div>
  </div>
</div>

<div class="grid-2">
  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">Activity by State</div>
      <div class="panel-meta">Top 15</div>
    </div>
    <div class="state-grid" id="state-grid"></div>
  </div>
  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">Property Type Mix</div>
      <div class="panel-meta">acquisitions only</div>
    </div>
    <div class="chart-wrap" style="height:220px"><canvas id="ptChart"></canvas></div>
  </div>
</div>

<div class="insight-row">
  <div class="insight">
    <div class="insight-icon">📈</div>
    <div class="insight-text"><strong>Peak activity: {peak_short} ({k['peak_n']} deals)</strong><br>
    Deal volume hit its highest monthly point in {peak_short} — 2026 YTD pace remains elevated vs. 2H 2025.</div>
  </div>
  <div class="insight">
    <div class="insight-icon">🌎</div>
    <div class="insight-text"><strong>Sunbelt dominance:</strong> CA, FL, TX, GA account for {k['sunbelt_n']} deals ({k['sunbelt_pct']}% of total). {k['top_metro']} leads all metros with {k['top_metro_n']} deals.</div>
  </div>
  <div class="insight">
    <div class="insight-icon">🏗️</div>
    <div class="insight-text"><strong>Supply pipeline accelerating:</strong> {k['dev_2026']} new development projects in 2026 YTD — a leading indicator of supply pressure in 18–24 months.</div>
  </div>
</div>

<footer>
  <p>
    Data sourced from SeniorsHousingBusiness.com · SeniorHousingNews.com<br>
    Extracted via automated pipeline using GPT-3.5 · Built by Jay Kim
  </p>
  <p style="text-align:right">
    {k['total_deals']} M&A deals · {k['dev_projects']} development projects<br>
    Updated {k['updated']}
  </p>
</footer>

<script>
const DATA = {data_json};

Chart.defaults.color = '#7a7f94';
Chart.defaults.font.family = "'DM Mono', monospace";
Chart.defaults.font.size = 11;
const GOLD = '#c8a96e', TEAL = '#7eb8a4', BLUE = '#8b9ed4';

// Volume chart
new Chart(document.getElementById('volumeChart').getContext('2d'), {{
  type: 'bar',
  data: {{
    labels: DATA.monthly.map(d => d.month),
    datasets: [
      {{ label: 'Acquisitions', data: DATA.monthly.map(d => d.Acquisition), backgroundColor: GOLD+'cc', borderColor: GOLD, borderWidth: 1 }},
      {{ label: 'Financing',    data: DATA.monthly.map(d => d.Financing),   backgroundColor: TEAL+'cc', borderColor: TEAL, borderWidth: 1 }},
      {{ label: 'Development',  data: DATA.monthly.map(d => d.Development), backgroundColor: BLUE+'cc', borderColor: BLUE, borderWidth: 1 }},
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: true,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{ backgroundColor: '#13161e', borderColor: '#252938', borderWidth: 1, titleColor: '#e8e6e0', bodyColor: '#7a7f94' }}
    }},
    scales: {{
      x: {{ stacked: true, grid: {{ color: '#252938', drawTicks: false }}, border: {{ color: '#252938' }}, ticks: {{ color: '#454a5e' }} }},
      y: {{ stacked: true, grid: {{ color: '#252938', drawTicks: false }}, border: {{ color: '#252938' }}, ticks: {{ stepSize: 5 }} }}
    }}
  }}
}});

// Buyers
const buyersMax = Math.max(...DATA.buyers.map(d => d.count));
const buyersList = document.getElementById('buyers-list');
DATA.buyers.forEach(d => {{
  buyersList.innerHTML += `<div class="bar-item"><div class="bar-label">${{d.name}}</div><div class="bar-track"><div class="bar-fill" style="width:${{(d.count/buyersMax*100).toFixed(0)}}%"></div></div><div class="bar-count">${{d.count}}</div></div>`;
}});

// Metros
const metroMax = Math.max(...DATA.metros.map(d => d.count));
const metroList = document.getElementById('metros-list');
DATA.metros.forEach(d => {{
  metroList.innerHTML += `<div class="bar-item"><div class="bar-label">${{d.metro}}</div><div class="bar-track"><div class="bar-fill teal" style="width:${{(d.count/metroMax*100).toFixed(0)}}%"></div></div><div class="bar-count">${{d.count}}</div></div>`;
}});

// Price dist
const priceMax = Math.max(...DATA.price_dist.map(d => d.count));
const priceBars = document.getElementById('price-bars');
DATA.price_dist.forEach(d => {{
  const h = Math.max(12, (d.count/priceMax*100).toFixed(0));
  priceBars.innerHTML += `<div class="price-col"><div class="price-n">${{d.count}}</div><div class="price-bar" style="height:${{h}}%"></div><div class="price-range">${{d.range}}</div></div>`;
}});

// States
const stateGrid = document.getElementById('state-grid');
DATA.states.forEach(d => {{
  stateGrid.innerHTML += `<div class="state-tile"><div class="state-abbr">${{d.state}}</div><div class="state-count">${{d.count}}</div><div class="state-label">deals</div></div>`;
}});

// Property type donut
const ptColors = [GOLD, TEAL, BLUE, '#e07b6a', '#a78bca', '#6ab4e0'];
new Chart(document.getElementById('ptChart').getContext('2d'), {{
  type: 'doughnut',
  data: {{
    labels: DATA.property_types.map(d => d.type),
    datasets: [{{ data: DATA.property_types.map(d => d.count), backgroundColor: ptColors.map(c => c+'cc'), borderColor: ptColors, borderWidth: 1, hoverOffset: 4 }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: true, cutout: '60%',
    plugins: {{
      legend: {{ position: 'right', labels: {{ boxWidth: 10, boxHeight: 10, padding: 12, color: '#7a7f94', font: {{ size: 11 }} }} }},
      tooltip: {{ backgroundColor: '#13161e', borderColor: '#252938', borderWidth: 1, titleColor: '#e8e6e0', bodyColor: '#7a7f94' }}
    }}
  }}
}});
</script>
</body>
</html>"""

    return html

# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("DB 읽는 중...")
    deals, dev = load_data()

    print("데이터 계산 중...")
    data = compute(deals, dev)

    print("index.html 생성 중...")
    html = generate(data)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    k = data["kpi"]
    print(f"\n✅ index.html 생성 완료!")
    print(f"   Deals: {k['total_deals']} | Dev: {k['dev_projects']} | Updated: {k['updated']}")
    print(f"\n다음 단계:")
    print(f"   git add index.html")
    print(f"   git commit -m \"Update dashboard\"")
    print(f"   git push")
