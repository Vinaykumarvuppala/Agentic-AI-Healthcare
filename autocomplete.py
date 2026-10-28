"""Ranked, typo-tolerant HCPCS and procedure-description autocomplete."""
from __future__ import annotations

from difflib import get_close_matches
import re
import pandas as pd

ALIASES = {
    "office visits": ("office", "o/p", "outpatient"),
    "office visit": ("office", "o/p", "outpatient"),
    "doctor visit": ("office", "o/p", "outpatient"),
    "doctor": ("office", "o/p"),
    "checkup": ("prev visit", "preventive"),
    "annual physical": ("prev visit", "preventive"),
    "physical": ("preventive", "prev visit"),
    "emergency room": ("emerg", "emergency", "er visit"),
    "xray": ("x-ray", "radiograph", "radiologic"),
    "x-ray": ("x-ray", "radiograph", "radiologic"),
    "blood test": ("blood", "laboratory"),
}

def _clean(value: str) -> str:
    return " ".join(str(value).strip().lower().split())

def suggest(df: pd.DataFrame, query: str, limit: int = 80) -> list[dict]:
    """Returns at most limit unique codes. Prefix > phrase > synonyms > fragments.

    Fuzzy matching is a fallback only, to avoid replacing a good exact match
    with an unrelated similarly-spelled service.
    """
    q = _clean(query)
    if not q or limit < 1:
        return []
    data = df[["hcpc", "sdesc"]].dropna().copy()
    data["hcpc"] = data["hcpc"].astype(str).str.strip().str.upper()
    data["sdesc"] = data["sdesc"].astype(str).str.strip()
    data = data.drop_duplicates(subset=["hcpc"], keep="first")
    code = data["hcpc"].str.lower()
    desc = data["sdesc"].str.lower()
    scores = pd.Series(-1, index=data.index, dtype="int64")
    def boost(mask, weight):
        scores.loc[mask & (scores < weight)] = weight

    boost(code == q, 110)
    boost(code.str.startswith(q), 100)
    boost(desc.str.startswith(q), 85)
    boost(desc.str.contains(q, regex=False), 75)
    for alias in ALIASES.get(q, ()):
        boost(desc.str.contains(alias, regex=False), 68)

    words = [word for word in re.findall(r"[a-z0-9]+", q) if word]
    if words:
        mask = pd.Series(True, index=data.index)
        for word in words:
            mask &= desc.str.contains(word, regex=False)
        boost(mask, 60)

    if len(q) >= 2 and any(ch.isdigit() for ch in q):
        boost(code.str.contains(q, regex=False), 40)

    # Abbreviated CMS descriptions ("o/p", "est", "prev") often don't contain
    # the layperson's exact phrase. Try a nearby dictionary term only when
    # nothing matched and the query consists of alphabetic words.
    if not (scores >= 0).any() and len(q) >= 4 and q.replace(" ", "").isalpha():
        vocabulary = set()
        for value in desc:
            vocabulary.update(token for token in re.findall(r"[a-z]{4,}", value) if len(token) <= 18)
        repaired = []
        for word in words:
            if word in vocabulary:
                repaired.append(word)
            else:
                choices = get_close_matches(word, vocabulary, n=1, cutoff=0.78)
                repaired.append(choices[0] if choices else word)
        if repaired != words:
            mask = pd.Series(True, index=data.index)
            for word in repaired:
                mask &= desc.str.contains(word, regex=False)
            boost(mask, 48)

    matches = data.loc[scores >= 0].copy()
    if matches.empty:
        return []
    matches["score"] = scores.loc[scores >= 0]
    matches = matches.sort_values(["score", "hcpc"], ascending=[False, True]).head(limit)
    return [{"code":r.hcpc, "description":r.sdesc} for r in matches.itertuples(index=False)]
