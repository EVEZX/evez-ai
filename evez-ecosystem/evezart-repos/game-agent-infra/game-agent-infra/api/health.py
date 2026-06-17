import json
from datetime import datetime

def handler(request):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({
            'status': 'healthy',
            'model': 'EVEZ-CS-v2.0',
            'version': '2.0.0',
            'endpoints': ['/api/score', '/api/batch', '/api/health'],
            'compliance': {'ecoa': True, 'fcra': True, 'model': 'EVEZ-CS-v2.0'},
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'platform': 'vercel',
            'supabase': 'https://vziaqxquzohqskesuxgz.supabase.co'
        })
    }
