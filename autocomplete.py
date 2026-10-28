"""Fast deterministic autocomplete for public CMS HCPCS codes and descriptions."""
from __future__ import annotations
import re
import pandas as pd

def suggest(df: pd.DataFrame, query: str, limit: int = 80) -> list[dict]:
    q = " ".join(query.strip().lower().split())
    if not q:
        return []
    data = df[["hcpc","sdesc"]].dropna().drop_duplicates(subset=["hcpc"]).copy()
    data["hcpc"] = data["hcpc"].astype(str).str.strip()
    data["sdesc"] = data["sdesc"].astype(str).str.strip()
    code = data["hcpc"].str.lower()
    desc = data["sdesc"].str.lower()
    aliases = {
        "office visits": ["office", "o/p", "outpatient"],
        "office visit": ["office", "o/p", "outpatient"],
        "doctor visit": ["office", "o/p"],
        "checkup": ["preventive", "prev visit"],
        "physical": ["preventive", "prev visit"],
        "emergency room": ["emergency", "er visit"],
        "xray": ["x-ray", "radiography"],
        "x-ray": ["x-ray", "radiography"],
    }
    words = [w for w in re.split(r"\W+", q) if w]
    # Rank exact/prefix codes first, followed by description phrases and token matches.
    score = pd.Series(-1, index=data.index, dtype="int64")
    score.loc[code == q] = 100
    score.loc[(code.str.startswith(q)) & (score < 90)] = 90
    score.loc[(desc.str.startswith(q)) & (score < 75)] = 75
    score.loc[(desc.str.contains(q, regex=False)) & (score < 65)] = 65
    for alias in aliases.get(q, []):
        match_alias = desc.str.contains(alias, regex=False)
        score.loc[match_alias & (score < 58)] = 58
    if words:
        tokens_match = pd.Series(True, index=data.index)
        for word in words:
            tokens_match &= desc.str.contains(word, regex=False)
        score.loc[tokens_match & (score < 50)] = 50
    # Short numeric fragments should match anywhere in HCPCS codes.
    if len(q) >= 2 and any(ch.isdigit() for ch in q):
        score.loc[code.str.contains(q, regex=False) & (score < 35)] = 35
    matches = data[score >= 0].copy()
    if matches.empty:
        return []
    matches["score"] = score[score >= 0]
    matches = matches.sort_values(["score","hcpc"],ascending=[False,True]).head(limit)
    return [{"code":r.hcpc,"description":r.sdesc} for r in matches.itertuples(index=False)]
