import pytest
from backend.app.agents.tactical_agent import tactical_agent

@pytest.mark.parametrize("mandate,family", [
    ("Find a fullback under 40M", "FB"),
    ("Find a left back for Bayern Munich under 50M", "LB"),
    ("Find a right back under 45M", "RB"),
    ("Find a striker under 40M", "ST"),
    ("Find a goalkeeper", "GK"),
    ("Find a centre-back under 45M", "CB"),
    ("Find a defensive midfielder under 40M", "DM"),
    ("Find a winger under 50M", "WINGER"),
    ("Find a number 10 playmaker under 35M", "AM"),
    ("Find a box to box midfielder under 45M", "CM"),
    ("Find an LB", "LB"), ("Find an RB", "RB"),
    ("Find me a good bloke for the team", "UNKNOWN"),
])
def test_position_taxonomy(mandate,family):
    assert tactical_agent.generate_profile(mandate).position_family == family
