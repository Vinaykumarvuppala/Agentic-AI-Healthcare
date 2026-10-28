from datetime import date
import json
import pandas as pd
import pytest
from custom_etl import export_rows,render_export

def sample():
    return pd.DataFrame([{"code":"A2046","release_change":"Appeared in newer release","old_record":"",
        "new_record":"O'Brien material","older_release":"July 2026","newer_release":"October 2026"}])

def dated():
    return pd.DataFrame([{"code":"A2046","effective_date":pd.Timestamp("2026-10-01"),
        "termination_date":pd.NaT}])

def test_selected_fields_only():
    cols=["hcpcs_code","effective_date"]
    rows=export_rows(sample(),cols,dated())
    assert list(rows[0])==cols
    assert rows[0]["effective_date"]=="2026-10-01"
    assert list(json.loads(render_export(rows,cols,"json"))[0])==cols

def test_inclusive_date_range_and_missing_dates():
    cols=["hcpcs_code","effective_date"]
    assert len(export_rows(sample(),cols,dated(),date(2026,10,1),date(2026,10,1)))==1
    assert export_rows(sample(),cols,None,date(2026,10,1),date(2026,10,31))==[]
    assert export_rows(sample(),cols,dated(),date(2026,11,1),date(2026,12,31))==[]

def test_sql_respects_selected_columns_and_escapes_quotes():
    cols=["hcpcs_code","new_record"]
    rows=export_rows(sample(),cols)
    for dialect in ("sqlserver","oracle"):
        sql=render_export(rows,cols,dialect)
        assert "O''Brien" in sql
        assert "effective_date" not in sql

def test_invalid_range():
    with pytest.raises(ValueError):
        export_rows(sample(),["hcpcs_code"],None,date(2026,10,2),date(2026,10,1))
