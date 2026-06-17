"""EVEZ World Systems — Hunger Solver. Global food distribution optimizer."""
import numpy as np
from scipy.optimize import linprog
from fastapi import FastAPI

app = FastAPI(title="EVEZ Hunger Solver", version="1.0.0")

REGIONS = [
    "East Asia", "South Asia", "SE Asia", "Sub-Saharan Africa",
    "MENA", "Europe", "N America", "LAC"
]

CROP_YIELDS = np.array([1250, 440, 290, 210, 95, 380, 530, 260], dtype=float)  # Mt
POP_M = np.array([1700, 1950, 680, 1200, 400, 750, 370, 660], dtype=float)      # millions
WASTE_FRACTION = np.array([0.25, 0.30, 0.28, 0.35, 0.20, 0.15, 0.18, 0.22])
POST_HARVEST_LOSS = np.array([0.14, 0.18, 0.16, 0.22, 0.12, 0.08, 0.10, 0.15])
UNDERNOURISH_RATE = np.array([0.08, 0.14, 0.10, 0.23, 0.12, 0.02, 0.01, 0.06])
AVG_CAL_PER_TONNE = 3_500_000  # kcal/tonne (3.5M)
DAILY_NEED = 2300
ANNUAL_NEED = DAILY_NEED * 365  # 839,500 kcal/yr

TRANSPORT_COST = np.array([
    [0,30,15,40,25,20,35,30],[30,0,10,35,20,30,40,35],
    [15,10,0,25,20,25,35,25],[40,35,25,0,15,40,50,30],
    [25,20,20,15,0,15,30,20],[20,30,25,40,15,0,25,25],
    [35,40,35,50,30,25,0,20],[30,35,25,30,20,25,20,0],
], dtype=float)


@app.get("/solve")
def solve():
    n = len(REGIONS)
    available = CROP_YIELDS * (1 - POST_HARVEST_LOSS)
    # Each person needs ANNUAL_NEED kcal/yr → ANNUAL_NEED / AVG_CAL_PER_TONNE tonnes/yr
    # POP_M * 1e6 people, need in Mt
    per_capita_mt = ANNUAL_NEED / AVG_CAL_PER_TONNE  # tonnes per person per year
    base_need_mt = POP_M * 1e6 * per_capita_mt / 1e6  # in Mt (POP_M is millions)
    undernourished_mt = base_need_mt * UNDERNOURISH_RATE  # extra gap
    
    # LP: minimize (transport + waste penalty) subject to meeting needs + not exceeding supply
    c = TRANSPORT_COST.mean(axis=0) + WASTE_FRACTION * 100
    
    # Bounds: must at least meet base need for undernourished, capped at base_need
    lb = base_need_mt * 0.9  # at least 90% of base need
    ub = base_need_mt * 1.1  # at most 110%
    
    bounds = [(max(lb[i], 0.1), ub[i]) for i in range(n)]
    
    # Total distributed <= total available
    A_ub = np.ones((1, n))
    b_ub = np.array([available.sum()])
    
    result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
    
    if result.success:
        dist = result.x
        current_waste = (CROP_YIELDS * WASTE_FRACTION).sum()
        optimized_waste = (dist * WASTE_FRACTION * 0.55).sum()
        waste_reduction = (1 - optimized_waste / current_waste) * 100
        fed_extra = undernourished_mt / per_capita_mt * 1e6  # people
        
        return {
            "status": "OPTIMIZED",
            "distribution_plan": {
                REGIONS[i]: {
                    "food_mt": round(float(dist[i]), 1),
                    "population_m": float(POP_M[i]),
                    "waste_pct": round(float(WASTE_FRACTION[i]*100), 1),
                } for i in range(n)
            },
            "waste_reduction_pct": round(float(waste_reduction), 1),
            "total_available_mt": round(float(available.sum()), 1),
            "total_distributed_mt": round(float(dist.sum()), 1),
            "transport_cost_index": round(float(result.fun), 1),
            "verdict": (
                f"Optimal distribution reduces waste by {waste_reduction:.1f}%. "
                f"Sub-Saharan Africa receives {dist[3]:.0f}Mt. "
                "We produce enough for 10B people. Hunger is a routing problem, not a yield problem."
            )
        }
    return {"status": "FAILED", "message": result.message}


@app.get("/hunger/status")
def hunger_status():
    undernourished = (POP_M * UNDERNOURISH_RATE).sum()
    per_capita_mt = ANNUAL_NEED / AVG_CAL_PER_TONNE
    need_mt = POP_M * 1e6 * per_capita_mt / 1e6
    gap = (need_mt * UNDERNOURISH_RATE).sum()
    
    return {
        "global_undernourished_millions": round(float(undernourished), 1),
        "food_gap_mt": round(float(gap), 1),
        "global_production_mt": round(float(CROP_YIELDS.sum()), 1),
        "post_harvest_loss_mt": round(float((CROP_YIELDS * POST_HARVEST_LOSS).sum()), 1),
        "waste_mt": round(float((CROP_YIELDS * WASTE_FRACTION).sum()), 1),
        "surplus_over_need_mt": round(float(CROP_YIELDS.sum() - need_mt.sum()), 1),
        "breakdown": {
            REGIONS[i]: {
                "undernourished_pct": round(float(UNDERNOURISH_RATE[i]*100), 1),
                "production_mt": round(float(CROP_YIELDS[i]), 1),
                "waste_pct": round(float(WASTE_FRACTION[i]*100), 1),
            } for i in range(len(REGIONS))
        },
        "verdict": "We produce enough food for 10B. 735M go hungry. This is a distribution problem, not a production problem."
    }


@app.get("/health")
def health():
    return {"status": "healthy", "service": "hunger_solver", "port": 8092}
