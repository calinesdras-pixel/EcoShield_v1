"""Lecture, contrôle qualité et traitement des CSV Giovanni (source climatique unique d'EcoShield v2).
Usage : python scripts/giovanni.py
Entrées : data/raw/giovanni/*.csv (jamais modifiés)
Sorties : data/processed/giovanni/<code>.csv, data/processed/giovanni/metadata.json, data/processed/giovanni/rapport_traitement.md"""
from __future__ import annotations
import calendar, hashlib, json, pathlib, re
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "giovanni"
PROC = ROOT / "data" / "processed" / "giovanni"

# Unités brutes lues dans les produits Giovanni ; conversions documentées.
VARIABLES = {
    "TAIR": dict(file="resultat_temperature_air.csv", name="Température de l'air", unit_raw="K", unit="°C", trend_unit="°C/an",
                 product="GLDAS Noah 0,25° mensuel (Tair_f_inst)", spatial_resolution="0,25° (≈ 28 km)",
                 conversion="°C = K − 273,15", decimals=2),
    "PRECIP": dict(file="resultat_precipitation.csv", name="Précipitations", unit_raw="mm/h (taux moyen mensuel, unité confirmée par l'utilisateur)", unit="mm/mois",
                   trend_unit="mm/mois par an", product="GPM IMERG Final Run mensuel (précipitation)", spatial_resolution="0,1° (≈ 11 km)",
                   conversion="cumul mensuel (mm) = taux (mm/h) × 24 × nombre de jours du mois", decimals=1),
    "SOILM": dict(file="resultat_humiditer_sol.csv", name="Humidité du sol (0–10 cm)", unit_raw="kg/m²", unit="kg/m²",
                  trend_unit="kg/m² par an", product="GLDAS Noah 0,25° mensuel (SoilMoi0_10cm_inst)", spatial_resolution="0,25° (≈ 28 km)",
                  conversion="aucune", decimals=2),
}


def read_giovanni(path):
    """Retourne (en-tête dict, DataFrame[date, value_raw]). Ne suppose rien : l'en-tête est lu jusqu'à la ligne 'time,'."""
    lines = pathlib.Path(path).read_text(encoding="utf-8").splitlines()
    idx = next(i for i, l in enumerate(lines) if l.lower().startswith("time,"))
    head = {}
    for l in lines[:idx]:
        if ":," in l:
            k, v = l.split(":,", 1)
            head[k.strip()] = v.strip().strip('"')
    fill = next((float(v) for k, v in head.items() if k.startswith("Fill Value")), None)
    df = pd.read_csv(path, skiprows=idx, names=["date", "value_raw"], header=0, parse_dates=["date"])
    return {**head, "fill_value": fill}, df


def process(code, spec):
    head, df = read_giovanni(RAW / spec["file"])
    n_rows = len(df)
    dup = int(df["date"].duplicated().sum())
    df = df.drop_duplicates("date", keep="first").sort_values("date").reset_index(drop=True)
    raw = df["value_raw"].astype(float)
    invalid = raw.isna() | (raw <= (head["fill_value"] + 1 if head.get("fill_value") is not None else -np.inf))
    raw[invalid] = np.nan                                  # valeur de remplissage → manquant, JAMAIS zéro
    if code == "TAIR":
        val = raw - 273.15
    elif code == "PRECIP":
        days = df["date"].apply(lambda d: calendar.monthrange(d.year, d.month)[1])
        val = raw * 24 * days
    else:
        val = raw.copy()
    df["value"] = val
    expected = pd.date_range(df["date"].min(), df["date"].max(), freq="MS")
    missing_months = [d.strftime("%Y-%m") for d in expected if d not in set(df["date"])]
    # valeurs atypiques : signalées (écart à la médiane du mois > 5 MAD), jamais supprimées
    clim = df.groupby(df["date"].dt.month)["value"].transform("median")
    res = df["value"] - clim
    mad = np.nanmedian(np.abs(res - np.nanmedian(res))) * 1.4826
    flagged = df.loc[(np.abs(res) > 5 * mad) & (mad > 0), "date"].dt.strftime("%Y-%m").tolist()
    years_full = [int(y) for y, g in df.dropna(subset=["value"]).groupby(df["date"].dt.year) if len(g) == 12]
    meta = {
        "code": code, "source": "NASA Giovanni", "fichier_source": spec["file"],
        "sha256_source": hashlib.sha256((RAW / spec["file"]).read_bytes()).hexdigest(),
        "titre_giovanni": head.get("Title"), "produit": spec["product"], "variable": spec["name"],
        "unite_brute": spec["unit_raw"], "unite": spec["unit"], "unite_pente": spec["trend_unit"], "conversion": spec["conversion"],
        "boite_englobante_lon_lat": head.get("User Bounding Box"), "resolution_spatiale": spec["spatial_resolution"],
        "resolution_temporelle": "Mensuelle", "date_collecte": "non fournie dans le fichier",
        "periode_demandee": [head.get("User Start Date"), head.get("User End Date")],
        "periode_analysee": [df["date"].min().strftime("%Y-%m"), df["date"].max().strftime("%Y-%m")],
        "annees_completes": years_full, "n_lignes_fichier": n_rows, "n_doublons": dup,
        "n_attendues": len(expected), "n_valides": int(df["value"].notna().sum()), "n_manquantes": int(df["value"].isna().sum()) + len(missing_months),
        "mois_absents": missing_months, "valeurs_atypiques_signalees": flagged,
        "nettoyage": "Valeur de remplissage → manquant ; doublons de date supprimés (garde la première) ; aucune valeur extrême supprimée ; aucune interpolation.",
        "agregation": "Moyenne spatiale sur la boîte englobante, calculée par Giovanni (non recalculée ici) ; agrégation mensuelle fournie par le produit.",
        "url_reproduction": head.get("URL to Reproduce Results"),
    }
    out = df[["date", "value_raw", "value"]].copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out.to_csv(PROC / f"{code}.csv", index=False, float_format="%.6f")
    return meta


def main():
    PROC.mkdir(parents=True, exist_ok=True)
    metas = [process(c, s) for c, s in VARIABLES.items()]
    (PROC / "metadata.json").write_text(json.dumps({"source": "NASA Giovanni", "series": metas}, ensure_ascii=False, indent=1), encoding="utf-8")
    L = ["# Rapport de traitement Giovanni", ""]
    for m in metas:
        L += [f"## {m['variable']} ({m['code']})", f"- Fichier : `{m['fichier_source']}` — produit {m['produit']}",
              f"- Boîte (lon_min, lat_min, lon_max, lat_max) : {m['boite_englobante_lon_lat']}",
              f"- Période analysée : {m['periode_analysee'][0]} → {m['periode_analysee'][1]} (demandée : {m['periode_demandee'][0][:10]} → {m['periode_demandee'][1][:10]})",
              f"- Unité brute → traitée : {m['unite_brute']} → {m['unite']} ({m['conversion']})",
              f"- Observations : {m['n_valides']} valides / {m['n_attendues']} attendues ; {m['n_manquantes']} manquantes ; {m['n_doublons']} doublons",
              f"- Années complètes (12 mois) : {m['annees_completes'][0]}–{m['annees_completes'][-1]} ({len(m['annees_completes'])})",
              f"- Valeurs atypiques signalées (conservées) : {m['valeurs_atypiques_signalees'] or 'aucune'}", ""]
    (PROC / "rapport_traitement.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
