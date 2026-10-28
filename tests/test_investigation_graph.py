from investigation_graph import make_investigation_graph

def test_investigation_nodes_and_report():
    graph = make_investigation_graph(
        lambda code: [{"sdesc":"Sample public record","modifier":"","proc_stat":"A"}],
        lambda query: [{"text":"Evidence passage","source":"https://www.cms.gov/test.pdf","page":4}],
    )
    result = graph.invoke({"code":"99213","question":"Explain context"})
    assert "Evidence passage" in result["report"]
    assert "Human review required" in result["report"]
    assert len(result["trace"]) == 4

def test_missing_policy_does_not_invent():
    graph = make_investigation_graph(lambda code: [])
    result = graph.invoke({"code":"G2211","question":"What does CMS publish?"})
    assert "No supporting policy passages" in result["report"]
