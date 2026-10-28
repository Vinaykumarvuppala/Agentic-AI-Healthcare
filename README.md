# CMS Agent Lab — public-data Agentic AI prototype

## 🚀 Live Demo

**[Launch CMS Agent Lab on Streamlit](https://agentic-ai-healthcare-edve5pakacrde7pvxy776r.streamlit.app)**

Try public CMS procedure-code lookup and semantic search directly in your browser. The optional LLM explanation requires a configured API key on the deployed app.

A runnable Python project using **real, publicly available CMS Physician Fee Schedule data**, local semantic embeddings, and a **LangGraph** routing/retrieval workflow.

## V16 — Automatic official CMS quarterly comparison

The Code lifecycle tab now includes **Load official CMS changes**, which discovers ZIP links on the CMS quarterly update page, downloads the selected full snapshots, parses the ANWEB primary code file and compares the code sets/text. The results show **Appeared in newer release**, **Absent from newer release**, and **Record text changed**, with source links and downloadable CSV. These are snapshot comparisons, **not exact code-level addition/termination dates**. For authoritative dates use the separate upload-and-map transaction record workflow; numeric AMA CPT is outside this Level II scope. CMS may change its file layout; the parser fails visibly rather than inventing results. Network/download reliability on Streamlit Community Cloud has not been verified.

## Guided LangGraph investigation nodes

The Investigate workflow now has explicit validation, PFS record retrieval, optional E/M policy retrieval, uncertainty review, and report-generation nodes. This is a deterministic LangGraph pipeline; it does not autonomously approve reimbursement or coding decisions. Missing source evidence is flagged for human review.

## V15 — HCPCS code lifecycle (new, effective, discontinued)

The **Code lifecycle** tab supports official CMS **HCPCS Level II** dated records, with an upload-and-column-map workflow for CSV or Excel extracts of the official quarterly files. Users can select an as-of date and change-window start, filter active/new/expired/future/unknown records, and export results. The app never treats a PFS data publication date as a code's original effective date. CMS termination date means the **last valid service date**; the next day is discontinued. Data must include explicit code-level dates. The current implementation does **not** automatically parse the CMS raw fixed-width ZIP, and does not cover AMA CPT (numeric Level I) lifecycle dates. Official source: https://www.cms.gov/medicare/coding-billing/healthcare-common-procedure-system/quarterly-update .

## V14 — Guided investigation report

In the **Investigate** tab, select a code, enter a research question and generate a Markdown analyst report. The workflow checks public CMS source rows, optionally retrieves passages from the configured CMS E/M guide for relevant office/outpatient code families, and produces source-linked findings, uncertainties, next steps and execution trace. Download the report as Markdown. No API key required; it does not infer real-world billing compliance or payment decisions.

## V13 — Explain code differences with evidence

The **Compare codes** tab now includes **Why are these codes different?**, which explains differences in the actual CMS fields without claiming that either code is medically appropriate. An optional **Retrieve official guidance** button searches chunks of the configured CMS Evaluation and Management PDF, providing source URLs and page references. Retrieval is not proof of code applicability; check coding rules, effective dates, and the complete source before making decisions.

## V12 — Side-by-side HCPCS comparison

The **Compare codes** tab supports searchable HCPCS selectors, such as 99213 vs 99214. It only compares common modifier variants to avoid misleading comparisons. A table highlights differences in description, procedure status, RVU totals, and conversion-factor fields, with a differences-only filter and downloadable CSV. These are reference fields, **not** calculated reimbursement amounts.

## V11 — Filter results and inspect procedure details

Meaning-based results now include a **Filter related results** dropdown with broad HCPCS/code-family browsing categories, and pagination runs over the filtered result set without recomputing embeddings. Categories are navigation aids, not verified medical specialties. Selecting any procedure opens a concise details card with description, modifier, status and a collapsible view of underlying CMS fields, plus a source link and Clear button.

## V10 — Browse more semantic matches

Click **Find related services by meaning** directly under the main search box. Results show six at a time with **Previous / Next** paging, and up to 60 distinct semantic candidates. Results are kept in session state so paging does not repeat model work. When the search is a code fragment containing digits (for example `9921`), discovery switches to prefix-aware code matching, returning up to 150 codes rather than five semantically unrelated results. The main instant suggestions remain available below.

## V8 — One search field with optional semantic discovery

The primary Find a service tab now combines fast keyword/code autocomplete with a **Find related services by meaning** button, using the same query text. No second search box or separate advanced search area is required. Regular autocomplete remains instant and API-key-free; semantic retrieval is run on demand because embedding preparation may take time and memory on Streamlit Community Cloud. Semantic suggestions can be clicked to inspect CMS code details. This is approximate retrieval, not coding or billing advice.

## V7 — Smarter search

Autocomplete now distinguishes exact codes, code prefixes, description phrases and numerical fragments, supports everyday aliases (e.g. "doctor visit", "checkup", "x-ray"), and uses conservative spelling correction as a fallback for inputs such as "offce". The search remains fast and deterministic; it does not require an LLM or charge API fees.

Selected-code details reset when the query changes, avoiding stale code information. Tests cover code fragments, duplicate prevention, natural-language aliases, and typo fallback.

## V6 — Search-first experience

The landing page now has three clear tabs: **Find a service**, **Ask CMS**, and **About**. A single prominent search field provides live ranked suggestions across public CMS procedure descriptions and partial HCPCS code matches. Six suggestions appear immediately, with up to 74 additional matches in a scrollable section. Selecting a match opens source fields and modifier variants. Semantic retrieval remains available under an Advanced expander, not as a competing landing-page form.

Common-language aliases help bridge phrases such as **doctor visit**, **office visits**, **checkup**, **physical**, and **emergency room** to shortened descriptions. This is keyword/alias autocomplete, not generative AI. The Ask CMS tab provides the separate LangGraph/document retrieval experience.

## Smart Procedure Finder

Type any HCPCS code, partial code (such as `22` or `992`), or service phrase (such as `office`). The app ranks up to 80 suggestions, displays the first several in a scrollable dropdown, and lets you inspect all modifier variants of the selected code. Unlike the embedding search, this fast autocomplete is deterministic and requires no LLM API.

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
