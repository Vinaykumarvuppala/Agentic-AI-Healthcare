from policy_rag import split_text, format_citations
from research_agent import make_research_agent

def test_chunking():
    chunks = split_text("one two three four five six", chunk_size=12, overlap=3)
    assert len(chunks) > 1
    assert "one" in chunks[0]
    assert "six" in chunks[-1]

def test_empty_chunking():
    assert split_text("") == []

def test_invalid_overlap():
    import pytest
    with pytest.raises(ValueError):
        split_text("hello", chunk_size=2, overlap=2)

def test_citations():
    out = format_citations([{"text":"rule","source":"https://www.cms.gov/test.pdf","page":4,"score":0.5}])
    assert out[0]["page"] == 4
    assert out[0]["number"] == 1

class FakeSearch:
    def search(self, query, k=5, exact_code=None):
        return [{"text":"CMS rule evidence","source":"https://www.cms.gov/","page":3,"score":0.9}]

def test_research_routes_policy():
    agent=make_research_agent(FakeSearch(),FakeSearch())
    result=agent.invoke({"question":"What are the documentation guidelines?","source":"Auto"})
    assert result["source"]=="policy"
    assert len(result["citations"])==1
    assert len(result["trace"])==3
