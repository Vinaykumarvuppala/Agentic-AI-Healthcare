"""Stateful LangGraph pipeline for CMS investigation, without autonomous payment decisions."""
from typing import TypedDict, Any
from langgraph.graph import StateGraph, START, END
from investigation import build_report

class InvestigationState(TypedDict, total=False):
    code: str
    question: str
    records: list[dict[str,Any]]
    evidence: list[dict[str,Any]]
    trace: list[str]
    warnings: list[str]
    report: str

def make_investigation_graph(record_lookup, policy_lookup=None):
    def validate(state: InvestigationState):
        code = state.get("code","").upper()
        if not code or not state.get("question","").strip():
            raise ValueError("Provide a code and a research question")
        return {"code":code,"trace":["Validation: code and question received"],"warnings":[]}
    def retrieve(state: InvestigationState):
        records = record_lookup(state["code"])
        return {"records":records,"trace":state["trace"]+[f"CMS PFS lookup: {len(records)} record(s)"]}
    def policy(state: InvestigationState):
        evidence=[]
        warnings=[]
        if policy_lookup is not None and state["code"].startswith(("992","993")):
            try:
                evidence=policy_lookup(state["question"]+" "+state["code"])
            except Exception as exc:
                warnings.append(f"Policy retrieval unavailable ({type(exc).__name__})")
        else:
            warnings.append("E/M guide retrieval skipped for this code family")
        return {"evidence":evidence,"warnings":warnings,
                "trace":state["trace"]+[f"CMS guidance retrieval: {len(evidence)} passage(s)"]}
    def review(state: InvestigationState):
        warnings=list(state["warnings"])
        if not state["records"]:
            warnings.append("No source record found")
        if not state["evidence"]:
            warnings.append("No supporting policy passage retrieved")
        return {"warnings":warnings,"trace":state["trace"]+["Evidence validation and uncertainty flags"]}
    def report(state: InvestigationState):
        result=build_report(state["code"],state["question"],state["records"],state["evidence"],
                            state["trace"] + state["warnings"] + ["Human review required before operational use"])
        return {"report":result}
    graph=StateGraph(InvestigationState)
    for name, fn in [("validate",validate),("retrieve",retrieve),("policy",policy),("review",review),("report",report)]:
        graph.add_node(name,fn)
    graph.add_edge(START,"validate")
    graph.add_edge("validate","retrieve")
    graph.add_edge("retrieve","policy")
    graph.add_edge("policy","review")
    graph.add_edge("review","report")
    graph.add_edge("report",END)
    return graph.compile()
