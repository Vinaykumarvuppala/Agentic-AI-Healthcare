import pytest
from investigation import build_report

def test_report_contains_evidence_and_uncertainties():
    report=build_report("99213","What does CMS say?",
        [{"sdesc":"Office visit","modifier":"","proc_stat":"A"}],
        [{"text":"Example passage","source":"https://www.cms.gov/test.pdf","page":4}],
        ["CMS indicator lookup"])
    assert "99213" in report
    assert "Example passage" in report
    assert "PDF page 4" in report
    assert "human verification" in report

def test_blank_question_rejected():
    with pytest.raises(ValueError):
        build_report("99213"," ",[],[],[])

def test_missing_policy_is_explicit():
    report=build_report("99213","Question",[],[],[])
    assert "No supporting policy passages retrieved." in report
