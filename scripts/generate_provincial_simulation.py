from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GEOJSON = ROOT / "data" / "regions" / "provinces.geojson"
OUT = ROOT / "data" / "demo"
SEED = 20261115

# Profils fictifs de démonstration.
# Ces paramètres ne sont PAS des normales climatiques observées.
PROFILES = {
    "estuaire":       {"temp": 26.2, "rain": 220, "soil": 24, "offset": 0.0},
    "woleu-ntem":     {"temp": 24.5, "rain": 190, "soil": 25, "offset": 0.2},
    "ogooue-ivindo":  {"temp": 25.0, "rain": 210, "soil": 27, "offset": 0.1},
    "moyen-ogooue":   {"temp": 26.0, "rain": 180, "soil": 23, "offset": 0.0},
    "ogooue-maritime":{"temp": 25.8, "rain": 200, "soil": 23, "offset": -0.2},
    "ogooue-lolo":    {"temp": 24.8, "rain": 185, "soil": 25, "offset": 0.1},
    "haut-ogooue":    {"temp": 25.5, "rain": 150, "soil": 20, "offset": 0.3},
    "ngounie":        {"temp": 25.6, "rain": 195, "soil": 25, "offset": 0.1},
    "nyanga":         {"temp": 26.0, "rain": 145, "soil": 19, "offset": 0.2},
}

# Facteurs saisonniers fictifs : saisonnalité simplifiée.
RAIN_SEASON = {
    1: 1.15, 2: 0.95, 3: 1.20, 4: 1.25,
    5: 0.95, 6: 0.55, 7: 0.30, 8: 0.25,
    9: 0.45, 10: 0.95, 11: 1.45, 12: 1.50
}

def main():
    rng = np.random.default_rng(SEED)

    geo = json.loads(GEOJSON.read_text(encoding="utf-8"))
    provinces = [
        f["properties"]
        for f in geo["features"]
    ]

    if len(provinces) != 9:
        raise ValueError(f"9 provinces attendues, {len(provinces)} trouvées.")

    dates = pd.date_range("2016-01-01", "2025-12-01", freq="MS")
    rows = []

    # Un épisode fictif commun, modulé par province.
    for province in provinces:
        pid = province["id"]
        name = province["name"]
        p = PROFILES[pid]

        previous_rain = p["rain"]

        for date in dates:
            month = date.month
            year = date.year

            # Variabilité fictive interannuelle et mensuelle.
            drought = rng.normal(0, 0.18)
            local_noise = rng.normal(0, 0.10)

            # Température simulée.
            seasonal_temp = 0.65 * np.cos(
                2 * np.pi * (month - 3) / 12
            )
            temperature = (
                p["temp"] + p["offset"] + seasonal_temp
                + 0.45 * max(0, -drought)
                + rng.normal(0, 0.35)
            )

            # Précipitations simulées.
            rain_factor = RAIN_SEASON[month]
            precipitation = (
                p["rain"] * rain_factor
                * np.exp(-drought + local_noise)
                * rng.lognormal(0, 0.12)
            )
            precipitation = max(0, precipitation)

            # Humidité du sol simulée, avec mémoire du mois précédent.
            soil = (
                0.68 * p["soil"]
                + 0.22 * previous_rain / max(p["rain"], 1)
                  * p["soil"]
                + 0.10 * precipitation / max(p["rain"], 1)
                  * p["soil"]
                + rng.normal(0, 1.2)
            )
            soil = max(1, soil)
            previous_rain = precipitation

            rows.append({
                "date": date,
                "province_id": pid,
                "province": name,
                "temperature_c": round(temperature, 3),
                "precipitation_mm": round(precipitation, 3),
                "humidite_sol_kg_m2": round(soil, 3),
                "source": "ECOSHIELD_SIMULATION",
                "statut_donnee": "SIMULATED",
            })

    df = pd.DataFrame(rows)

    # Anomalies mensuelles calculées par province.
    variables = {
        "temperature_c": "temperature",
        "precipitation_mm": "precipitation",
        "humidite_sol_kg_m2": "humidite_sol",
    }

    baseline = df[df["date"].dt.year <= 2024].copy()

    for column, prefix in variables.items():
        stats = (
            baseline.groupby(
                ["province_id", baseline["date"].dt.month]
            )[column]
            .agg(["mean", "std"])
        )
        stats.index.names = ["province_id", "month"]

        keys = pd.MultiIndex.from_arrays([
            df["province_id"],
            df["date"].dt.month
        ])

        means = stats["mean"].reindex(keys).to_numpy()
        stds = stats["std"].reindex(keys).to_numpy()

        df[f"{prefix}_anomalie"] = df[column].to_numpy() - means
        df[f"{prefix}_zscore"] = (
            df[f"{prefix}_anomalie"].to_numpy()
            / np.where(stds > 0, stds, np.nan)
        )

    rain_deficit = df["precipitation_zscore"] <= -1
    soil_deficit = df["humidite_sol_zscore"] <= -1
    heat = df["temperature_zscore"] >= 1

    df["niveau_signal"] = "AUCUN SIGNAL COMBINÉ"
    df.loc[rain_deficit | soil_deficit | heat,
           "niveau_signal"] = "SIGNAL ISOLÉ À SURVEILLER"
    df.loc[rain_deficit & soil_deficit,
           "niveau_signal"] = "DÉFICIT HYDRIQUE POTENTIEL"
    df.loc[rain_deficit & soil_deficit & heat,
           "niveau_signal"] = "SIGNAL HYDRIQUE RENFORCÉ"

    df["recommandation"] = (
        "Aucun signal combiné détecté selon les seuils exploratoires."
    )
    df.loc[rain_deficit | soil_deficit | heat,
           "recommandation"] = (
        "Surveiller les prochains relevés simulés."
    )
    df.loc[rain_deficit & soil_deficit,
           "recommandation"] = (
        "Suivre conjointement les déficits simulés de pluie et d'humidité."
    )
    df.loc[rain_deficit & soil_deficit & heat,
           "recommandation"] = (
        "Renforcer la surveillance dans ce scénario de démonstration."
    )

    OUT.mkdir(parents=True, exist_ok=True)

    csv_path = OUT / "provincial_climate_simulation.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    metadata = {
        "project": "EcoShield",
        "dataset": "Provincial climate simulation",
        "source": "ECOSHIELD_SIMULATION",
        "status": "SIMULATED",
        "seed": SEED,
        "period": ["2016-01", "2025-12"],
        "provinces": len(provinces),
        "records": len(df),
        "variables": list(variables.keys()),
        "reference_period": "2016-2024",
        "methodology": (
            "Synthetic values generated from illustrative provincial "
            "profiles, simplified seasonality and random variability."
        ),
        "warning": (
            "These values are fictional demonstration data. "
            "They are not satellite observations, measurements, "
            "forecasts or validated climate estimates."
        ),
    }

    meta_path = OUT / "simulation_metadata.json"
    meta_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\n===== ECOSHIELD : SIMULATION NATIONALE =====")
    print("Provinces :", df["province_id"].nunique())
    print("Observations :", len(df))
    print("Période :", df["date"].min(), "->", df["date"].max())
    print("\nRépartition des signaux :")
    print(df["niveau_signal"].value_counts().to_string())
    print("\nFichiers créés :")
    print(csv_path)
    print(meta_path)
    print("\nSTATUT : DONNÉES SYNTHÉTIQUES — NE PAS CONFONDRE AVEC DES OBSERVATIONS.")

if __name__ == "__main__":
    main()
