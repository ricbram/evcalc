from __future__ import annotations

import json
from dataclasses import asdict

import altair as alt
import pandas as pd
import streamlit as st

from ev_calc_core_v2 import (
    DEFAULT_EV,
    DEFAULT_GLOBAL,
    DEFAULT_ICE,
    GlobalInputs,
    VehicleInputs,
    compute_ev,
    compute_ice,
    payback_analysis,
    scenario_payload,
    summary_table,
)

st.set_page_config(page_title="EV cost calculator", page_icon="⚡", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1200px;}
    .hero {
        padding: 1.2rem 1.4rem;
        border: 1px solid rgba(49, 51, 63, 0.15);
        border-radius: 18px;
        background: linear-gradient(135deg, rgba(12,166,120,0.10), rgba(91,123,250,0.08));
        margin-bottom: 1rem;
    }
    .small-note {color: #6b7280; font-size: 0.92rem;}
    div[data-testid="stMetric"] {
        border: 1px solid rgba(49, 51, 63, 0.12);
        padding: 0.8rem 1rem;
        border-radius: 16px;
        background: rgba(255,255,255,0.7);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "ice_defaults" not in st.session_state:
    st.session_state.ice_defaults = asdict(DEFAULT_ICE)
    st.session_state.ev_defaults = asdict(DEFAULT_EV)
    st.session_state.global_defaults = asdict(DEFAULT_GLOBAL)

st.markdown(
    """
    <div class="hero">
      <h1 style="margin-bottom:0.3rem;">EV cost calculator</h1>
      <div>Compare total cost of ownership for an ICE vehicle and an EV using the logic from your spreadsheet.</div>
      <div class="small-note" style="margin-top:0.5rem;">This version is designed as a cleaner client-facing web app, with scenario controls, charts, and export options.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Scenario settings")
    if st.button("Reset to spreadsheet defaults", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    finance_rate = st.number_input(
        "Finance rate (%)",
        min_value=0.0,
        value=DEFAULT_GLOBAL.finance_rate * 100,
        step=0.5,
        help="Used for annualising purchase costs and discounted payback.",
    ) / 100
    include_emissions_cost = st.toggle(
        "Include emissions cost",
        value=DEFAULT_GLOBAL.include_emissions_cost,
        help="Applies the carbon price to vehicle and electricity emissions.",
    )
    emissions_price = st.number_input(
        "Emissions price ($/t)",
        min_value=0.0,
        value=float(DEFAULT_GLOBAL.emissions_price_per_tonne),
        step=10.0,
    )
    st.caption("Tip: for a public app, you can later hide advanced inputs and show them behind an 'assumptions' panel.")

    g = GlobalInputs(
        finance_rate=finance_rate,
        include_emissions_cost=include_emissions_cost,
        emissions_price_per_tonne=emissions_price,
    )

left, right = st.columns(2)

with left:
    st.subheader("Petrol / ICE vehicle")
    ice = VehicleInputs(
        name=st.text_input("Vehicle name", value=DEFAULT_ICE.name, key="ice_name"),
        annual_mileage_km=st.number_input("Annual mileage (km/year)", min_value=0.0, value=float(DEFAULT_ICE.annual_mileage_km), step=1000.0, key="ice_mileage"),
        life_years=int(st.number_input("Life (years)", min_value=1.0, value=float(DEFAULT_ICE.life_years), step=1.0, key="ice_life")),
        purchase_cost=st.number_input("Purchase cost ($)", min_value=0.0, value=float(DEFAULT_ICE.purchase_cost), step=1000.0, key="ice_purchase"),
        purchase_rebate=st.number_input("Rebate or grant ($)", min_value=0.0, value=float(DEFAULT_ICE.purchase_rebate), step=500.0, key="ice_rebate"),
        sale_value_pct=st.slider("Sale value at end of life (%)", min_value=0.0, max_value=50.0, value=float(DEFAULT_ICE.sale_value_pct * 100), step=1.0, key="ice_sale") / 100,
        annual_maintenance_cost=st.number_input("Maintenance ($/year)", min_value=0.0, value=float(DEFAULT_ICE.annual_maintenance_cost), step=100.0, key="ice_maint"),
        annual_insurance_registration_cost=st.number_input("Insurance + registration ($/year)", min_value=0.0, value=float(DEFAULT_ICE.annual_insurance_registration_cost), step=100.0, key="ice_rego"),
        fuel_cost_per_litre=st.number_input("Fuel cost ($/litre)", min_value=0.0, value=float(DEFAULT_ICE.fuel_cost_per_litre), step=0.05, key="ice_fuel_cost"),
        fuel_efficiency_km_per_litre=st.number_input("Fuel efficiency (km/litre)", min_value=0.0, value=float(DEFAULT_ICE.fuel_efficiency_km_per_litre), step=0.5, key="ice_eff"),
        road_user_charges_per_1000km=st.number_input("Road user charges ($/1000 km)", min_value=0.0, value=float(DEFAULT_ICE.road_user_charges_per_1000km), step=5.0, key="ice_ruc"),
        emissions_rate_g_per_km=st.number_input("Vehicle emissions (g/km)", min_value=0.0, value=float(DEFAULT_ICE.emissions_rate_g_per_km), step=5.0, key="ice_emissions"),
    )

with right:
    st.subheader("Electric vehicle")
    ev = VehicleInputs(
        name=st.text_input("Vehicle name ", value=DEFAULT_EV.name, key="ev_name"),
        annual_mileage_km=st.number_input("Annual mileage (km/year) ", min_value=0.0, value=float(DEFAULT_EV.annual_mileage_km), step=1000.0, key="ev_mileage"),
        life_years=int(st.number_input("Life (years) ", min_value=1.0, value=float(DEFAULT_EV.life_years), step=1.0, key="ev_life")),
        purchase_cost=st.number_input("Purchase cost ($) ", min_value=0.0, value=float(DEFAULT_EV.purchase_cost), step=1000.0, key="ev_purchase"),
        purchase_rebate=st.number_input("Rebate or grant ($) ", min_value=0.0, value=float(DEFAULT_EV.purchase_rebate), step=500.0, key="ev_rebate"),
        sale_value_pct=st.slider("Sale value at end of life (%) ", min_value=0.0, max_value=50.0, value=float(DEFAULT_EV.sale_value_pct * 100), step=1.0, key="ev_sale") / 100,
        annual_maintenance_cost=st.number_input("Maintenance ($/year) ", min_value=0.0, value=float(DEFAULT_EV.annual_maintenance_cost), step=100.0, key="ev_maint"),
        annual_insurance_registration_cost=st.number_input("Insurance + registration ($/year) ", min_value=0.0, value=float(DEFAULT_EV.annual_insurance_registration_cost), step=100.0, key="ev_rego"),
        electricity_cost_per_kwh=st.number_input("Electricity cost ($/kWh)", min_value=0.0, value=float(DEFAULT_EV.electricity_cost_per_kwh), step=0.01, key="ev_power_cost"),
        ev_efficiency_wh_per_km=st.number_input("EV efficiency (Wh/km)", min_value=0.0, value=float(DEFAULT_EV.ev_efficiency_wh_per_km), step=1.0, key="ev_eff"),
        road_user_charges_per_1000km=st.number_input("Road user charges ($/1000 km) ", min_value=0.0, value=float(DEFAULT_EV.road_user_charges_per_1000km), step=5.0, key="ev_ruc"),
        grid_emissions_g_per_kwh=st.number_input("Grid emissions (g/kWh)", min_value=0.0, value=float(DEFAULT_EV.grid_emissions_g_per_kwh), step=5.0, key="ev_grid_emissions"),
    )

ice_results = compute_ice(ice, g)
ev_results = compute_ev(ev, g)
payback = payback_analysis(ice, ev, g)
summary = summary_table(ice, ev, g)
annual_saving = ice_results["total_annual_cost"] - ev_results["total_annual_cost"]
upfront_gap = ev_results["net_purchase_cost"] - ice_results["net_purchase_cost"]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Annual saving from EV", f"${annual_saving:,.0f}")
k2.metric("Upfront price difference", f"${upfront_gap:,.0f}")
k3.metric("EV cost per km", f"${ev_results['total_cost_per_km']:.3f}")
k4.metric(
    "Discounted payback",
    "Never" if payback["payback_discounted"] is None else f"{payback['payback_discounted']:.1f} years",
)

summary_tab, charts_tab, cashflow_tab, export_tab = st.tabs(["Summary", "Charts", "Annual cashflows", "Export"])

with summary_tab:
    left_summary, right_summary = st.columns([1.2, 1])
    with left_summary:
        st.subheader("Cost comparison")
        formatted_summary = summary.copy()
        value_cols = [c for c in formatted_summary.columns if c != "Metric"]
        st.dataframe(
            formatted_summary.style.format({col: "{:,.2f}" for col in value_cols}),
            use_container_width=True,
            hide_index=True,
        )
    with right_summary:
        st.subheader("Headline takeaways")
        disc = payback["payback_discounted"]
        undisc = payback["payback_undiscounted"]
        st.write(f"**{ev.name} annual cost:** ${ev_results['total_annual_cost']:,.0f} per year")
        st.write(f"**{ice.name} annual cost:** ${ice_results['total_annual_cost']:,.0f} per year")
        if annual_saving >= 0:
            st.success(f"The EV is cheaper to run by about ${annual_saving:,.0f} per year.")
        else:
            st.warning(f"The EV is currently dearer to run by about ${-annual_saving:,.0f} per year.")
        st.write(f"**Undiscounted payback:** {'Never' if undisc is None else f'{undisc:.1f} years'}")
        st.write(f"**Discounted payback:** {'Never' if disc is None else f'{disc:.1f} years'}")
        st.caption("Discounted payback uses the finance rate in the sidebar, matching the spreadsheet's treatment of time value of money.")

    breakdown_rows = [
        ("Annualised purchase", ice_results["annual_purchase_cost"], ev_results["annual_purchase_cost"]),
        ("Fuel / charging", ice_results["annual_fuel_or_charging_cost"], ev_results["annual_fuel_or_charging_cost"]),
        ("Road user charges", ice_results["annual_ruc_cost"], ev_results["annual_ruc_cost"]),
        ("Maintenance + rego", ice_results["annual_maintenance_and_rego"], ev_results["annual_maintenance_and_rego"]),
        ("Emissions", ice_results["annual_emissions_cost"], ev_results["annual_emissions_cost"]),
    ]
    breakdown_df = pd.DataFrame(breakdown_rows, columns=["Category", ice.name, ev.name])
    chart_df = breakdown_df.melt("Category", var_name="Vehicle", value_name="Annual cost")
    bar_chart = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Category:N", sort=None),
            y=alt.Y("Annual cost:Q", title="Annual cost ($)"),
            color=alt.Color("Vehicle:N"),
            xOffset="Vehicle:N",
            tooltip=["Category", "Vehicle", alt.Tooltip("Annual cost:Q", format=",.0f")],
        )
        .properties(height=320)
    )
    st.altair_chart(bar_chart, use_container_width=True)

with charts_tab:
    st.subheader("Payback profile")
    payback_df = payback["table"][["Year", "Cumulative undisc.", "Cumulative disc."]].melt(
        "Year", var_name="Series", value_name="Value"
    )
    payback_chart = (
        alt.Chart(payback_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("Year:Q", scale=alt.Scale(nice=False)),
            y=alt.Y("Value:Q", title="Cumulative savings ($)"),
            color="Series:N",
            tooltip=[alt.Tooltip("Year:Q", format=".0f"), "Series", alt.Tooltip("Value:Q", format=",.0f")],
        )
        .properties(height=380)
    )
    zero_rule = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule().encode(y="y:Q")
    st.altair_chart(payback_chart + zero_rule, use_container_width=True)

    emissions_df = pd.DataFrame(
        {
            "Vehicle": [ice.name, ev.name],
            "Annual emissions (t)": [ice_results["annual_emissions_tonnes"], ev_results["annual_emissions_tonnes"]],
        }
    )
    st.subheader("Annual emissions")
    emissions_chart = (
        alt.Chart(emissions_df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x="Vehicle:N",
            y=alt.Y("Annual emissions (t):Q", title="Tonnes CO2e per year"),
            tooltip=["Vehicle", alt.Tooltip("Annual emissions (t):Q", format=",.3f")],
        )
        .properties(height=280)
    )
    st.altair_chart(emissions_chart, use_container_width=True)

with cashflow_tab:
    st.subheader("Annual cashflow difference: ICE minus EV")
    cashflow_df = payback["table"][
        [
            "Year",
            "Purchase cost after rebate",
            "Sale value",
            "Fuel / charging",
            "Road user charges",
            "Maintenance + rego",
            "Emissions",
            "Total",
            "Discounted total",
            "Cumulative undisc.",
            "Cumulative disc.",
        ]
    ]
    st.dataframe(
        cashflow_df.style.format({col: "{:,.2f}" for col in cashflow_df.columns if col != "Year"}),
        use_container_width=True,
        hide_index=True,
    )

with export_tab:
    st.subheader("Download scenario")
    payload = scenario_payload(ice, ev, g)
    payload_json = json.dumps(payload, indent=2)
    st.download_button(
        "Download scenario JSON",
        data=payload_json,
        file_name="ev_cost_scenario.json",
        mime="application/json",
    )
    st.download_button(
        "Download annual cashflow CSV",
        data=payback["table"].to_csv(index=False),
        file_name="ev_cost_cashflows.csv",
        mime="text/csv",
    )
    with st.expander("Preview JSON"):
        st.code(payload_json, language="json")
