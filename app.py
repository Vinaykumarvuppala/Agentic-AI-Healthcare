"""CMS Agent Lab: one search-first experience with optional research tools."""
import os
import pandas as pd
import streamlit as st
from autocomplete import suggest
from cms_agent import CMS_CSV_URL, VectorSearch, build_agent, build_documents, load_cms_data
from llm_rag import answer_with_llm
from policy_rag import load_policy_chunks
from research_agent import make_research_agent

st.set_page_config(page_title="CMS Intelligence | Agent Lab", page_icon="🔎", layout="wide")

st.markdown("""
<style>
.block-container {max-width:1060px;padding-top:2rem;padding-bottom:4rem}
h1 {letter-spacing:-.035em}
div[data-testid="stMetric"] {background:var(--secondary-background-color);border:1px solid rgba(128,128,128,.16);border-radius:14px;padding:13px}
div[data-testid="stButton"] button {border-radius:11px;text-align:left}
div[data-testid="stTextInput"] input {border-radius:13px;font-size:1.05rem;padding:13px}
div[data-testid="stExpander"] {border-radius:13px}
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=86400, show_spinner="Connecting to public CMS data…")
def data():
    return load_cms_data()

@st.cache_resource(show_spinner="Preparing semantic index…")
def code_engine(version):
    return VectorSearch(build_documents(data()))

@st.cache_resource(show_spinner="Reading and indexing CMS policy guidance…")
def policy_engine(version):
    return VectorSearch(load_policy_chunks("CMS E/M Services Guide (Sep 2025)"))

try:
    df = data()
except Exception as exc:
    st.error(f"Unable to load CMS data: {exc}")
    st.markdown(f"[Official CMS dataset]({CMS_CSV_URL})")
    st.stop()

st.title("CMS Intelligence")
st.write("**Find a medical service, explore HCPCS codes, or ask a question about CMS guidance.**")
st.caption("Public CMS Physician Fee Schedule indicators · Educational research · 2026")
tab_search, tab_ask, tab_info = st.tabs(["🔎 Find a service", "💬 Ask CMS", "ℹ️ About"])

with tab_search:
    st.subheader("What are you looking for?")
    q = st.text_input("Search codes or services", placeholder="Search: office visits, checkup, 99213, 22, even offce…", key="search_v6")
    if st.session_state.get("last_query_v7") != q:
        st.session_state.pop("selected_code_v6", None)
        st.session_state["last_query_v7"] = q
        st.session_state.pop("semantic_request_v8", None)
    if q.strip():
        # Single search input: direct results render immediately; users can
        # request a deeper vector search without learning a second interface.
        if st.button("✨ Find related services by meaning", key="semantic_fallback_v8", use_container_width=True):
            st.session_state["semantic_request_v8"] = q
        if st.session_state.get("semantic_request_v8") == q:
            try:
                with st.spinner("Searching CMS codes by meaning…"):
                    results = build_agent(code_engine("hybrid-v8")).invoke({"question": q}).get("results", [])
                st.markdown("**AI-powered related procedures**")
                seen = set()
                for idx, item in enumerate(results):
                    code = item["hcpc"]
                    if code in seen:
                        continue
                    seen.add(code)
                    if st.button(f"{code}   ·   {item['description']}", key=f"semantic_{idx}_{code}", use_container_width=True):
                        st.session_state["selected_code_v6"] = code
                if not seen:
                    st.caption("No related procedures found.")
                st.caption("Semantic results are approximate. Confirm codes against CMS documentation.")
            except Exception as exc:
                st.warning(f"Meaning-based search is unavailable: {exc}")

            st.divider()
    if not q.strip():
        st.caption("Start typing to see matching procedures. Search descriptions, partial codes, or common terms.")
        st.markdown("**Popular searches**")
        choices = ["doctor visit", "99213", "22", "checkup", "x-ray"]
        cols = st.columns(len(choices))
        def select_popular_search(value):
            # Streamlit callbacks run before widgets are instantiated on rerun.
            st.session_state["search_v6"] = value
            st.session_state.pop("selected_code_v6", None)
            st.session_state.pop("semantic_request_v8", None)

        for col, value in zip(cols, choices):
            with col:
                st.button(
                    value,
                    key="chip_" + value,
                    use_container_width=True,
                    on_click=select_popular_search,
                    args=(value,),
                )
    else:
        hits = suggest(df, q, limit=80)
        if hits:
            st.caption(f"Matching CMS records for **{q}** · top {min(6,len(hits))} shown · additional matches below")
            for i,item in enumerate(hits[:6]):
                if st.button(f"{item['code']}   ·   {item['description']}", key=f"hit_{i}_{item['code']}", use_container_width=True):
                    st.session_state["selected_code_v6"] = item["code"]
            if len(hits)>6:
                with st.expander(f"Show more matching procedures ({len(hits)-6} additional)"):
                    with st.container(height=265):
                        for i,item in enumerate(hits[6:],start=6):
                            if st.button(f"{item['code']}   ·   {item['description']}", key=f"hit_{i}_{item['code']}", use_container_width=True):
                                st.session_state["selected_code_v6"] = item["code"]
            if len(hits)==80:
                st.caption("Showing the top 80; refine your search for more precise matches.")
        else:
            st.info("No direct code matches. Use meaning-based results above or try a shorter term.")


    chosen = st.session_state.get("selected_code_v6")
    if chosen:
        st.divider()
        st.subheader(f"HCPCS {chosen}")
        records = df[df["hcpc"]==chosen]
        if not records.empty:
            st.write(records.iloc[0]["sdesc"])
            cols = [c for c in ("hcpc","modifier","sdesc","proc_stat","nfac_total","fac_total","conv_fact") if c in records]
            st.dataframe(records[cols],use_container_width=True,hide_index=True)
            st.caption("Source record variants shown. These values are not a claim payment quote.")

with tab_ask:
    st.subheader("Ask a question about CMS")
    st.caption("Retrieves public procedure records or CMS E/M policy passages. Answers include sources.")
    source = st.selectbox("Research source",["Auto","CMS procedure codes","CMS policy PDF"],key="source_v6")
    use_llm = st.toggle("AI-generated explanation (requires configured OpenAI API key)",value=False)
    if "chat_v6" not in st.session_state:
        st.session_state.chat_v6=[]
    for x in st.session_state.chat_v6:
        with st.chat_message("user"): st.write(x["question"])
        with st.chat_message("assistant"):
            st.markdown(x["answer"])
            with st.expander("Source evidence and execution steps"):
                for cit in x["citations"]:
                    st.markdown(f"[CMS source {cit['number']}]({cit['url']})" + (f" · page {cit['page']}" if cit["page"] else ""))
                    st.caption(cit["excerpt"])
                st.code("\n".join(x["trace"]),language="text")
    prompt = st.chat_input("Ask about office visits, G2211 or E/M documentation…")
    if prompt:
        with st.chat_message("user"): st.write(prompt)
        with st.chat_message("assistant"):
            try:
                words=("documentation","guideline","policy","modifier","medical decision","g2211","billing rule")
                use_policy = source=="CMS policy PDF" or (source=="Auto" and any(w in prompt.lower() for w in words))
                with st.spinner("Finding supporting CMS evidence…"):
                    code_index = None if use_policy else code_engine("intent-aware-v4")
                    pdf_index = policy_engine("v5") if use_policy else None
                    result = make_research_agent(code_index,pdf_index).invoke({"question":prompt,"source":source})
                answer=result["answer"]
                if use_llm and result.get("evidence"):
                    if os.getenv("OPENAI_API_KEY"):
                        try: answer=answer_with_llm(prompt,result["evidence"])
                        except Exception as exc: st.warning(f"AI explanation unavailable: {exc}")
                    else:
                        st.info("No API key configured. Showing sourced retrieval instead.")
                st.markdown(answer)
                with st.expander("Source evidence and execution steps"):
                    for cit in result["citations"]:
                        st.markdown(f"[CMS source {cit['number']}]({cit['url']})"+(f" · page {cit['page']}" if cit["page"] else ""))
                        st.caption(cit["excerpt"])
                    st.code("\n".join(result["trace"]),language="text")
                st.session_state.chat_v6.append({"question":prompt,"answer":answer,"citations":result["citations"],"trace":result["trace"]})
            except Exception as exc:
                st.error(f"Research retrieval failed: {exc}")

with tab_info:
    a,b,c=st.columns(3)
    a.metric("CMS rows",f"{len(df):,}")
    b.metric("Unique codes",f"{df['hcpc'].nunique():,}")
    c.metric("Release year","2026")
    st.markdown(f"**Data source:** [CMS PFS indicators]({CMS_CSV_URL})")
    st.write("Autocomplete uses the actual public CMS descriptions and simple search aliases. 'Ask CMS' uses LangGraph routing and optional PDF chunk retrieval. The AI explanation is optional and needs an API key.")
    st.warning("Educational prototype: not medical advice, coding guidance, or a reimbursement determination. Verify current CMS rules and code effective dates.")
st.caption("CMS Intelligence · V9 · Search without scrolling")
