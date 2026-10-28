"""Inspect CMS ZIP transaction workbook structures before interpreting dated fields."""
from io import BytesIO
from zipfile import ZipFile
import pandas as pd

def inspect_archive(blob: bytes) -> list[dict]:
    results=[]
    with ZipFile(BytesIO(blob)) as archive:
        for item in archive.infolist():
            if item.is_dir() or not item.filename.lower().endswith(".xlsx"):
                continue
            if item.file_size > 15_000_000:
                results.append({"filename":item.filename,"sheet":"(skipped)","headers":"","note":"Oversized spreadsheet"})
                continue
            try:
                workbook=pd.ExcelFile(BytesIO(archive.read(item)))
                for sheet in workbook.sheet_names:
                    preview=pd.read_excel(workbook,sheet_name=sheet,header=None,nrows=12,dtype=str)
                    headers=[]
                    for index in range(min(12,len(preview))):
                        cells=[str(x).strip() for x in preview.iloc[index] if pd.notna(x)]
                        if any("hcpcs" in x.lower() for x in cells):
                            headers=cells
                            break
                    results.append({"filename":item.filename,"sheet":sheet,
                                    "headers":" | ".join(headers)[:1500],
                                    "note":"Detected candidate header" if headers else "No HCPCS header detected in first 12 rows"})
            except Exception as exc:
                results.append({"filename":item.filename,"sheet":"(unreadable)","headers":"",
                                "note":type(exc).__name__})
    return results
