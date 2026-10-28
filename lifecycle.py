"""Date-aware HCPCS Level II lifecycle checks from explicit dated source records.

Never infer a code's add/termination date from a PFS release timestamp.
"""
from __future__ import annotations
from datetime import date
import re
import pandas as pd

REQUIRED = {"code", "effective_date", "termination_date"}
SOURCE = "https://www.cms.gov/medicare/coding-billing/healthcare-common-procedure-system/quarterly-update"

def clean_date(value):
    if pd.isna(value) or str(value).strip().lower() in ("", "nan", "none", "nat"):
        return pd.NaT
    raw = str(value).strip()
    if re.fullmatch(r"\d{8}", raw):
        return pd.to_datetime(raw, format="%Y%m%d", errors="coerce")
    return pd.to_datetime(raw, errors="coerce")

def normalize_lifecycle(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """mapping: canonical key -> selected actual source column."""
    if not REQUIRED.issubset(mapping):
        raise ValueError("Map code, effective_date, termination_date")
    if any(col not in df.columns for col in mapping.values()):
        raise ValueError("Mapped column not present in uploaded file")
    out = pd.DataFrame()
    out["code"] = df[mapping["code"]].fillna("").astype(str).str.strip().str.upper()
    out["effective_date"] = df[mapping["effective_date"]].map(clean_date)
    out["termination_date"] = df[mapping["termination_date"]].map(clean_date)
    desc_col = mapping.get("description")
    out["description"] = df[desc_col].fillna("").astype(str) if desc_col else ""
    out = out.loc[out["code"].str.fullmatch(r"[A-Z][0-9A-Z]{4}", na=False)].copy()
    out = out.drop_duplicates(subset=["code","effective_date","termination_date"])
    if out.empty:
        raise ValueError("No valid five-character alphanumeric HCPCS Level II codes in selected columns")
    # Reject apparent date inversion instead of publishing misleading statuses.
    invalid = out["effective_date"].notna() & out["termination_date"].notna() & (out["termination_date"] < out["effective_date"])
    if invalid.any():
        raise ValueError("Termination date precedes effective date for some rows")
    return out.reset_index(drop=True)

def classify(df: pd.DataFrame, as_of: date, since: date) -> pd.DataFrame:
    if since > as_of:
        raise ValueError("Comparison start must not be after as-of date")
    result = df.copy()
    day = pd.Timestamp(as_of)
    start = pd.Timestamp(since)
    add = result["effective_date"]
    end = result["termination_date"]
    # CMS termination dates are last valid days, not first invalid days.
    active = add.notna() & (add <= day) & (end.isna() | (end >= day))
    expired = end.notna() & (end < day)
    future = add.notna() & (add > day)
    result["status"] = "Unknown date"
    result.loc[active,"status"] = "Active"
    result.loc[expired,"status"] = "Expired"
    result.loc[future,"status"] = "Future"
    result["change"] = "Existing / undetermined"
    result.loc[add.notna() & (add >= start) & (add <= day),"change"] = "New in period"
    result.loc[end.notna() & (end >= start) & (end < day),"change"] = "Expired in period"
    return result
