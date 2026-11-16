"""Assemble le paquet de données lu par l'interface : frontend/data/bundle.js (chargeable depuis file://, sans serveur).
Usage : python scripts/export_results.py --source demo|real"""
import argparse, csv, json, pathlib, datetime as dt

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config" / "config.json").read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--source", choices=["demo", "real"], default="demo")
    demo = ap.parse_args().source == "demo"
    src = ROOT / "data" / ("demo" if demo else "processed")
    meta = json.loads((src / "metadata.json").read_text(encoding="utf-8"))
    trends = json.loads((ROOT / "results" / "trends" / "trends.json").read_text(encoding="utf-8"))
    geo = {k: json.loads((ROOT / "data" / "regions" / f"{k}.geojson").read_text(encoding="utf-8")) for k in ("gabon", "provinces", "local_areas")}
    series = {}
    for s in meta["series"]:
        rows = list(csv.DictReader(open(src / f"{s['variable']}__{s['region']}.csv", encoding="utf-8")))
        series[f"{s['variable']}|{s['region']}"] = {"start": rows[0]["date"][:7], "v": [None if r["value"] == "" else round(float(r["value"]), 3) for r in rows]}
    regions = []
    for r in CFG["regions"]:
        coarse_local = r["level"] == "local"
        regions.append({**r, "reliable": {k: not (coarse_local and v["coarse"]) for k, v in CFG["variables"].items()}})
    bundle = {"meta": {"demo": demo, "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                       "period": [CFG["study_period"]["start_year"], CFG["study_period"]["end_year"]], "project": CFG["project"], "version": CFG["version"],
                       "geo_provenance": {k: g.get("provenance") for k, g in geo.items()}},
              "stats": CFG["stats"], "variables": CFG["variables"], "regions": regions, "geo": geo,
              "series_meta": {f"{s['variable']}|{s['region']}": s for s in meta["series"]}, "series": series, "trends": trends}
    out = ROOT / "frontend" / "data" / "bundle.js"
    out.write_text("window.ECOSHIELD_DATA = " + json.dumps(bundle, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print("écrit", out, f"({out.stat().st_size // 1024} Ko)")


if __name__ == "__main__":
    main()
