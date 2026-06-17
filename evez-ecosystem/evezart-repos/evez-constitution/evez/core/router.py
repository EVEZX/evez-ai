"""EVEZ Core Router - Dynamic Task Routing"""
from evez.modules.logic import validate_schema, compute_hash
from evez.modules.vector import vector_store
from evez.modules.temporal import timeline, TemporalPredictor
from evez.modules.code import executor

ROUTER = {
    "reasoning": "logic",
    "memory": "vector",
    "prediction": "temporal",
    "code": "code"
}

class Router:
    def __init__(self):
        self.timeline = timeline
        self.vector = vector_store
        self.predictor = TemporalPredictor()
    
    def route(self, request: str) -> dict:
        """Route request to appropriate module"""
        request_lower = request.lower()
        
        if "reason" in request_lower or "logic" in request_lower:
            module = ROUTER["reasoning"]
        elif "memory" in request_lower or "recall" in request_lower:
            module = ROUTER["memory"]
        elif "predict" in request_lower or "when" in request_lower:
            module = ROUTER["prediction"]
        elif "code" in request_lower or "run" in request_lower:
            module = ROUTER["code"]
        else:
            module = ROUTER["reasoning"]
        
        return {
            "module": module,
            "request": request,
            "transform_hash": compute_hash(request)
        }

router = Router()