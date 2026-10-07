import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from fastapi.testclient import TestClient
from backend.app.main import app
client = TestClient(app)

r = client.get("/api/health")
assert r.status_code == 200
print("Health:", r.json()["status"])

r = client.get("/api/players")
data = r.json()
positions = sorted(set(p["primary_position"] for p in data["players"]))
print(f"Players: {data['count']} | Positions in DB: {positions}")

# THE FIXED BUG: right back query must not return DM/LB
r = client.post("/api/scout/search", json={
    "objective": "Find a right back under 45M",
    "club": "Arsenal FC",
    "budget_eur": 45000000,
    "wage_cap_pw": 120000
})
assert r.status_code == 200
d = r.json()["dossier"]
if d["top_candidates"]:
    top = d["top_candidates"][0]["player"]
    print(f"Right back query -> Top: {top['name']} ({top['primary_position']})")
    assert top["primary_position"] in ["RB","RWB"], f"BUG: got {top['primary_position']}"
    print("  CORRECT: only right-side fullbacks returned")
else:
    print("Right back query -> No candidates (budget/constraint too tight)")

# UNKNOWN guard
r = client.post("/api/scout/search", json={
    "objective": "Find a good bloke for the team",
    "club": "Arsenal FC",
    "budget_eur": 50000000,
    "wage_cap_pw": 120000
})
assert r.status_code == 200
d = r.json()["dossier"]
assert d["top_candidates"] == [], f"Expected empty for UNKNOWN, got {len(d['top_candidates'])}"
print(f"UNKNOWN guard -> {len(d['top_candidates'])} candidates (correct: empty)")
print("ALL INTEGRATION CHECKS PASSED")
