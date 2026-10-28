"""Extract explicitly dated HCPCS changes from CMS transaction Excel files in official ZIPs.

Fail closed when dates or columns cannot be validated. No inferred dates.
"""
from io import BytesIO
from zipfile import ZipFile
import re
import pandas as pd
from cms_quarterly import CMS_PAGE, discover_releases, download_bytes, RELEASES
from lifecycle import clean_date
from cms_source_diagnostics import inspect_archive

def _norm(text):
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())

def _find(headers, aliases):
    for alias in aliases:
        for col in headers:
            if _norm(col)==_norm(alias):
                return col
    return None

def parse_transaction_workbook(blob: bytes, source: str) -> pd.DataFrame:
    with ZipFile(BytesIO(blob)) as archive:
        sheets=[x for x in archive.namelist() if x.lower().endswith((".xlsx",".xls")) and
                ("transaction" in x.lower() or "trans" in x.lower())]
        if not sheets:
            raise ValueError("No CMS transaction spreadsheet found in ZIP; cannot verify dates")
        book=pd.ExcelFile(BytesIO(archive.read(sheets[0])))
        rows=[]
        for tab in book.sheet_names:
            raw=pd.read_excel(book,sheet_name=tab,header=None,dtype=str,nrows=100000)
            for index in range(min(20,len(raw))):
                names=[str(v).strip() if pd.notna(v) else "" for v in raw.iloc[index].tolist()]
                code_col=_find(names,["HCPCS","HCPCS Code","HCPCS Level II Code","Code"])
                eff_col=_find(names,["Effective Date","Action Effective Date","HCPCS Action Effective Date","Add Date"])
                term_col=_find(names,["Termination Date","Term Date","HCPCS Termination Date","Deletion Date","Discontinuation Date"])
                if code_col is None or (eff_col is None and term_col is None):
                    continue
                data=raw.iloc[index+1:].copy()
                data.columns=names
                for _,record in data.iterrows():
                    code=str(record.get(code_col,"")).strip().upper()
                    if not re.fullmatch(r"[A-Z][A-Z0-9]{4}",code):
                        continue
                    effective=clean_date(record.get(eff_col)) if eff_col else pd.NaT
                    termination=clean_date(record.get(term_col)) if term_col else pd.NaT
                    if pd.isna(effective) and pd.isna(termination):
                        continue
                    if pd.notna(effective) and pd.notna(termination) and termination<effective:
                        continue
                    rows.append({"code":code,"effective_date":effective,"termination_date":termination,
                                 "date_source":source+"#"+sheets[0]+"/"+tab})
                break
        if not rows:
            raise ValueError("No unambiguous dated code rows found; CMS workbook layout needs mapping")
        result=pd.DataFrame(rows).drop_duplicates()
        # Multiple rows for the same code can represent distinct events.
        # Do not collapse them into a single effective/termination period.
        counts=result.groupby("code").size()
        ambiguous=set(counts.index[counts>1])
        result=result.loc[~result["code"].isin(ambiguous)]
        if result.empty:
            raise ValueError("All dated codes had conflicting source records")
        return result.reset_index(drop=True)

def fetch_dated_release(release: str):
    import requests
    page=requests.get(CMS_PAGE,timeout=30)
    page.raise_for_status()
    links=discover_releases(page.text)
    if release not in links:
        raise ValueError("Official release not found: "+release)
    return parse_transaction_workbook(download_bytes(links[release]),links[release])


def inspect_official_release(release: str):
    """Download the official source and return safe schema diagnostic metadata."""
    import requests
    page=requests.get(CMS_PAGE,timeout=30)
    page.raise_for_status()
    links=discover_releases(page.text)
    if release not in links:
        raise ValueError("Official release not found: "+release)
    data=download_bytes(links[release])
    return inspect_archive(data),links[release]
