from vector_lab import query

def test_query_maps_code():
    class Model:
        def encode(self, texts, normalize_embeddings=True): return [[0.1,0.2]]
    class Store:
        def count(self): return 1
        def query(self,**kwargs):
            return {"metadatas":[[{"hcpc":"99213"}]],"documents":[["Office visit"]],"distances":[[0.12]]}
    assert query(Store(),Model(),"office")[0]["code"]=="99213"
