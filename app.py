from __future__ import annotations
import json
from dataclasses import asdict
import pandas as pd
import streamlit as st
from ev_calc_core_v2 import (
    DEFAULT_EV, DEFAULT_GLOBAL, DEFAULT_ICE,
    GlobalInputs, VehicleInputs,
    compute_ev, compute_ice, payback_analysis, summary_table, scenario_payload,
)

st.set_page_config(page_title='EV cost calculator', page_icon='⚡', layout='wide')
st.title('EV cost calculator')
st.caption('Simple deployment-safe version')

with st.sidebar:
    st.header('Global assumptions')
    finance_rate = st.number_input('Finance rate (%)', 0.0, 100.0, float(DEFAULT_GLOBAL.finance_rate*100), 0.5)/100
    include_emissions_cost = st.checkbox('Include emissions cost', value=DEFAULT_GLOBAL.include_emissions_cost)
    emissions_price = st.number_input('Emissions price ($/t)', 0.0, 10000.0, float(DEFAULT_GLOBAL.emissions_price_per_tonne), 10.0)
    g = GlobalInputs(finance_rate=finance_rate, include_emissions_cost=include_emissions_cost, emissions_price_per_tonne=emissions_price)

c1, c2 = st.columns(2)
with c1:
    st.subheader('ICE vehicle')
    ice = VehicleInputs(
        name=st.text_input('Vehicle name', DEFAULT_ICE.name, key='ice_name'),
        annual_mileage_km=st.number_input('Annual mileage (km/year)', 0.0, 200000.0, float(DEFAULT_ICE.annual_mileage_km), 1000.0, key='ice_mileage'),
        life_years=int(st.number_input('Life (years)', 1.0, 50.0, float(DEFAULT_ICE.life_years), 1.0, key='ice_life')),
        purchase_cost=st.number_input('Purchase cost ($)', 0.0, 500000.0, float(DEFAULT_ICE.purchase_cost), 1000.0, key='ice_purchase'),
        purchase_rebate=st.number_input('Rebate or grant ($)', 0.0, 500000.0, float(DEFAULT_ICE.purchase_rebate), 500.0, key='ice_rebate'),
        sale_value_pct=st.slider('Sale value at end of life (%)', 0.0, 50.0, float(DEFAULT_ICE.sale_value_pct*100), 1.0, key='ice_sale')/100,
        annual_maintenance_cost=st.number_input('Maintenance ($/year)', 0.0, 100000.0, float(DEFAULT_ICE.annual_maintenance_cost), 100.0, key='ice_maint'),
        annual_insurance_registration_cost=st.number_input('Insurance + registration ($/year)', 0.0, 100000.0, float(DEFAULT_ICE.annual_insurance_registration_cost), 100.0, key='ice_rego'),
        fuel_cost_per_litre=st.number_input('Fuel cost ($/litre)', 0.0, 20.0, float(DEFAULT_ICE.fuel_cost_per_litre), 0.05, key='ice_fuel_cost'),
        fuel_efficiency_km_per_litre=st.number_input('Fuel efficiency (km/litre)', 0.01, 100.0, float(DEFAULT_ICE.fuel_efficiency_km_per_litre), 0.5, key='ice_eff'),
        road_user_charges_per_1000km=st.number_input('Road user charges ($/1000 km)', 0.0, 1000.0, float(DEFAULT_ICE.road_user_charges_per_1000km), 5.0, key='ice_ruc'),
        emissions_rate_g_per_km=st.number_input('Vehicle emissions (g/km)', 0.0, 2000.0, float(DEFAULT_ICE.emissions_rate_g_per_km), 5.0, key='ice_emissions'),
    )
with c2:
    st.subheader('EV vehicle')
    ev = VehicleInputs(
        name=st.text_input('Vehicle name ', DEFAULT_EV.name, key='ev_name'),
        annual_mileage_km=st.number_input('Annual mileage (km/year) ', 0.0, 200000.0, float(DEFAULT_EV.annual_mileage_km), 1000.0, key='ev_mileage'),
        life_years=int(st.number_input('Life (years) ', 1.0, 50.0, float(DEFAULT_EV.life_years), 1.0, key='ev_life')),
        purchase_cost=st.number_input('Purchase cost ($) ', 0.0, 500000.0, float(DEFAULT_EV.purchase_cost), 1000.0, key='ev_purchase'),
        purchase_rebate=st.number_input('Rebate or grant ($) ', 0.0, 500000.0, float(DEFAULT_EV.purchase_rebate), 500.0, key='ev_rebate'),
        sale_value_pct=st.slider('Sale value at end of life (%) ', 0.0, 50.0, float(DEFAULT_EV.sale_value_pct*100), 1.0, key='ev_sale')/100,
        annual_maintenance_cost=st.number_input('Maintenance ($/year) ', 0.0, 100000.0, float(DEFAULT_EV.annual_maintenance_cost), 100.0, key='ev_maint'),
        annual_insurance_registration_cost=st.number_input('Insurance + registration ($/year) ', 0.0, 100000.0, float(DEFAULT_EV.annual_insurance_registration_cost), 100.0, key='ev_rego'),
        electricity_cost_per_kwh=st.number_input('Electricity cost ($/kWh)', 0.0, 10.0, float(DEFAULT_EV.electricity_cost_per_kwh), 0.01, key='ev_power_cost'),
        ev_efficiency_wh_per_km=st.number_input('EV efficiency (Wh/km)', 0.0, 1000.0, float(DEFAULT_EV.ev_efficiency_wh_per_km), 1.0, key='ev_eff'),
        road_user_charges_per_1000km=st.number_input('Road user charges ($/1000 km) ', 0.0, 1000.0, float(DEFAULT_EV.road_user_charges_per_1000km), 5.0, key='ev_ruc'),
        grid_emissions_g_per_kwh=st.number_input('Grid emissions (g/kWh)', 0.0, 2000.0, float(DEFAULT_EV.grid_emissions_g_per_kwh), 5.0, key='ev_grid_emissions'),
    )

ice_results = compute_ice(ice, g)
ev_results = compute_ev(ev, g)
payback = payback_analysis(ice, ev, g)
annual_saving = ice_results['total_annual_cost'] - ev_results['total_annual_cost']
upfront_gap = ev_results['net_purchase_cost'] - ice_results['net_purchase_cost']

m1,m2,m3,m4=st.columns(4)
m1.metric('Annual saving from EV', f"${annual_saving:,.0f}")
m2.metric('Upfront price difference', f"${upfront_gap:,.0f}")
m3.metric('EV cost per km', f"${ev_results['total_cost_per_km']:.3f}")
m4.metric('Discounted payback', 'Never' if payback['payback_discounted'] is None else f"{payback['payback_discounted']:.1f} years")

st.subheader('Summary')
summary = summary_table(ice, ev, g)
st.dataframe(summary, use_container_width=True, hide_index=True)

st.subheader('Annual cost breakdown')
breakdown = pd.DataFrame({
    'Category':['Annualised purchase','Fuel / charging','Road user charges','Maintenance + rego','Emissions'],
    ice.name:[ice_results['annual_purchase_cost'], ice_results['annual_fuel_or_charging_cost'], ice_results['annual_ruc_cost'], ice_results['annual_maintenance_and_rego'], ice_results['annual_emissions_cost']],
    ev.name:[ev_results['annual_purchase_cost'], ev_results['annual_fuel_or_charging_cost'], ev_results['annual_ruc_cost'], ev_results['annual_maintenance_and_rego'], ev_results['annual_emissions_cost']],
}).set_index('Category')
st.bar_chart(breakdown)

st.subheader('Payback table')
st.dataframe(payback['table'], use_container_width=True, hide_index=True)

payload_json = json.dumps(scenario_payload(ice, ev, g), indent=2)
st.download_button('Download scenario JSON', payload_json, 'ev_cost_scenario.json', 'application/json')
st.download_button('Download annual cashflow CSV', payback['table'].to_csv(index=False), 'ev_cost_cashflows.csv', 'text/csv')
