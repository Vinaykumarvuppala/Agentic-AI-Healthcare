"""Project roadmap: source-controlled feature status, not user-editable success claims."""
ROADMAP = [
    {"area":"Foundation","feature":"Python, Streamlit app and GitHub CI","status":"Implemented","phase":1,"evidence":"app.py; .github/workflows/ci.yml","next":"Verify all checks and deployed startup"},
    {"area":"Ingestion","feature":"Public CMS CSV ingestion","status":"Implemented","phase":1,"evidence":"cms_agent.py","next":"Validate source refresh and metadata"},
    {"area":"Search","feature":"Autocomplete, typo tolerance and code prefixes","status":"Implemented","phase":1,"evidence":"autocomplete.py","next":"Measure search relevance"},
    {"area":"Search","feature":"Local embeddings and semantic retrieval","status":"Implemented","phase":1,"evidence":"cms_agent.py","next":"Persist a vector index and benchmark"},
    {"area":"RAG","feature":"CMS PDF chunking and cited retrieval","status":"Prototype / needs validation","phase":2,"evidence":"policy_rag.py; research_agent.py","next":"Verify PDF source availability and retrieval accuracy"},
    {"area":"LangGraph","feature":"Routing and investigation workflow","status":"Implemented","phase":2,"evidence":"research_agent.py; investigation_graph.py","next":"Add durable state, approvals and recovery"},
    {"area":"LLMs","feature":"Optional OpenAI answer generation","status":"Prototype / needs validation","phase":2,"evidence":"llm_rag.py","next":"Verify credentials, citations, reliability and costs"},
    {"area":"Healthcare ETL","feature":"CMS lifecycle, configurable SQL/JSON exports","status":"Prototype / needs validation","phase":2,"evidence":"lifecycle.py; custom_etl.py; cms_transactions.py","next":"Validate real CMS archives and SQL engines"},
    {"area":"Vector DB","feature":"Local Chroma persistent index sample","status":"Prototype / needs validation","phase":3,"evidence":"vector_lab.py","next":"Verify indexed sample and move to durable cloud storage"},
    {"area":"LangChain","feature":"Reusable retrievers, loaders and tool integrations","status":"Planned","phase":3,"evidence":"","next":"Add LangChain retrieval and tool layer"},
    {"area":"Agentic AI","feature":"Multi-agent tool use and human approval checkpoints","status":"Planned","phase":3,"evidence":"","next":"Implement specialist agents and audit trail"},
    {"area":"Evaluation","feature":"Initial retrieval evaluation with Recall@K and MRR","status":"Prototype / needs validation","phase":3,"evidence":"retrieval_eval.py","next":"Grow to 50+ expert-reviewed healthcare questions"},
    {"area":"Models","feature":"Multi-LLM/version comparison and fallback","status":"Planned","phase":4,"evidence":"","next":"Benchmark quality, latency and token cost"},
    {"area":"AWS","feature":"Bedrock, SageMaker AI and S3 pipelines","status":"Planned","phase":4,"evidence":"","next":"Deploy model/inference and ingestion experiments"},
    {"area":"Deployment","feature":"Docker/Kubernetes and scaling","status":"Prototype / needs validation","phase":4,"evidence":"Dockerfile","next":"Run container tests and deploy to EKS or local Kubernetes"},
    {"area":"Operations","feature":"Tracing, security, monitoring and cost controls","status":"Planned","phase":4,"evidence":"","next":"Add OpenTelemetry, secrets, access policies, and alerts"},
]
STATUSES=("Implemented","Prototype / needs validation","Planned")
def counts():
    return {status:sum(x["status"]==status for x in ROADMAP) for status in STATUSES}
