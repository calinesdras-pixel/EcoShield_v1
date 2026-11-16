"""Génère le JEU DE DÉMONSTRATION d'EcoShield : géométries schématiques + séries mensuelles SYNTHÉTIQUES.

⚠ Rien ici n'est une mesure. Les géométries sont des polygones grossiers (hors échelle officielle) et les séries
sont simulées avec des tendances connues pour tester la chaîne. Tout est marqué "demo": true et l'interface affiche
une bannière permanente. Pour les vraies données : fetch_boundaries.py, fetch_power.py, preprocess.py.
Usage : python scripts/build_demo_data.py"""
import csv, json, pathlib, calendar, datetime as dt
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config" / "config.json").read_text(encoding="utf-8"))
REG = ROOT / "data" / "regions"
DEMO = ROOT / "data" / "demo"
START, END = CFG["study_period"]["start_year"], CFG["study_period"]["end_year"]
NOTE = "Géométrie schématique de démonstration — ne pas utiliser pour une analyse réelle."

# ── Polygones schématiques (lon, lat) ; sommets partagés pour que les provinces se jouxtent ─────────────────────
PROV = {
 "estuaire": [(9.6,1.0),(9.9,0.6),(11.0,0.55),(11.2,-0.2),(10.3,-0.5),(9.35,-0.15),(9.3,0.1),(9.45,0.4)],
 "woleu-ntem": [(9.6,1.0),(11.33,1.0),(11.33,2.3),(12.9,2.3),(12.3,0.9),(11.0,0.55),(9.9,0.6)],
 "ogooue-ivindo": [(12.9,2.3),(13.25,2.3),(13.9,1.9),(14.2,0.5),(13.9,-0.3),(12.4,-0.5),(11.2,-0.2),(11.0,0.55),(12.3,0.9)],
 "moyen-ogooue": [(10.3,-0.5),(11.2,-0.2),(11.4,-1.0),(10.6,-1.3),(10.0,-1.0),(9.9,-0.55)],
 "ogooue-maritime": [(9.35,-0.15),(10.3,-0.5),(9.9,-0.55),(10.0,-1.0),(10.6,-1.3),(10.6,-2.2),(10.3,-2.75),(10.0,-2.65),(9.2,-1.9),(8.7,-0.65)],
 "ogooue-lolo": [(11.2,-0.2),(12.4,-0.5),(13.9,-0.3),(13.8,-1.4),(13.0,-1.9),(12.2,-1.9),(12.0,-1.4),(11.4,-1.0)],
 "haut-ogooue": [(13.9,-0.3),(14.1,-1.2),(14.5,-2.3),(13.6,-2.35),(12.9,-2.9),(12.6,-2.5),(13.0,-1.9),(13.8,-1.4)],
 "ngounie": [(10.6,-1.3),(11.4,-1.0),(12.0,-1.4),(12.2,-1.9),(13.0,-1.9),(12.6,-2.5),(12.9,-2.9),(12.4,-2.9),(11.7,-2.95),(11.3,-2.5),(10.6,-2.2)],
 "nyanga": [(10.0,-2.65),(10.3,-2.75),(10.6,-2.2),(11.3,-2.5),(11.7,-2.95),(11.4,-3.7),(10.8,-3.95),(10.65,-3.43)],
}
OUTLINE = [(9.6,1.0),(11.33,1.0),(11.33,2.3),(13.25,2.3),(13.9,1.9),(14.2,0.5),(13.9,-0.3),(14.1,-1.2),(14.5,-2.3),(13.6,-2.35),
           (12.9,-2.9),(12.4,-2.9),(11.7,-2.95),(11.4,-3.7),(10.8,-3.95),(10.65,-3.43),(10.0,-2.65),(9.2,-1.9),(8.7,-0.65),
           (9.35,-0.15),(9.3,0.1),(9.45,0.4)]
RAIL = [(9.50,0.28),(10.77,-0.18),(11.93,-0.09),(12.72,-0.82),(13.20,-1.57),(13.58,-1.63)]  # Owendo → Franceville (approx.)


def ring(pts):
    pts = [list(p) for p in pts]
    return [pts + [pts[0]]]


def square(lon, lat, d):
    return [(lon-d, lat-d), (lon+d, lat-d), (lon+d, lat+d), (lon-d, lat+d)]


def corridor(line, w=0.1):
    up = [(x, y + w) for x, y in line]; dn = [(x, y - w) for x, y in reversed(line)]
    return up + dn


def fc(features, kind):
    return {"type": "FeatureCollection", "features": features,
            "provenance": {"source": "Polygones schématiques générés par build_demo_data.py", "crs": "EPSG:4326 (WGS 84)",
                           "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "demo": True, "note": NOTE, "kind": kind}}


def feat(rid, name, level, pts):
    return {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": ring(pts)},
            "properties": {"id": rid, "name": name, "level": level, "demo": True}}


# ── Séries synthétiques ──────────────────────────────────────────────────────────────────────────────────────
T_SEAS = np.array([0.4, 0.8, 0.9, 0.7, 0.3, -0.5, -1.3, -1.4, -0.6, -0.1, 0.0, 0.1])
P_SEAS = np.array([1.0, 1.15, 1.4, 1.5, 1.0, 0.2, 0.05, 0.1, 0.55, 1.6, 2.0, 1.2]); P_SEAS /= P_SEAS.mean()
B_SEAS = np.array([0.4, 0.2, 0.1, 0.1, 0.1, 0.8, 3.5, 4.0, 1.9, 0.4, 0.2, 0.4]); B_SEAS /= B_SEAS.mean()
#            T base, T trend/an, P moyen mm/mois, P trend, B moyen km²/mois, B trend
PARAMS = {
 "estuaire":        (26.0, 0.030, 190, -0.4,  6, 0.00),
 "haut-ogooue":     (24.5, 0.040, 150,  0.0, 55, 0.60),
 "moyen-ogooue":    (25.5, 0.025, 170, -0.8, 18, 0.10),
 "ngounie":         (25.0, 0.028, 165,  0.5, 35, 0.30),
 "nyanga":          (25.3, 0.020, 155,  0.0, 70, -0.50),
 "ogooue-ivindo":   (24.6, 0.035, 150, -1.2, 28, 0.00),
 "ogooue-lolo":     (24.8, 0.030, 140,  0.3, 40, 0.80),
 "ogooue-maritime": (26.0, 0.018, 200,  0.0, 90, -0.90),
 "woleu-ntem":      (24.7, 0.045, 160,  1.1, 22, 0.20),
}


def simulate(rng, p):
    tb, tt, pm, pt, bm, bt = p
    n = (END - START + 1) * 12
    yrs = np.repeat(np.arange(START, END + 1), 12); mon = np.tile(np.arange(1, 13), END - START + 1)
    t = yrs + (mon - 1) / 12; tc = t - t.mean()
    e = np.zeros(n)
    for i in range(1, n):
        e[i] = 0.5 * e[i - 1] + rng.normal(0, 0.32)
    T = tb + T_SEAS[mon - 1] + tt * tc + e
    P = np.clip(pm * P_SEAS[mon - 1] * (1 + pt / pm * tc), 0, None) * rng.gamma(6, 1 / 6, n)
    B = np.clip(bm * B_SEAS[mon - 1] * (1 + bt / bm * tc), 0, None) * rng.lognormal(0, 0.45, n)
    B[rng.random(n) < 0.02] = np.nan                      # quelques mois manquants (démonstration du signalement)
    return yrs, mon, T, P, B


def write(var, rid, yrs, mon, vals, meta, name_unit):
    v = CFG["variables"][var]
    with open(DEMO / f"{var}__{rid}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["date", "value"])
        for y, m, x in zip(yrs, mon, vals):
            w.writerow([f"{y}-{m:02d}-01", "" if np.isnan(x) else f"{x:.4f}"])
    meta.append({"variable": var, "region": rid, "source": "DONNÉES SYNTHÉTIQUES (démonstration) — simulation, non mesurée",
                 "product": "synthetic/" + v["product"], "unit": v["unit"], "temporal_resolution": v["temporal_resolution"],
                 "spatial_resolution": v["spatial_resolution"], "period": [f"{yrs[0]}-01", f"{yrs[-1]}-12"],
                 "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                 "aggregation": v["aggregation"], "n_cells": 0, "single_cell_fallback": False,
                 "n_months": int(len(vals)), "n_missing": int(np.isnan(vals).sum()), "demo": True})


def main():
    REG.mkdir(parents=True, exist_ok=True); DEMO.mkdir(parents=True, exist_ok=True)
    names = {r["id"]: r["name"] for r in CFG["regions"]}
    area = {r["id"]: r["area_km2_approx"] for r in CFG["regions"]}
    (REG / "provinces.geojson").write_text(json.dumps(fc([feat(k, names[k], "province", v) for k, v in PROV.items()], "provinces"), ensure_ascii=False))
    (REG / "gabon.geojson").write_text(json.dumps(fc([feat("gabon", names["gabon"], "national", OUTLINE)], "national"), ensure_ascii=False))
    (REG / "local_areas.geojson").write_text(json.dumps(fc([feat("moanda", names["moanda"], "local", square(13.20, -1.57, 0.12)),
                                                           feat("transgabonais", names["transgabonais"], "local", corridor(RAIL))], "local"), ensure_ascii=False))
    rng = np.random.default_rng(20260614)
    meta, sim = [], {}
    for rid, p in PARAMS.items():
        sim[rid] = simulate(rng, p)
    yrs, mon = sim["estuaire"][0], sim["estuaire"][1]
    tot = sum(area[r] for r in PARAMS)
    W = {r: area[r] / tot for r in PARAMS}
    for rid, (_, _, T, P, B) in sim.items():
        write("T2M", rid, yrs, mon, T, meta, ""); write("PRECTOTCORR", rid, yrs, mon, P, meta, ""); write("BURNED_AREA", rid, yrs, mon, B, meta, "")
    nat_T = sum(W[r] * sim[r][2] for r in PARAMS); nat_P = sum(W[r] * sim[r][3] for r in PARAMS)
    nat_B = np.nansum([sim[r][4] for r in PARAMS], axis=0)
    nat_B[np.all([np.isnan(sim[r][4]) for r in PARAMS], axis=0)] = np.nan
    write("T2M", "gabon", yrs, mon, nat_T, meta, ""); write("PRECTOTCORR", "gabon", yrs, mon, nat_P, meta, ""); write("BURNED_AREA", "gabon", yrs, mon, nat_B, meta, "")
    # zones locales : dérivées d'une province de référence + bruit local (sans prétendre à une précision locale)
    for rid, ref, ratio in (("moanda", "haut-ogooue", area["moanda"] / area["haut-ogooue"]), ("transgabonais", "ogooue-lolo", area["transgabonais"] / area["ogooue-lolo"])):
        r = np.random.default_rng(7 if rid == "moanda" else 11)
        _, _, T, P, B = sim[ref]
        write("T2M", rid, yrs, mon, T + r.normal(0, 0.15, len(T)), meta, "")
        write("PRECTOTCORR", rid, yrs, mon, np.clip(P * r.gamma(30, 1 / 30, len(P)), 0, None), meta, "")
        write("BURNED_AREA", rid, yrs, mon, B * ratio * r.lognormal(0, 0.3, len(B)), meta, "")
    (DEMO / "metadata.json").write_text(json.dumps({"demo": True, "series": meta}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(meta), "séries de démonstration + 3 fichiers GeoJSON (schématiques)")


if __name__ == "__main__":
    main()
