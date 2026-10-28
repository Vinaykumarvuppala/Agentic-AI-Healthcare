"""Streamlit interface to a public-data CMS semantic retrieval agent."""
import pandas as pd
import streamlit as st

from cms_agent import CMS_CSV_URL, VectorSearch, build_agent, build_documents, load_cms_data
from llm_rag import answer_with_llm

st.set_page_config(page_title="CMS Agent Lab", page_icon="🩺", layout="wide")
st.title("CMS Agent Lab")
st.caption("Actual public CMS 2026 Physician Fee Schedule data · Vector embeddings · LangGraph · Python")
st.info("Educational research tool only. Fee schedule indicators do not constitute a patient-specific reimbursement calculation.")

@st.cache_data(ttl=86400, show_spinner="Downloading public CMS data…")
def get_data() -> pd.DataFrame:
    return load_cms_data()

@st.cache_resource(show_spinner="Building vector embeddings (first run may take several minutes)…")
def get_search_engine(index_version: str):
    return VectorSearch(build_documents(get_data()))

try:
    df = get_data()
except Exception as exc:
    st.error(f"Could not fetch public CMS dataset: {exc}")
    st.markdown(f"[Open official CSV source]({CMS_CSV_URL})")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("CMS rows", f"{len(df):,}")
c2.metric("Unique HCPCS codes", f"{df['hcpc'].nunique():,}")
c3.metric("Data year", "2026")
st.markdown(f"**Official source:** [CMS Physician Fee Schedule Indicators]({CMS_CSV_URL})")

mode = st.radio("Search mode", ["HCPCS code lookup", "Semantic meaning search"], horizontal=True)
if mode == "HCPCS code lookup":
    code = st.text_input("Enter a HCPCS/CPT code", value="99213").strip().upper()
    rows = df[df["hcpc"] == code]
    if rows.empty:
        st.warning("No matching code in this release.")
    else:
        shown = [c for c in ["hcpc", "modifier", "sdesc", "proc_stat", "nfac_total", "fac_total", "conv_fact"] if c in rows.columns]
        st.dataframe(rows[shown], use_container_width=True, hide_index=True)
        st.caption("RVUs, indicator values, and conversion factors are not a final payable amount.")
else:
    st.caption("Search version: dedup-medical-v3 · distinct HCPCS results")
    question = st.text_input("Ask about services", value="Which procedures relate to office visits?")
    use_llm = st.checkbox("Generate an LLM explanation with cited evidence (requires OPENAI_API_KEY)")
    if st.button("Ask the retrieval agent", type="primary") and question.strip():
        try:
            search = get_search_engine("dedup-medical-v3")
            result = build_agent(search).invoke({"question": question})
            # Defense in depth: dedupe the displayed evidence even when an
            # older cached index or repeated source rows were encountered.
            unique_results = []
            seen_codes = set()
            for item in result["results"]:
                code = item["hcpc"]
                if code not in seen_codes:
                    unique_results.append(item)
                    seen_codes.add(code)
            result["results"] = unique_results
            if len(unique_results) < 5:
                st.caption("Showing distinct HCPCS codes only.")
            st.markdown("### Relevant CMS codes")
            for item in unique_results:
                st.markdown(f"- **{item['hcpc']}** — {item['description']} (modifier: {item['modifier'] or 'none'}, status: {item['procedure_status'] or 'not specified'})")

            if use_llm:
                try:
                    st.markdown(answer_with_llm(question, result["results"]))
                except Exception as llm_exc:
                    st.warning(f"LLM explanation unavailable: {llm_exc}")
            st.subheader("Retrieved evidence")
            for item in result["results"]:
                st.write(f"**{item['hcpc']} — {item['description']}**")
                st.caption(f"Similarity {item['score']:.3f} · Modifier {item['modifier'] or 'none'} · Year {item['year']}")
        except Exception as exc:
            st.error(f"Unable to run semantic retrieval: {exc}")

with st.expander("Architecture and safeguards"):
    st.markdown("""
    1. Ingest real CMS public CSV, validate columns, and normalize records.
    2. Convert descriptions to sentence-transformer embeddings.
    3. Search by semantic similarity, or exact HCPCS code when present.
    4. LangGraph runs routing → retrieval → grounded response.
    5. Show sources and limitations. No patient data, private contracts, or fabricated payment amounts.

    **Next milestones:** persisted vector index, document chunking for PDF policies,
    optional LLM explanations with citations, read-only SQL tools, human review,
    Docker/Kubernetes deployment, and evaluation datasets.
    """)
