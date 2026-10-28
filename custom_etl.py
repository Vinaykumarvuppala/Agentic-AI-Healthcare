"""User-configured HCPCS ETL exports: chosen fields, release/date windows."""
from __future__ import annotations
from datetime import date
import json
import pandas as pd
from etl_exports import COLS, records

DATE_COLS={"effective_date","termination_date"}
SQL_TYPES={
"hcpcs_code":("VARCHAR(5)","VARCHAR2(5)"),
"change_type":("NVARCHAR(80)","VARCHAR2(80)"),
"old_record":("NVARCHAR(MAX)","CLOB"),
"new_record":("NVARCHAR(MAX)","CLOB"),
"older_release":("NVARCHAR(40)","VARCHAR2(40)"),
"newer_release":("NVARCHAR(40)","VARCHAR2(40)"),
"effective_date":("DATE","DATE"),
"termination_date":("DATE","DATE"),
"date_source":("NVARCHAR(500)","VARCHAR2(500)")
}

def export_rows(frame, columns, verified_dates=None, start=None, end=None, date_field="effective_date"):
    if not columns or len(set(columns))!=len(columns) or any(c not in COLS for c in columns):
        raise ValueError("Select at least one unique supported export field")
    if date_field not in DATE_COLS:
        raise ValueError("Invalid date filter field")
    if start is not None and end is not None and start>end:
        raise ValueError("Start date must be on or before end date")
    all_rows=records(frame,verified_dates)
    selected=[]
    for record in all_rows:
        if start is not None or end is not None:
            raw=record[date_field]
            if not raw:
                continue  # unknown date cannot pass a date filter
            value=date.fromisoformat(raw)
            if start is not None and value<start: continue
            if end is not None and value>end: continue
        selected.append({c:record[c] for c in columns})
    return selected

def render_export(rows, columns, destination):
    if destination=="json":
        return json.dumps(rows,ensure_ascii=False,indent=2)
    if destination=="jsonl":
        return "".join(json.dumps(row,ensure_ascii=False)+"\n" for row in rows)
    if destination not in ("sqlserver","oracle"):
        raise ValueError("Unsupported destination")
    sqlserver=destination=="sqlserver"
    table="dbo.cms_hcpcs_export" if sqlserver else "cms_hcpcs_export"
    type_index=0 if sqlserver else 1
    ddl=",\n ".join(c+" "+SQL_TYPES[c][type_index]+" NULL" for c in columns)
    if sqlserver:
        lines=["-- Run CREATE TABLE once; inserts are not automatically idempotent.",
               f"IF OBJECT_ID(N'{table}',N'U') IS NULL CREATE TABLE {table} (\n {ddl}\n);"]
    else:
        lines=["-- Run CREATE TABLE once; rerun INSERT statements only when appropriate.",
               f"CREATE TABLE {table} (\n {ddl}\n);"]
    for row in rows:
        values=[]
        for col in columns:
            val=row[col]
            if val is None:
                values.append("NULL")
            elif col in DATE_COLS and not sqlserver:
                values.append("DATE '"+val+"'")
            else:
                prefix="N" if sqlserver and col not in ("hcpcs_code",) else ""
                values.append(prefix+"'"+str(val).replace("'","''")+"'")
        lines.append(f"INSERT INTO {table} ("+", ".join(columns)+") VALUES ("+", ".join(values)+");")
    if not sqlserver: lines.append("COMMIT;")
    return "\n".join(lines)+"\n"
