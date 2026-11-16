import csv
import math
from pathlib import Path

import pymannkendall as mk


# =====================================================
# 1. CONFIGURATION
# =====================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data/processed/precipitation_nationale_annuelle.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data/processed/precipitation_trend_validation.txt"
)

ALPHA = 0.05


# =====================================================
# 2. CHARGEMENT ET VALIDATION DES DONNÉES
# =====================================================

years = []
values = []

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        if row["complete_year"].lower() == "true":
            years.append(int(row["year"]))
            values.append(
                float(row["annual_precipitation_mm"])
            )

if len(values) < 10:
    raise ValueError("Série temporelle trop courte.")

if len(years) != len(set(years)):
    raise ValueError("Années dupliquées détectées.")

if any(
    years[i] >= years[i + 1]
    for i in range(len(years) - 1)
):
    raise ValueError("Les années doivent être chronologiques.")

if any(
    years[i + 1] - years[i] != 1
    for i in range(len(years) - 1)
):
    raise ValueError("Des années consécutives sont manquantes.")


# =====================================================
# 3. TESTS DE MANN-KENDALL
# =====================================================

original = mk.original_test(values)

hamed_rao = mk.hamed_rao_modification_test(values)

yue_wang = mk.yue_wang_modification_test(values)

sen = mk.sens_slope(values)


# =====================================================
# 4. AUTOCORRÉLATION DES RÉSIDUS
# =====================================================

# Retrait d'une tendance linéaire par moindres carrés.
n = len(values)

mean_year = sum(years) / n
mean_value = sum(values) / n

numerator = sum(
    (years[i] - mean_year) * (values[i] - mean_value)
    for i in range(n)
)

denominator = sum(
    (years[i] - mean_year) ** 2
    for i in range(n)
)

linear_slope = numerator / denominator

linear_intercept = mean_value - linear_slope * mean_year

residuals = [
    values[i] - (
        linear_intercept + linear_slope * years[i]
    )
    for i in range(n)
]


def autocorrelation(data, lag):
    """Calcule l'autocorrélation empirique à un retard donné."""

    mean = sum(data) / len(data)

    numerator = sum(
        (data[i] - mean) * (data[i - lag] - mean)
        for i in range(lag, len(data))
    )

    denominator = sum(
        (x - mean) ** 2
        for x in data
    )

    if denominator == 0:
        return float("nan")

    return numerator / denominator


autocorrelations = {}

for lag in range(1, min(6, n)):
    autocorrelations[lag] = autocorrelation(
        residuals,
        lag
    )

# Seuil indicatif de bruit blanc.
# Ce seuil n'est pas un test formel de significativité.
acf_limit = 1.96 / math.sqrt(n)


# =====================================================
# 5. CONSTRUCTION DU RAPPORT
# =====================================================

report = f"""
=====================================================
       VALIDATION SCIENTIFIQUE - ECOSHIELD
=====================================================

PÉRIODE ANALYSÉE
----------------

Début : {years[0]}
Fin : {years[-1]}
Nombre d'années : {n}

Variable : Précipitations annuelles estimées
Unité : mm/an
Source : NASA POWER - PRECTOTCORR


=====================================================
1. MANN-KENDALL ORIGINAL
=====================================================

Tendance : {original.trend}
Statistique S : {original.s}
Tau : {original.Tau:.4f}
Z : {original.z:.4f}
p-value : {original.p:.6f}

Significatif à 5 % : {original.p < ALPHA}


=====================================================
2. MANN-KENDALL HAMED-RAO
=====================================================

Tendance : {hamed_rao.trend}
Statistique S : {hamed_rao.s}
Tau : {hamed_rao.Tau:.4f}
Z : {hamed_rao.z:.4f}
p-value : {hamed_rao.p:.6f}

Significatif à 5 % : {hamed_rao.p < ALPHA}


=====================================================
3. MANN-KENDALL YUE-WANG
=====================================================

Tendance : {yue_wang.trend}
Statistique S : {yue_wang.s}
Tau : {yue_wang.Tau:.4f}
Z : {yue_wang.z:.4f}
p-value : {yue_wang.p:.6f}

Significatif à 5 % : {yue_wang.p < ALPHA}


=====================================================
4. ESTIMATION DE LA PENTE DE SEN
=====================================================

Pente annuelle : {sen.slope:.4f} mm/an

Pente décennale : {sen.slope * 10:.4f} mm/décennie

Ordonnée à l'origine : {sen.intercept:.4f}


=====================================================
5. AUTOCORRÉLATION DES RÉSIDUS
=====================================================

Tendance linéaire retirée avant le calcul.

Limite indicative : +/- {acf_limit:.4f}

"""

for lag, acf in autocorrelations.items():
    report += (
        f"Retard {lag} : {acf:.4f}\n"
    )

report += """

Attention :
Les limites indiquées sont des repères approximatifs.
Elles ne remplacent pas un test formel d'autocorrélation.


=====================================================
6. COMPARAISON DES MÉTHODES
=====================================================

Mann-Kendall original :
{}

Hamed-Rao :
{}

Yue-Wang :
{}

=====================================================
7. LIMITES MÉTHODOLOGIQUES
=====================================================

- Série limitée à 25 observations annuelles.
- Données NASA POWER dérivées de produits de réanalyse.
- Agrégation spatiale fondée sur les centres des cellules
  situées à l'intérieur du polygone du Gabon.
- Absence de pondération par intersection exacte des cellules
  avec les frontières nationales.
- Les méthodes statistiques partagent la même série
  et ne constituent pas des validations indépendantes.
- Une tendance décroissante ne démontre pas une causalité
  liée au changement climatique.
- Une diminution des précipitations annuelles ne signifie
  pas nécessairement une diminution uniforme dans toutes
  les régions du Gabon.

=====================================================
""".format(
    original.p < ALPHA,
    hamed_rao.p < ALPHA,
    yue_wang.p < ALPHA
)


# =====================================================
# 6. AFFICHAGE ET EXPORT
# =====================================================

print(report)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(report)

print("Rapport enregistré :", OUTPUT_FILE)