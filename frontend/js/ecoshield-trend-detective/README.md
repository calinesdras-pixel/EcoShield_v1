# EcoShield — Earth System Trend Detective

Application web d'exploration des tendances environnementales du Gabon (température, précipitations, surfaces brûlées),
de l'échelle nationale aux neuf provinces. Projet issu du cahier des charges v3.0 et de la direction artistique v2.0
(anciennement « MineSafe »), pour le NASA Space Apps Challenge *Be An Earth System Trend Detective!*.

## Démarrer (jeu de démonstration)

```bash
pip install -r requirements.txt
python scripts/build_demo_data.py          # géométries schématiques + séries SYNTHÉTIQUES
python scripts/trend_analysis.py --source demo
python scripts/export_results.py --source demo
```
Puis ouvrir `frontend/index.html` dans un navigateur (aucun serveur ni connexion requis ; seules les tuiles du fond
de carte demandent internet). Une bannière rappelle en permanence que les données sont de démonstration.

## Passer aux données réelles

```bash
python scripts/fetch_boundaries.py         # limites officielles (geoBoundaries) → data/regions/
python scripts/fetch_power.py              # NASA POWER mensuel, une requête par cellule de grille → data/raw/nasa_power/
python scripts/preprocess.py               # agrégation région + conversion mm/jour → mm/mois → data/processed/
python scripts/trend_analysis.py --source real
python scripts/export_results.py --source real
```
La surface brûlée (MODIS MCD64A1, priorité 2) n'est pas téléchargée automatiquement : déposer des statistiques mensuelles
par région dans `data/raw/modis/burned_<region>.csv` (`date,burned_km2,valid_fraction`) ; voir `scripts/fetch_burned_area.py`.
Les zones locales (`local_areas.geojson`) restent à tracer et à valider.

## Organisation

| Dossier | Rôle |
|---|---|
| `scripts/` | collecte, prétraitement, agrégation spatiale, moteur statistique, export |
| `data/` | `raw/`, `processed/`, `regions/` (GeoJSON), `demo/` |
| `results/` | séries CSV et `trends/trends.json` (paramètres statistiques conservés) |
| `frontend/` | HTML5, CSS3, JavaScript, Leaflet, Chart.js, Lucide (embarqués dans `vendor/`) |
| `tests/` | moteur statistique sur séries synthétiques à tendance connue (`pytest`) |

## Méthodes en bref

Mann-Kendall **saisonnier** (comparaison mois par mois) + pente de Sen saisonnière avec IC 95 %, variance corrigée de
l'autocorrélation d'ordre 1 (approximation), seuil 5 %, périodes d'au moins 10 années entières. L'interface n'affiche
que des résultats calculés par le pipeline ; elle ne recalcule rien. Limites : significativité ≠ importance
environnementale, p > 0,05 ≠ absence de changement, tests multiples non corrigés, résolution ≈ 55 × 70 km pour
T2M/PRECTOTCORR.
