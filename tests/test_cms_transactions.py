from io import BytesIO
from zipfile import ZipFile
import pandas as pd
import pytest
from cms_transactions import parse_transaction_workbook

def workbook_bytes(rows):
    b=BytesIO()
    pd.DataFrame(rows).to_excel(b,index=False)
    return b.getvalue()

def zipped(rows):
    b=BytesIO()
    with ZipFile(b,"w") as z:
        z.writestr("HCPC2026_OCT_ANWEB_Transaction Report.xlsx",workbook_bytes(rows))
    return b.getvalue()

def test_explicit_dates_only():
    result=parse_transaction_workbook(zipped([
        {"HCPCS Code":"A1234","Effective Date":"20261001","Termination Date":None},
        {"HCPCS Code":"G1234","Effective Date":None,"Termination Date":"20260930"},
    ]),"https://www.cms.gov/source.zip")
    assert len(result)==2
    assert result.loc[result["code"]=="A1234","effective_date"].iloc[0].year==2026
    assert pd.isna(result.loc[result["code"]=="G1234","effective_date"].iloc[0])

def test_missing_date_fields_fail_closed():
    with pytest.raises(ValueError,match="No unambiguous"):
        parse_transaction_workbook(zipped([{"HCPCS Code":"A1234","Description":"Test"}]),"https://www.cms.gov/test.zip")
