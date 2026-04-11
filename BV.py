import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Business Valuation",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Helpers ────────────────────────────────────────────────────────────────────
def fmt_currency(value):
    if abs(value) >= 1_000:
        return f"€{value/1_000:,.1f}bn"
    return f"€{value:,.1f}m"

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">📊 Business Valuation</h1>', unsafe_allow_html=True)

# ── About expander ─────────────────────────────────────────────────────────────
with st.expander("ℹ️ About this tool", expanded=False):
    st.markdown("""
    This tool estimates the value of a firm using two widely used methods:
    - **DCF Valuation**: discounts future free cash flows (FCF) to the firm at the WACC to derive enterprise value,
      then subtracts net debt to obtain equity value. Revenue, EBIT margin, tax rate, and D&A, Capex and NWC
      as a percentage of revenue are entered year by year. ΔNWC is computed automatically as the change in NWC
      from the prior year.
    - **Comparable Multiples**: applies observed trading multiples (EV/EBITDA, EV/EBIT, P/E, EV/Revenue)
      from comparable companies to the target firm's financials to derive implied valuations.

    **Key formulas:**
    - FCF = NOPAT + D&A − Capex − ΔNWC, where NOPAT = EBIT × (1 − tax rate)
    - Terminal value (Gordon Growth): TV = FCF<sub>H+1</sub> / (WACC − g)
    - Enterprise value = PV of forecast FCFs + PV of terminal value
    - Equity value = Enterprise value − Net debt
    """, unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_dcf, tab_mult = st.tabs(["📈  DCF Valuation", "🔢  Comparable Multiples"])

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — DCF
# ══════════════════════════════════════════════════════════════════════════════
with tab_dcf:

    col_inputs, col_charts = st.columns([1, 2])

    with col_inputs:
        st.subheader("Discount & Terminal")
        wacc = st.slider("WACC (%):", 3.0, 20.0, 9.0, 0.25)
        terminal_g = st.slider("Terminal growth rate, g (%):", 0.0, 5.0, 2.0, 0.25)
        rev_year0 = st.slider("Year 0 revenue (€m):", 100, 5000, 500, 50)

        st.subheader("Capital Structure")
        net_debt = st.slider("Net debt (€m):", 0, 5000, 500, 50)
        shares   = st.slider("Shares outstanding (m):", 1, 500, 100, 1)

        st.subheader("Forecast Horizon")
        horizon = st.slider("Forecast horizon, H (years):", 3, 10, 5, 1)

    # ── Forecast assumptions table (full width) ────────────────────────────────
    st.subheader("Forecast Assumptions")

    st.markdown(
        "Set the annual revenue growth rate and other assumptions for each year below. "
        "Revenues are derived automatically from Year 0 revenue × cumulative growth rates. "
        "D&A, Capex, and NWC are expressed as a percentage of that year's revenue. "
        "ΔNWC is computed automatically as the change in NWC from the prior year."
    )

    df_input = pd.DataFrame({
        "Year":            [f"Year {i}" for i in range(1, horizon + 1)],
        "Rev growth (%)":  [8.0] * horizon,
        "EBIT margin (%)": [15.0] * horizon,
        "Tax rate (%)":    [25.0] * horizon,
        "D&A (% rev)":     [4.0]  * horizon,
        "Capex (% rev)":   [5.0]  * horizon,
        "NWC (% rev)":     [8.0]  * horizon,
    })

    edited = st.data_editor(
        df_input,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Year":            st.column_config.TextColumn("Year", disabled=True),
            "Rev growth (%)":  st.column_config.NumberColumn("Rev growth %",    min_value=-100, max_value=100, format="%.1f"),
            "EBIT margin (%)": st.column_config.NumberColumn("EBIT margin %",   min_value=0,    max_value=100, format="%.1f"),
            "Tax rate (%)":    st.column_config.NumberColumn("Tax rate %",       min_value=0,    max_value=100, format="%.1f"),
            "D&A (% rev)":     st.column_config.NumberColumn("D&A % of rev",    min_value=0,    max_value=100, format="%.1f"),
            "Capex (% rev)":   st.column_config.NumberColumn("Capex % of rev",  min_value=0,    max_value=100, format="%.1f"),
            "NWC (% rev)":     st.column_config.NumberColumn("NWC % of rev",    min_value=0,    max_value=100, format="%.1f"),
        },
    )

    # Cascade revenues from Year 0
    revenues = [rev_year0]
    for i in range(horizon):
        revenues.append(revenues[i] * (1 + edited.iloc[i]["Rev growth (%)"] / 100))
    revenues = revenues[1:]  # Years 1–H only

    # Compute FCFs
    fcfs       = []
    da_vals    = []
    cap_vals   = []
    nwc_vals   = []
    dnwc_vals  = []
    nopat_vals = []
    prev_nwc   = rev_year0 * edited.iloc[0]["NWC (% rev)"] / 100
    for i in range(horizon):
        row   = edited.iloc[i]
        rev   = revenues[i]
        ebit  = rev * row["EBIT margin (%)"] / 100
        nopat = ebit * (1 - row["Tax rate (%)"] / 100)
        da    = rev * row["D&A (% rev)"]   / 100
        capex = rev * row["Capex (% rev)"] / 100
        nwc   = rev * row["NWC (% rev)"]   / 100
        d_nwc = nwc - prev_nwc
        fcf   = nopat + da - capex - d_nwc
        fcfs.append(fcf)
        da_vals.append(da)
        cap_vals.append(capex)
        nwc_vals.append(nwc)
        dnwc_vals.append(d_nwc)
        nopat_vals.append(nopat)
        prev_nwc = nwc

    # Read-only computed table
    st.subheader("Computed Cash Flows (€m)")
    df_computed = pd.DataFrame({
        "Year":    [f"Year {i}" for i in range(1, horizon + 1)],
        "Revenue": [round(r, 1) for r in revenues],
        "NOPAT":   [round(v, 1) for v in nopat_vals],
        "+ D&A":   [round(v, 1) for v in da_vals],
        "− Capex": [round(v, 1) for v in cap_vals],
        "− ΔNWC":  [round(v, 1) for v in dnwc_vals],
        "= FCF":   [round(v, 1) for v in fcfs],
    })
    st.dataframe(df_computed, hide_index=True, use_container_width=True)

    # ── Calculations ───────────────────────────────────────────────────────────
    wacc_dec = wacc / 100
    tg_dec   = terminal_g / 100

    if wacc_dec <= tg_dec:
        st.error("⚠️ WACC must be greater than the terminal growth rate for a finite valuation.")
        st.stop()

    pv_fcfs     = [fcf / (1 + wacc_dec) ** t for t, fcf in enumerate(fcfs, 1)]
    pv_forecast = sum(pv_fcfs)

    # Terminal value: TV = FCF_{H+1} / (WACC - g)
    terminal_fcf   = fcfs[-1] * (1 + tg_dec)
    terminal_value = terminal_fcf / (wacc_dec - tg_dec)
    pv_terminal    = terminal_value / (1 + wacc_dec) ** horizon

    enterprise_value = pv_forecast + pv_terminal
    equity_value     = enterprise_value - net_debt
    price_per_share  = equity_value / shares if shares > 0 else 0
    tv_pct           = pv_terminal / enterprise_value * 100 if enterprise_value > 0 else 0

    # ── Summary metrics ────────────────────────────────────────────────────────
    with col_inputs:
        st.subheader("Valuation Summary")
        st.metric("Enterprise value", fmt_currency(enterprise_value))
        st.metric("Equity value",     fmt_currency(equity_value))
        st.metric("Price per share",  f"€{price_per_share:,.2f}")
        st.metric("Terminal value %", f"{tv_pct:.1f}%")

    # ── Charts ─────────────────────────────────────────────────────────────────
    with col_charts:
        st.subheader("Value Breakdown")

        years_labels = [f"Yr {i}" for i in range(1, horizon + 1)] + ["Terminal (PV)"]
        bar_values   = pv_fcfs + [pv_terminal]
        bar_colors   = ["#1E3A8A"] * horizon + ["#2ca02c"]

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=years_labels,
            y=bar_values,
            marker_color=bar_colors,
            text=[f"€{v:,.0f}m" for v in bar_values],
            textposition="outside",
            textfont=dict(size=14),
        ))
        fig_bar.update_layout(
            title=dict(text="PV of FCFs and Terminal Value", font=dict(size=22)),
            yaxis_title="€m",
            height=380,
            font=dict(size=16),
            margin=dict(l=60, r=40, t=60, b=40),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig_bar.update_xaxes(showgrid=False, tickfont=dict(size=14))
        fig_bar.update_yaxes(showgrid=True, gridcolor="#e8e8e4", tickfont=dict(size=14))
        st.plotly_chart(fig_bar, use_container_width=True)

        fig_pie = go.Figure(go.Pie(
            labels=["PV of forecast FCFs", "PV of terminal value"],
            values=[pv_forecast, pv_terminal],
            hole=0.55,
            marker_colors=["#1E3A8A", "#2ca02c"],
            textinfo="label+percent",
            textfont=dict(size=14),
            hovertemplate="%{label}<br>€%{value:,.0f}m<extra></extra>",
        ))
        fig_pie.update_layout(
            title=dict(text="Forecast vs Terminal Value", font=dict(size=22)),
            height=380,
            font=dict(size=16),
            margin=dict(l=40, r=40, t=60, b=40),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            annotations=[dict(
                text=f"EV<br><b>{fmt_currency(enterprise_value)}</b>",
                x=0.5, y=0.5, font=dict(size=15), showarrow=False,
            )],
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── Sensitivity table ──────────────────────────────────────────────────────
    st.subheader("Sensitivity Analysis — Equity Value per Share (€)")
    st.markdown("Each cell shows the implied share price for a given combination of WACC and terminal "
                "growth rate g. The equity value per share for your current assumptions is **highlighted in red**.", unsafe_allow_html=True)

    wacc_range = np.arange(max(wacc - 2.5, tg_dec * 100 + 0.5), wacc + 3.0, 0.5)
    tg_range   = np.arange(max(terminal_g - 1.5, 0.0), terminal_g + 2.0, 0.5)

    rows = []
    for tg in tg_range:
        row = []
        for w in wacc_range:
            if w / 100 <= tg / 100:
                row.append(np.nan)
                continue
            pv_f = sum([fcfs[t] / (1 + w / 100) ** (t + 1) for t in range(horizon)])
            tv   = fcfs[-1] * (1 + tg / 100) / (w / 100 - tg / 100)
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

    vmin = sens_df.min().min()
    vmax = sens_df.max().max()
    closest_row = min(range(len(tg_range)),   key=lambda i: abs(tg_range[i]  - terminal_g))
    closest_col = min(range(len(wacc_range)), key=lambda i: abs(wacc_range[i] - wacc))

    def combined_style(df):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        for i in range(len(df.index)):
            for j in range(len(df.columns)):
                if i == closest_row and j == closest_col:
                    styles.iloc[i, j] = "background-color: #d62728; color: white; font-weight: 600;"
                else:
                    val = df.iloc[i, j]
                    if np.isnan(val):
                        styles.iloc[i, j] = "background-color: #f5f5f3; color: #9a9a96;"
                    else:
                        t = (val - vmin) / (vmax - vmin) if vmax > vmin else 0.5
                        r = int(232 - t * (232 - 30))
                        g = int(241 - t * (241 - 58))
                        b = int(251 - t * (251 - 138))
                        text = "white" if t > 0.6 else "#1a1a18"
                        styles.iloc[i, j] = f"background-color: rgb({r},{g},{b}); color: {text};"
        return styles

    styled = (
        sens_df.style
        .apply(combined_style, axis=None)
        .format(lambda v: f"€{v:,.1f}" if not np.isnan(v) else "—")
        .set_properties(**{"font-size": "0.85rem"})
    )
    st.dataframe(styled, use_container_width=True)

    st.markdown(
        "**How to read this:** Enterprise value = PV of forecast FCFs + PV of terminal value, "
        "where TV = FCF<sub>H+1</sub> / (WACC − g). Subtracting net debt gives equity value; "
        "dividing by shares outstanding gives the implied share price.",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — COMPARABLE MULTIPLES
# ══════════════════════════════════════════════════════════════════════════════
with tab_mult:

    st.markdown("Enter your target company's financials and the observed trading multiples of "
                "comparable companies. The app estimates implied enterprise and equity values under each multiple.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Target Company Financials")
        t_ebitda   = st.number_input("EBITDA (€m):",           min_value=1.0, value=150.0, step=5.0)
        t_ebit     = st.number_input("EBIT (€m):",             min_value=1.0, value=110.0, step=5.0)
        t_earnings = st.number_input("Net earnings (€m):",     min_value=1.0, value=75.0,  step=5.0)
        t_revenue  = st.number_input("Revenue (€m):",          min_value=1.0, value=800.0, step=10.0)
        t_debt     = st.number_input("Net debt (€m):",         min_value=0.0, value=200.0, step=10.0)
        t_shares   = st.number_input("Shares outstanding (m):", min_value=1.0, value=80.0,  step=1.0)

        st.subheader("Comparable Company Multiples")
        m_ev_ebitda = st.slider("EV / EBITDA (×):", 3.0, 30.0, 10.0, 0.5)
        m_ev_ebit   = st.slider("EV / EBIT (×):",   3.0, 40.0, 14.0, 0.5)
        m_pe        = st.slider("P / E (×):",        5.0, 50.0, 18.0, 0.5)
        m_ev_rev    = st.slider("EV / Revenue (×):", 0.5, 10.0,  2.0, 0.1)

    with col2:
        results = {
            "EV/EBITDA": {
                "multiple": f"{m_ev_ebitda:.1f}×",
                "metric":   f"€{t_ebitda:,.0f}m EBITDA",
                "ev":       t_ebitda * m_ev_ebitda,
                "eq":       t_ebitda * m_ev_ebitda - t_debt,
                "price":    (t_ebitda * m_ev_ebitda - t_debt) / t_shares,
            },
            "EV/EBIT": {
                "multiple": f"{m_ev_ebit:.1f}×",
                "metric":   f"€{t_ebit:,.0f}m EBIT",
                "ev":       t_ebit * m_ev_ebit,
                "eq":       t_ebit * m_ev_ebit - t_debt,
                "price":    (t_ebit * m_ev_ebit - t_debt) / t_shares,
            },
            "P/E": {
                "multiple": f"{m_pe:.1f}×",
                "metric":   f"€{t_earnings:,.0f}m earnings",
                "ev":       t_earnings * m_pe + t_debt,
                "eq":       t_earnings * m_pe,
                "price":    t_earnings * m_pe / t_shares,
            },
            "EV/Revenue": {
                "multiple": f"{m_ev_rev:.1f}×",
                "metric":   f"€{t_revenue:,.0f}m revenue",
                "ev":       t_revenue * m_ev_rev,
                "eq":       t_revenue * m_ev_rev - t_debt,
                "price":    (t_revenue * m_ev_rev - t_debt) / t_shares,
            },
        }

        prices = [v["price"] for v in results.values()]
        evs    = [v["ev"]    for v in results.values()]

        st.subheader("Valuation Summary")
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric("Median share price", f"€{np.median(prices):,.2f}")
        with m_col2:
            st.metric("Price range", f"€{min(prices):,.1f} – €{max(prices):,.1f}")
        with m_col3:
            st.metric("Median EV", fmt_currency(np.median(evs)))

        st.subheader("Implied Share Price by Multiple")
        methods        = list(results.keys())
        implied_prices = [results[m]["price"] for m in methods]
        bar_colors_m   = ["#1E3A8A", "#2ca02c", "#9467bd", "#d62728"]

        fig_mult = go.Figure()
        fig_mult.add_trace(go.Bar(
            x=methods,
            y=implied_prices,
            marker_color=bar_colors_m,
            text=[f"€{p:,.2f}" for p in implied_prices],
            textposition="outside",
            textfont=dict(size=14),
            width=0.5,
        ))
        fig_mult.add_hline(
            y=np.median(implied_prices),
            line_dash="dot",
            line_color="#888",
            annotation_text=f"Median: €{np.median(implied_prices):,.2f}",
            annotation_position="top right",
            annotation_font_size=13,
        )
        fig_mult.update_layout(
            title=dict(text="Implied Share Price by Multiple", font=dict(size=22)),
            yaxis_title="Implied share price (€)",
            height=380,
            font=dict(size=16),
            margin=dict(l=60, r=40, t=60, b=40),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig_mult.update_xaxes(showgrid=False, tickfont=dict(size=14))
        fig_mult.update_yaxes(showgrid=True, gridcolor="#e8e8e4", tickfont=dict(size=14))
        st.plotly_chart(fig_mult, use_container_width=True)

        st.subheader("Detailed Results")
        detail_df = pd.DataFrame([{
            "Method":              m,
            "Multiple applied":    results[m]["multiple"],
            "Based on":            results[m]["metric"],
            "Implied EV (€m)":     f"€{results[m]['ev']:,.0f}m",
            "Implied equity (€m)": f"€{results[m]['eq']:,.0f}m",
            "Implied price (€)":   f"€{results[m]['price']:,.2f}",
        } for m in methods])
        st.dataframe(detail_df, hide_index=True, use_container_width=True)

        st.markdown(
            "**How to read this:** Each multiple is applied to the target's corresponding financial "
            "metric to derive an implied enterprise value. Subtracting net debt gives implied equity "
            "value; dividing by shares outstanding gives the implied share price. The median across "
            "methods provides a central estimate; the range reflects valuation uncertainty."
        )

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="text-align:center; color:#888; font-size:0.8rem; margin-top:2rem;">'
    'Business Valuation | Developed by Prof. Marc Goergen with the help of Claude'
    '</div>',
    unsafe_allow_html=True,
)
