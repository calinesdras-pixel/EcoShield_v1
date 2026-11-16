# Rapport de traitement Giovanni

## Température de l'air (TAIR)
- Fichier : `resultat_temperature_air.csv` — produit GLDAS Noah 0,25° mensuel (Tair_f_inst)
- Boîte (lon_min, lat_min, lon_max, lat_max) : 9.4,0.25,9.8,0.6
- Période analysée : 2014-12 → 2026-07 (demandée : 2014-12-01 → 2026-11-30)
- Unité brute → traitée : K → °C (°C = K − 273,15)
- Observations : 140 valides / 140 attendues ; 0 manquantes ; 0 doublons
- Années complètes (12 mois) : 2015–2025 (11)
- Valeurs atypiques signalées (conservées) : aucune

## Précipitations (PRECIP)
- Fichier : `resultat_precipitation.csv` — produit GPM IMERG Final Run mensuel (précipitation)
- Boîte (lon_min, lat_min, lon_max, lat_max) : 9.3,-0.7,9.7,0.6
- Période analysée : 2014-12 → 2025-09 (demandée : 2014-12-01 → 2026-11-30)
- Unité brute → traitée : mm/h (taux moyen mensuel, unité confirmée par l'utilisateur) → mm/mois (cumul mensuel (mm) = taux (mm/h) × 24 × nombre de jours du mois)
- Observations : 130 valides / 130 attendues ; 0 manquantes ; 0 doublons
- Années complètes (12 mois) : 2015–2024 (10)
- Valeurs atypiques signalées (conservées) : ['2017-11']

## Humidité du sol (0–10 cm) (SOILM)
- Fichier : `resultat_humiditer_sol.csv` — produit GLDAS Noah 0,25° mensuel (SoilMoi0_10cm_inst)
- Boîte (lon_min, lat_min, lon_max, lat_max) : 9.3,-0.7,9.7,0.6
- Période analysée : 2014-12 → 2026-07 (demandée : 2014-12-01 → 2026-11-30)
- Unité brute → traitée : kg/m² → kg/m² (aucune)
- Observations : 140 valides / 140 attendues ; 0 manquantes ; 0 doublons
- Années complètes (12 mois) : 2015–2025 (11)
- Valeurs atypiques signalées (conservées) : aucune
