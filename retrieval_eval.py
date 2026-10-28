"""Reproducible retrieval ranking metrics against manually specified expected codes."""
from __future__ import annotations

CASES=[
 {"question":"established patient office visit","expected":["99213","99214"]},
 {"question":"new patient outpatient evaluation","expected":["99202","99203"]},
 {"question":"preventive medicine visit","expected":["99395","99396"]},
 {"question":"visit complexity add-on","expected":["G2211"]},
]
def evaluate(cases, search_fn, k=5):
    rows=[]
    for case in cases:
        returned=list(dict.fromkeys(search_fn(case["question"],k)))[:k]
        expected=set(case["expected"])
        hits=len(expected.intersection(returned))
        first=next((i+1 for i,c in enumerate(returned) if c in expected),None)
        rows.append({"question":case["question"],"expected":sorted(expected),
                     "returned":returned,"recall_at_k":hits/len(expected),
                     "precision_at_k":hits/k,
                     "reciprocal_rank":0 if first is None else 1/first})
    return {"cases":rows,
            "mean_recall_at_k":sum(x["recall_at_k"] for x in rows)/len(rows) if rows else 0,
            "mean_reciprocal_rank":sum(x["reciprocal_rank"] for x in rows)/len(rows) if rows else 0}
