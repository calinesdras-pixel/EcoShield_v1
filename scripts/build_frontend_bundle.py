import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def read_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def number(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

# Métadonnées et résultats scientifiques
metadata = read_json(ROOT / "data/processed/giovanni/metadata.json")
trends = read_json(ROOT / "results/giovanni/trends.json")
decision_summary = read_json(ROOT / "results/giovanni/decision_summary.json")

scientific_series = {}

for code in ["TAIR", "PRECIP", "SOILM"]:
    rows = read_csv(ROOT / f"data/processed/giovanni/{code}.csv")
    scientific_series[code] = [
        {
            "date": row["date"],
            "value": number(row["value"])
        }
        for row in rows
    ]

indicators = read_csv(
    ROOT / "data/processed/giovanni/decision_indicators.csv"
)

indicator_rows = []
for row in indicators:
    item = {}
    for key, value in row.items():
        if key in ["date", "niveau_signal", "recommandation"]:
            item[key] = value
        elif key in [
            "signal_deficit_hydrique",
            "signal_thermique",
            "signal_renforce"
        ]:
            item[key] = value.lower() == "true"
        else:
            item[key] = number(value)
    indicator_rows.append(item)

# Simulation provinciale
simulation_metadata = read_json(
    ROOT / "data/demo/simulation_metadata.json"
)

simulation_rows = read_csv(
    ROOT / "data/demo/provincial_climate_simulation.csv"
)

simulation = []
for row in simulation_rows:
    item = {}
    for key, value in row.items():
        if key in [
            "date", "province_id", "province", "source",
            "statut_donnee", "niveau_signal", "recommandation"
        ]:
            item[key] = value
        else:
            item[key] = number(value)
    simulation.append(item)

provinces = sorted(set(row["province"] for row in simulation))

bundle = {
    "meta": metadata,
    "trends": trends,
    "decision_summary": decision_summary,
    "series": scientific_series,
    "indicators": indicator_rows,
    "simulation": {
        "meta": simulation_metadata,
        "provinces": provinces,
        "records": simulation
    }
}

output = ROOT / "frontend/data/bundle.js"
output.parent.mkdir(parents=True, exist_ok=True)

payload = json.dumps(bundle, ensure_ascii=False, separators=(",", ":"))
output.write_text(
    "window.ECOSHIELD_DATA = " + payload + ";",
    encoding="utf-8"
)

print("Bundle frontend généré :", output)
print("Séries Giovanni :", {
    key: len(value) for key, value in scientific_series.items()
})
print("Indicateurs :", len(indicator_rows))
print("Observations simulées :", len(simulation))
print("Provinces :", ", ".join(provinces))
print("Taille :", round(output.stat().st_size / 1024), "Ko")
