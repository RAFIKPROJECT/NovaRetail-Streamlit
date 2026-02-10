import streamlit as st
import plotly.express as px

from src.analysis import compute_kpis_by_channel, freq, crosstab_percent, sector_client_rate

st.title("Analyse statistique (univariée & bivariée)")

if "df" not in st.session_state:
    st.warning("Retourne sur Home et lance le traitement.")
    st.stop()

df = st.session_state["df"]
kpi = compute_kpis_by_channel(df)

st.subheader("Univariée — quantitatives (campagnes)")
st.dataframe(kpi, use_container_width=True)

st.subheader("Univariée — qualitatives (fréquences)")
c1,c2,c3 = st.columns(3)
with c1:
    st.caption("Device")
    st.dataframe(freq(df, "device"))
with c2:
    st.caption("Status")
    st.dataframe(freq(df, "status"))
with c3:
    st.caption("Company size")
    st.dataframe(freq(df, "company_size"))

st.subheader("Bivariée — croisements métier")
st.caption("Channel × Status (%, par canal)")
st.dataframe(crosstab_percent(df, "channel", "status"), use_container_width=True)

st.caption("Company size × Status (%, par taille)")
if df["company_size"].notna().any():
    st.dataframe(crosstab_percent(df, "company_size", "status"), use_container_width=True)

st.caption("Sector × %Clients")
if df["sector"].notna().any():
    st.dataframe(sector_client_rate(df), use_container_width=True)
