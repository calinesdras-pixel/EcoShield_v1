import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "precipitation_gabon.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

features = data["features"]

print("\n========== INFORMATIONS GÉNÉRALES ==========")
print("Nombre de points :", len(features))

print("\n========== MÉTADONNÉES ==========")
print(json.dumps(data.get("properties", {}), indent=2))

print("\n========== PREMIER POINT ==========")
print(json.dumps(features[0], indent=2))

print("\n========== DERNIER POINT ==========")
print(json.dumps(features[-1], indent=2))

print("\n========== COUVERTURE GÉOGRAPHIQUE ==========")

longitudes = [f["geometry"]["coordinates"][0] for f in features]
latitudes = [f["geometry"]["coordinates"][1] for f in features]

print("Longitude minimale :", min(longitudes))
print("Longitude maximale :", max(longitudes))
print("Latitude minimale :", min(latitudes))
print("Latitude maximale :", max(latitudes))

print("\n========== STRUCTURE TEMPORELLE ==========")

values = features[0]["properties"]["parameter"]["PRECTOTCORR"]

dates = [date for date in values if date[-2:] != "13"]

print("Première date :", min(dates))
print("Dernière date :", max(dates))
print("Nombre de mois :", len(dates))