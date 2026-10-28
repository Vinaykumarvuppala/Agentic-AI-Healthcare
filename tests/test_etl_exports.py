import json
import pandas as pd
from etl_exports import records, jsonl, json_array, sqlserver_script, oracle_script

def fixture():
    return pd.DataFrame([{"code":"A2046","release_change":"Appeared in newer release",
      "old_record":"","new_record":"O'Brien material","older_release":"July 2026","newer_release":"October 2026"}])

def test_json_schema_and_null_dates():
    row=json.loads(jsonl(fixture()).strip())
    assert row["hcpcs_code"]=="A2046"
    assert row["effective_date"] is None
    assert row["termination_date"] is None
    assert len(json.loads(json_array(fixture())))==1

def test_sqlserver_quote_escaping():
    text=sqlserver_script(fixture())
    assert "O''Brien" in text
    assert "effective_date DATE NULL" in text

def test_oracle_upsert_and_dates():
    text=oracle_script(fixture())
    assert "MERGE INTO cms_hcpcs_changes" in text
    assert "O''Brien" in text
    assert "effective_date DATE" in text
