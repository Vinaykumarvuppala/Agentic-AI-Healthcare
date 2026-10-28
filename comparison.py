"""CMS procedure comparison helpers: compare like-for-like modifier records."""
import pandas as pd

FIELDS = ("sdesc","proc_stat","modifier","nfac_total","fac_total","conv_fact")
LABELS = {"sdesc":"Description","proc_stat":"Procedure status","modifier":"Modifier",
          "nfac_total":"Non-facility total RVU","fac_total":"Facility total RVU",
          "conv_fact":"Conversion factor"}

def variants(df: pd.DataFrame, code: str) -> list[str]:
    rows = df.loc[df["hcpc"].astype(str).str.upper() == code.upper()]
    if rows.empty:
        return []
    if "modifier" not in rows:
        return [""]
    return sorted({str(m).strip() for m in rows["modifier"].fillna("")})

def compare_codes(df: pd.DataFrame, left: str, right: str, modifier: str = "") -> pd.DataFrame:
    if not left or not right or left == right:
        raise ValueError("Choose two different codes.")
    def select(code):
        rows = df.loc[df["hcpc"].astype(str).str.upper() == code.upper()]
        if rows.empty:
            raise ValueError(f"Code {code} not found")
        if "modifier" in rows:
            rows = rows.loc[rows["modifier"].fillna("").astype(str).str.strip() == modifier]
        if rows.empty:
            raise ValueError(f"No matching modifier '{modifier or 'none'}' for {code}.")
        return rows.iloc[0]
    a,b=select(left),select(right)
    output=[]
    for field in FIELDS:
        if field not in df.columns:
            continue
        l = "" if pd.isna(a[field]) else str(a[field]).strip()
        r = "" if pd.isna(b[field]) else str(b[field]).strip()
        output.append({"Field":LABELS[field], left:l or "—", right:r or "—",
                       "Different":"Yes" if l!=r else "No"})
    return pd.DataFrame(output)
