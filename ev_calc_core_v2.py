from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Optional, Tuple
import pandas as pd


@dataclass
class VehicleInputs:
    name: str
    annual_mileage_km: float
    life_years: int
    purchase_cost: float
    purchase_rebate: float
    sale_value_pct: float
    annual_maintenance_cost: float
    annual_insurance_registration_cost: float
    fuel_cost_per_litre: float = 0.0
    fuel_efficiency_km_per_litre: float = 0.0
    road_user_charges_per_1000km: float = 0.0
    emissions_rate_g_per_km: float = 0.0
    electricity_cost_per_kwh: float = 0.0
    ev_efficiency_wh_per_km: float = 0.0
    grid_emissions_g_per_kwh: float = 0.0


@dataclass
class GlobalInputs:
    finance_rate: float
    include_emissions_cost: bool
    emissions_price_per_tonne: float


DEFAULT_ICE = VehicleInputs(
    name="Toyota Corolla 2020 (2nd hand)",
    annual_mileage_km=30000,
    life_years=10,
    purchase_cost=15000,
    purchase_rebate=0,
    sale_value_pct=0.10,
    annual_maintenance_cost=1000,
    annual_insurance_registration_cost=0,
    fuel_cost_per_litre=2.70,
    fuel_efficiency_km_per_litre=14,
    road_user_charges_per_1000km=0,
    emissions_rate_g_per_km=210,
)

DEFAULT_EV = VehicleInputs(
    name="Nissan Leaf 2020 (2nd hand)",
    annual_mileage_km=30000,
    life_years=10,
    purchase_cost=25000,
    purchase_rebate=0,
    sale_value_pct=0.10,
    annual_maintenance_cost=200,
    annual_insurance_registration_cost=0,
    electricity_cost_per_kwh=0.15,
    ev_efficiency_wh_per_km=166,
    road_user_charges_per_1000km=76,
    grid_emissions_g_per_kwh=136,
)

DEFAULT_GLOBAL = GlobalInputs(
    finance_rate=0.10,
    include_emissions_cost=False,
    emissions_price_per_tonne=150,
)


def pmt(rate: float, nper: int, pv: float, fv: float = 0.0, when: int = 0) -> float:
    """Excel PMT-compatible implementation."""
    if nper <= 0:
        return 0.0
    if abs(rate) < 1e-12:
        return -(fv + pv) / nper
    return -((fv + pv * (1 + rate) ** nper) * rate) / ((1 + rate * when) * ((1 + rate) ** nper - 1))


def annualised_purchase_cost(net_purchase_cost: float, sale_value_pct: float, life_years: int, finance_rate: float) -> float:
    if life_years <= 0:
        return 0.0
    salvage_adjusted_pv = -(net_purchase_cost - net_purchase_cost * sale_value_pct * (1 - finance_rate) ** life_years)
    annual_payment = pmt(finance_rate, life_years, salvage_adjusted_pv, fv=0.0, when=1)
    return annual_payment * (1 + finance_rate) ** 0.5


def compute_ice(v: VehicleInputs, g: GlobalInputs) -> Dict[str, float]:
    net_purchase_cost = v.purchase_cost - v.purchase_rebate
    annual_purchase_cost = annualised_purchase_cost(net_purchase_cost, v.sale_value_pct, v.life_years, g.finance_rate)
    fuel_cost_per_km = v.fuel_cost_per_litre / v.fuel_efficiency_km_per_litre if v.fuel_efficiency_km_per_litre else 0.0
    annual_fuel_cost = fuel_cost_per_km * v.annual_mileage_km
    annual_ruc_cost = v.road_user_charges_per_1000km * v.annual_mileage_km / 1000.0
    annual_maint_rego = v.annual_maintenance_cost + v.annual_insurance_registration_cost
    emissions_tonnes_per_year = v.emissions_rate_g_per_km * v.annual_mileage_km / 1_000_000.0
    annual_emissions_cost = emissions_tonnes_per_year * g.emissions_price_per_tonne if g.include_emissions_cost else 0.0
    total_annual_cost = annual_purchase_cost + annual_fuel_cost + annual_ruc_cost + annual_maint_rego + annual_emissions_cost
    total_cost_per_km = total_annual_cost / v.annual_mileage_km if v.annual_mileage_km else 0.0
    return {
        "net_purchase_cost": net_purchase_cost,
        "annual_purchase_cost": annual_purchase_cost,
        "annual_fuel_or_charging_cost": annual_fuel_cost,
        "annual_ruc_cost": annual_ruc_cost,
        "annual_maintenance_and_rego": annual_maint_rego,
        "annual_emissions_cost": annual_emissions_cost,
        "total_annual_cost": total_annual_cost,
        "total_cost_per_km": total_cost_per_km,
        "sale_value": net_purchase_cost * v.sale_value_pct,
        "annual_emissions_tonnes": emissions_tonnes_per_year,
    }


def compute_ev(v: VehicleInputs, g: GlobalInputs) -> Dict[str, float]:
    net_purchase_cost = v.purchase_cost - v.purchase_rebate
    annual_purchase_cost = annualised_purchase_cost(net_purchase_cost, v.sale_value_pct, v.life_years, g.finance_rate)
    charging_cost_per_km = v.electricity_cost_per_kwh * v.ev_efficiency_wh_per_km / 1000.0
    annual_charging_cost = charging_cost_per_km * v.annual_mileage_km
    annual_ruc_cost = v.road_user_charges_per_1000km * v.annual_mileage_km / 1000.0
    annual_maint_rego = v.annual_maintenance_cost + v.annual_insurance_registration_cost
    emissions_tonnes_per_year = v.annual_mileage_km * v.ev_efficiency_wh_per_km / 1000.0 * v.grid_emissions_g_per_kwh / 1_000_000.0
    annual_emissions_cost = emissions_tonnes_per_year * g.emissions_price_per_tonne if g.include_emissions_cost else 0.0
    total_annual_cost = annual_purchase_cost + annual_charging_cost + annual_ruc_cost + annual_maint_rego + annual_emissions_cost
    total_cost_per_km = total_annual_cost / v.annual_mileage_km if v.annual_mileage_km else 0.0
    return {
        "net_purchase_cost": net_purchase_cost,
        "annual_purchase_cost": annual_purchase_cost,
        "annual_fuel_or_charging_cost": annual_charging_cost,
        "annual_ruc_cost": annual_ruc_cost,
        "annual_maintenance_and_rego": annual_maint_rego,
        "annual_emissions_cost": annual_emissions_cost,
        "total_annual_cost": total_annual_cost,
        "total_cost_per_km": total_cost_per_km,
        "sale_value": net_purchase_cost * v.sale_value_pct,
        "annual_emissions_tonnes": emissions_tonnes_per_year,
    }


def annual_cashflow_series(v: VehicleInputs, g: GlobalInputs, mode: str) -> pd.DataFrame:
    results = compute_ice(v, g) if mode == "ice" else compute_ev(v, g)
    rows = []
    for year in range(1, int(v.life_years) + 1):
        purchase = results["net_purchase_cost"] if year == 1 else 0.0
        sale = -results["sale_value"] if year == v.life_years else 0.0
        fuel_or_charging = results["annual_fuel_or_charging_cost"]
        ruc = results["annual_ruc_cost"]
        maintenance = results["annual_maintenance_and_rego"]
        emissions = results["annual_emissions_cost"]
        total = purchase + sale + fuel_or_charging + ruc + maintenance + emissions
        rows.append(
            {
                "Year": year,
                "Purchase cost after rebate": purchase,
                "Sale value": sale,
                "Fuel / charging": fuel_or_charging,
                "Road user charges": ruc,
                "Maintenance + rego": maintenance,
                "Emissions": emissions,
                "Total": total,
            }
        )
    return pd.DataFrame(rows)


def _interpolate_payback(years, values) -> Optional[float]:
    values = list(values)
    years = list(years)
    for i in range(1, len(values)):
        if values[i] >= 0 and values[i - 1] < 0:
            return years[i - 1] - values[i - 1] / (-values[i - 1] + values[i])
    return None


def payback_analysis(ice: VehicleInputs, ev: VehicleInputs, g: GlobalInputs) -> Dict[str, object]:
    ice_cf = annual_cashflow_series(ice, g, "ice")
    ev_cf = annual_cashflow_series(ev, g, "ev")
    max_year = int(max(ice.life_years, ev.life_years))
    full_index = pd.Index(range(1, max_year + 1), name="Year")
    ice_cf = ice_cf.set_index("Year").reindex(full_index, fill_value=0.0).reset_index()
    ev_cf = ev_cf.set_index("Year").reindex(full_index, fill_value=0.0).reset_index()

    diff = ice_cf.copy()
    diff.iloc[:, 1:] = ice_cf.iloc[:, 1:].values - ev_cf.iloc[:, 1:].values

    # Spreadsheet-equivalent discounting from the hidden worksheet.
    # The workbook applies a beginning-of-year factor to each annual difference row.
    # This is intentionally preserved here so the app matches the spreadsheet outputs.
    start_factor = []
    for year in diff["Year"]:
        start = 1 / ((1 + g.finance_rate) ** (year - 1)) if g.finance_rate != -1 else 0.0
        start_factor.append(start)

    diff["Discount factor - beginning"] = start_factor

    for col in ["Purchase cost after rebate", "Sale value", "Fuel / charging", "Road user charges", "Maintenance + rego", "Emissions", "Total"]:
        diff[f"Discounted {col}"] = diff[col] * diff["Discount factor - beginning"]

    diff["Cumulative undisc."] = diff["Total"].cumsum()
    diff["Discounted total"] = diff["Discounted Total"]
    diff["Cumulative disc."] = diff["Discounted total"].cumsum()

    return {
        "table": diff,
        "payback_undiscounted": _interpolate_payback(diff["Year"], diff["Cumulative undisc."]),
        "payback_discounted": _interpolate_payback(diff["Year"], diff["Cumulative disc."]),
    }


def summary_table(ice: VehicleInputs, ev: VehicleInputs, g: GlobalInputs) -> pd.DataFrame:
    ice_results = compute_ice(ice, g)
    ev_results = compute_ev(ev, g)
    return pd.DataFrame(
        {
            "Metric": [
                "Annualised purchase cost ($/year)",
                "Annual fuel / charging cost ($/year)",
                "Annual road user charges ($/year)",
                "Annual maintenance + rego ($/year)",
                "Annual emissions cost ($/year)",
                "Total annual cost ($/year)",
                "Total cost per km ($/km)",
            ],
            ice.name: [
                ice_results["annual_purchase_cost"],
                ice_results["annual_fuel_or_charging_cost"],
                ice_results["annual_ruc_cost"],
                ice_results["annual_maintenance_and_rego"],
                ice_results["annual_emissions_cost"],
                ice_results["total_annual_cost"],
                ice_results["total_cost_per_km"],
            ],
            ev.name: [
                ev_results["annual_purchase_cost"],
                ev_results["annual_fuel_or_charging_cost"],
                ev_results["annual_ruc_cost"],
                ev_results["annual_maintenance_and_rego"],
                ev_results["annual_emissions_cost"],
                ev_results["total_annual_cost"],
                ev_results["total_cost_per_km"],
            ],
        }
    )


def scenario_payload(ice: VehicleInputs, ev: VehicleInputs, g: GlobalInputs) -> Dict[str, object]:
    payback = payback_analysis(ice, ev, g)
    return {
        "global": asdict(g),
        "ice": asdict(ice),
        "ev": asdict(ev),
        "ice_results": compute_ice(ice, g),
        "ev_results": compute_ev(ev, g),
        "discounted_payback_years": payback["payback_discounted"],
        "undiscounted_payback_years": payback["payback_undiscounted"],
    }
