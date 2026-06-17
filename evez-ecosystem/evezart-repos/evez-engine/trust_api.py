#!/usr/bin/env python3
"""
Agent Trust Scoring API - Monetizable Service
Score any AI agent for $0.01/call
"""

from flask import Flask, request, jsonify
from agent_trust_engine import SpectralTrustEngine, AgentProfile, ActionType, AgentAction
import time

app = Flask(__name__)
engine = SpectralTrustEngine()

@app.route('/score', methods=['POST'])
def score_agent():
    """Score an AI agent's trustworthiness"""
    data = request.json
    profile = AgentProfile(
        agent_id=data.get('agent_id', 'unknown'),
        name=data.get('name'),
        version=data.get('version'),
        capabilities=data.get('capabilities', [])
    )
    
    # Convert string action_type to enum
    for action in data.get('actions', []):
        at = action.get('action_type')
        if isinstance(at, str):
            action['action_type'] = ActionType(at)
        profile.actions.append(AgentAction(**action))
    
    result = engine.score_agent(profile)
    return jsonify({
        'score': result['score'],
        'tier': result['tier'],
        'factors': {k: float(v) if hasattr(v, 'item') else v for k, v in result['factors'].items()},
        'cost': '$0.01'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9112)