"""Tendances des séries Giovanni. Usage : python scripts/trend_giovanni.py   (après giovanni.py)
Analyse principale : Mann-Kendall saisonnier + pente de Sen (mois par mois) sur la période réellement couverte.
Sensibilité : Mann-Kendall + Sen sur moyennes (ou cumuls) annuels des années complètes uniquement.
Famille de tests pour Benjamini-Hochberg : les 3 variables × (analyse saisonnière), puis les 3 × (analyse annuelle), corrigées séparément.
Sortie : results/giovanni/trends.json"""
import json, pathlib
import numpy as np, pandas as pd
from stats_engine import analyze, bh_adjust, mk_sen_annual

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed" / "giovanni"
ALPHA = 0.05


def label(sig, slope):
    if not sig:
        return "Tendance non significative au seuil retenu (absence de preuve statistique, pas preuve d'absence de tendance)"
    return "Tendance croissante statistiquement significative" if slope > 0 else "Tendance décroissante statistiquement significative"


def main():
    meta = {m["code"]: m for m in json.loads((PROC / "metadata.json").read_text(encoding="utf-8"))["series"]}
    res, seas_p, ann_p = {}, [], []
    for code, m in meta.items():
        df = pd.read_csv(PROC / f"{code}.csv", parse_dates=["date"])
        y, mo, v = df.date.dt.year.values, df.date.dt.month.values, df.value.values
        r = analyze(y, mo, v, ALPHA, 10, 8)
        full = m["annees_completes"]
        ann = df[df.date.dt.year.isin(full)].groupby(df.date.dt.year)["value"].agg(["mean", "sum"])
        annual_vals = ann["sum"] if code == "PRECIP" else ann["mean"]
        a = mk_sen_annual(annual_vals.index.values, annual_vals.values, ALPHA)
        res[code] = {"variable": m["variable"], "unite": m["unite"], "periode": m["periode_analysee"], "saisonnier": r, "annuel": a,
                     "serie_annuelle": {"statistique": "cumul annuel (mm/an)" if code == "PRECIP" else "moyenne annuelle",
                                        "annees": [int(i) for i in annual_vals.index], "valeurs": [round(float(x), 4) for x in annual_vals.values]},
                     "unite_pente_saisonnier": m["unite_pente"], "unite_pente_annuel": "mm/an par an (mm/an²)" if code == "PRECIP" else m["unite_pente"]}
        seas_p.append((code, r.get("p_value", np.nan))); ann_p.append((code, a.get("p_value", np.nan)))
    for fam, key in ((seas_p, "saisonnier"), (ann_p, "annuel")):
        adj = bh_adjust([p for _, p in fam])
        for (code, p), q in zip(fam, adj):
            r = res[code][key]
            if r["status"] == "ok":
                r["p_value_ajustee_BH"] = float(q); r["significatif_apres_BH"] = bool(q < ALPHA)
                r["conclusion"] = label(q < ALPHA, r["sen_slope"])
    out = {"parametres": {"alpha": ALPHA, "correction": "Benjamini-Hochberg",
                          "famille": "3 variables (une zone) ; analyse saisonnière et analyse annuelle corrigées séparément (famille de 3 tests chacune)",
                          "autocorrelation": "Facteur de variance (1+r1)/(1−r1), appliqué si r1 > 1,96/√n, plafonné à 10 : approximation (Yue & Wang 2004), pas une correction exacte",
                          "zone": "Boîtes englobantes Giovanni (région de Libreville) ; aucune extrapolation aux provinces"}, "resultats": res}
    (ROOT / "results" / "giovanni").mkdir(parents=True, exist_ok=True)
    (ROOT / "results" / "giovanni" / "trends.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for c, r in res.items():
        for k in ("saisonnier", "annuel"):
            x = r[k]
            if x["status"] != "ok": print(c, k, x); continue
            print(f"{c:6s} {k:10s} n={x['n_obs']:3d} pente={x['sen_slope']:+.4f} IC95=[{x['ci_low']:+.4f},{x['ci_high']:+.4f}] p={x['p_value']:.4f} p_BH={x['p_value_ajustee_BH']:.4f}"
                  + (f" r1={x['autocorr_r1']:.2f} infl={x['variance_inflation']:.2f}" if 'autocorr_r1' in x else "") + f" -> {x['conclusion']}")


if __name__ == "__main__":
    main()
