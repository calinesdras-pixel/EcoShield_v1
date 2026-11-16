import csv
from pathlib import Path
import pymannkendall as mk

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data/processed/precipitation_nationale_annuelle.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data/processed/precipitation_trend_results.txt"
)

years = []
precipitations = []

with open(INPUT_FILE, "r", encoding="utf-8") as f:

    reader = csv.DictReader(f)

    for row in reader:
        if row["complete_year"].lower() == "true":
            years.append(int(row["year"]))
            precipitations.append(
                float(row["annual_precipitation_mm"])
            )

if len(precipitations) < 10:
    raise ValueError("Nombre d'années insuffisant pour l'analyse.")

if len(set(years)) != len(years):
    raise ValueError("Des années sont dupliquées.")

if years != list(range(years[0], years[-1] + 1)):
    raise ValueError("La série annuelle contient des années manquantes.")

# Test de Mann-Kendall
mk_result = mk.original_test(precipitations)

# Pente de Sen
sen_result = mk.sens_slope(precipitations)

# Interprétation
if mk_result.p < 0.05:
    significance = "Significative au seuil de 5 %"
else:
    significance = "Non significative au seuil de 5 %"

if mk_result.trend == "increasing":
    direction = "Croissante"
elif mk_result.trend == "decreasing":
    direction = "Décroissante"
else:
    direction = "Aucune tendance détectée"

report = f"""
========== ANALYSE DES TENDANCES : ECOSHIELD ==========

Période : {years[0]} - {years[-1]}
Nombre d'années : {len(years)}

========== MANN-KENDALL ==========

Tendance détectée : {direction}
Statistique S : {mk_result.s}
Tau de Kendall : {mk_result.Tau:.4f}
Valeur Z : {mk_result.z:.4f}
Valeur p : {mk_result.p:.6f}
Significativité : {significance}

========== PENTE DE SEN ==========

Pente annuelle : {sen_result.slope:.4f} mm/an
Pente décennale : {sen_result.slope * 10:.4f} mm/décennie
Ordonnée à l'origine : {sen_result.intercept:.4f}

========== CONCLUSION AUTOMATIQUE ==========

"""

if mk_result.p < 0.05:
    report += (
        f"Une tendance {direction.lower()} statistiquement "
        "significative a été détectée.\n"
    )
else:
    report += (
        "Aucune tendance monotone statistiquement significative "
        "n'a été détectée.\n"
    )

report += """
Attention : le test original de Mann-Kendall ne corrige pas
automatiquement l'autocorrélation temporelle.

Ces résultats doivent être interprétés avec les limites
spatiales et méthodologiques des données NASA POWER.

=======================================================
"""

print(report)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(report)

print("Rapport enregistré :", OUTPUT_FILE)