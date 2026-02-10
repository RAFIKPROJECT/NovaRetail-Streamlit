import streamlit as st
import pandas as pd

st.title("Nettoyage & sélection (périmètre)")

if "df" not in st.session_state or "dq" not in st.session_state:
    st.warning("Retourne sur Home et lance le traitement.")
    st.stop()

df = st.session_state["df"]
dq = st.session_state["dq"]

st.subheader("Rapport qualité (preuve attendue)")
st.json({
    "rows_in": dq.rows_in,
    "rows_out": dq.rows_out,
    "duplicates_removed": dq.duplicates_removed,
    "notes": dq.notes
})

st.subheader("Valeurs manquantes (avant)")
c1,c2,c3 = st.columns(3)
with c1:
    st.caption("Leads")
    st.dataframe(pd.DataFrame.from_dict(dq.missing_before["leads"], orient="index", columns=["missing"]))
with c2:
    st.caption("CRM")
    st.dataframe(pd.DataFrame.from_dict(dq.missing_before["crm"], orient="index", columns=["missing"]))
with c3:
    st.caption("Campaigns")
    st.dataframe(pd.DataFrame.from_dict(dq.missing_before["campaigns"], orient="index", columns=["missing"]))

st.subheader("Valeurs manquantes (après)")
st.dataframe(pd.DataFrame.from_dict(dq.missing_after["final"], orient="index", columns=["missing"]))

st.subheader("Aperçu dataset final")
st.dataframe(df.head(50), use_container_width=True)

st.download_button("Télécharger dataset final (CSV)", df.to_csv(index=False).encode("utf-8"), "leads_enrichis_clean.csv", "text/csv")
