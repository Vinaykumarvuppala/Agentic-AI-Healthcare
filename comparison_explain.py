"""Evidence-based differences for two public CMS indicator records."""
from __future__ import annotations

import pandas as pd

FIELD_EXPLANATIONS = {
    "Description": "The published short descriptions differ. This does not by itself establish clinical coding criteria.",
    "Procedure status": "CMS assigns different procedure-status indicators to these records; consult the official indicator documentation before interpreting them.",
    "Non-facility total RVU": "The published non-facility total relative value units differ; these are not payment amounts.",
    "Facility total RVU": "The published facility total relative value units differ; these are not payment amounts.",
    "Conversion factor": "The published conversion-factor fields differ. Actual Medicare payment depends on additional rules and adjustments.",
    "Modifier": "The modifier values differ; only like-for-like modifier comparisons should be used.",
}

def summarize_differences(comparison: pd.DataFrame, left: str, right: str) -> list[str]:
    """Summarize actual field differences, never infer medical necessity or reimbursement."""
    needed = {"Field", "Different", left, right}
    if not needed.issubset(comparison.columns):
        raise ValueError("Comparison table lacks required fields")
    output = []
    for _, row in comparison.loc[comparison["Different"] == "Yes"].iterrows():
        field = str(row["Field"])
        output.append(
            f"**{field}:** {left} = {row[left]}, {right} = {row[right]}. "
            + FIELD_EXPLANATIONS.get(field, "The published source values differ.")
        )
    return output or ["The selected CMS fields have the same published values for these variants."]
