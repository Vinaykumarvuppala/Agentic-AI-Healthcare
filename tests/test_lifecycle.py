from datetime import date
import pandas as pd
import pytest
from lifecycle import normalize_lifecycle, classify

def data():
    return pd.DataFrame({
        "HCPCS":["A1234","G1111","J2222","99213"],
        "Add Date":["20261001","20260101","20250101","20260101"],
        "Termination Date":["","20260930","",""],
        "Description":["New","Ended","Active","Numeric CPT"],
    })

def loaded():
    return normalize_lifecycle(data(),{
        "code":"HCPCS","effective_date":"Add Date",
        "termination_date":"Termination Date","description":"Description"
    })

def test_level_two_and_dates():
    rows=loaded()
    assert len(rows)==3
    assert str(rows.loc[rows["code"]=="A1234","effective_date"].iloc[0].date())=="2026-10-01"

def test_new_and_expired_at_october():
    rows=classify(loaded(),date(2026,10,28),date(2026,7,1))
    assert rows.loc[rows["code"]=="A1234","change"].iloc[0]=="New in period"
    assert rows.loc[rows["code"]=="G1111","status"].iloc[0]=="Expired"
    assert rows.loc[rows["code"]=="G1111","change"].iloc[0]=="Expired in period"

def test_termination_day_is_valid():
    rows=classify(loaded(),date(2026,9,30),date(2026,7,1))
    assert rows.loc[rows["code"]=="G1111","status"].iloc[0]=="Active"

def test_unknown_dates_not_active():
    df=pd.DataFrame({"code":["A9999"],"effective_date":[""],"termination_date":[""]})
    norm=normalize_lifecycle(df,{"code":"code","effective_date":"effective_date","termination_date":"termination_date"})
    assert classify(norm,date(2026,10,28),date(2026,7,1)).iloc[0]["status"]=="Unknown date"
