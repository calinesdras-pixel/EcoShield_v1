# Limites géographiques

- `gabon.geojson`, `provinces.geojson` : **fichiers de démonstration (polygones schématiques)** tant que
  `python scripts/fetch_boundaries.py` n'a pas été exécuté. Ce script les remplace par les limites geoBoundaries
  (ADM0/ADM1, WGS 84) avec leur provenance (identifiant, licence, date de récupération).
- `local_areas.geojson` : zones locales (Moanda, corridor du Transgabonais) définies à la main, à remplacer par des
  tracés vérifiés. Pour la température et les précipitations, ces zones sont plus petites qu'une cellule de grille
  (≈ 55 × 70 km) : l'interface les signale comme non interprétables localement.
- Chaque fichier porte un bloc `provenance` (source, CRS, date, `demo: true|false`).
