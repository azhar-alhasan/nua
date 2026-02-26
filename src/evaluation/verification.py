from __future__ import annotations


def validate_final_output(final_output: str | None) -> dict:
    errors: list[str] = []
    text = (final_output or "").strip()
    if not text:
        errors.append("final_output is empty")
    if len(text.split()) < 3:
        errors.append("final_output is too short")
    return {"is_valid": len(errors) == 0, "errors": errors}
