import json
import csv
from pathlib import Path
from shapely.geometry import shape, Point

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data/raw/precipitation_gabon.json"
GEOJSON_FILE = PROJECT_ROOT / "data/regions/gabon.geojson"
OUTPUT_FILE = PROJECT_ROOT / "data/processed/precipitation_gabon.csv"

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Charger les données
with open(INPUT_FILE, encoding="utf-8") as f:
    data = json.load(f)

# Charger les frontières du Gabon
with open(GEOJSON_FILE, encoding="utf-8") as f:
    gabon_data = json.load(f)

gabon_polygon = shape(gabon_data["features"][0]["geometry"])

selected_points = []
excluded_points = []

# Examiner chaque point
for feature in data["features"]:

    coordinates = feature["geometry"]["coordinates"]
    longitude, latitude = coordinates[:2]

    point = Point(longitude, latitude)

    if gabon_polygon.covers(point):
        selected_points.append(feature)
    else:
        excluded_points.append(feature)

# Exporter les observations
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:

    writer = csv.writer(f)

    writer.writerow([
        "longitude",
        "latitude",
        "date",
        "precipitation"
    ])

    for feature in selected_points:

        longitude, latitude = feature["geometry"]["coordinates"][:2]

        values = feature["properties"]["parameter"]["PRECTOTCORR"]

        for date, value in values.items():

            # Exclure les valeurs annuelles YYYY13
            if date.endswith("13"):
                continue

            writer.writerow([
                longitude,
                latitude,
                date,
                value
            ])

print("\n========== FILTRAGE SPATIAL ==========")
print("Points initiaux :", len(data["features"]))
print("Points conservés :", len(selected_points))
print("Points exclus :", len(excluded_points))
print("Observations exportées :", len(selected_points) * 300)
print("Fichier :", OUTPUT_FILE)

print("\n========== TERMINÉ ==========")