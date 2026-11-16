"""Collecte NASA POWER (API temporelle mensuelle, point) pour chaque cellule de grille couvrant les régions.
Usage : python scripts/fetch_power.py [--start 2001 --end 2025]
Sortie : data/raw/nasa_power/cell_<lat>_<lon>.json (paramètres, coordonnées, période, unités, date de récupération)."""
import argparse, json, pathlib, time, datetime as dt
import requests
from spatial_analysis import load_regions, cells_for_geometry

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "nasa_power"
URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
PARAMS = "T2M,PRECTOTCORR"


def fetch_cell(lat, lon, start, end):
    q = {"parameters": PARAMS, "community": "AG", "latitude": lat, "longitude": lon,
         "start": start, "end": end, "format": "JSON"}
    for attempt in range(4):
        try:
            r = requests.get(URL, params=q, timeout=90)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            print(f"  essai {attempt + 1} échoué : {e}")
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"NASA POWER indisponible pour {lat},{lon}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2001)
    ap.add_argument("--end", type=int, default=2025)
    a = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    cells = set()
    for f in load_regions(ROOT / "data" / "regions").values():
        c, _ = cells_for_geometry(f["geometry"])
        cells.update(c)
    print(f"{len(cells)} cellules à récupérer")
    for lat, lon in sorted(cells):
        out = RAW / f"cell_{lat}_{lon}.json"
        if out.exists():
            continue
        data = fetch_cell(lat, lon, a.start, a.end)
        data["_ecoshield"] = {"latitude": lat, "longitude": lon, "start": a.start, "end": a.end,
                              "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                              "parameters": PARAMS}
        out.write_text(json.dumps(data), encoding="utf-8")
        print("ok", lat, lon)
        time.sleep(1.0)  # politesse envers l'API


if __name__ == "__main__":
    main()
