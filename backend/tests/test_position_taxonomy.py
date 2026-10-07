import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from backend.app.agents.tactical_agent import tactical_agent
from backend.app.agents.scout_agent import scout_agent
from backend.app.agents.orchestrator import director_orchestrator

test_cases = [
    ("Find a fullback under 40M",                     "FB",     ["LB","RB","LWB","RWB"]),
    ("Find a left back for Bayern Munich under 50M",   "LB",     ["LB","LWB"]),
    ("Find a right back under 45M",                    "RB",     ["RB","RWB"]),
    ("Find a striker under 40M",                       "ST",     ["ST","CF"]),
    ("Find a goalkeeper",                              "GK",     ["GK"]),
    ("Find a centre-back under 45M",                   "CB",     ["CB"]),
    ("Find a defensive midfielder under 40M",          "DM",     ["DM"]),
    ("Find a winger under 50M",                        "WINGER", ["LW","RW","AM"]),  # Cherki plays RW
    ("Find a number 10 playmaker under 35M",           "AM",     ["AM","ST","CF"]),  # Zirkzee plays ST/AM
    ("Find a box to box midfielder under 45M",         "CM",     ["CM","DM"]),       # Wharton plays DM/CM
]

print("=== POSITION TAXONOMY VERIFICATION TESTS ===\n")
all_pass = True
for mandate, expected_family, expected_positions in test_cases:
    profile = tactical_agent.generate_profile(mandate)
    got_family = profile.position_family
    got_pos = profile.position

    try:
        pool, ranked = scout_agent.retrieve_and_rank_candidates(profile, mandate)
        top = ranked[0].player if ranked else None
        top_pos = f"{top.name} ({top.primary_position})" if top else "No matching candidates"
        top_in_family = top and (top.primary_position in expected_positions or any(p in expected_positions for p in top.secondary_positions))
    except ValueError as e:
        top_pos = "CLARIFICATION RETURNED"
        top_in_family = False

    ok = got_family == expected_family and (top_in_family or "No matching" in str(top_pos))
    status = "PASS" if ok else "FAIL"
    if not ok:
        all_pass = False

    print(f"[{status}] {mandate[:55]}")
    print(f"       family={got_family} (expected={expected_family}) pos={got_pos}")
    print(f"       Top result: {top_pos}\n")

print("--- UNKNOWN POSITION GUARD TEST (orchestrator) ---")
state, dossier = director_orchestrator.execute_recruitment_workflow(
    "Find me a good bloke for the team", club="Arsenal FC"
)
is_unknown = (dossier.top_candidates == [] and "unclear" in dossier.director_executive_summary.lower())
status = "PASS" if is_unknown else "FAIL"
if not is_unknown:
    all_pass = False
print(f"[{status}] UNKNOWN position returns clarification dossier (empty candidates)")
print(f"       Summary: {dossier.director_executive_summary[:80]}...\n")

print("=== RESULT:", "ALL TESTS PASSED" if all_pass else "SOME TESTS FAILED", "===")
