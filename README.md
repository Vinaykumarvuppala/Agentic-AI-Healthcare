# CMS Agent Lab — public-data Agentic AI prototype

## 🚀 Live Demo

**[Launch CMS Agent Lab on Streamlit](https://agentic-ai-healthcare-edve5pakacrde7pvxy776r.streamlit.app)**

Try public CMS procedure-code lookup and semantic search directly in your browser. The optional LLM explanation requires a configured API key on the deployed app.

A runnable Python project using **real, publicly available CMS Physician Fee Schedule data**, local semantic embeddings, and a **LangGraph** routing/retrieval workflow.

## V5 CMS Research Assistant

The app now includes a chat-style research interface (below the code-search tool) that routes questions with LangGraph between **procedure-code retrieval** and a public **CMS Evaluation and Management Services** guidance PDF. Policy PDF text is extracted page-by-page, chunked with overlap, embedded locally, and returned with page/source links and an execution trace. API-key-enabled LLM synthesis is optional; the default response is extractive, not a generated policy interpretation.

Source policy: https://www.cms.gov/outreach-and-education/medicare-learning-network-mln/mlnproducts/downloads/eval-mgmt-serv-guide-icn006764.pdf

**Scope:** This is a prototype with a single public policy PDF, not a fully autonomous multi-agent system. OpenAI API access is optional and is never needed for the source-backed retrieval mode. The PDF and model downloads on Streamlit Community Cloud may use substantial memory; if they fail, the original HCPCS lookup remains available.

## Dataset and provenance

Official CMS 2026 PFS Indicators CSV (July 2026 release):
https://pfs.data.cms.gov/sites/default/files/data/indicators2026-07-01-2026.csv

CMS dataset directory: https://pfs.data.cms.gov/dataset/7c7df311-5315-4f38-b9ed-fd62f8bebe11

The app fetches the CSV when started. No patient data or private contracts are used. CMS may publish newer quarterly releases; this prototype pins July 2026 for reproducibility.

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

Open the URL shown in the terminal, usually http://localhost:8501.

The first semantic-search run downloads the open MiniLM embedding model and computes vectors; CPU usage and startup time depend on hardware. Exact HCPCS lookup works without model downloads.

## What is implemented

- Real public data ingestion with schema validation.
- HCPCS/CPT code search and table display.
- Sentence-transformer embeddings and cosine similarity retrieval.
- LangGraph state machine: route -> retrieve -> response.
- Source attribution and limitations for medical payment interpretation.
- Unit tests for parsing and HCPCS extraction.

## What is NOT implemented yet

An **optional** generative LLM can synthesize a grounded answer with [numbered citations] from retrieved CMS rows when OPENAI_API_KEY is configured. The LangGraph workflow is still a grounded retrieval agent, **not** an autonomous multi-agent system. There is no real claims adjudication, private provider contract analysis, persistent vector DB, or production deployment. Those are later milestones.

## Tests

```bash
pytest -q
```

## Responsible use

CMS indicators are **not** sufficient to calculate a claim's actual payable amount. Geographic adjustment, service location, eligible provider type, effective date, applicable policy and fee schedule, modifiers, and other factors matter. Do not use this tool for real payment decisions or PHI.

## Optional LLM and deployment

Set `OPENAI_API_KEY` in your local environment or Streamlit Cloud secrets (never commit the key). Choose the LLM explanation checkbox after a semantic search. The default OpenAI model is configured in `llm_rag.py` and may require API access and incur usage charges.

Run in Docker:

```bash
docker build -t cms-agent-lab .
docker run --rm -p 8501:8501 -e OPENAI_API_KEY cms-agent-lab
```

For Streamlit Community Cloud: create an app using this repository, branch `main`, and entrypoint `app.py`. Configure `OPENAI_API_KEY` as a secret for optional LLM answers. Large embedding indexes may exceed free hosting limits; consider an external persisted vector index for production.

GitHub Actions checks unit tests and Python syntax on pushes and pull requests.

## Next phase

- Add public CMS documentation PDFs, extract sections, chunk and embed them.
- Persist vectors in Chroma or pgvector and enable hybrid retrieval.
- Add a configurable LLM (Bedrock or another provider), answer citations, and evaluation.
- Add deterministic reimbursement examples, human approval, and audit logs.
- Containerize, then optionally deploy APIs to AWS ECS/EKS.
