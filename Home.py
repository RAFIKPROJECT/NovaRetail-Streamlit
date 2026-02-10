# =========================
# Home.py — NovaRetail Bloc 2
# Page principale Streamlit
# =========================

import os
import sys

# --- FIX IMPORT PATH (OBLIGATOIRE POUR STREAMLIT CLOUD) ---
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "src"))

# --- LIBS ---
import streamlit as st
import pandas as pd

# --- IMPORTS PROJET ---
from data_prep import load_raw_from_uploads, clean_and_prepare
from analysis import compute_kpis

# ---------------------
# CONFIG STREAMLIT
# ---------------------
st.set_page_config(
    page_title="NovaRetail – Bloc 2",
    page_icon="📊",
    layout="wide"
)

# ---------------------
# TITRE
# ---------------------
st.title("📊 NovaRetail — Analyse Marketing (Bloc 2)")
st.caption("Python • Streamlit • Analyse de données • KPI • Dashboard décisionnel")

st.markdown("---")

# ---------------------
# SIDEBAR — UPLOAD
# ---------------------
st.sidebar.header("📁 Import des données")

leads_file = st.sidebar.file_uploader(
    "Leads (CSV)",
    type=["csv"],
    key="leads"
)

campaign_file = st.sidebar.file_uploader(
    "Campagnes (JSON)",
    type=["json"],
    key="campaign"
)

crm_file = st.sidebar.file_uploader(
    "CRM (Excel)",
    type=["xlsx"],
    key="crm"
)

# ---------------------
# CONTROLE UPLOAD
# ---------------------
if not (leads_file and campaign_file and crm_file):
    st.info(
        "⬅️ Veuillez importer les **3 fichiers requis** pour commencer :\n"
        "- leads (CSV)\n"
        "- campagnes (JSON)\n"
        "- CRM (Excel)"
    )
    st.stop()

# ---------------------
# CHARGEMENT DONNÉES
# ---------------------
with st.spinner("📥 Chargement des fichiers..."):
    raw_data = load_raw_from_uploads(
        leads_file=leads_file,
        campaign_file=campaign_file,
        crm_file=crm_file
    )

st.success("✅ Fichiers chargés avec succès")

# ---------------------
# NETTOYAGE / PRÉPARATION
# ---------------------
with st.spinner("🧹 Nettoyage et préparation des données..."):
    df_clean = clean_and_prepare(raw_data)

st.success("✅ Données prêtes à l’analyse")

# ---------------------
# APERÇU DES DONNÉES
# ---------------------
with st.expander("🔍 Aperçu des données préparées", expanded=False):
    st.dataframe(df_clean.head(20), use_container_width=True)
    st.write(f"**Nombre de lignes :** {len(df_clean)}")

# ---------------------
# KPI PRINCIPAUX
# ---------------------
st.markdown("## 🎯 Indicateurs clés (KPI)")

kpis = compute_kpis(df_clean)

c1, c2, c3, c4 = st.columns(4)

c1.metric("CTR moyen", f"{kpis['ctr']:.2%}")
c2.metric("Taux de conversion", f"{kpis['conversion_rate']:.2%}")
c3.metric("CPL moyen", f"{kpis['cpl']:.2f} €")
c4.metric("Conversions", int(kpis["conversions"]))

# ---------------------
# MESSAGE ORIENTATION
# ---------------------
st.markdown("---")
st.success(
    "👉 Utilisez le **menu à gauche** pour accéder aux pages :\n"
    "- 🧹 Nettoyage\n"
    "- 📊 Analyse\n"
    "- 📈 Graphiques\n"
    "- 🧭 Dashboard\n"
    "- 📄 Exports\n"
)

# ---------------------
# FOOTER
# ---------------------
st.markdown(
    """
    <hr>
    <center>
    <small>
    Projet académique — Bloc 2 — Sélection et interprétation des données<br>
    NovaRetail • Python • Streamlit
    </small>
    </center>
    """,
    unsafe_allow_html=True
)
