import io
import json
import zipfile
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="NovaRetail — Bloc 2", page_icon="📊", layout="wide")

VALID_CHANNELS = ["Emailing", "Google Ads", "LinkedIn Ads"]

CHANNEL_NORMALIZATION = {
    "googleads": "Google Ads",
    "google ads": "Google Ads",
    "linkedin": "LinkedIn Ads",
    "linkedin ads": "LinkedIn Ads",
    "e-mailing": "Emailing",
    "emailing": "Emailing",
}
DEVICE_NORMALIZATION = {"desktop": "Desktop", "mobile": "Mobile", "tablet": "Tablet"}
REGION_NORMALIZATION = {"Ile-de-France": "Île-de-France"}
COMPANY_SIZE_NORMALIZATION = {"10 - 50": "10-50", "50- 100": "50-100"}

STATUS_RANK = {"Client": 3, "SQL": 2, "MQL": 1, "Lost": 0}

# =========================
# UTILS
# =========================
def _count_missing(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for c in df.columns:
        s = df[c]
        na = int(s.isna().sum())
        empty = int((s.astype(str).str.strip() == "").sum())
        rows.append({"variable": c, "missing_count": na + empty})
    out = pd.DataFrame(rows).sort_values("missing_count", ascending=False)
    return out

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

def compute_campaign_kpis_by_channel(camp_agg: pd.DataFrame) -> pd.DataFrame:
    out = camp_agg.copy()
    out["CTR"] = out["clicks"] / out["impressions"]
    out["conversion_rate"] = out["conversions"] / out["clicks"]
    out["CPL"] = out["cost"] / out["conversions"]
    return out

def freq_table(df: pd.DataFrame, col: str) -> pd.DataFrame:
    s = df[col].fillna("NA")
    out = s.value_counts(dropna=False).rename("count").to_frame()
    out["percent"] = (out["count"] / out["count"].sum()).round(4)
    return out

def crosstab_percent(df: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    return (pd.crosstab(df[a], df[b], normalize="index").fillna(0) * 100).round(1)

# =========================
# APP HEADER
# =========================
st.title("📊 NovaRetail — Bloc 2 : Sélection & Interprétation des Données (IA)")
st.caption("Upload → Filtrage périmètre → Nettoyage → KPI → Analyses → Graphiques → Dashboard → Exports")

st.sidebar.header("1) Upload des fichiers")
leads_file = st.sidebar.file_uploader("leads (CSV)", type=["csv"])
camp_file = st.sidebar.file_uploader("campaigns (JSON)", type=["json"])
crm_file = st.sidebar.file_uploader("crm (XLSX)", type=["xlsx"])

st.sidebar.header("2) Périmètre")
month = st.sidebar.selectbox("Mois (périmètre imposé)", ["2025-10"], index=0)
channels_sel = st.sidebar.multiselect("Canaux analysés", VALID_CHANNELS, default=VALID_CHANNELS)

run = st.sidebar.button("🚀 Exécuter", type="primary")

if not (leads_file and camp_file and crm_file):
    st.info("⬅️ Importer les 3 fichiers pour commencer (CSV + JSON + XLSX).")
    st.stop()

if not run and "final_df" not in st.session_state:
    st.warning("Clique sur **Exécuter**.")
    st.stop()

# =========================
# PIPELINE
# =========================
if run:
    with st.spinner("Traitement (chargement + nettoyage + KPI)..."):
        # ---- Load
        leads = pd.read_csv(leads_file)
        campaigns = pd.read_json(camp_file)
        crm = pd.read_excel(crm_file)

        # ---- Report before
        before = {
            "leads_rows": len(leads),
            "crm_rows": len(crm),
            "campaign_rows": len(campaigns),
            "missing_leads": _count_missing(leads),
            "missing_crm": _count_missing(crm),
            "missing_campaigns": _count_missing(campaigns),
        }

        # ---- Normalize / Types
        leads = leads.copy()
        crm = crm.copy()
        campaigns = campaigns.copy()

        leads["date"] = pd.to_datetime(leads["date"], errors="coerce")
        leads["channel"] = leads["channel"].apply(norm_channel)
        leads["device"] = leads["device"].apply(norm_device)

        for col in ["company_size", "sector", "region", "status"]:
            if col not in crm.columns:
                crm[col] = np.nan

        crm["company_size"] = crm["company_size"].astype(str).str.strip().replace(COMPANY_SIZE_NORMALIZATION)
        crm["company_size"] = crm["company_size"].replace({"": np.nan, "nan": np.nan})
        crm["sector"] = crm["sector"].astype(str).str.strip().replace({"": np.nan, "nan": np.nan})
        crm["region"] = crm["region"].astype(str).str.strip().replace(REGION_NORMALIZATION).replace({"": np.nan, "nan": np.nan})
        crm["status"] = crm["status"].astype(str).str.strip().replace({"": np.nan, "nan": np.nan})

        # ---- Filter scope (Oct 2025)
        month_start = pd.to_datetime(f"{month}-01")
        month_end = month_start + pd.offsets.MonthEnd(1)
        leads = leads[(leads["date"] >= month_start) & (leads["date"] <= month_end)]

        # ---- Keep valid channels + selected channels
        leads = leads[leads["channel"].isin(VALID_CHANNELS)]
        leads = leads[leads["channel"].isin(channels_sel)]

        # ---- Deduplicate leads by lead_id
        leads_before = len(leads)
        leads = leads.sort_values(["lead_id", "date"]).drop_duplicates(subset=["lead_id"], keep="first")
        dup_leads_removed = leads_before - len(leads)

        # ---- Deduplicate CRM keep best status
        crm["_rank"] = crm["status"].map(STATUS_RANK).fillna(-1)
        crm_before = len(crm)
        crm = crm.sort_values(["lead_id", "_rank"], ascending=[True, False]).drop_duplicates(subset=["lead_id"], keep="first")
        crm = crm.drop(columns=["_rank"])
        dup_crm_removed = crm_before - len(crm)

        # ---- Aggregate campaigns by channel (sum) for KPI
        camp_agg = campaigns.groupby("channel", as_index=False).agg(
            cost=("cost", "sum"),
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            conversions=("conversions", "sum"),
        )
        camp_agg = camp_agg[camp_agg["channel"].isin(channels_sel)]

        # ---- Merge
        df = leads.merge(crm, on="lead_id", how="left", validate="one_to_one")
        df = df.merge(camp_agg, on="channel", how="left", validate="many_to_one")

        # ---- After report
        after = {
            "final_rows": len(df),
            "dup_leads_removed": int(dup_leads_removed),
            "dup_crm_removed": int(dup_crm_removed),
            "missing_final": _count_missing(df),
        }

        st.session_state["final_df"] = df
        st.session_state["before"] = before
        st.session_state["after"] = after
        st.session_state["camp_agg"] = camp_agg

df = st.session_state["final_df"]
before = st.session_state["before"]
after = st.session_state["after"]
camp_agg = st.session_state["camp_agg"]

# =========================
# KPI / ANALYSES
# =========================
camp_kpi = compute_campaign_kpis_by_channel(camp_agg)

total_leads = len(df)
clients = int((df["status"] == "Client").sum())
sql = int((df["status"] == "SQL").sum())
mql = int((df["status"] == "MQL").sum())
unknown = int(df["status"].isna().sum())
client_rate = (clients / total_leads) if total_leads else 0.0

best_cpl_channel = camp_kpi.sort_values("CPL").iloc[0]["channel"] if len(camp_kpi) else "—"
best_ctr_channel = camp_kpi.sort_values("CTR", ascending=False).iloc[0]["channel"] if len(camp_kpi) else "—"

# =========================
# DASHBOARD (3–6 KPI)
# =========================
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Leads (Oct 2025)", f"{total_leads:,}".replace(",", " "))
c2.metric("Clients", f"{clients:,}".replace(",", " "))
c3.metric("% Clients", f"{client_rate*100:.1f}%")
c4.metric("SQL", f"{sql:,}".replace(",", " "))
c5.metric("Meilleur CPL", f"{camp_kpi['CPL'].min():.2f} €" if len(camp_kpi) else "—")
c6.metric("Canal + rentable", best_cpl_channel)

st.divider()

# =========================
# TABS
# =========================
tab1, tab2, tab3, tab4 = st.tabs([
    "1) Sélection & Nettoyage (preuves)",
    "2) Analyse uni/bivariée",
    "3) Graphiques (3–6)",
    "4) Exports (livrables)",
])

with tab1:
    st.subheader("1) Sélection des observations & variables (périmètre)")
    st.markdown(
        f"""
- **Périmètre** : {month} uniquement (Octobre 2025)  
- **Canaux** : {", ".join(channels_sel)}  
- **Variables retenues (utiles métier)** :  
  - Leads : `lead_id`, `date`, `channel`, `device` (identification + source acquisition + device)  
  - CRM : `company_size`, `sector`, `region`, `status` (segmentation + qualité lead)  
  - Campagnes : `cost`, `impressions`, `clicks`, `conversions` (KPI CTR/Conv/CPL)  
- **Variables exclues** : non présentes / non utiles (pas de suppressions arbitraires).
"""
    )

    st.write("### Preuves attendues — valeurs manquantes (avant)")
    colA, colB, colC = st.columns(3)
    with colA:
        st.caption("Leads")
        st.dataframe(before["missing_leads"], use_container_width=True, height=240)
    with colB:
        st.caption("CRM")
        st.dataframe(before["missing_crm"], use_container_width=True, height=240)
    with colC:
        st.caption("Campaigns")
        st.dataframe(before["missing_campaigns"], use_container_width=True, height=240)

    st.write("### Nettoyage appliqué (résumé)")
    st.json({
        "filtrage_perimetre": month,
        "canaux_valides": VALID_CHANNELS,
        "doublons_supprimes_leads": after["dup_leads_removed"],
        "doublons_supprimes_crm": after["dup_crm_removed"],
        "normalisation": ["channel", "device", "region", "company_size"],
        "campagnes": "agrégation par canal (sommes)",
    })

    st.write("### Preuves attendues — valeurs manquantes (après)")
    st.dataframe(after["missing_final"], use_container_width=True, height=280)

    st.write("### Aperçu dataset final (après filtrage + fusion)")
    st.dataframe(df.head(30), use_container_width=True)

with tab2:
    st.subheader("2) Analyse univariée et bivariée")

    st.write("### Quantitatives (campagnes par canal)")
    st.dataframe(camp_kpi[["channel","cost","impressions","clicks","conversions","CTR","conversion_rate","CPL"]], use_container_width=True)

    st.write("### Qualitatives (fréquences)")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.caption("Channel")
        st.dataframe(freq_table(df, "channel"), use_container_width=True, height=220)
    with f2:
        st.caption("Device")
        st.dataframe(freq_table(df, "device"), use_container_width=True, height=220)
    with f3:
        st.caption("Status")
        st.dataframe(freq_table(df, "status"), use_container_width=True, height=220)
    with f4:
        st.caption("Region")
        st.dataframe(freq_table(df, "region"), use_container_width=True, height=220)

    st.write("### Bivariée (croisements métier pertinents)")
    st.caption("Channel × Status (% par canal) — qualité des leads par levier")
    st.dataframe(crosstab_percent(df, "channel", "status"), use_container_width=True)

    st.caption("Company size × Status (% par taille) — segments les plus ‘clients’")
    if df["company_size"].notna().any():
        st.dataframe(crosstab_percent(df, "company_size", "status"), use_container_width=True)
    else:
        st.info("company_size manquant après fusion/filtrage (selon CRM).")

    st.caption("Sector × Status (% par secteur)")
    if df["sector"].notna().any():
        st.dataframe(crosstab_percent(df, "sector", "status"), use_container_width=True)
    else:
        st.info("sector manquant après fusion/filtrage (selon CRM).")

with tab3:
    st.subheader("3) Visualisations (5 graphiques) — chaque graphe répond à une question métier")

    # 1) CTR
    fig1 = px.bar(camp_kpi, x="channel", y="CTR",
                  title="CTR par canal — Quel canal capte le mieux l’attention ?")
    st.plotly_chart(fig1, use_container_width=True)

    # 2) CPL
    fig2 = px.bar(camp_kpi, x="channel", y="CPL",
                  title="CPL par canal — Quel canal est le plus rentable ?")
    st.plotly_chart(fig2, use_container_width=True)

    # 3) Conversion rate
    fig3 = px.bar(camp_kpi, x="channel", y="conversion_rate",
                  title="Taux de conversion (clic → conversion) par canal — Qualité du trafic")
    st.plotly_chart(fig3, use_container_width=True)

    # 4) Status distribution per channel
    dist = df.groupby(["channel","status"]).size().reset_index(name="count")
    fig4 = px.bar(dist, x="channel", y="count", color="status", barmode="stack",
                  title="Funnel marketing — Répartition MQL/SQL/Client par canal")
    st.plotly_chart(fig4, use_container_width=True)

    # 5) Clients by region (if possible)
    if df["region"].notna().any():
        clients_region = (df[df["status"]=="Client"]
                          .groupby("region").size().reset_index(name="clients")
                          .sort_values("clients", ascending=False))
        fig5 = px.bar(clients_region, x="region", y="clients",
                      title="Clients par région — Où concentrer la prospection ?")
        st.plotly_chart(fig5, use_container_width=True)

with tab4:
    st.subheader("4) Livrables — Exports + Note métier + Carnet technique")

    # Note métier (1–2 pages max, synthétique)
    note = f"""
# Note d’analyse métier — NovaRetail (Bloc 2)

## Contexte & objectifs
NovaRetail (SaaS B2B) a lancé plusieurs campagnes (Emailing, Google Ads, LinkedIn Ads) et alimente un CRM.
L’objectif est de sélectionner les données du périmètre **octobre 2025**, nettoyer et fusionner les sources,
calculer des KPI marketing (**CTR**, **taux de conversion**, **CPL**), analyser la qualité des leads (MQL/SQL/Client)
et proposer des recommandations opérationnelles.

## Résultats clés
- Leads analysés (après nettoyage/fusion) : **{total_leads}**
- Clients : **{clients}** (taux client : **{client_rate*100:.1f}%**)
- Meilleur CTR : **{best_ctr_channel}**
- Meilleur CPL (rentabilité) : **{best_cpl_channel}**

## Interprétation métier
- Un canal avec un CTR élevé n’est pas forcément le plus rentable : le **CPL** et la part de **Clients** sont critiques.
- La distribution **MQL → SQL → Client** par canal indique la qualité du trafic et la performance commerciale.
- Les segmentations (taille, secteur, région) permettent de cibler les segments les plus convertisseurs.

## Recommandations opérationnelles
1) Réallouer une partie du budget vers **{best_cpl_channel}** (meilleure rentabilité).
2) Optimiser le canal le moins rentable : ciblage, message, landing page, nurturing CRM.
3) Prioriser les segments (secteur/région/taille) qui présentent la plus forte proportion de **Clients**.
4) Mettre en place un suivi hebdomadaire des KPI (dashboard) et un contrôle de qualité des données (doublons/manquants).
""".strip()

    # Carnet technique (problèmes + solutions)
    carnet = pd.DataFrame([
        {"Problème":"Lignes hors périmètre", "Solution":"Filtrer les dates sur Octobre 2025", "Justification":"Respect consigne, comparabilité des analyses."},
        {"Problème":"Doublons lead_id", "Solution":"Déduplication leads (1 ligne/lead) + CRM (meilleur statut)", "Justification":"Évite biais sur volumes et taux."},
        {"Problème":"Catégories incohérentes", "Solution":"Normalisation channel/device/region/company_size", "Justification":"Agrégations fiables (KPI & segmentations)."},
        {"Problème":"Valeurs manquantes", "Solution":"Conserver NA + reporting des manquants", "Justification":"Traçabilité, pas de suppression globale interdite."},
        {"Problème":"Campagnes multiples", "Solution":"Agrégation par canal (somme des coûts/impressions/clicks/conversions)", "Justification":"KPI comparables entre canaux."},
    ])

    st.download_button("📥 Dataset nettoyé (CSV)", df.to_csv(index=False).encode("utf-8"), "novaretail_clean.csv", "text/csv")
    st.download_button("📥 KPI campagnes (CSV)", camp_kpi.to_csv(index=False).encode("utf-8"), "novaretail_kpi_campaigns.csv", "text/csv")
    st.download_button("📥 Note métier (MD)", note.encode("utf-8"), "novaretail_note_metier.md", "text/markdown")
    st.download_button("📥 Carnet technique (CSV)", carnet.to_csv(index=False).encode("utf-8"), "novaretail_carnet_technique.csv", "text/csv")

    # Export ZIP complet
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("exports/novaretail_clean.csv", df.to_csv(index=False))
        z.writestr("exports/novaretail_kpi_campaigns.csv", camp_kpi.to_csv(index=False))
        z.writestr("exports/novaretail_note_metier.md", note)
        z.writestr("exports/novaretail_carnet_technique.csv", carnet.to_csv(index=False))
        z.writestr("exports/rapport_qualite_avant_missing.csv", before["missing_leads"].to_csv(index=False))
        z.writestr("exports/rapport_qualite_apres_missing.csv", after["missing_final"].to_csv(index=False))
    st.download_button("📦 Télécharger TOUS les livrables (ZIP)", buf.getvalue(), "novaretail_livrables.zip", "application/zip")

    st.write("### Prévisualisation — Note métier")
    st.code(note, language="markdown")

    st.write("### Prévisualisation — Carnet technique")
    st.dataframe(carnet, use_container_width=True)
