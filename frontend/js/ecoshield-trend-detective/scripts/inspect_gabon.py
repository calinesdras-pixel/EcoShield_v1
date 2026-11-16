import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GEOJSON_FILE = PROJECT_ROOT / "data" / "regions" / "gabon.geojson"

with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

feature = data["features"][0]
geometry = feature["geometry"]

def extract_coordinates(coords):
    points = []

    if isinstance(coords[0], (int, float)):
        points.append(coords)
    else:
        for item in coords:
            points.extend(extract_coordinates(item))

    return points

coordinates = extract_coordinates(geometry["coordinates"])

longitudes = [point[0] for point in coordinates]
latitudes = [point[1] for point in coordinates]

print("\n========== FRONTIÈRES DU GABON ==========")
print("Type :", geometry["type"])
print("Nombre de coordonnées :", len(coordinates))
print("Longitude minimale :", min(longitudes))
print("Longitude maximale :", max(longitudes))
print("Latitude minimale :", min(latitudes))
print("Latitude maximale :", max(latitudes))

print("\n========== VÉRIFICATION ==========")

if (
    8 <= min(longitudes) <= 10
    and 13 <= max(longitudes) <= 15
    and -5 <= min(latitudes) <= -3
    and 1 <= max(latitudes) <= 3
):
    print("Les coordonnées semblent compatibles avec le Gabon.")
else:
    print("ATTENTION : les coordonnées méritent une vérification.")

print("\n========== TERMINÉ ==========")