# CMS Agent Lab — public-data Agentic AI prototype

A runnable Python project using **real, publicly available CMS Physician Fee Schedule data**, local semantic embeddings, and a **LangGraph** routing/retrieval workflow.

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

A generative LLM is **not** called. The LangGraph workflow is a grounded retrieval agent, not an autonomous multi-agent system. There is no real claims adjudication, private provider contract analysis, persistent vector DB, or production deployment. Those are later milestones.

## Tests

```bash
pytest -q
```

## Responsible use

CMS indicators are **not** sufficient to calculate a claim's actual payable amount. Geographic adjustment, service location, eligible provider type, effective date, applicable policy and fee schedule, modifiers, and other factors matter. Do not use this tool for real payment decisions or PHI.

## Next phase

- Add public CMS documentation PDFs, extract sections, chunk and embed them.
- Persist vectors in Chroma or pgvector and enable hybrid retrieval.
- Add a configurable LLM (Bedrock or another provider), answer citations, and evaluation.
- Add deterministic reimbursement examples, human approval, and audit logs.
- Containerize, then optionally deploy APIs to AWS ECS/EKS.
