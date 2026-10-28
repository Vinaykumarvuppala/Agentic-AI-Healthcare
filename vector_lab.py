"""Persistent local Chroma vector store for a bounded public CMS sample."""
from __future__ import annotations
import hashlib
from pathlib import Path

def build_or_open(documents, directory=".cache/chroma", collection="cms_lab_v1", max_documents=2500):
    import chromadb
    from sentence_transformers import SentenceTransformer
    if not documents:
        raise ValueError("No documents supplied")
    subset=documents[:max_documents]
    Path(directory).mkdir(parents=True,exist_ok=True)
    client=chromadb.PersistentClient(path=directory)
    store=client.get_or_create_collection(name=collection,metadata={"hnsw:space":"cosine"})
    model=SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    new=[(hashlib.sha256((str(d.get("hcpc"))+"|"+d["text"]).encode()).hexdigest(),d) for d in subset]
    known=set(store.get(ids=[x[0] for x in new],include=[])["ids"])
    missing=[(key,d) for key,d in new if key not in known]
    for start in range(0,len(missing),128):
        batch=missing[start:start+128]
        embeddings=model.encode([d["text"] for _,d in batch],normalize_embeddings=True).tolist()
        store.upsert(ids=[key for key,_ in batch],documents=[d["text"] for _,d in batch],
                     embeddings=embeddings,
                     metadatas=[{"hcpc":str(d.get("hcpc","")),"source":str(d.get("source",""))} for _,d in batch])
    return store,model,{"indexed":store.count(),"added":len(missing),"sample_limit":max_documents}

def query(store,model,question,k=5):
    vec=model.encode([question],normalize_embeddings=True).tolist()[0]
    response=store.query(query_embeddings=[vec],n_results=min(k,store.count()),
                         include=["documents","metadatas","distances"])
    return [{"code":m["hcpc"],"text":t,"distance":float(dist)}
            for m,t,dist in zip(response["metadatas"][0],response["documents"][0],response["distances"][0])]
