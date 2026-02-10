import io, json, zipfile
import streamlit as st
import pandas as pd
from src.analysis import compute_kpis_by_channel, crm_kpis

st.title("Exports (livrables)")

if "df" not in st.session_state or "dq" not in st.session_state:
    st.warning("Retourne sur Home et lance le traitement.")
    st.stop()

df = st.session_state["df"]
dq = st.session_state["dq"]
kpi = compute_kpis_by_channel(df)
ck = crm_kpis(df)

best_cpl = kpi.sort_values("CPL").iloc[0]["channel"] if len(kpi) else "—"
best_ctr = kpi.sort_values("CTR", ascending=False).iloc[0]["channel"] if len(kpi) else "—"

note = f"""
# Note d’analyse métier — NovaRetail (Bloc 2)

## Contexte & objectifs
Données issues d’outils marketing & CRM intégrant de l’automatisation et du scoring (IA).
Objectif: évaluer la performance par canal (CTR, taux de conversion, CPL) et la qualité des leads (MQL/SQL/Client) pour guider la décision.

## Résultats clés
- Meilleur CPL: **{best_cpl}**
- Meilleur CTR: **{best_ctr}**
- Leads analysés: **{ck['total_leads']}**
- Clients: **{ck['clients']}** (taux client: **{ck['client_rate']*100:.1f}%**)

## Interprétation métier
- Prioriser les canaux à faible CPL (ROI).
- Suivre le funnel MQL→SQL→Client pour mesurer la qualité des leads.
- Exploiter la segmentation (secteur/région/taille) pour orienter la prospection.

## Recommandations
1) Réallouer budget vers {best_cpl}.
2) Optimiser le canal le moins rentable (ciblage, message, landing).
3) Prioriser les segments à forte conversion observés.
4) Suivi hebdomadaire KPI + funnel.
""".strip()

carnet = pd.DataFrame([
    {"Problème":"Dates hors périmètre", "Solution":"Filtrage Octobre 2025", "Justification":"Respect consigne."},
    {"Problème":"Doublons lead_id", "Solution":"Déduplication (leads) + meilleur statut (CRM)", "Justification":"Évite biais."},
    {"Problème":"Valeurs manquantes", "Solution":"Conserver NA + reporting", "Justification":"Traçabilité (pas suppression globale)."},
    {"Problème":"Catégories incohérentes", "Solution":"Normalisation", "Justification":"Agrégations fiables."},
    {"Problème":"Multiples campagnes", "Solution":"Agrégation par canal", "Justification":"KPI comparables."},
])

st.download_button("Dataset nettoyé (CSV)", df.to_csv(index=False).encode("utf-8"), "leads_enrichis_clean.csv", "text/csv")
st.download_button("KPI par canal (CSV)", kpi.to_csv(index=False).encode("utf-8"), "kpi_by_channel.csv", "text/csv")
st.download_button("Note métier (MD)", note.encode("utf-8"), "note_analyse_metier.md", "text/markdown")
st.download_button("Carnet technique (CSV)", carnet.to_csv(index=False).encode("utf-8"), "carnet_technique.csv", "text/csv")

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
    z.writestr("exports/leads_enrichis_clean.csv", df.to_csv(index=False))
    z.writestr("exports/kpi_by_channel.csv", kpi.to_csv(index=False))
    z.writestr("exports/note_analyse_metier.md", note)
    z.writestr("exports/carnet_technique.csv", carnet.to_csv(index=False))
    z.writestr("exports/rapport_qualite.json", json.dumps({
        "rows_in": dq.rows_in,
        "rows_out": dq.rows_out,
        "duplicates_removed": dq.duplicates_removed,
        "missing_before": dq.missing_before,
        "missing_after": dq.missing_after,
        "notes": dq.notes,
    }, ensure_ascii=False, indent=2))

st.download_button("Tout exporter (ZIP)", buf.getvalue(), "novaretail_livrables.zip", "application/zip")

st.subheader("Prévisualisation — note métier")
st.code(note, language="markdown")
st.subheader("Prévisualisation — carnet technique")
st.dataframe(carnet, use_container_width=True)
