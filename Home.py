import io, json, zipfile
import streamlit as st
import pandas as pd
import plotly.express as px

from src.data_prep import load_raw_from_uploads, clean_and_prepare
from src.analysis import compute_kpis_by_channel, crm_kpis

st.set_page_config(page_title="NovaRetail — Bloc 2", layout="wide")
st.title("NovaRetail — Projet Bloc 2 (IA: sélection & interprétation des données)")
st.caption("Interface complète: upload → nettoyage → KPI → graphiques → dashboard → exports")

st.sidebar.header("Upload des fichiers")
leads = st.sidebar.file_uploader("leads (CSV)", type=["csv"])
campaigns = st.sidebar.file_uploader("campaigns (JSON)", type=["json"])
crm = st.sidebar.file_uploader("crm (XLSX)", type=["xlsx"])

st.sidebar.header("Paramètres")
month = st.sidebar.selectbox("Périmètre (mois)", ["2025-10"], index=0)
run = st.sidebar.button("🚀 Lancer le traitement", type="primary")

if not (leads and campaigns and crm):
    st.info("⬅️ Importer les 3 fichiers pour démarrer. (CSV + JSON + XLSX)")
    st.stop()

if run:
    leads_df, camp_df, crm_df = load_raw_from_uploads(leads.getvalue(), campaigns.getvalue(), crm.getvalue())
    df, dq = clean_and_prepare(leads_df, camp_df, crm_df, month=month)
    st.session_state["df"] = df
    st.session_state["dq"] = dq
    st.success("Traitement terminé. Ouvre les pages (Nettoyage / Analyse / Dashboard / Exports).")

if "df" not in st.session_state:
    st.warning("Clique sur **Lancer le traitement**.")
    st.stop()

df = st.session_state["df"]
kpi = compute_kpis_by_channel(df)
ck = crm_kpis(df)

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Leads", f"{ck['total_leads']:,}".replace(","," "))
c2.metric("Clients", f"{ck['clients']:,}".replace(","," "))
c3.metric("% Clients", f"{ck['client_rate']*100:.1f}%")
c4.metric("SQL", f"{ck['sql']:,}".replace(","," "))
c5.metric("MQL", f"{ck['mql']:,}".replace(","," "))
c6.metric("Statut inconnu", f"{ck['unknown_status']:,}".replace(","," "))

st.divider()
st.subheader("KPI campagnes (par canal) — CTR / Taux de conversion / CPL")
kpi_show = kpi.copy()
kpi_show["CTR"] = (kpi_show["CTR"]*100).round(2).astype(str) + "%"
kpi_show["conversion_rate"] = (kpi_show["conversion_rate"]*100).round(2).astype(str) + "%"
kpi_show["CPL"] = kpi_show["CPL"].round(2)
st.dataframe(kpi_show, use_container_width=True)

fig = px.bar(kpi, x="channel", y="CPL", title="CPL par canal — rentabilité (plus petit = mieux)")
st.plotly_chart(fig, use_container_width=True)

st.info("➡️ Continue avec les pages à gauche (menu Streamlit): Nettoyage / Analyse / Dashboard / Exports.")
