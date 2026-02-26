from evaluation.evaluators import evaluate_run
from evaluation.metrics import MetricCollector
from evaluation.verification import validate_final_output


def test_validate_final_output_rejects_empty():
    result = validate_final_output("")
    assert result["is_valid"] is False
    assert result["errors"]


def test_metric_collector_counts():
    metrics = MetricCollector()
    metrics.inc("runs")
    metrics.inc("runs", 2)
    assert metrics.snapshot()["runs"] == 3


def test_evaluate_run_returns_expected_keys():
    result = evaluate_run(
        objective="Research Python frameworks and write report",
        final_output="Researched top frameworks and wrote report with findings.",
        artifacts={"report.md": "content"},
    )
    assert "objective_coverage" in result
    assert result["artifact_count"] == 1
