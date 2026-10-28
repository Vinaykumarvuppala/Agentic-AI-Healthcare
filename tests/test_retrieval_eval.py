from retrieval_eval import evaluate,CASES

def test_metrics():
    result=evaluate([{"question":"visit","expected":["99213","99214"]}],lambda q,k:["99214","D9430"],k=2)
    assert result["mean_recall_at_k"]==0.5
    assert result["mean_reciprocal_rank"]==1.0

def test_empty_cases():
    assert evaluate([],lambda q,k:[])["mean_recall_at_k"]==0
