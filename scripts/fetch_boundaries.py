"""Télécharge les limites officielles (geoBoundaries gbOpen, ADM0 + ADM1 du Gabon) et les normalise.
Usage : python scripts/fetch_boundaries.py
Sortie : data/regions/gabon.geojson, provinces.geojson (+ fichier de provenance).
Les zones locales (local_areas.geojson) sont définies à la main : voir data/regions/README.md."""
import json, pathlib, sys, unicodedata, datetime as dt
import requests

OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "regions"
API = "https://www.geoboundary.org/api/current/gbOpen/GAB/{lvl}/"


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return s.replace("_", "-").replace(" ", "-").replace("'", "")


def grab(level):
    meta = requests.get(API.format(lvl=level), timeout=60).json()
    geo = requests.get(meta["simplifiedGeometryGeoJSON"], timeout=120).json()
    return meta, geo


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    m0, g0 = grab("ADM0")
    m1, g1 = grab("ADM1")
    stamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    prov = {"type": "FeatureCollection", "features": []}
    for f in g1["features"]:
        name = f["properties"]["shapeName"]
        pid = slug(name)
        prov["features"].append({"type": "Feature", "geometry": f["geometry"],
                                 "properties": {"id": pid, "name": name, "level": "province"}})
    if len(prov["features"]) != 9:
        sys.exit(f"Attendu 9 provinces, reçu {len(prov['features'])} : vérifier les noms et corriger config/config.json")
    nat = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": g0["features"][0]["geometry"],
           "properties": {"id": "gabon", "name": "Gabon (national)", "level": "national"}}]}
    prov["provenance"] = nat["provenance"] = {
        "source": "geoBoundaries gbOpen (simplified)", "boundary_id_adm0": m0.get("boundaryID"),
        "boundary_id_adm1": m1.get("boundaryID"), "license": m1.get("boundaryLicense"),
        "year": m1.get("boundaryYearRepresented"), "crs": "EPSG:4326 (WGS 84)", "retrieved_at": stamp, "demo": False}
    (OUT / "provinces.geojson").write_text(json.dumps(prov, ensure_ascii=False), encoding="utf-8")
    (OUT / "gabon.geojson").write_text(json.dumps(nat, ensure_ascii=False), encoding="utf-8")
    print("Limites enregistrées dans", OUT)


if __name__ == "__main__":
    main()
