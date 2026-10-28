"""Grounded CMS Physician Fee Schedule search agent (public data only)."""
from __future__ import annotations

import io
import re
from functools import lru_cache
from typing import TypedDict

import numpy as np
import pandas as pd
import requests
from langgraph.graph import END, START, StateGraph

# Official CMS CSV source; data is retrieved at runtime, not reproduced in GitHub.
CMS_CSV_URL = "https://pfs.data.cms.gov/sites/default/files/data/indicators2026-07-01-2026.csv"
REQUIRED_COLUMNS = {"hcpc", "sdesc", "year"}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip().lower() for col in df.columns]
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"CMS file missing columns: {sorted(missing)}")
    df["hcpc"] = df["hcpc"].astype(str).str.strip().str.upper()
    df["sdesc"] = df["sdesc"].fillna("").astype(str).str.strip()
    if "modifier" not in df:
        df["modifier"] = ""
    df["modifier"] = df["modifier"].fillna("").astype(str).str.strip()
    return df


@lru_cache(maxsize=1)
def load_cms_data() -> pd.DataFrame:
    response = requests.get(CMS_CSV_URL, timeout=90, headers={"User-Agent": "CMS-PFS-Educational-Agent/0.1"})
    response.raise_for_status()
    return normalize_columns(pd.read_csv(io.BytesIO(response.content), dtype=str, low_memory=False))


def build_documents(df: pd.DataFrame) -> list[dict]:
    result = []
    for _, row in df.iterrows():
        code = str(row["hcpc"])
        desc = str(row["sdesc"])
        if not code or not desc:
            continue
        result.append({
            "text": f"HCPCS {code}. {desc}. Modifier {row.get('modifier','')}. Procedure status {row.get('proc_stat','')}.",
            "hcpc": code,
            "description": desc,
            "modifier": str(row.get("modifier", "")),
            "procedure_status": str(row.get("proc_stat", "")),
            "year": str(row.get("year", "")),
            "source": CMS_CSV_URL,
        })
    return result


class VectorSearch:
    """Local embeddings + cosine search. Downloads an open embedding model on first use."""

    def __init__(self, documents: list[dict], model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        if not documents:
            raise ValueError("No searchable CMS records")
        self.documents = documents
        self.model = SentenceTransformer(model_name)
        self.vectors = self.model.encode(
            [d["text"] for d in documents], batch_size=128,
            normalize_embeddings=True, show_progress_bar=False
        )

    def search(self, query: str, k: int = 5, exact_code: str | None = None) -> list[dict]:
        query = query.strip()
        if not query:
            return []
        if exact_code:
            matches = [d for d in self.documents if d["hcpc"] == exact_code.upper()]
            if matches:
                return [dict(d, score=1.0) for d in matches[:k]]
        q = self.model.encode([query], normalize_embeddings=True)[0]
        scores = np.asarray(self.vectors) @ np.asarray(q)
        indices = np.argsort(-scores)[:k]
        return [dict(self.documents[int(i)], score=float(scores[i])) for i in indices]


def extract_hcpcs(query: str) -> str | None:
    match = re.search(r"\b[A-Z]\d{4}\b|\b\d{5}\b", query.upper())
    return match.group(0) if match else None


class AgentState(TypedDict, total=False):
    question: str
    exact_code: str | None
    results: list[dict]
    answer: str


def build_agent(search: VectorSearch):
    def route(state: AgentState) -> dict:
        return {"exact_code": extract_hcpcs(state["question"])}

    def retrieve(state: AgentState) -> dict:
        return {"results": search.search(state["question"], k=5, exact_code=state.get("exact_code"))}

    def respond(state: AgentState) -> dict:
        rows = state.get("results", [])
        if not rows:
            return {"answer": "No matching CMS records. Try a different query."}
        lines = ["Relevant CMS 2026 Physician Fee Schedule indicator records:"]
        for row in rows:
            lines.append(
                f"- {row['hcpc']} — {row['description']} "
                f"(modifier: {row['modifier'] or 'none'}, status: {row['procedure_status'] or 'not specified'})"
            )
        lines.append("Source: " + CMS_CSV_URL)
        lines.append("This is evidence retrieval, not a Medicare payment quote or claim adjudication.")
        return {"answer": "\n".join(lines)}

    graph = StateGraph(AgentState)
    graph.add_node("route", route)
    graph.add_node("retrieve", retrieve)
    graph.add_node("respond", respond)
    graph.add_edge(START, "route")
    graph.add_edge("route", "retrieve")
    graph.add_edge("retrieve", "respond")
    graph.add_edge("respond", END)
    return graph.compile()
