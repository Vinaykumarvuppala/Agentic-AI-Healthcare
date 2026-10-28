"""CMS Agent Lab: one search-first experience with optional research tools."""
import os
import pandas as pd
import streamlit as st
from autocomplete import suggest
from comparison import compare_codes, variants
from comparison_explain import summarize_differences
from investigation import build_report
from lifecycle import normalize_lifecycle, classify, SOURCE as LIFECYCLE_SOURCE
from investigation_graph import make_investigation_graph
from cms_quarterly import load_quarterly_changes, CMS_PAGE
from etl_exports import jsonl, json_array, sqlserver_script, oracle_script
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
tab_search, tab_compare, tab_lifecycle, tab_investigate, tab_ask, tab_info = st.tabs(["🔎 Find a service", "⚖️ Compare codes", "📅 Code lifecycle", "🧭 Investigate", "💬 Ask CMS", "ℹ️ About"])

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




with tab_lifecycle:
    st.subheader("HCPCS Level II code lifecycle")
    st.caption("New codes · effective dates · terminated codes · date-of-service checks")
    st.info("The PFS indicator file used elsewhere in this app does not prove an individual code's effective date. Load the official CMS Level II quarterly change data below to verify lifecycle dates.")
    st.markdown(f"[Official CMS quarterly releases]({LIFECYCLE_SOURCE}) · October 2026, July 2026, April 2026 and earlier.")
    with st.expander("How to prepare the CMS source data", expanded=False):
        st.write("Download the official CMS HCPCS Level II quarterly ZIP and locate its dated code/transaction records. Upload a CSV or Excel sheet with code, effective/add date, and termination date fields, or a normalized extract from those records. Map the columns below. The original raw fixed-width text is not yet parsed automatically.")
        st.caption("Level II only: letter-prefixed HCPCS codes. Numeric CPT/HCPCS Level I code dates require a separate licensed source.")
    st.markdown("#### Automatic CMS release comparison")
    st.caption("Compare official full quarterly ZIP snapshots. This detects added/removed/changed records between releases, not exact code-level effective or termination dates.")
    @st.cache_data(ttl=86400,show_spinner="Downloading and checking official CMS ZIP files…")
    def auto_changes(old_release,new_release):
        return load_quarterly_changes(old_release,new_release)
    lcol,rcol=st.columns(2)
    with lcol: older=st.selectbox("Previous release",["July 2026","April 2026","January 2026"],key="old_auto_v16")
    with rcol: newer=st.selectbox("Current release",["October 2026","July 2026"],key="new_auto_v16")
    if st.button("Load official CMS changes",key="load_auto_v16",type="primary"):
        st.session_state["auto_requested_v16"]=(older,newer)
    if st.session_state.get("auto_requested_v16")== (older,newer):
        try:
            from datetime import datetime
            release_dates={"January 2026":(2026,1),"April 2026":(2026,4),"July 2026":(2026,7),"October 2026":(2026,10)}
            if release_dates[older]>=release_dates[newer]:
                st.warning("Choose an older release followed by a newer release.")
            else:
                changes, links=auto_changes(older,newer)
                st.success(f"{len(changes):,} changed code records between {older} and {newer}")
                if not changes.empty:
                    kinds=["All changes"]+sorted(changes["release_change"].unique().tolist())
                    kind=st.selectbox("Change type",kinds,key="auto_kind_v16")
                    subset=changes if kind=="All changes" else changes.loc[changes["release_change"]==kind]
                    code_filter=st.text_input("Filter changed HCPCS codes",key="auto_code_v16")
                    if code_filter.strip():
                        subset=subset.loc[subset["code"].str.contains(code_filter.strip().upper(),regex=False)]
                    st.dataframe(subset,hide_index=True,use_container_width=True)
                    st.download_button("Download release changes CSV",subset.to_csv(index=False).encode("utf-8"),
                                       "cms_quarterly_changes.csv","text/csv",key="auto_export_v16")
                st.markdown(f"[Official {older} ZIP]({links[older]}) · [Official {newer} ZIP]({links[newer]})")
                st.warning("An appearance in a new snapshot is not necessarily a new code's original effective date. Removal from a snapshot is not proof of a termination date. Use official transaction records for that.")
                with st.expander("Data Export / ETL — SQL Server, Oracle, JSON", expanded=False):
                    st.caption("Exports the filtered comparison rows. Dates are NULL until verified code-level effective and termination dates are available.")
                    verified = None
                    dated_upload = st.file_uploader("Optional: attach verified code-level effective / termination dates (CSV or XLSX)",type=["csv","xlsx"],key="etl_dated_v17")
                    if dated_upload is not None:
                        try:
                            dates_raw = pd.read_csv(dated_upload,dtype=str) if dated_upload.name.lower().endswith(".csv") else pd.read_excel(dated_upload,dtype=str)
                            date_columns = list(dates_raw.columns)
                            mapped_code = st.selectbox("Date source: HCPCS code column",date_columns,key="etl_map_code_v17")
                            mapped_effective = st.selectbox("Date source: effective date column",date_columns,key="etl_map_effective_v17")
                            mapped_term = st.selectbox("Date source: termination date column",date_columns,key="etl_map_term_v17")
                            if len({mapped_code,mapped_effective,mapped_term})!=3:
                                st.warning("Map three distinct columns before exporting with dates.")
                            else:
                                verified = normalize_lifecycle(dates_raw,{"code":mapped_code,"effective_date":mapped_effective,"termination_date":mapped_term})
                                st.success(f"{len(verified):,} valid dated Level II record(s) available for matching.")
                        except Exception as date_error:
                            st.warning(f"Dated data not usable: {date_error}")
                    export_format = st.selectbox("Choose destination",[
                        "JSON Lines (S3 / Glue / Snowflake)",
                        "JSON array (API / cloud storage)",
                        "SQL Server (T-SQL)",
                        "Oracle (SQL / PL-SQL)"
                    ],key="etl_format_v17")
                    if export_format.startswith("JSON Lines"):
                        payload,filename,mime=jsonl(subset,verified),"hcpcs_changes.jsonl","application/x-ndjson"
                    elif export_format.startswith("JSON array"):
                        payload,filename,mime=json_array(subset,verified),"hcpcs_changes.json","application/json"
                    elif export_format.startswith("SQL Server"):
                        payload,filename,mime=sqlserver_script(subset,verified),"hcpcs_changes_sqlserver.sql","application/sql"
                    else:
                        payload,filename,mime=oracle_script(subset,verified),"hcpcs_changes_oracle.sql","application/sql"
                    st.code(payload[:2800],language="json" if "JSON" in export_format else "sql")
                    st.download_button("Download "+filename,payload.encode("utf-8"),
                                       file_name=filename,mime=mime,key="etl_download_v17")
                    st.caption(f"{len(subset):,} row(s) included. Script / JSON matches current filters.")

        except Exception as exc:
            st.error(f"Automatic CMS comparison unavailable: {exc}")
            st.markdown(f"[Download quarterly releases from CMS]({CMS_PAGE})")
    st.divider()
    st.markdown("#### Exact effective/termination dates (dated transaction records)")
    upload = st.file_uploader("Upload dated HCPCS Level II CSV or Excel", type=["csv","xlsx"], key="hcpcs_lifecycle_upload_v15")
    if upload is not None:
        try:
            if upload.name.lower().endswith(".csv"):
                raw = pd.read_csv(upload, dtype=str)
            else:
                raw = pd.read_excel(upload, dtype=str)
            if raw.empty:
                st.warning("This sheet contains no records.")
            else:
                col_names = list(raw.columns)
                def default_col(*candidates):
                    norm = lambda x:"".join(ch for ch in str(x).lower() if ch.isalnum())
                    for wanted in candidates:
                        for i,col in enumerate(col_names):
                            if norm(col)==norm(wanted):
                                return i
                    return 0
                with st.expander("Map official source columns",expanded=True):
                    a,b,c,d = st.columns(4)
                    with a:
                        code_col = st.selectbox("HCPCS code",col_names,index=default_col("HCPCS","HCPCS Code","code"),key="map_code_v15")
                    with b:
                        effective_col = st.selectbox("Effective/add date",col_names,index=default_col("Add Date","Effective Date","effective_date"),key="map_eff_v15")
                    with c:
                        terminate_col = st.selectbox("Termination date",col_names,index=default_col("Termination Date","termination_date","end date"),key="map_end_v15")
                    with d:
                        descriptions = ["(none)"]+col_names
                        description_col = st.selectbox("Description (optional)",descriptions,key="map_desc_v15")
                mapping = {"code":code_col,"effective_date":effective_col,"termination_date":terminate_col}
                if description_col!="(none)": mapping["description"]=description_col
                parsed = normalize_lifecycle(raw,mapping)
                st.caption(f"{len(parsed):,} dated records loaded. Unknown dates remain unknown; no dates are inferred.")
                a,b=st.columns(2)
                with a: as_of=st.date_input("Check validity on date",value=pd.Timestamp("2026-10-28").date(),key="life_asof_v15")
                with b: since=st.date_input("Show changes since",value=pd.Timestamp("2026-07-01").date(),key="life_since_v15")
                result=classify(parsed,as_of,since)
                states=["All","Active","New in period","Expired","Expired in period","Future","Unknown date"]
                filter_status=st.selectbox("Show codes",states,key="life_filter_v15")
                if filter_status=="New in period" or filter_status=="Expired in period":
                    result=result.loc[result["change"]==filter_status]
                elif filter_status!="All":
                    result=result.loc[result["status"]==filter_status]
                query_life=st.text_input("Filter by code or description",key="life_query_v15")
                if query_life.strip():
                    mask=result["code"].str.contains(query_life.strip().upper(),regex=False) | result["description"].str.contains(query_life.strip(),case=False,regex=False)
                    result=result.loc[mask]
                display=result.copy()
                for field in ["effective_date","termination_date"]:
                    display[field]=display[field].dt.strftime("%Y-%m-%d").fillna("Unknown")
                st.metric("Matching codes",f"{len(display):,}")
                st.dataframe(display,hide_index=True,use_container_width=True)
                st.download_button("Download lifecycle results CSV",display.to_csv(index=False).encode("utf-8"),
                                   file_name="hcpcs_lifecycle_results.csv",mime="text/csv",key="life_export_v15")
                st.caption("Termination date is treated as the last valid service date. Unknown or incomplete records are not marked active.")
        except Exception as exc:
            st.error(f"Could not interpret lifecycle file: {exc}")

with tab_investigate:
    st.subheader("Guided CMS investigation")
    st.caption("Three steps: choose a code, ask a question, and review a source-linked analyst report.")
    available_codes = sorted(df["hcpc"].dropna().astype(str).str.upper().unique().tolist())
    selected = st.selectbox("1 · Choose a procedure", available_codes,
                            index=available_codes.index("99213") if "99213" in available_codes else 0,
                            key="investigate_code_v14")
    inquiry = st.text_area("2 · What do you want to investigate?",
                           value="What does CMS publish about this procedure and its office/outpatient E/M context?",
                           key="investigate_question_v14", height=90)
    if st.button("3 · Generate investigation report", key="run_investigation_v14", type="primary"):
        if not inquiry.strip():
            st.warning("Enter a research question first.")
        else:
            try:
                with st.spinner("Retrieving official CMS evidence…"):
                    def lookup(code):
                        return df.loc[df["hcpc"] == code].fillna("").to_dict("records")
                    def lookup_policy(query):
                        return policy_engine("v15-policy").search(query, k=4)
                    graph = make_investigation_graph(lookup, lookup_policy)
                    outcome = graph.invoke({"code":selected, "question":inquiry})
                    report = outcome["report"]
                    st.session_state["investigation_report_v14"] = report
                    st.session_state["investigation_selection_v14"] = (selected, inquiry)
            except Exception as exc:
                st.error(f"Investigation could not complete: {exc}")
    if st.session_state.get("investigation_selection_v14") == (selected, inquiry):
        report = st.session_state.get("investigation_report_v14")
        if report:
            st.markdown(report)
            st.download_button("Download analyst report (.md)", report.encode("utf-8"),
                               file_name=f"cms_investigation_{selected}.md",
                               mime="text/markdown",key="download_investigation_v14")
    st.caption("Research findings require human verification. No patient data or private payer contracts are used.")

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
st.caption("CMS Intelligence · V17 · ETL exports")
