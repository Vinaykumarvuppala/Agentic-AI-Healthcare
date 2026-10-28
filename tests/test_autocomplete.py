import pandas as pd
from autocomplete import suggest

def fixture():
    return pd.DataFrame([
        {"hcpc": "99213", "sdesc": "Office o/p est low 20 min"},
        {"hcpc": "99214", "sdesc": "Office o/p est mod 30 min"},
        {"hcpc": "A2222", "sdesc": "Unrelated procedure"},
        {"hcpc": "G2221", "sdesc": "Other service"},
        {"hcpc": "99213", "sdesc": "Office o/p est low 20 min"},
    ])

def test_prefix_code_and_description():
    assert suggest(fixture(), "992")[0]["code"] == "99213"
    assert all("Office" in row["description"] for row in suggest(fixture(), "office"))

def test_numeric_fragment_and_dedup():
    codes = [row["code"] for row in suggest(fixture(), "22")]
    assert "A2222" in codes and "G2221" in codes
    assert len(codes) == len(set(codes))

def test_empty_and_unknown():
    assert suggest(fixture(), "") == []
    assert suggest(fixture(), "nonmatchingxyz") == []

def test_plain_language_aliases():
    codes = [x["code"] for x in suggest(fixture(), "doctor visit")]
    assert "99213" in codes

def test_typo_fallback():
    codes = [x["code"] for x in suggest(fixture(), "offce")]
    assert "99213" in codes

def test_numeric_prefix_wins():
    rows = suggest(fixture(), "992", limit=2)
    assert len(rows) == 2
    assert all(x["code"].startswith("992") for x in rows)

def test_limit_and_no_fuzzy_numeric():
    assert len(suggest(fixture(), "office", limit=1)) == 1
    assert suggest(fixture(), "998877") == []
