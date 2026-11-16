"""Outils spatiaux sans dépendance lourde : point-dans-polygone et sélection des cellules de grille NASA POWER."""
from __future__ import annotations
import json, pathlib

LAT_STEP, LON_STEP = 0.5, 0.625  # grille native MERRA-2 / POWER


def _ring_contains(ring, x, y):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def geometry_contains(geom, lon, lat):
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    for poly in polys:
        if _ring_contains(poly[0], lon, lat) and not any(_ring_contains(h, lon, lat) for h in poly[1:]):
            return True
    return False


def bounds(geom):
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    pts = [p for poly in polys for p in poly[0]]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def snap(lat, lon):
    return round(round(lat / LAT_STEP) * LAT_STEP, 3), round(round(lon / LON_STEP) * LON_STEP, 4)


def cells_for_geometry(geom):
    """Centres de cellules POWER dont le centre tombe dans la géométrie.
    Si aucune (zone plus petite qu'une cellule) : cellule contenant le centre de la zone, signalée comme telle."""
    x0, y0, x1, y1 = bounds(geom)
    cells = []
    lat = round(y0 / LAT_STEP) * LAT_STEP
    while lat <= y1 + LAT_STEP:
        lon = round(x0 / LON_STEP) * LON_STEP
        while lon <= x1 + LON_STEP:
            if geometry_contains(geom, lon, lat):
                cells.append(snap(lat, lon))
            lon += LON_STEP
        lat += LAT_STEP
    if cells:
        return cells, False
    return [snap((y0 + y1) / 2, (x0 + x1) / 2)], True


def load_regions(path_dir):
    """Retourne {region_id: feature} pour national, provinces et zones locales."""
    out = {}
    for fn in ("gabon.geojson", "provinces.geojson", "local_areas.geojson"):
        p = pathlib.Path(path_dir) / fn
        if p.exists():
            for f in json.loads(p.read_text(encoding="utf-8"))["features"]:
                out[f["properties"]["id"]] = f
    return out
