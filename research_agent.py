"""LangGraph tool-routing workflow for CMS code and CMS policy retrieval."""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from cms_agent import extract_hcpcs
from policy_rag import format_citations

class ResearchState(TypedDict, total=False):
    question: str
    source: str
    evidence: list[dict]
    citations: list[dict]
    trace: list[str]
    answer: str

def make_research_agent(code_search, policy_search):
    def plan(state: ResearchState):
        q = state["question"].lower()
        # Explicit source selection makes tool behavior inspectable.
        preferred = state.get("source","Auto")
        policy_signals = ("documentation", "guideline", "policy", "modifier", "medical decision", "g2211", "billing rule")
        route = ("policy" if preferred == "CMS policy PDF" or
                 (preferred == "Auto" and any(x in q for x in policy_signals)) else "codes")
        return {"source":route, "trace":[f"Router: selected {route} retrieval"]}

    def policy(state: ResearchState):
        data = policy_search.search(state["question"], k=5)
        return {"evidence":data, "trace":state["trace"]+[f"Policy retriever: {len(data)} chunks"]}

    def codes(state: ResearchState):
        data = code_search.search(state["question"], k=5, exact_code=extract_hcpcs(state["question"]))
        return {"evidence":data, "trace":state["trace"]+[f"HCPCS retriever: {len(data)} records"]}

    def answer(state: ResearchState):
        citations = format_citations(state.get("evidence",[]))
        body = ["Retrieved evidence (not an LLM-generated interpretation):"]
        for item in citations:
            where = f"page {item['page']}" if item["page"] else "HCPCS listing"
            body.append(f"[{item['number']}] {item['excerpt']} ({where})")
        if not citations:
            body = ["No relevant source evidence was found."]
        return {"citations":citations, "answer":"\n\n".join(body),
                "trace":state["trace"]+["Grounded response: source references attached"]}

    graph = StateGraph(ResearchState)
    for name, fn in [("plan",plan),("policy",policy),("codes",codes),("answer",answer)]:
        graph.add_node(name,fn)
    graph.add_edge(START,"plan")
    graph.add_conditional_edges("plan",lambda state: state["source"],
                                {"policy":"policy","codes":"codes"})
    graph.add_edge("policy","answer")
    graph.add_edge("codes","answer")
    graph.add_edge("answer",END)
    return graph.compile()
