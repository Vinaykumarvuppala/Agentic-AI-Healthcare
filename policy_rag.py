"""Public CMS policy PDF ingestion, chunking and retrieval. No patient data."""
from __future__ import annotations
from functools import lru_cache
from io import BytesIO
import requests
from pypdf import PdfReader

POLICIES = {
    "CMS E/M Services Guide (Sep 2025)": "https://www.cms.gov/outreach-and-education/medicare-learning-network-mln/mlnproducts/downloads/eval-mgmt-serv-guide-icn006764.pdf",
}
MAX_DOWNLOAD_BYTES = 15_000_000
MAX_PAGES = 40

def split_text(text: str, chunk_size: int = 1100, overlap: int = 180) -> list[str]:
    """Overlapping character chunks with forward progress guarantees."""
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Require chunk_size > overlap >= 0")
    text = " ".join(text.split())
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + int(chunk_size * 0.65), end)
            if boundary > start:
                end = boundary
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks

@lru_cache(maxsize=2)
def load_policy_chunks(name: str) -> list[dict]:
    if name not in POLICIES:
        raise ValueError("Unknown public document")
    url = POLICIES[name]
    response = requests.get(url, timeout=45, stream=True, headers={"User-Agent":"CMSResearchDemo/1.0"})
    response.raise_for_status()
    content = bytearray()
    for block in response.iter_content(chunk_size=65536):
        content.extend(block)
        if len(content) > MAX_DOWNLOAD_BYTES:
            raise ValueError("PDF too large for demo")
    reader = PdfReader(BytesIO(content))
    documents = []
    for page_num, page in enumerate(reader.pages[:MAX_PAGES], 1):
        body = page.extract_text() or ""
        for idx, chunk in enumerate(split_text(body)):
            documents.append({
                "text": chunk,
                "description": chunk[:140],
                "hcpc": f"PDF-{page_num}-{idx+1}",
                "modifier": "",
                "procedure_status": "",
                "year": "2025",
                "source": url,
                "page": page_num,
                "document": name,
                "kind": "policy",
            })
    if not documents:
        raise ValueError("PDF contains no extractable text")
    return documents

def format_citations(results: list[dict]) -> list[dict]:
    return [
        {"number": i, "title": item.get("document","CMS PFS indicators"), "page": item.get("page"),
         "url": item["source"], "excerpt":item.get("text","")[:420],
         "score":round(float(item.get("score",0)),3), "kind":item.get("kind","code")}
        for i,item in enumerate(results,1)
    ]
