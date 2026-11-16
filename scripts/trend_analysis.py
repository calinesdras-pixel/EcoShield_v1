"""Calcule les tendances de toutes les séries pour toutes les périodes (années entières, ≥ min_years).
Usage : python scripts/trend_analysis.py --source demo|real
Sortie : results/trends/trends.json (paramètres statistiques + résultats) et results/timeseries/*.csv (copie des séries)."""
import argparse, csv, json, pathlib, shutil, sys
import numpy as np
from stats_engine import analyze

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config" / "config.json").read_text(encoding="utf-8"))
FIELDS = ["sen_slope", "ci_low", "ci_high", "mk_z", "p_value", "total_change", "direction", "autocorr_r1", "n_obs"]


def load(path):
    y, m, v = [], [], []
    for r in csv.DictReader(open(path, encoding="utf-8")):
        y.append(int(r["date"][:4])); m.append(int(r["date"][5:7])); v.append(float(r["value"]) if r["value"] != "" else np.nan)
    return np.array(y), np.array(m), np.array(v)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--source", choices=["demo", "real"], default="demo")
    src = ROOT / "data" / ("demo" if ap.parse_args().source == "demo" else "processed")
    meta = json.loads((src / "metadata.json").read_text(encoding="utf-8"))
    st = CFG["stats"]; s0, s1 = CFG["study_period"]["start_year"], CFG["study_period"]["end_year"]
    out = {"demo": meta["demo"], "params": {"alpha": st["alpha"], "min_years": st["min_years"], "min_obs_per_month": st["min_obs_per_month"], "method": st["method"],
                                             "periods": "toutes les périodes d'années entières, longueur ≥ min_years"}, "fields": FIELDS, "data": {}}
    (ROOT / "results" / "timeseries").mkdir(parents=True, exist_ok=True)
    for s in meta["series"]:
        var, rid = s["variable"], s["region"]
        f = src / f"{var}__{rid}.csv"
        shutil.copy(f, ROOT / "results" / "timeseries" / f.name)
        Y, M, V = load(f)
        for a in range(s0, s1 + 1):
            for b in range(a + st["min_years"] - 1, s1 + 1):
                sel = (Y >= a) & (Y <= b)
                r = analyze(Y[sel], M[sel], V[sel], st["alpha"], st["min_years"], st["min_obs_per_month"])
                if r["status"] != "ok":
                    continue
                d = {"up": 1, "down": -1, "none": 0}[r["direction"]]
                out["data"][f"{var}|{rid}|{a}|{b}"] = [round(r["sen_slope"], 5), round(r["ci_low"], 5), round(r["ci_high"], 5), round(r["mk_z"], 3),
                                                         round(r["p_value"], 5), round(r["total_change"], 4), d, round(r["autocorr_r1"], 3), r["n_obs"]]
    (ROOT / "results" / "trends").mkdir(parents=True, exist_ok=True)
    (ROOT / "results" / "trends" / "trends.json").write_text(json.dumps(out), encoding="utf-8")
    print(len(out["data"]), "résultats de tendance")


if __name__ == "__main__":
    main()
