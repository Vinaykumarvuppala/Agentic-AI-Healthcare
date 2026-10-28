from project_roadmap import ROADMAP, STATUSES, counts

def test_roadmap_status_and_coverage():
    assert len(ROADMAP) >= 12
    assert all(x["status"] in STATUSES and x["phase"] in (1,2,3,4) for x in ROADMAP)
    assert sum(counts().values()) == len(ROADMAP)
    assert any("Vector DB" in x["area"] for x in ROADMAP)
    assert any("Kubernetes" in x["feature"] for x in ROADMAP)
