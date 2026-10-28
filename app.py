"""CMS Agent Lab: one search-first experience with optional research tools."""
import os
import pandas as pd
import streamlit as st
from autocomplete import suggest
from comparison import compare_codes, variants
from comparison_explain import summarize_differences
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
tab_search, tab_compare, tab_ask, tab_info = st.tabs(["🔎 Find a service", "⚖️ Compare codes", "💬 Ask CMS", "ℹ️ About"])

with tab_search:
    st.subheader("What are you looking for?")
    q = st.text_input("Search codes or services", placeholder="Search: office visits, checkup, 99213, 22, even offce…", key="search_v6")
    if st.session_state.get("last_query_v7") != q:
        st.session_state.pop("selected_code_v6", None)
        st.session_state["last_query_v7"] = q
        st.session_state.pop("semantic_request_v8", None)
        st.session_state.pop("semantic_cache_query_v10", None)
        st.session_state.pop("semantic_results_v10", None)
        st.session_state["semantic_page_v10"] = 1
        st.session_state.pop("semantic_category_v11", None)
    if q.strip():
        # Single search input: direct results render immediately; users can
        # request a deeper vector search without learning a second interface.
        if st.button("✨ Find related services by meaning", key="semantic_fallback_v8", use_container_width=True):
            st.session_state["semantic_request_v8"] = q
        if st.session_state.get("semantic_request_v8") == q:
            try:
                # Persist results per query: changing page must not re-embed/re-query.
                if st.session_state.get("semantic_cache_query_v10") != q:
                    with st.spinner("Searching CMS codes by meaning…"):
                        if q.strip().isalnum() and any(ch.isdigit() for ch in q):
                            # Partial HCPCS input: prefix matches are more useful than vectors.
                            matches = suggest(df, q, limit=150)
                            items = [{"hcpc": x["code"], "description": x["description"]} for x in matches]
                        else:
                            index = code_engine("hybrid-v10")
                            items = index.search(q, k=60)
                    unique = []
                    seen = set()
                    for item in items:
                        if item["hcpc"] not in seen:
                            seen.add(item["hcpc"])
                            unique.append(item)
                    st.session_state["semantic_results_v10"] = unique
                    st.session_state["semantic_cache_query_v10"] = q
                    st.session_state["semantic_page_v10"] = 1
                found = st.session_state.get("semantic_results_v10", [])
                def category_for(code):
                    # HCPCS families are broad browsing labels, not clinical classifications.
                    if code.startswith("D"): return "Dental (D)"
                    if code.startswith(("99", "98")): return "E/M and related (98–99)"
                    if code.startswith(("7", "8")) and code.isdigit(): return "Imaging / lab families (7–8)"
                    if code[0].isalpha(): return "Other alphanumeric HCPCS"
                    return "Other numeric CPT"
                categories = ["All categories"] + sorted({category_for(row["hcpc"]) for row in found})
                category = st.selectbox("Filter related results", categories, key="semantic_category_v11")
                filtered = [row for row in found if category == "All categories" or category_for(row["hcpc"]) == category]
                st.markdown(f"**Related procedures ({len(filtered)} of {len(found)} shown)**")
                if filtered:
                    page_size = 6
                    total_pages = (len(filtered) + page_size - 1) // page_size
                    current_page = min(st.session_state.get("semantic_page_v10", 1), total_pages)
                    st.caption(f"Showing {((current_page-1)*page_size)+1}–{min(current_page*page_size,len(filtered))} of {len(filtered)} · page {current_page}/{total_pages}")
                    for i, item in enumerate(filtered[(current_page-1)*page_size:current_page*page_size]):
                        code = item["hcpc"]
                        if st.button(f"{code}   ·   {item['description']}", key=f"related_{current_page}_{i}_{code}", use_container_width=True):
                            st.session_state["selected_code_v6"] = code
                    prev_col, next_col = st.columns(2)
                    with prev_col:
                        if st.button("← Previous", disabled=current_page<=1, key="semantic_prev_v10", use_container_width=True):
                            st.session_state["semantic_page_v10"] = current_page-1
                            st.rerun()
                    with next_col:
                        if st.button("Next →", disabled=current_page>=total_pages, key="semantic_next_v10", use_container_width=True):
                            st.session_state["semantic_page_v10"] = current_page+1
                            st.rerun()
                else:
                    st.info("No related procedures found. Try a more specific phrase.")
                st.caption("Results are approximate; verify CMS codes and effective dates.")
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
        with st.container(border=True):
            top, close = st.columns([5, 1])
            with top:
                st.subheader(f"Procedure details · {chosen}")
            with close:
                if st.button("Clear", key="clear_details_v11"):
                    st.session_state.pop("selected_code_v6", None)
                    st.rerun()
            records = df[df["hcpc"] == chosen]
            if not records.empty:
                st.markdown(f"**Description:** {records.iloc[0]['sdesc']}")
                st.caption(f"{len(records)} source row(s) for code {chosen}; variants may differ in modifier or status.")
                summary_fields = [("modifier", "Modifier"), ("proc_stat", "Procedure status")]
                for column, label in summary_fields:
                    if column in records.columns:
                        values = sorted({str(x).strip() for x in records[column].dropna() if str(x).strip()})
                        st.write(f"**{label}:** {', '.join(values) if values else 'Not specified'}")
                with st.expander("View full CMS source fields", expanded=False):
                    cols = [name for name in ("hcpc", "modifier", "sdesc", "proc_stat", "nfac_total", "fac_total", "conv_fact") if name in records.columns]
                    st.dataframe(records[cols], use_container_width=True, hide_index=True)
                st.markdown(f"[Official CMS PFS data source]({CMS_CSV_URL})")
                st.caption("This is a code reference, not a payable amount or coding recommendation.")


with tab_compare:
    st.subheader("Compare two HCPCS codes")
    st.caption("Search for two procedures, select matching modifier variants, and review their CMS fields side by side.")
    codes = sorted(df["hcpc"].dropna().astype(str).str.upper().unique().tolist())
    a_col,b_col = st.columns(2)
    with a_col:
        left = st.selectbox("First procedure", codes, index=codes.index("99213") if "99213" in codes else 0,
                            key="compare_left_v12")
    with b_col:
        right = st.selectbox("Second procedure", codes, index=codes.index("99214") if "99214" in codes else min(1,len(codes)-1),
                             key="compare_right_v12")
    if left == right:
        st.info("Choose two different codes to compare.")
    else:
        available_a = set(variants(df,left))
        available_b = set(variants(df,right))
        common = sorted(available_a & available_b)
        if not common:
            st.warning("These codes have no common modifier variant. Choose other codes for a like-for-like comparison.")
        else:
            modifier = st.selectbox("Common modifier", common, format_func=lambda m:m or "No modifier",key="compare_modifier_v12")
            try:
                table = compare_codes(df,left,right,modifier)
                only_diff = st.checkbox("Show differences only", key="compare_diff_v12")
                if only_diff:
                    table = table.loc[table["Different"] == "Yes"]
                st.dataframe(table, use_container_width=True, hide_index=True)
                st.download_button("Download comparison CSV", table.to_csv(index=False).encode("utf-8"),
                                   file_name=f"cms_compare_{left}_{right}.csv", mime="text/csv", key="compare_download_v12")
                st.caption("RVU and conversion-factor columns are displayed as published. No payment amounts are calculated.")
                st.markdown("#### Why are these codes different?")
                # The explanation is derived from the complete comparison table,
                # not the differences-only display setting.
                full_comparison = compare_codes(df, left, right, modifier)
                for explanation in summarize_differences(full_comparison, left, right):
                    st.markdown("- " + explanation)
                with st.expander("Find supporting CMS E/M policy passages"):
                    st.caption("Optional policy retrieval. A similar passage is not proof that a particular CPT code is appropriate.")
                    if st.button("Retrieve official guidance", key="compare_policy_v13"):
                        try:
                            with st.spinner("Searching public CMS E/M guidance…"):
                                terms = f"office outpatient E/M visits medical decision making time {left} {right}"
                                passages = policy_engine("v13-cms-policy").search(terms, k=4)
                            if not passages:
                                st.info("No relevant passages found in the current guide.")
                            for number, passage in enumerate(passages, 1):
                                st.markdown(f"**Evidence {number} · PDF page {passage.get('page', 'unknown')}**")
                                st.write(passage["text"][:750])
                                st.markdown(f"[Open CMS source]({passage['source']})")
                        except Exception as exc:
                            st.warning(f"CMS policy retrieval unavailable: {exc}")
                    st.caption("Policy coverage is limited to the currently configured CMS E/M PDF, which may not address every code pair.")
            except ValueError as exc:
                st.warning(str(exc))
    st.markdown(f"[CMS source data]({CMS_CSV_URL})")


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
st.caption("CMS Intelligence · V13 · Evidence-backed comparison")
