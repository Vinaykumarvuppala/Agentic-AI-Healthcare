"""Guided, evidence-first CMS investigation report builder."""
from __future__ import annotations
from datetime import datetime, timezone
import re

def build_report(code: str, question: str, rows: list[dict], evidence: list[dict], trace: list[str]) -> str:
    if not re.fullmatch(r"[A-Z0-9]{4,5}", code.upper()):
        raise ValueError("Invalid HCPCS code")
    if not question.strip():
        raise ValueError("A research question is required")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# CMS Procedure Investigation",
        f"**HCPCS:** {code.upper()}",
        f"**Question:** {question.strip()}",
        f"**Generated:** {now}",
        "**Status:** Research only — human verification required",
        "",
        "## Published CMS record facts",
    ]
    if not rows:
        lines.append("No matching record in the loaded CMS release.")
    else:
        for row in rows[:5]:
            desc = str(row.get("sdesc", "")).replace("\n", " ")
            lines.append(f"- {code.upper()}: {desc}; modifier={row.get('modifier') or 'none'}; status={row.get('proc_stat') or 'unspecified'}")
    lines.extend(["", "## Supporting evidence"])
    if evidence:
        for i, item in enumerate(evidence[:6], 1):
            excerpt = " ".join(str(item.get("text") or item.get("description") or "").split())[:500]
            url = item.get("source", "")
            page = f" (PDF page {item['page']})" if item.get("page") else ""
            lines.append(f"{i}. {excerpt}{page} — {url}")
    else:
        lines.append("No supporting policy passages retrieved.")
    lines.extend([
        "", "## Findings and uncertainties",
        "- Source values and excerpts above are observations, not a determination of correct billing or reimbursement.",
        "- Confirm the relevant service date, code year, modifiers, setting, applicable payer policy, and complete CMS guidance.",
        "- The public indicator data and limited E/M guide do not establish patient-specific medical necessity.",
        "", "## Analyst next steps",
        "1. Check original CMS publication, revisions and effective dates.",
        "2. Review the complete policy sections surrounding the cited passages.",
        "3. Escalate ambiguous interpretation to a qualified coding or compliance reviewer.",
        "", "## Workflow trace",
    ])
    lines.extend(f"- {event}" for event in trace)
    return "\n".join(lines)
