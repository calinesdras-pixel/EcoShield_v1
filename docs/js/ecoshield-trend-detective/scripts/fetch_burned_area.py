"""MODIS MCD64A1 (priorité 2 du MVP — à brancher après validation de la chaîne T2M/PRECTOTCORR).

Ce module contient la logique d'agrégation (pixels valides uniquement). Le téléchargement des tuiles exige
un compte NASA Earthdata : identifiants dans .env (jamais dans le frontend). Il n'est pas automatisé ici."""
import numpy as np

# Valeurs spéciales de BurnDate (MCD64A1) : -2 eau, -1 donnée insuffisante, 0 non brûlé, 1..366 jour de brûlage.
# À revérifier dans le guide utilisateur de la collection utilisée avant toute analyse réelle.
PIXEL_AREA_KM2 = (463.3127165 / 1000) ** 2  # pixel sinusoïdal MODIS ≈ 0,2146 km² (« 500 m » nominal)


def aggregate_burned_km2(burn_date: np.ndarray, region_mask: np.ndarray, min_valid_fraction=0.8):
    """Retourne (surface brûlée km², fraction de pixels valides). Surface = NaN si trop de pixels invalides.
    Les pixels invalides (-1) ne sont JAMAIS comptés comme non brûlés."""
    inside = region_mask & (burn_date != -2)            # on exclut l'eau
    if inside.sum() == 0:
        return float("nan"), 0.0
    valid = inside & (burn_date != -1)
    frac = valid.sum() / inside.sum()
    if frac < min_valid_fraction:
        return float("nan"), float(frac)
    burned = valid & (burn_date >= 1)
    return float(burned.sum() * PIXEL_AREA_KM2), float(frac)


def main():
    raise NotImplementedError(
        "Téléchargement MCD64A1 non automatisé : exporter les statistiques mensuelles par région (CSV : date,burned_km2,"
        "valid_fraction) dans data/raw/modis/burned_<region>.csv, puis lancer preprocess.py.")


if __name__ == "__main__":
    main()
