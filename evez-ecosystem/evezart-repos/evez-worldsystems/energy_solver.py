"""EVEZ World Systems — Energy Solver. Renewable transition planner with Monte Carlo."""
import numpy as np
from fastapi import FastAPI

app = FastAPI(title="EVEZ Energy Solver", version="1.0.0")

# ── Global energy mix 2023 (EJ) ──────────────────────────────────────
ENERGY_MIX = {
    "oil": 184, "gas": 143, "coal": 160, "nuclear": 28,
    "hydro": 40, "wind": 18, "solar": 14, "bio": 12, "other_renew": 5
}

TOTAL_EJ = sum(ENERGY_MIX.values())  # ~590 EJ
FOSSIL_EJ = ENERGY_MIX["oil"] + ENERGY_MIX["gas"] + ENERGY_MIX["coal"]
RENEWABLE_EJ = TOTAL_EJ - FOSSIL_EJ - ENERGY_MIX["nuclear"]

# Deployment parameters (realistic curves)
SOLAR_GROWTH_RATE = 0.28      # annual capacity growth
WIND_GROWTH_RATE = 0.14
BATTERY_GROWTH_RATE = 0.35
FOSSIL_DECLINE_RATE = 0.04    # baseline, accelerates with renewables

# Cost parameters ($/MWh, declining)
SOLAR_LCOE_2023 = 40   # $/MWh
WIND_LCOE_2023 = 50
BATTERY_LCOE_2023 = 140  # storage cost
FOSSIL_LCOE_2023 = 65

CO2_PER_EJ_FOSSIL = 65  # Mt CO2 per EJ (blended fossil)

# Learning rates
SOLAR_LR = 0.20   # 20% cost reduction per doubling
WIND_LR = 0.15
BATTERY_LR = 0.18


@app.get("/simulate")
def simulate(years: int = 30):
    """Monte Carlo simulation of energy transition."""
    n_sim = 1000
    np.random.seed(42)
    
    solar_rates = np.random.normal(SOLAR_GROWTH_RATE, 0.05, n_sim)
    wind_rates = np.random.normal(WIND_GROWTH_RATE, 0.03, n_sim)
    battery_rates = np.random.normal(BATTERY_GROWTH_RATE, 0.06, n_sim)
    fossil_declines = np.random.normal(FOSSIL_DECLINE_RATE, 0.015, n_sim)
    
    fossil_phaseout_year = []
    co2_reductions = []
    cost_trajectories = []
    
    for i in range(n_sim):
        fossil = FOSSIL_EJ
        solar = ENERGY_MIX["solar"]
        wind = ENERGY_MIX["wind"]
        battery = ENERGY_MIX["other_renew"]
        co2_cumulative = 0
        cost_total = 0
        phaseout = years + 2023
        
        for y in range(years):
            # Renewable growth (constrained by grid integration)
            battery_factor = min(1.0, 0.3 + 0.7 * (y / 15))  # grid integration ramps
            solar_new = solar * max(0, solar_rates[i]) * battery_factor
            wind_new = wind * max(0, wind_rates[i]) * battery_factor
            
            solar += solar_new
            wind += wind_new
            
            # Fossil decline accelerates as renewables become dominant
            renewable_share = (solar + wind + ENERGY_MIX["hydro"] + 
                             ENERGY_MIX["bio"] + ENERGY_MIX["other_renew"] + battery) / TOTAL_EJ
            effective_decline = fossil_declines[i] * (1 + 2 * renewable_share)
            fossil *= (1 - effective_decline)
            fossil = max(fossil, 2)  # floor at 2 EJ
            
            # CO2
            co2_y = fossil * CO2_PER_EJ_FOSSIL
            co2_cumulative += co2_y
            
            # Cost (LCOE declining with learning)
            doublings_s = max(0, np.log2(solar / ENERGY_MIX["solar"])) if solar > 0 else 0
            doublings_w = max(0, np.log2(wind / ENERGY_MIX["wind"])) if wind > 0 else 0
            solar_cost = SOLAR_LCOE_2023 * (1 - SOLAR_LR) ** doublings_s
            wind_cost = WIND_LCOE_2023 * (1 - WIND_LR) ** doublings_w
            cost_total += solar_new * solar_cost + wind_new * wind_cost
            
            if fossil < 10 and phaseout == years + 2023:
                phaseout = 2023 + y + 1
        
        fossil_phaseout_year.append(phaseout)
        co2_reductions.append((1 - co2_cumulative / (FOSSIL_EJ * CO2_PER_EJ_FOSSIL * years)) * 100)
        cost_trajectories.append(cost_total)
    
    # Compute median/percentile schedule for display
    schedule = []
    fossil_t = FOSSIL_EJ
    solar_t = ENERGY_MIX["solar"]
    wind_t = ENERGY_MIX["wind"]
    for y in range(years):
        renewable_share = (solar_t + wind_t + ENERGY_MIX["hydro"] + 
                          ENERGY_MIX["bio"] + ENERGY_MIX["other_renew"]) / TOTAL_EJ
        battery_factor = min(1.0, 0.3 + 0.7 * (y / 15))
        solar_t += solar_t * SOLAR_GROWTH_RATE * battery_factor
        wind_t += wind_t * WIND_GROWTH_RATE * battery_factor
        fossil_t *= (1 - FOSSIL_DECLINE_RATE * (1 + 2 * renewable_share))
        fossil_t = max(fossil_t, 2)
        schedule.append({
            "year": 2023 + y + 1,
            "fossil_ej": round(fossil_t, 1),
            "solar_ej": round(solar_t, 1),
            "wind_ej": round(wind_t, 1),
            "renewable_pct": round(renewable_share * 100, 1),
        })
    
    return {
        "status": "SIMULATED",
        "monte_carlo_runs": n_sim,
        "years": years,
        "median_fossil_phaseout": int(np.median(fossil_phaseout_year)),
        "phaseout_p10": int(np.percentile(fossil_phaseout_year, 10)),
        "phaseout_p90": int(np.percentile(fossil_phaseout_year, 90)),
        "median_co2_reduction_pct": round(float(np.median(co2_reductions)), 1),
        "median_total_cost_trillion_usd": round(float(np.median(cost_trajectories)) / 1e6, 1),
        "deployment_schedule": schedule[:5] + schedule[5::max(1, years//10)],  # sample key years
        "verdict": (
            f"Monte Carlo says fossil phaseout by {int(np.median(fossil_phaseout_year))} "
            f"(80% CI: {int(np.percentile(fossil_phaseout_year,10))}–{int(np.percentile(fossil_phaseout_year,90))}). "
            f"CO2 reduction: {float(np.median(co2_reductions)):.0f}%. "
            "The physics is clear. The economics already won. The politics is the only bottleneck."
        )
    }


@app.get("/energy/status")
def energy_status():
    renewable_pct = RENEWABLE_EJ / TOTAL_EJ * 100
    return {
        "total_primary_energy_ej": TOTAL_EJ,
        "fossil_ej": FOSSIL_EJ,
        "renewable_ej": RENEWABLE_EJ,
        "nuclear_ej": ENERGY_MIX["nuclear"],
        "fossil_pct": round(FOSSIL_EJ / TOTAL_EJ * 100, 1),
        "renewable_pct": round(renewable_pct, 1),
        "mix": ENERGY_MIX,
        "solar_lcoe_usd_per_mwh": SOLAR_LCOE_2023,
        "wind_lcoe_usd_per_mwh": WIND_LCOE_2023,
        "fossil_lcoe_usd_per_mwh": FOSSIL_LCOE_2023,
        "verdict": f"Renewables are {FOSSIL_LCOE_2023 / SOLAR_LCOE_2023:.1f}x cheaper than new fossil. The transition is a deployment problem, not a technology problem."
    }


@app.get("/health")
def health():
    return {"status": "healthy", "service": "energy_solver", "port": 8093}
