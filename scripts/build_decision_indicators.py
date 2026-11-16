from pathlib import Path
import pandas as pd
import json

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed" / "giovanni"
OUT = PROC / "decision_indicators.csv"

def load(code, column):
    df = pd.read_csv(PROC / f"{code}.csv", parse_dates=["date"])
    return df[["date", "value"]].rename(columns={"value": column})

# Chargement des trois séries Giovanni
df = (
    load("TAIR", "temperature_c")
    .merge(load("PRECIP", "precipitation_mm"), on="date")
    .merge(load("SOILM", "humidite_sol_kg_m2"), on="date")
)

# Période commune réellement disponible
df = df[
    (df["date"] >= "2016-01-01") &
    (df["date"] <= "2025-09-01")
].copy()

df["mois"] = df["date"].dt.month

# Référence exploratoire : neuf années complètes
reference = df[
    (df["date"] >= "2016-01-01") &
    (df["date"] <= "2024-12-01")
]

variables = {
    "temperature_c": "temperature",
    "precipitation_mm": "precipitation",
    "humidite_sol_kg_m2": "humidite_sol",
}

for column, prefix in variables.items():
    stats = reference.groupby(reference["date"].dt.month)[column].agg(
        moyenne="mean",
        ecart_type="std"
    )

    moyenne = df["mois"].map(stats["moyenne"])
    ecart_type = df["mois"].map(stats["ecart_type"])

    df[f"{prefix}_reference"] = moyenne
    df[f"{prefix}_anomalie"] = df[column] - moyenne
    df[f"{prefix}_zscore"] = (
        df[f"{prefix}_anomalie"] / ecart_type.where(ecart_type > 0)
    )

# Détection de signaux exploratoires
deficit_pluie = df["precipitation_zscore"] <= -1
deficit_sol = df["humidite_sol_zscore"] <= -1
chaleur = df["temperature_zscore"] >= 1

df["signal_deficit_hydrique"] = deficit_pluie & deficit_sol
df["signal_thermique"] = chaleur
df["signal_renforce"] = df["signal_deficit_hydrique"] & chaleur

def classify(row):
    if row["signal_renforce"]:
        return "SIGNAL HYDRIQUE RENFORCÉ"
    if row["signal_deficit_hydrique"]:
        return "DÉFICIT HYDRIQUE POTENTIEL"
    if row["signal_thermique"] or (
        row["precipitation_zscore"] <= -1
    ) or (
        row["humidite_sol_zscore"] <= -1
    ):
        return "SIGNAL ISOLÉ À SURVEILLER"
    return "AUCUN SIGNAL COMBINÉ"

def recommendation(row):
    if row["signal_renforce"]:
        return (
            "Renforcer la surveillance locale : déficit de précipitations "
            "et d'humidité du sol accompagné d'une anomalie thermique positive."
        )
    if row["signal_deficit_hydrique"]:
        return (
            "Suivre l'évolution de la disponibilité en eau : "
            "précipitations et humidité du sol sous leurs références mensuelles."
        )
    if row["niveau_signal"] == "SIGNAL ISOLÉ À SURVEILLER":
        return (
            "Surveiller les prochains relevés et vérifier si l'anomalie "
            "se confirme."
        )
    return "Aucun signal combiné détecté selon les seuils exploratoires retenus."

df["niveau_signal"] = df.apply(classify, axis=1)
df["recommandation"] = df.apply(recommendation, axis=1)

# Export des indicateurs
df.to_csv(OUT, index=False, encoding="utf-8-sig")

# Résumé synthétique
latest = df.iloc[-1]
summary = {
    "periode_analysee": [
        str(df["date"].min().date()),
        str(df["date"].max().date())
    ],
    "periode_reference": "2016-2024",
    "nombre_mois": int(len(df)),
    "dernier_releve": str(latest["date"].date()),
    "dernier_niveau_signal": latest["niveau_signal"],
    "derniere_recommandation": latest["recommandation"],
    "nombre_mois_par_signal": {
        str(k): int(v)
        for k, v in df["niveau_signal"].value_counts().items()
    },
    "limite": (
        "Indicateurs exploratoires, non validés comme alertes opérationnelles. "
        "Données Giovanni localisées autour de Libreville."
    )
}

summary_path = ROOT / "results" / "giovanni" / "decision_summary.json"
summary_path.parent.mkdir(parents=True, exist_ok=True)
summary_path.write_text(
    json.dumps(summary, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("\n========== ECOSHIELD : INDICATEURS DÉCISIONNELS ==========")
print("Mois analysés :", len(df))
print("Période :", summary["periode_analysee"])
print("Référence : 2016-2024")
print("\nRépartition des signaux :")
for signal, count in summary["nombre_mois_par_signal"].items():
    print(f"- {signal} : {count} mois")

print("\nDernier relevé :", summary["dernier_releve"])
print("Signal :", summary["dernier_niveau_signal"])
print("Recommandation :", summary["derniere_recommandation"])
print("\nFichiers générés :")
print(OUT)
print(summary_path)
