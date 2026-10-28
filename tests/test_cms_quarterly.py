from io import BytesIO
from zipfile import ZipFile
import pytest
from cms_quarterly import discover_releases, parse_snapshot_archive, compare_snapshots

def test_discover_official_link_only():
    html='<a href="/files/zip/october-2026-alpha-numeric-hcpcs-file.zip">October 2026 Alpha-Numeric HCPCS File (ZIP)</a>'
    assert discover_releases(html)["October 2026"].startswith("https://www.cms.gov/")

def test_changes_dont_claim_effective_dates():
    result=compare_snapshots({"A1000":"old","B2000":"still"},
                             {"B2000":"still","C3000":"new"},"July 2026","October 2026")
    assert set(result["release_change"])=={"Appeared in newer release","Absent from newer release"}
    assert "effective_date" not in result.columns

def test_reject_non_anweb():
    buffer=BytesIO()
    with ZipFile(buffer,"w") as archive:
        archive.writestr("readme.txt","sample")
    with pytest.raises(ValueError,match="ANWEB"):
        parse_snapshot_archive(buffer.getvalue())
