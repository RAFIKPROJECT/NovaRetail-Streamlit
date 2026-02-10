import streamlit as st
import plotly.express as px
from src.analysis import compute_kpis_by_channel

st.title("Graphiques (3 à 6) — questions métier")

if "df" not in st.session_state:
    st.warning("Retourne sur Home et lance le traitement.")
    st.stop()

df = st.session_state["df"]
kpi = compute_kpis_by_channel(df)

st.plotly_chart(px.bar(kpi, x="channel", y="CTR", title="CTR par canal — Quel canal capte le mieux l’attention ?"), use_container_width=True)
st.plotly_chart(px.bar(kpi, x="channel", y="CPL", title="CPL par canal — Quel canal est le plus rentable ?"), use_container_width=True)

dist = df.groupby(["channel","status"]).size().reset_index(name="count")
st.plotly_chart(px.bar(dist, x="channel", y="count", color="status", barmode="stack",
                       title="Qualité des leads — Statut (MQL/SQL/Client) par canal"), use_container_width=True)

if df["sector"].notna().any():
    cs = df[df["status"]=="Client"].groupby("sector").size().reset_index(name="clients").sort_values("clients", ascending=False)
    st.plotly_chart(px.bar(cs, x="sector", y="clients", title="Clients par secteur — Quels segments prioriser ?"), use_container_width=True)

if df["region"].notna().any():
    cr = df[df["status"]=="Client"].groupby("region").size().reset_index(name="clients").sort_values("clients", ascending=False)
    st.plotly_chart(px.bar(cr, x="region", y="clients", title="Clients par région — Où concentrer la prospection ?"), use_container_width=True)
