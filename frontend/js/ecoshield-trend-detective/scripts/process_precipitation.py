import json

with open("data/raw/precipitation_gabon.json") as f:
    data = json.load(f)

print("Nombre de points :", len(data["features"]))

print("Premier point :", data["features"][0]["geometry"]["coordinates"])

print("Dernier point :", data["features"][-1]["geometry"]["coordinates"])