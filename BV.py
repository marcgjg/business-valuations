import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Business Valuation | GOMBA Finance",
    page_icon="📊",
    layout="wide",
)

# ── Global style ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Header */
.app-header {
    padding: 1.5rem 0 1rem 0;
    border-bottom: 1px solid #e8e8e4;
    margin-bottom: 1.5rem;
}
.app-header h1 {
    font-size: 1.6rem;
    font-weight: 600;
    color: #1a1a18;
    margin: 0;
    line-height: 1.2;
}
.app-header p {
    font-size: 0.875rem;
    color: #5a5a57;
    margin: 0.3rem 0 0 0;
}
.session-tag {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: #185FA5;
    background: #E6F1FB;
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 0.5rem;
}

/* Metric cards */
.metric-row {
    display: flex;
    gap: 12px;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}
.metric-card {
    flex: 1;
    min-width: 140px;
    background: #f5f5f3;
    border-radius: 10px;
    padding: 1rem 1.25rem;
}
.metric-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #9a9a96;
    margin-bottom: 4px;
}
.metric-value {
    font-size: 1.5rem;
    font-weight: 600;
    color: #1a1a18;
    font-family: 'DM Mono', monospace;
}
.metric-sub {
    font-size: 0.75rem;
    color: #5a5a57;
    margin-top: 2px;
}
.metric-card.highlight {
    background: #185FA5;
}
.metric-card.highlight .metric-label { color: #a8cef0; }
.metric-card.highlight .metric-value { color: #ffffff; }
.metric-card.highlight .metric-sub   { color: #c8dff5; }

/* Section headings */
.section-heading {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: #9a9a96;
    margin: 1.5rem 0 0.75rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #e8e8e4;
}

/* Toggle pill */
.stRadio > div {
    display: flex;
    gap: 8px;
    flex-direction: row !important;
}
.stRadio > div > label {
    background: #f0f0ee;
    border-radius: 20px;
    padding: 4px 16px;
    font-size: 0.82rem;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all 0.15s;
}
.stRadio > div > label:has(input:checked) {
    background: #185FA5;
    color: white;
    border-color: #185FA5;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 1px solid #e8e8e4;
}
.stTabs [data-baseweb="tab"] {
    font-size: 0.875rem;
    font-weight: 500;
    padding: 8px 20px;
    border-radius: 6px 6px 0 0;
    color: #5a5a57;
}
.stTabs [aria-selected="true"] {
    color: #185FA5 !important;
    border-bottom: 2px solid #185FA5 !important;
    background: transparent !important;
}

/* Sensitivity table */
.sens-table {
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
}

/* Info box */
.info-box {
    background: #E6F1FB;
    border-left: 3px solid #185FA5;
    border-radius: 0 8px 8px 0;
    padding: 0.75rem 1rem;
    font-size: 0.83rem;
    color: #1a3a5c;
    margin-bottom: 1rem;
}

/* Divider */
hr.light { border: none; border-top: 1px solid #e8e8e4; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
def fmt_currency(value, unit="€"):
    if abs(value) >= 1_000:
        return f"{unit}{value/1_000:,.1f}bn"
    return f"{unit}{value:,.1f}m"

def fmt_pct(value):
    return f"{value:.1f}%"

PLOTLY_LAYOUT = dict(
    font_family="DM Sans",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=40, b=40, l=10, r=10),
    colorway=["#185FA5", "#3B6D11", "#534AB7", "#854F0B", "#0F6E56"],
)

# ══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="app-header">
  <div class="session-tag">Session 13</div>
  <h1>Business Valuation</h1>
  <p>Estimate the value of a firm using discounted cash flow analysis and comparable company multiples.</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_dcf, tab_mult = st.tabs(["📈  DCF Valuation", "🔢  Comparable Multiples"])

# ─────────────────────────────────────────────────────────────────────────────
#  TAB 1 — DCF
# ─────────────────────────────────────────────────────────────────────────────
with tab_dcf:

    st.markdown('<p class="section-heading">Input mode</p>', unsafe_allow_html=True)
    mode = st.radio("", ["Simple", "Detailed"], horizontal=True, label_visibility="collapsed")

    st.markdown('<hr class="light">', unsafe_allow_html=True)

    # ── Inputs ────────────────────────────────────────────────────────────────
    if mode == "Simple":
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<p class="section-heading">Cash flows</p>', unsafe_allow_html=True)
            base_fcff   = st.slider("Base free cash flow (€m)", 10, 2000, 200, 10)
            growth_rate = st.slider("Near-term growth rate (%)", 0.0, 30.0, 8.0, 0.5)
            horizon     = st.slider("Forecast horizon (years)", 3, 15, 5, 1)
        with col2:
            st.markdown('<p class="section-heading">Discount & terminal</p>', unsafe_allow_html=True)
            wacc        = st.slider("WACC (%)", 3.0, 20.0, 9.0, 0.25)
            terminal_g  = st.slider("Terminal growth rate (%)", 0.0, 5.0, 2.0, 0.25)
        with col3:
            st.markdown('<p class="section-heading">Capital structure</p>', unsafe_allow_html=True)
            net_debt    = st.slider("Net debt (€m)", 0, 5000, 500, 50)
            shares      = st.slider("Shares outstanding (m)", 1, 500, 100, 1)

        # Build FCFFs
        fcffs = [base_fcff * (1 + growth_rate / 100) ** t for t in range(1, horizon + 1)]

    else:  # Detailed
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown('<p class="section-heading">Forecast cash flows (€m)</p>', unsafe_allow_html=True)
            horizon = st.slider("Forecast horizon (years)", 3, 10, 5, 1)

            df_input = pd.DataFrame({
                "Year": [f"Year {i}" for i in range(1, horizon + 1)],
                "Revenue": [500 + 50 * i for i in range(1, horizon + 1)],
                "EBIT margin (%)": [15.0] * horizon,
                "Tax rate (%)": [25.0] * horizon,
                "D&A (€m)": [30.0] * horizon,
                "Capex (€m)": [40.0] * horizon,
                "ΔNWC (€m)": [10.0] * horizon,
            })

            edited = st.data_editor(
                df_input,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Year": st.column_config.TextColumn("Year", disabled=True),
                    "Revenue": st.column_config.NumberColumn("Revenue (€m)", min_value=0, format="%.0f"),
                    "EBIT margin (%)": st.column_config.NumberColumn("EBIT margin %", min_value=0, max_value=100, format="%.1f"),
                    "Tax rate (%)": st.column_config.NumberColumn("Tax rate %", min_value=0, max_value=100, format="%.1f"),
                    "D&A (€m)": st.column_config.NumberColumn("D&A (€m)", min_value=0, format="%.1f"),
                    "Capex (€m)": st.column_config.NumberColumn("Capex (€m)", min_value=0, format="%.1f"),
                    "ΔNWC (€m)": st.column_config.NumberColumn("ΔNWC (€m)", format="%.1f"),
                }
            )

            # Compute FCFF from inputs
            fcffs = []
            for _, row in edited.iterrows():
                ebit  = row["Revenue"] * row["EBIT margin (%)"] / 100
                nopat = ebit * (1 - row["Tax rate (%)"] / 100)
                fcff  = nopat + row["D&A (€m)"] - row["Capex (€m)"] - row["ΔNWC (€m)"]
                fcffs.append(fcff)

        with col2:
            st.markdown('<p class="section-heading">Discount & terminal</p>', unsafe_allow_html=True)
            wacc       = st.slider("WACC (%)", 3.0, 20.0, 9.0, 0.25)
            terminal_g = st.slider("Terminal growth rate (%)", 0.0, 5.0, 2.0, 0.25)
            st.markdown('<p class="section-heading">Capital structure</p>', unsafe_allow_html=True)
            net_debt   = st.slider("Net debt (€m)", 0, 5000, 500, 50)
            shares     = st.slider("Shares outstanding (m)", 1, 500, 100, 1)

    # ── Calculations ──────────────────────────────────────────────────────────
    wacc_dec      = wacc / 100
    tg_dec        = terminal_g / 100

    if wacc_dec <= tg_dec:
        st.error("⚠️ WACC must be greater than the terminal growth rate for a finite valuation.")
        st.stop()

    # PV of forecast FCFFs
    pv_fcffs = [fcff / (1 + wacc_dec) ** t for t, fcff in enumerate(fcffs, 1)]
    pv_forecast = sum(pv_fcffs)

    # Terminal value (Gordon Growth)
    terminal_fcff = fcffs[-1] * (1 + tg_dec)
    terminal_value = terminal_fcff / (wacc_dec - tg_dec)
    pv_terminal   = terminal_value / (1 + wacc_dec) ** horizon

    enterprise_value = pv_forecast + pv_terminal
    equity_value     = enterprise_value - net_debt
    price_per_share  = equity_value / shares if shares > 0 else 0

    tv_pct = pv_terminal / enterprise_value * 100 if enterprise_value > 0 else 0

    # ── Metric cards ──────────────────────────────────────────────────────────
    st.markdown('<hr class="light">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-card highlight">
        <div class="metric-label">Equity value</div>
        <div class="metric-value">{fmt_currency(equity_value)}</div>
        <div class="metric-sub">Enterprise value − net debt</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Enterprise value</div>
        <div class="metric-value">{fmt_currency(enterprise_value)}</div>
        <div class="metric-sub">PV forecast + PV terminal</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Price per share</div>
        <div class="metric-value">€{price_per_share:,.2f}</div>
        <div class="metric-sub">Equity value ÷ shares</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Terminal value %</div>
        <div class="metric-value">{tv_pct:.0f}%</div>
        <div class="metric-sub">Share of enterprise value</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    chart_col1, chart_col2 = st.columns(2)

    # Chart 1 — Value breakdown waterfall
    with chart_col1:
        st.markdown('<p class="section-heading">Value breakdown</p>', unsafe_allow_html=True)

        years = [f"Yr {i}" for i in range(1, horizon + 1)]
        bar_colors = ["#185FA5"] * horizon + ["#3B6D11", "#e8e8e4", "#534AB7"]

        fig_wf = go.Figure()
        # Individual FCFFs
        fig_wf.add_trace(go.Bar(
            name="PV of forecast FCFFs",
            x=years,
            y=pv_fcffs,
            marker_color="#185FA5",
            text=[f"€{v:,.0f}m" for v in pv_fcffs],
            textposition="outside",
            textfont_size=10,
        ))
        fig_wf.add_trace(go.Bar(
            name="PV of terminal value",
            x=["Terminal"],
            y=[pv_terminal],
            marker_color="#3B6D11",
            text=[f"€{pv_terminal:,.0f}m"],
            textposition="outside",
            textfont_size=10,
        ))
        fig_wf.update_layout(
            **PLOTLY_LAYOUT,
            barmode="group",
            yaxis_title="€m",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            height=320,
        )
        fig_wf.update_xaxes(showgrid=False)
        fig_wf.update_yaxes(showgrid=True, gridcolor="#e8e8e4")
        st.plotly_chart(fig_wf, use_container_width=True)

    # Chart 2 — Pie: forecast vs terminal
    with chart_col2:
        st.markdown('<p class="section-heading">Forecast vs terminal value</p>', unsafe_allow_html=True)
        fig_pie = go.Figure(go.Pie(
            labels=["PV of forecast FCFFs", "PV of terminal value"],
            values=[pv_forecast, pv_terminal],
            hole=0.55,
            marker_colors=["#185FA5", "#3B6D11"],
            textinfo="label+percent",
            textfont_size=12,
            hovertemplate="%{label}<br>€%{value:,.0f}m<extra></extra>",
        ))
        fig_pie.update_layout(
            **PLOTLY_LAYOUT,
            showlegend=False,
            height=320,
            annotations=[dict(
                text=f"EV<br><b>{fmt_currency(enterprise_value)}</b>",
                x=0.5, y=0.5, font_size=13, showarrow=False,
                font_color="#1a1a18",
            )]
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── Sensitivity table ─────────────────────────────────────────────────────
    st.markdown('<p class="section-heading">Sensitivity analysis — Equity value per share (€)</p>', unsafe_allow_html=True)
    st.markdown('<div class="info-box">Each cell shows the implied share price for a given combination of WACC and terminal growth rate. Your current assumptions are highlighted.</div>', unsafe_allow_html=True)

    wacc_range = np.arange(max(wacc - 2.5, tg_dec * 100 + 0.5), wacc + 3.0, 0.5)
    tg_range   = np.arange(max(terminal_g - 1.5, 0.0), terminal_g + 2.0, 0.5)

    rows = []
    for tg in tg_range:
        row = []
        for w in wacc_range:
            if w / 100 <= tg / 100:
                row.append(np.nan)
                continue
            pv_f = sum([fcffs[t] / (1 + w / 100) ** (t + 1) for t in range(horizon)])
            tv   = fcffs[-1] * (1 + tg / 100) / (w / 100 - tg / 100)
            pv_t = tv / (1 + w / 100) ** horizon
            ev   = pv_f + pv_t
            eq   = ev - net_debt
            row.append(eq / shares if shares > 0 else 0)
        rows.append(row)

    sens_df = pd.DataFrame(
        rows,
        index=[f"g = {tg:.1f}%" for tg in tg_range],
        columns=[f"WACC = {w:.1f}%" for w in wacc_range],
    )

    # Highlight nearest cell to current assumptions
    def highlight_cell(val):
        return ""

    def style_sens(df):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        # Find closest row/col
        closest_row = min(range(len(tg_range)), key=lambda i: abs(tg_range[i] - terminal_g))
        closest_col = min(range(len(wacc_range)), key=lambda i: abs(wacc_range[i] - wacc))
        styles.iloc[closest_row, closest_col] = "background-color: #185FA5; color: white; font-weight: 600;"
        return styles

    styled = (
        sens_df.style
        .apply(style_sens, axis=None)
        .format(lambda v: f"€{v:,.1f}" if not np.isnan(v) else "—")
        .set_properties(**{"font-family": "DM Mono, monospace", "font-size": "0.8rem"})
        .background_gradient(cmap="Blues", axis=None, vmin=sens_df.min().min(), vmax=sens_df.max().max(), gmap=sens_df)
    )
    st.dataframe(styled, use_container_width=True)

    st.markdown('<hr class="light">', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
    <b>How to read this:</b> The DCF value equals the present value of all future free cash flows to the firm (FCFF),
    discounted at the WACC. The terminal value captures all cash flows beyond the forecast horizon using the Gordon Growth Model:
    TV = FCFF<sub>n+1</sub> / (WACC − g). Subtracting net debt from enterprise value gives equity value.
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 2 — COMPARABLE MULTIPLES
# ─────────────────────────────────────────────────────────────────────────────
with tab_mult:

    st.markdown('<div class="info-box">Enter your target company\'s financials and the observed trading multiples of comparable companies. The app estimates implied enterprise and equity values under each multiple.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 3])

    with col1:
        st.markdown('<p class="section-heading">Target company financials</p>', unsafe_allow_html=True)
        t_ebitda  = st.number_input("EBITDA (€m)", min_value=1.0, value=150.0, step=5.0)
        t_ebit    = st.number_input("EBIT (€m)", min_value=1.0, value=110.0, step=5.0)
        t_earnings= st.number_input("Net earnings (€m)", min_value=1.0, value=75.0, step=5.0)
        t_revenue = st.number_input("Revenue (€m)", min_value=1.0, value=800.0, step=10.0)
        t_debt    = st.number_input("Net debt (€m)", min_value=0.0, value=200.0, step=10.0)
        t_shares  = st.number_input("Shares outstanding (m)", min_value=1.0, value=80.0, step=1.0)

        st.markdown('<p class="section-heading">Comparable company multiples</p>', unsafe_allow_html=True)
        m_ev_ebitda = st.slider("EV / EBITDA (×)", 3.0, 30.0, 10.0, 0.5)
        m_ev_ebit   = st.slider("EV / EBIT (×)", 3.0, 40.0, 14.0, 0.5)
        m_pe        = st.slider("P / E (×)", 5.0, 50.0, 18.0, 0.5)
        m_ev_rev    = st.slider("EV / Revenue (×)", 0.5, 10.0, 2.0, 0.1)

    with col2:
        # Implied values
        results = {
            "EV/EBITDA": {
                "multiple": f"{m_ev_ebitda:.1f}×",
                "metric": f"€{t_ebitda:,.0f}m EBITDA",
                "ev": t_ebitda * m_ev_ebitda,
                "eq": t_ebitda * m_ev_ebitda - t_debt,
                "price": (t_ebitda * m_ev_ebitda - t_debt) / t_shares,
            },
            "EV/EBIT": {
                "multiple": f"{m_ev_ebit:.1f}×",
                "metric": f"€{t_ebit:,.0f}m EBIT",
                "ev": t_ebit * m_ev_ebit,
                "eq": t_ebit * m_ev_ebit - t_debt,
                "price": (t_ebit * m_ev_ebit - t_debt) / t_shares,
            },
            "P/E": {
                "multiple": f"{m_pe:.1f}×",
                "metric": f"€{t_earnings:,.0f}m earnings",
                "ev": t_earnings * m_pe + t_debt,
                "eq": t_earnings * m_pe,
                "price": t_earnings * m_pe / t_shares,
            },
            "EV/Revenue": {
                "multiple": f"{m_ev_rev:.1f}×",
                "metric": f"€{t_revenue:,.0f}m revenue",
                "ev": t_revenue * m_ev_rev,
                "eq": t_revenue * m_ev_rev - t_debt,
                "price": (t_revenue * m_ev_rev - t_debt) / t_shares,
            },
        }

        # Summary metrics
        prices = [v["price"] for v in results.values()]
        evs    = [v["ev"] for v in results.values()]

        st.markdown('<p class="section-heading">Implied valuation range</p>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="metric-row">
          <div class="metric-card highlight">
            <div class="metric-label">Median share price</div>
            <div class="metric-value">€{np.median(prices):,.2f}</div>
            <div class="metric-sub">Across all multiples</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Price range</div>
            <div class="metric-value">€{min(prices):,.1f}–{max(prices):,.1f}</div>
            <div class="metric-sub">Min to max</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Median EV</div>
            <div class="metric-value">{fmt_currency(np.median(evs))}</div>
            <div class="metric-sub">Across all multiples</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Chart — implied share prices
        st.markdown('<p class="section-heading">Implied share price by multiple</p>', unsafe_allow_html=True)

        methods = list(results.keys())
        implied_prices = [results[m]["price"] for m in methods]
        colors = ["#185FA5", "#3B6D11", "#534AB7", "#854F0B"]

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=methods,
            y=implied_prices,
            marker_color=colors,
            text=[f"€{p:,.2f}" for p in implied_prices],
            textposition="outside",
            textfont_size=12,
            width=0.5,
        ))
        # Median line
        fig_bar.add_hline(
            y=np.median(implied_prices),
            line_dash="dot",
            line_color="#9a9a96",
            annotation_text=f"Median: €{np.median(implied_prices):,.2f}",
            annotation_position="top right",
            annotation_font_size=11,
        )
        fig_bar.update_layout(
            **PLOTLY_LAYOUT,
            yaxis_title="Implied share price (€)",
            showlegend=False,
            height=300,
        )
        fig_bar.update_xaxes(showgrid=False)
        fig_bar.update_yaxes(showgrid=True, gridcolor="#e8e8e4")
        st.plotly_chart(fig_bar, use_container_width=True)

        # Detail table
        st.markdown('<p class="section-heading">Detailed results</p>', unsafe_allow_html=True)
        detail_df = pd.DataFrame([{
            "Method": m,
            "Multiple applied": results[m]["multiple"],
            "Based on": results[m]["metric"],
            "Implied EV (€m)": f"€{results[m]['ev']:,.0f}m",
            "Implied equity (€m)": f"€{results[m]['eq']:,.0f}m",
            "Implied price (€)": f"€{results[m]['price']:,.2f}",
        } for m in methods])

        st.dataframe(detail_df, hide_index=True, use_container_width=True)

        st.markdown('<hr class="light">', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
        <b>How to read this:</b> Each multiple is applied to the target's corresponding financial metric to derive an implied
        enterprise value (EV). Subtracting net debt gives implied equity value; dividing by shares outstanding gives the
        implied share price. The median across methods provides a central estimate; the range reflects valuation uncertainty.
        </div>
        """, unsafe_allow_html=True)
