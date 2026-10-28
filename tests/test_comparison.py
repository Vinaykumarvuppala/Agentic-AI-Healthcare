import pandas as pd
import pytest
from comparison import compare_codes, variants

@pytest.fixture
def sample():
    return pd.DataFrame([
        {"hcpc":"99213","sdesc":"Office est low","modifier":"","proc_stat":"A","nfac_total":"2.5","fac_total":"1.5","conv_fact":"33"},
        {"hcpc":"99214","sdesc":"Office est mod","modifier":"","proc_stat":"A","nfac_total":"3.5","fac_total":"2.5","conv_fact":"33"},
        {"hcpc":"99214","sdesc":"Office est mod","modifier":"26","proc_stat":"A","nfac_total":"1.2","fac_total":"1.1","conv_fact":"33"},
    ])

def test_comparison(sample):
    out = compare_codes(sample,"99213","99214")
    assert list(out.columns)==["Field","99213","99214","Different"]
    row = out.loc[out["Field"]=="Description"].iloc[0]
    assert row["Different"]=="Yes"

def test_modifier_intersection(sample):
    assert variants(sample,"99213")==[""]
    assert variants(sample,"99214")==["","26"]

def test_identical_code_rejected(sample):
    with pytest.raises(ValueError):
        compare_codes(sample,"99213","99213")

def test_missing_modifier_rejected(sample):
    with pytest.raises(ValueError):
        compare_codes(sample,"99213","99214","26")
