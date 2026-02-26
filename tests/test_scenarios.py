from pathlib import Path


def test_scenario_definitions_exist():
    scenario = Path("tests/scenarios/bug_hunt.md")
    assert scenario.exists()
    assert "Expected supervisor behavior" in scenario.read_text()
