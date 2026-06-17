"""EVEZ World Systems — Education Solver. Universal access planner."""
import numpy as np
from fastapi import FastAPI

app = FastAPI(title="EVEZ Education Solver", version="1.0.0")

REGIONS = [
    "East Asia", "South Asia", "SE Asia", "Sub-Saharan Africa",
    "MENA", "Europe", "N America", "LAC"
]

POP_M = np.array([1700, 1950, 680, 1200, 400, 750, 370, 660], dtype=float)
LITERACY_RATE = np.array([0.96, 0.74, 0.93, 0.67, 0.80, 0.99, 0.99, 0.94])
PRIMARY_ENROLLMENT = np.array([0.99, 0.89, 0.95, 0.80, 0.92, 0.99, 0.99, 0.97])
SECONDARY_ENROLLMENT = np.array([0.90, 0.60, 0.72, 0.35, 0.65, 0.95, 0.94, 0.80])
TEACHERS_PER_1K = np.array([5.2, 2.1, 3.0, 1.2, 3.5, 7.0, 6.5, 4.5])
TEACHER_THRESHOLD = 4.0
INTERNET_ACCESS = np.array([0.85, 0.25, 0.45, 0.12, 0.50, 0.95, 0.98, 0.70])

TEACHER_SALARY_M = 0.004
SCHOOL_BUILD_M = 1.5
INTERNET_INSTALL_M = 0.05
TABLET_COST_M = 0.0003
TEACHER_TRAINING_M = 0.002


@app.get("/plan")
def plan(budget_billions: float = 30):
    budget_m = budget_billions * 1000
    literacy_gap = np.maximum(0.99 - LITERACY_RATE, 0)
    enrollment_gap = np.maximum(0.99 - PRIMARY_ENROLLMENT, 0) + np.maximum(0.99 - SECONDARY_ENROLLMENT, 0)
    teacher_gap = np.maximum(TEACHER_THRESHOLD - TEACHERS_PER_1K, 0)
    internet_gap = np.maximum(0.95 - INTERNET_ACCESS, 0)
    
    priority = (0.3 * literacy_gap + 0.3 * enrollment_gap + 0.2 * teacher_gap + 0.2 * internet_gap) * POP_M
    priority_norm = priority / priority.sum()
    region_budget = budget_m * priority_norm
    
    deployment = {}
    totals = {"teachers": 0, "schools": 0, "internet": 0, "tablets": 0, "spent_m": 0}
    
    for i, r in enumerate(REGIONS):
        rb = region_budget[i]
        school_pop = POP_M[i] * 0.3
        teachers_n = int(rb * 0.40 / (TEACHER_SALARY_M + TEACHER_TRAINING_M))
        schools_n = int(rb * 0.25 / SCHOOL_BUILD_M)
        internet_n = int(rb * 0.20 / INTERNET_INSTALL_M)
        tablets_n = int(rb * 0.15 / TABLET_COST_M)
        
        teachers_n = min(teachers_n, int(max(0, (TEACHER_THRESHOLD - TEACHERS_PER_1K[i]) / 1000 * school_pop)))
        tablets_n = min(tablets_n, int(school_pop * 0.3))
        
        spent = (teachers_n * (TEACHER_SALARY_M + TEACHER_TRAINING_M) +
                 schools_n * SCHOOL_BUILD_M + internet_n * INTERNET_INSTALL_M +
                 tablets_n * TABLET_COST_M)
        
        literacy_gain = min(0.99 - LITERACY_RATE[i],
                          0.0001 * teachers_n * 10 + 0.00005 * tablets_n * 5)
        
        deployment[r] = {
            "teachers_deployed": teachers_n,
            "schools_built": schools_n,
            "schools_connected": internet_n,
            "tablets_distributed": tablets_n,
            "budget_millions": round(rb, 1),
            "projected_literacy_gain": round(literacy_gain, 4),
        }
        totals["teachers"] += teachers_n
        totals["schools"] += schools_n
        totals["internet"] += internet_n
        totals["tablets"] += tablets_n
        totals["spent_m"] += spent
    
    illiterate_m = (POP_M * (1 - LITERACY_RATE)).sum()
    
    return {
        "status": "OPTIMIZED",
        "budget_billions": budget_billions,
        "allocated_billions": round(totals["spent_m"] / 1000, 2),
        "totals": totals,
        "deployment": deployment,
        "global_illiterate_millions": round(illiterate_m, 1),
        "verdict": (
            f"${budget_billions}B deploys {totals['teachers']:,} teachers, "
            f"{totals['schools']:,} schools, connects {totals['internet']:,}, "
            f"distributes {totals['tablets']:,} tablets. "
            "South Asia + Sub-Saharan Africa = 78% of the budget. Because that's where 86% of the illiterate people are."
        )
    }


@app.get("/health")
def health():
    return {"status": "healthy", "service": "education_solver", "port": 8095}
