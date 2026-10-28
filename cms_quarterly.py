"""Automated, conservative CMS quarterly snapshot comparison.

This detects appearances/disappearances between full HCPCS Level II releases.
It NEVER asserts an original code effective or termination date from snapshots.
"""
from __future__ import annotations
from io import BytesIO
from zipfile import ZipFile, BadZipFile
from urllib.parse import urljoin, urlparse
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup

CMS_PAGE="https://www.cms.gov/medicare/coding-billing/healthcare-common-procedure-system/quarterly-update"
MAX_ZIP=35_000_000
RELEASES=("October 2026","July 2026","April 2026","January 2026")

def discover_releases(html: str) -> dict[str,str]:
    soup=BeautifulSoup(html,"html.parser")
    result={}
    for a in soup.select("a[href]"):
        label=" ".join(a.get_text(" ",strip=True).split())
        href=a.get("href","")
        for release in RELEASES:
            if release.lower() in label.lower() and "alpha" in label.lower() and ".zip" in href.lower():
                url=urljoin(CMS_PAGE,href)
                parsed=urlparse(url)
                if parsed.hostname in ("www.cms.gov","cms.gov") and parsed.path.lower().endswith(".zip"):
                    result[release]=url
    return result

def download_bytes(url: str, limit: int=MAX_ZIP) -> bytes:
    if urlparse(url).hostname not in ("www.cms.gov","cms.gov"):
        raise ValueError("Only official cms.gov archives allowed")
    with requests.get(url,stream=True,timeout=60,headers={"User-Agent":"CMS-Research-Lab/1.0"}) as r:
        r.raise_for_status()
        data=bytearray()
        for chunk in r.iter_content(chunk_size=65536):
            data.extend(chunk)
            if len(data)>limit:
                raise ValueError("Official archive exceeds safety size limit")
    return bytes(data)

def parse_snapshot_archive(blob: bytes) -> dict[str,str]:
    """Read ANWEB text records; first five characters are HCPCS code.

    Exclude transaction reports and supplementary modifier files. Fail closed
    if a plausible primary ANWEB file cannot be identified.
    """
    try:
        with ZipFile(BytesIO(blob)) as z:
            candidates=[x for x in z.infolist()
                        if not x.is_dir() and x.filename.lower().endswith(".txt")
                        and "anweb" in x.filename.lower()
                        and not any(t in x.filename.lower() for t in ("transaction","modifier","readme","layout"))
                        and x.file_size < 25_000_000]
            if not candidates:
                raise ValueError("No primary ANWEB text file detected; CMS archive layout needs review")
            selected=max(candidates,key=lambda x:x.file_size)
            raw=z.read(selected).decode("latin-1")
    except BadZipFile as exc:
        raise ValueError("Invalid CMS ZIP archive") from exc
    found={}
    for line in raw.splitlines():
        match=re.match(r"^([A-Z][0-9A-Z]{4})(?=\s|[A-Z0-9])",line)
        if match:
            code=match.group(1)
            found[code]=line[5:].strip()[:180]
    if len(found)<1000:
        raise ValueError("Parsed fewer than 1,000 codes; source record layout may have changed")
    return found

def compare_snapshots(older: dict[str,str], newer: dict[str,str],
                      old_label: str, new_label: str) -> pd.DataFrame:
    a,b=set(older),set(newer)
    entries=[]
    for code in sorted(a|b):
        if code in b and code not in a: status="Appeared in newer release"
        elif code in a and code not in b: status="Absent from newer release"
        elif older[code]!=newer[code]: status="Record text changed"
        else: continue
        entries.append({"code":code,"release_change":status,
                        "old_record":older.get(code,""),
                        "new_record":newer.get(code,""),
                        "older_release":old_label,"newer_release":new_label})
    return pd.DataFrame(entries,columns=["code","release_change","old_record",
                                          "new_record","older_release","newer_release"])

def load_quarterly_changes(old_label="July 2026",new_label="October 2026"):
    page=requests.get(CMS_PAGE,timeout=30,headers={"User-Agent":"CMS-Research-Lab/1.0"})
    page.raise_for_status()
    links=discover_releases(page.text)
    missing=[x for x in (old_label,new_label) if x not in links]
    if missing:
        raise ValueError("CMS quarterly archive links were not found: "+", ".join(missing))
    before=parse_snapshot_archive(download_bytes(links[old_label]))
    after=parse_snapshot_archive(download_bytes(links[new_label]))
    return compare_snapshots(before,after,old_label,new_label),links
