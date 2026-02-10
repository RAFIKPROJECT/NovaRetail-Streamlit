from __future__ import annotations
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, List

VALID_CHANNELS = ["Emailing", "Google Ads", "LinkedIn Ads"]

CHANNEL_NORMALIZATION = {
    "googleads": "Google Ads",
    "google ads": "Google Ads",
    "linkedin": "LinkedIn Ads",
    "linkedin ads": "LinkedIn Ads",
    "e-mailing": "Emailing",
    "emailing": "Emailing",
}

DEVICE_NORMALIZATION = {
    "desktop": "Desktop",
    "mobile": "Mobile",
    "tablet": "Tablet",
    "mOBILE".lower(): "Mobile",
    "MOBILE": "Mobile",
}

COMPANY_SIZE_NORMALIZATION = {
    "10 - 50": "10-50",
    "50- 100": "50-100",
}

REGION_NORMALIZATION = {
    "Ile-de-France": "Île-de-France",
}

STATUS_RANK = {"Client": 3, "SQL": 2, "MQL": 1, "Lost": 0}

@dataclass
class DataQualityReport:
    rows_in: Dict[str, int]
    rows_out: Dict[str, int]
    duplicates_removed: Dict[str, int]
    missing_before: Dict[str, Dict[str, int]]
    missing_after: Dict[str, Dict[str, int]]
    notes: List[str]

def _count_missing(df: pd.DataFrame) -> Dict[str, int]:
    out = {}
    for c in df.columns:
        s = df[c]
        na = int(s.isna().sum())
        empty = int((s.astype(str).str.strip() == "").sum())
        out[c] = na + empty
    return out

def load_raw_from_uploads(leads_bytes: bytes, campaigns_bytes: bytes, crm_bytes: bytes) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    import io
    leads = pd.read_csv(io.BytesIO(leads_bytes))
    campaigns = pd.read_json(io.BytesIO(campaigns_bytes))
    crm = pd.read_excel(io.BytesIO(crm_bytes), sheet_name=0)
    return leads, campaigns, crm

def clean_and_prepare(leads: pd.DataFrame, campaigns: pd.DataFrame, crm: pd.DataFrame, month: str = "2025-10") -> Tuple[pd.DataFrame, DataQualityReport]:
    notes: List[str] = []
    rows_in = {"leads": len(leads), "campaigns": len(campaigns), "crm": len(crm)}
    duplicates_removed = {"leads": 0, "crm": 0}

    leads = leads.copy()
    crm = crm.copy()
    campaigns = campaigns.copy()

    # Types
    leads["date"] = pd.to_datetime(leads.get("date"), errors="coerce")

    # Normalize leads
    def norm_channel(x):
        if pd.isna(x):
            return np.nan
        s = str(x).strip()
        if not s:
            return np.nan
        return CHANNEL_NORMALIZATION.get(s.lower(), s)

    def norm_device(x):
        if pd.isna(x):
            return np.nan
        s = str(x).strip()
        if not s:
            return np.nan
        return DEVICE_NORMALIZATION.get(s.lower(), s.title())

    leads["channel"] = leads.get("channel").apply(norm_channel)
    leads["device"] = leads.get("device").apply(norm_device)

    # Normalize CRM
    for col in ["company_size","sector","region","status"]:
        if col not in crm.columns:
            crm[col] = np.nan

    crm["company_size"] = crm["company_size"].astype(str).str.strip().replace(COMPANY_SIZE_NORMALIZATION)
    crm["company_size"] = crm["company_size"].replace({"": np.nan, "nan": np.nan})
    crm["sector"] = crm["sector"].astype(str).str.strip().replace({"": np.nan, "nan": np.nan})
    crm["region"] = crm["region"].astype(str).str.strip().replace(REGION_NORMALIZATION)
    crm["region"] = crm["region"].replace({"": np.nan, "nan": np.nan})
    crm["status"] = crm["status"].astype(str).str.strip().replace({"": np.nan, "nan": np.nan})

    missing_before = {"leads": _count_missing(leads), "crm": _count_missing(crm), "campaigns": _count_missing(campaigns)}

    # Scope filter
    month_start = pd.to_datetime(f"{month}-01")
    month_end = month_start + pd.offsets.MonthEnd(1)
    leads = leads[(leads["date"] >= month_start) & (leads["date"] <= month_end)]

    # Keep valid channels only
    leads = leads[leads["channel"].isin(VALID_CHANNELS)]

    # Dedup leads
    before_leads = len(leads)
    leads = leads.sort_values(["lead_id", "date"]).drop_duplicates(subset=["lead_id"], keep="first")
    duplicates_removed["leads"] = before_leads - len(leads)

    # Dedup CRM keeping best status
    crm["_rank"] = crm["status"].map(STATUS_RANK).fillna(-1)
    before_crm = len(crm)
    crm = crm.sort_values(["lead_id","_rank"], ascending=[True, False]).drop_duplicates(subset=["lead_id"], keep="first")
    crm = crm.drop(columns=["_rank"])
    duplicates_removed["crm"] = before_crm - len(crm)

    # Aggregate campaigns per channel (multiple campaigns allowed)
    agg = campaigns.groupby("channel", as_index=False).agg(
        cost=("cost","sum"),
        impressions=("impressions","sum"),
        clicks=("clicks","sum"),
        conversions=("conversions","sum"),
    )

    # Merge
    df = leads.merge(crm, on="lead_id", how="left", validate="one_to_one")
    df = df.merge(agg, on="channel", how="left", validate="many_to_one")

    notes += [
        f"Périmètre appliqué: {month} (Octobre 2025).",
        "Exclusions: dates hors octobre + canaux invalides + doublons lead_id.",
        "Normalisation: channel/device/company_size/region.",
        "Campagnes: agrégation par canal (sommes).",
    ]

    dq = DataQualityReport(
        rows_in=rows_in,
        rows_out={"final": len(df)},
        duplicates_removed=duplicates_removed,
        missing_before=missing_before,
        missing_after={"final": _count_missing(df)},
        notes=notes,
    )
    return df, dq
