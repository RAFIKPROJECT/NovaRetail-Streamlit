import streamlit as st
import plotly.express as px
from src.analysis import compute_kpis_by_channel, crm_kpis

st.title("Dashboard décisionnel (3 à 6 KPI max)")

if "df" not in st.session_state:
    st.warning("Retourne sur Home et lance le traitement.")
    st.stop()

df = st.session_state["df"]
kpi = compute_kpis_by_channel(df)
ck = crm_kpis(df)

# KPI cards (max 6)
c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Leads", f"{ck['total_leads']:,}".replace(","," "))
c2.metric("Clients", f"{ck['clients']:,}".replace(","," "))
c3.metric("% Clients", f"{ck['client_rate']*100:.1f}%")
c4.metric("CTR (meilleur canal)", f"{(kpi['CTR'].max()*100):.1f}%")
c5.metric("CPL (meilleur canal)", f"{kpi['CPL'].min():.2f}")
c6.metric("Canal + rentable", kpi.sort_values("CPL").iloc[0]["channel"])

st.divider()
st.plotly_chart(px.bar(kpi, x="channel", y="CPL", title="CPL par canal"), use_container_width=True)
st.plotly_chart(px.bar(kpi, x="channel", y="conversion_rate", title="Taux de conversion par canal"), use_container_width=True)
