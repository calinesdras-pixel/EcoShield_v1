import csv
from pathlib import Path
import numpy as np
from scipy.stats import linregress

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data/processed/precipitation_nationale_annuelle.csv"
)

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

values = np.array(values, dtype=float)
years = np.array(years)

# Retirer la tendance linéaire
regression = linregress(years, values)
residuals = values - (
    regression.intercept + regression.slope * years
)

# Autocorrélation des résidus au retard 1
lag_1 = np.corrcoef(
    residuals[:-1],
    residuals[1:]
)[0, 1]

print("\n===== AUTOCORRÉLATION DES PRÉCIPITATIONS =====")
print("Nombre d'années :", len(values))
print("Autocorrélation lag 1 :", round(lag_1, 4))

print("\n===== INTERPRÉTATION INDICATIVE =====")

if lag_1 > 0:
    print("Autocorrélation positive.")
elif lag_1 < 0:
    print("Autocorrélation négative.")
else:
    print("Autocorrélation nulle.")

print(
    "\nAttention : cette valeur est un diagnostic descriptif, "
    "pas un test statistique de significativité."
)