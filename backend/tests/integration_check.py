"""Standalone smoke check. Run from the repository root."""
from fastapi.testclient import TestClient
from backend.app.main import app

def main():
    with TestClient(app) as client:
        health = client.get('/api/health').json()
        assert health['player_count'] > 0
        r = client.post('/api/scout/search',json={'objective':'Find a right back under 45M'})
        if health.get('mode') in ('statsbomb','openplay'):
            assert r.status_code==422
            r=client.post('/api/scout/search',json={'objective':'Find a right back'})
        assert r.status_code == 200
        payload=r.json()
        for c in payload.get('candidates',payload.get('dossier',{}).get('top_candidates',[])):
            positions = {c['player']['primary_position'], *c['player']['secondary_positions']}
            assert positions & {'RB','RWB'}
        payload=client.post('/api/scout/search',json={'objective':'Find a fast player'}).json()
        d=payload.get('dossier',payload)
        assert d['status'] == 'needs_clarification' and not d.get('candidates',d.get('top_candidates',[]))
    print('Startup, right-back eligibility and clarification checks passed.')

if __name__ == '__main__':
    main()
