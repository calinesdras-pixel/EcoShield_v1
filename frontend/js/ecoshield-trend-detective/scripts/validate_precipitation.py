import json
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "precipitation_gabon.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

features = data["features"]

longitudes = sorted({
    feature["geometry"]["coordinates"][0]
    for feature in features
})

latitudes = sorted({
    feature["geometry"]["coordinates"][1]
    for feature in features
})

print("\n========== GRILLE GÉOGRAPHIQUE ==========")
print("Nombre de points :", len(features))
print("Longitudes distinctes :", len(longitudes))
print("Latitudes distinctes :", len(latitudes))
print("Longitudes :", longitudes)
print("Latitudes :", latitudes)

print("\n========== QUALITÉ DES DONNÉES ==========")

missing = 0
valid = 0
invalid = 0
all_values = []
month_counts = Counter()

for feature in features:

    values = feature["properties"]["parameter"]["PRECTOTCORR"]

    months = {
        date: value
        for date, value in values.items()
        if date[-2:] != "13"
    }

    month_counts[len(months)] += 1

    for date, value in months.items():

        if value is None:
            missing += 1

        elif value == -999:
            missing += 1

        elif value < 0:
            invalid += 1

        else:
            valid += 1
            all_values.append(value)

print("Observations valides :", valid)
print("Valeurs manquantes :", missing)
print("Valeurs négatives invalides :", invalid)

print("Nombre de mois par point :", dict(month_counts))

if all_values:
    print("Valeur minimale :", min(all_values))
    print("Valeur maximale :", max(all_values))
    print("Moyenne générale des valeurs :", sum(all_values) / len(all_values))

print("\n========== VÉRIFICATION TERMINÉE ==========")
