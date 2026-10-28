from io import BytesIO
from zipfile import ZipFile
import pandas as pd
from cms_source_diagnostics import inspect_archive

def test_detect_real_sheet_headers():
    workbook=BytesIO()
    pd.DataFrame([["HCPCS Code","Effective Date","Termination Date"],["A1234","20261001",""]]).to_excel(workbook,header=False,index=False)
    archive=BytesIO()
    with ZipFile(archive,"w") as z:
        z.writestr("HCPC2026_OCT_ANWEB_Transaction Report.xlsx",workbook.getvalue())
    rows=inspect_archive(archive.getvalue())
    assert len(rows)==1
    assert "Effective Date" in rows[0]["headers"]
    assert rows[0]["sheet"]=="Sheet1"
