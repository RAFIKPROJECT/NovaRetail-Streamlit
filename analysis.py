from __future__ import annotations
import pandas as pd
from typing import Dict

def compute_kpis_by_channel(df: pd.DataFrame) -> pd.DataFrame:
    ch = df.drop_duplicates(subset=["channel"])[["channel","cost","impressions","clicks","conversions"]].copy()
    ch["CTR"] = ch["clicks"] / ch["impressions"]
    ch["conversion_rate"] = ch["conversions"] / ch["clicks"]
    ch["CPL"] = ch["cost"] / ch["conversions"]
    return ch.sort_values("CPL")

def crm_kpis(df: pd.DataFrame) -> Dict[str, float]:
    total = len(df)
    clients = int((df["status"]=="Client").sum())
    sql = int((df["status"]=="SQL").sum())
    mql = int((df["status"]=="MQL").sum())
    lost = int((df["status"]=="Lost").sum())
    unknown = int(df["status"].isna().sum())
    return {
        "total_leads": total,
        "clients": clients,
        "sql": sql,
        "mql": mql,
        "lost": lost,
        "unknown_status": unknown,
        "client_rate": clients/total if total else 0.0
    }

def freq(df: pd.DataFrame, col: str) -> pd.DataFrame:
    s = df[col].fillna("NA")
    out = s.value_counts(dropna=False).rename("count").to_frame()
    out["percent"] = out["count"] / out["count"].sum()
    return out

def crosstab_percent(df: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    return (pd.crosstab(df[a], df[b], normalize="index").fillna(0) * 100).round(1)

def sector_client_rate(df: pd.DataFrame) -> pd.DataFrame:
    tmp = df.copy()
    tmp["is_client"] = tmp["status"].eq("Client")
    return (tmp.groupby("sector")["is_client"].mean().sort_values(ascending=False) * 100).to_frame("%Clients").round(1)

def region_clients(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["status"].eq("Client")].groupby("region").size().sort_values(ascending=False).rename("clients").to_frame()
