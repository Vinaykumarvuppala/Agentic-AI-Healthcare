"""Safe source-preserving CMS quarterly exports for SQL Server, Oracle and cloud JSON."""
import json
import re
import pandas as pd

COLS=("hcpcs_code","change_type","old_record","new_record","older_release","newer_release","effective_date","termination_date","date_source")
def records(frame:pd.DataFrame, verified_dates=None)->list[dict]:
    result=[]
    for row in frame.to_dict("records"):
        def val(k):
            v=row.get(k)
            return None if v is None or pd.isna(v) or str(v).strip()=="" else str(v).strip()
        result.append(dict(hcpcs_code=val("code"),change_type=val("release_change"),
            old_record=val("old_record"),new_record=val("new_record"),
            older_release=val("older_release"),newer_release=val("newer_release"),
            effective_date=None,termination_date=None,date_source=None))
    if verified_dates is not None and not verified_dates.empty:
        dated = verified_dates.copy()
        dated["code"] = dated["code"].astype(str).str.upper()
        for item in result:
            matches = dated.loc[dated["code"] == item["hcpcs_code"]]
            if len(matches) != 1:
                continue
            row = matches.iloc[0]
            for field in ("effective_date", "termination_date"):
                value = row.get(field)
                if pd.notna(value):
                    item[field] = pd.Timestamp(value).strftime("%Y-%m-%d")
            if item["effective_date"] or item["termination_date"]:
                item["date_source"] = "Mapped dated source record; verify provenance"
    return result

def jsonl(frame, verified_dates=None):
    return "\n".join(json.dumps(row,ensure_ascii=False) for row in records(frame, verified_dates))+"\n"

def json_array(frame, verified_dates=None):
    return json.dumps(records(frame, verified_dates),indent=2,ensure_ascii=False)

def sql_literal(value):
    return "NULL" if value is None else "N'"+str(value).replace("'","''")+"'"

def sqlserver_script(frame, verified_dates=None):
    lines=["-- CMS snapshot comparison: effective/termination dates UNKNOWN, not inferred",
"""IF OBJECT_ID(N'dbo.cms_hcpcs_changes', N'U') IS NULL
CREATE TABLE dbo.cms_hcpcs_changes (
 hcpcs_code VARCHAR(5) NOT NULL, change_type NVARCHAR(60) NOT NULL,
 old_record NVARCHAR(MAX) NULL, new_record NVARCHAR(MAX) NULL,
 older_release NVARCHAR(30) NOT NULL, newer_release NVARCHAR(30) NOT NULL,
 effective_date DATE NULL, termination_date DATE NULL, date_source NVARCHAR(500) NULL,
 CONSTRAINT PK_cms_hcpcs_changes PRIMARY KEY (hcpcs_code,older_release,newer_release)
);"""]
    for r in records(frame, verified_dates):
        vals=[sql_literal(r[c]) for c in COLS]
        values=", ".join(vals)
        lines.append("IF NOT EXISTS (SELECT 1 FROM dbo.cms_hcpcs_changes WHERE hcpcs_code = "+sql_literal(r["hcpcs_code"])+
            " AND older_release = "+sql_literal(r["older_release"])+" AND newer_release = "+sql_literal(r["newer_release"])+
            ") INSERT INTO dbo.cms_hcpcs_changes ("+", ".join(COLS)+") VALUES ("+values+");")
    return "\n".join(lines)+"\n"

def oracle_script(frame, verified_dates=None):
    lines=["-- Oracle SQL/PLSQL: dates are NULL because snapshot comparisons cannot establish lifecycle dates.",
"""CREATE TABLE cms_hcpcs_changes (
 hcpcs_code VARCHAR2(5) NOT NULL, change_type VARCHAR2(60) NOT NULL,
 old_record CLOB, new_record CLOB,
 older_release VARCHAR2(30) NOT NULL, newer_release VARCHAR2(30) NOT NULL,
 effective_date DATE, termination_date DATE, date_source VARCHAR2(500),
 CONSTRAINT pk_cms_hcpcs_changes PRIMARY KEY (hcpcs_code,older_release,newer_release)
);
-- Run CREATE TABLE once. Re-run only MERGE statements below for subsequent loads."""]
    # Avoid huge VARCHAR2 literal limits: 180-char snapshots are supported.
    for r in records(frame):
        val=lambda key: "NULL" if r[key] is None else "'"+r[key].replace("'","''")+"'"
        select=", ".join(val(k)+" AS "+k for k in COLS)
        lines.append("MERGE INTO cms_hcpcs_changes t USING (SELECT "+select+" FROM dual) s ON ("+
             "t.hcpcs_code=s.hcpcs_code AND t.older_release=s.older_release AND t.newer_release=s.newer_release) "+
             "WHEN NOT MATCHED THEN INSERT ("+", ".join(COLS)+") VALUES ("+", ".join("s."+c for c in COLS)+");")
    lines.append("COMMIT;")
    return "\n".join(lines)+"\n"
