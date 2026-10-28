import pandas as pd
from cms_agent import normalize_columns, build_documents, extract_hcpcs


def test_normalize_and_documents():
    df = pd.DataFrame([{"HCPC": "99213 ", "SDESC": "Office/outpatient visit", "YEAR": "2026"}])
    normalized = normalize_columns(df)
    assert normalized.loc[0, "hcpc"] == "99213"
    docs = build_documents(normalized)
    assert docs[0]["hcpc"] == "99213"
    assert docs[0]["year"] == "2026"


def test_code_extraction():
    assert extract_hcpcs("Tell me about 99213 reimbursement") == "99213"
    assert extract_hcpcs("What is G2211?") == "G2211"
    assert extract_hcpcs("outpatient services") is None
