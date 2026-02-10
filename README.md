# NovaRetail — Bloc 2 (Python + Streamlit) — Projet complet

## Ce que fait l'app (conforme consigne)
- Import des 3 fichiers (CSV/JSON/XLSX) via l'interface
- Filtrage du périmètre (Octobre 2025)
- Nettoyage (doublons, valeurs manquantes, incohérences de catégories)
- Fusion leads + CRM + campagnes (agrégation par canal)
- KPI: CTR, Taux de conversion, CPL
- Analyses: univariée (quant/quali) + bivariée (croisements métier)
- 3 à 6 visualisations (5 incluses)
- Dashboard décisionnel (KPI max 6)
- Exports (dataset clean + KPI + note métier + carnet technique + ZIP)

## Lancer en local
```bash
pip install -r requirements.txt
streamlit run Home.py
```

## Héberger sur Streamlit Cloud (via GitHub)
1) Crée un repo GitHub (ex: `novaretail-bloc2`)
2) Mets ces fichiers à la racine du repo (ne mets pas les données si tu veux uniquement upload via UI)
3) Push sur GitHub
4) Va sur Streamlit Community Cloud -> New app
5) Choisis ton repo + branche + Main file path: `Home.py`
6) Deploy

### Exemple commandes Git
```bash
git init
git add .
git commit -m "NovaRetail Bloc2 Streamlit"
git branch -M main
git remote add origin <URL_DU_REPO>
git push -u origin main
```
