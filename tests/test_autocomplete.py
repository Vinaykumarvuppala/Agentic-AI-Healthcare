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
