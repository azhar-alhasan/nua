from __future__ import annotations

from evaluation.verification import validate_final_output


def evaluate_run(objective: str, final_output: str, artifacts: dict[str, str] | None = None) -> dict:
    """
    Lightweight evaluator intended for LangSmith trace post-processing.
    Returns deterministic quality signals to support regression checks.
    """
    artifacts = artifacts or {}
    verification = validate_final_output(final_output)
    objective_terms = {w.lower() for w in objective.split() if len(w) > 3}
    output_terms = {w.lower() for w in final_output.split()}
    overlap = len(objective_terms.intersection(output_terms))
    coverage = overlap / max(1, len(objective_terms))
    return {
        "valid_output": verification["is_valid"],
        "validation_errors": verification["errors"],
        "objective_coverage": round(coverage, 3),
        "artifact_count": len(artifacts),
    }
