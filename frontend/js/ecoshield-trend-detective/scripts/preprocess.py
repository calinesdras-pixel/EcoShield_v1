"""Nettoyage, agrégation spatiale (cellules → région) et temporelle ; écriture des séries CSV + métadonnées (F03, §3.4).
Usage : python scripts/preprocess.py
Entrées : data/raw/nasa_power/*.json, data/raw/modis/burned_<region>.csv, data/regions/*.geojson
Sorties : data/processed/<VARIABLE>__<region>.csv (date,value ; vide = manquant) + data/processed/metadata.json"""
import calendar, csv, json, pathlib, datetime as dt
import numpy as np
from spatial_analysis import load_regions, cells_for_geometry

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config" / "config.json").read_text(encoding="utf-8"))
RAW, PROC = ROOT / "data" / "raw", ROOT / "data" / "processed"
FILL = -999.0


def month_keys(start, end):
    return [f"{y}{m:02d}" for y in range(start, end + 1) for m in range(1, 13)]


def cell_series(path, param, keys):
    d = json.loads(path.read_text(encoding="utf-8"))
    raw = d["properties"]["parameter"][param]
    vals = np.array([raw.get(k, FILL) for k in keys], dtype=float)
    vals[vals <= FILL + 1] = np.nan                       # valeur de remplissage → manquant (jamais zéro)
    if param == "PRECTOTCORR":                            # mm/jour (moyenne mensuelle) → mm/mois
        days = np.array([calendar.monthrange(int(k[:4]), int(k[4:]))[1] for k in keys])
        vals = vals * days
    return vals, d.get("_ecoshield", {})


def write_csv(var, rid, keys, vals):
    with open(PROC / f"{var}__{rid}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["date", "value"])
        for k, v in zip(keys, vals):
            w.writerow([f"{k[:4]}-{k[4:]}-01", "" if np.isnan(v) else f"{v:.4f}"])


def main():
    PROC.mkdir(parents=True, exist_ok=True)
    s, e = CFG["study_period"]["start_year"], CFG["study_period"]["end_year"]
    keys = month_keys(s, e)
    regions = load_regions(ROOT / "data" / "regions")
    meta, now = [], dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    for rid, feat in regions.items():
        cells, nearest = cells_for_geometry(feat["geometry"])
        for var in ("T2M", "PRECTOTCORR"):
            stack, retrieved = [], []
            for lat, lon in cells:
                p = RAW / "nasa_power" / f"cell_{lat}_{lon}.json"
                if p.exists():
                    v, m = cell_series(p, var, keys); stack.append(v); retrieved.append(m.get("retrieved_at"))
            if not stack:
                continue
            vals = np.nanmean(np.vstack(stack), axis=0) if len(stack) > 1 else stack[0]   # moyenne régionale (valeurs valides)
            write_csv(var, rid, keys, vals)
            meta.append(entry(var, rid, keys, vals, len(stack), nearest, max(filter(None, retrieved), default=now)))
        bp = RAW / "modis" / f"burned_{rid}.csv"
        if bp.exists():
            rows = list(csv.DictReader(open(bp, encoding="utf-8")))
            by = {r["date"][:7].replace("-", ""): r for r in rows}
            vals = np.array([float(by[k]["burned_km2"]) if k in by and by[k]["burned_km2"] != "" and float(by[k].get("valid_fraction", 1)) >= 0.8 else np.nan for k in keys])
            write_csv("BURNED_AREA", rid, keys, vals)
            meta.append(entry("BURNED_AREA", rid, keys, vals, 0, False, now))
    (PROC / "metadata.json").write_text(json.dumps({"demo": False, "series": meta}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(meta), "séries écrites dans", PROC)


def entry(var, rid, keys, vals, n_cells, nearest, retrieved):
    v = CFG["variables"][var]
    return {"variable": var, "region": rid, "source": v["source"], "product": v["product"], "unit": v["unit"],
            "temporal_resolution": v["temporal_resolution"], "spatial_resolution": v["spatial_resolution"],
            "period": [keys[0][:4] + "-" + keys[0][4:], keys[-1][:4] + "-" + keys[-1][4:]],
            "retrieved_at": retrieved, "aggregation": v["aggregation"], "n_cells": n_cells,
            "single_cell_fallback": bool(nearest), "n_months": len(vals), "n_missing": int(np.isnan(vals).sum()), "demo": False}


if __name__ == "__main__":
    main()
