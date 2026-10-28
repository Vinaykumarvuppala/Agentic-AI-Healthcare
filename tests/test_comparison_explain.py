import pandas as pd
import pytest
from comparison_explain import summarize_differences

def test_explain_only_actual_differences():
    df = pd.DataFrame([
        {"Field":"Description","99213":"low","99214":"moderate","Different":"Yes"},
        {"Field":"Procedure status","99213":"A","99214":"A","Different":"No"},
    ])
    notes=summarize_differences(df,"99213","99214")
    assert len(notes)==1
    assert "moderate" in notes[0]
    assert "Procedure status" not in notes[0]

def test_equal_values():
    df=pd.DataFrame([{"Field":"Modifier","99213":"—","99214":"—","Different":"No"}])
    assert "same published values" in summarize_differences(df,"99213","99214")[0]

def test_missing_columns():
    with pytest.raises(ValueError):
        summarize_differences(pd.DataFrame(), "99213", "99214")
