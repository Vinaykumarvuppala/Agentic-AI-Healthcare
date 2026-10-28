from llm_rag import make_evidence, answer_with_llm
import pytest


def test_citations_are_numbered():
    result = make_evidence("office", [
        {"hcpc": "99213", "description": "Office visit", "year": "2026",
         "source": "https://example.gov", "modifier": "", "procedure_status": "A"}
    ])
    assert "[1]" in result
    assert "99213" in result


def test_no_evidence_no_api_call():
    assert "No evidence" in answer_with_llm("question", [])
