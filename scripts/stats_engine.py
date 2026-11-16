"""Moteur statistique EcoShield (F04).

Mann-Kendall saisonnier + pente de Sen saisonnière sur séries mensuelles.
- Les comparaisons sont faites mois par mois (tous les « janvier » entre eux, etc.),
  ce qui neutralise la saisonnalité.
- Autocorrélation : la variance de S est multipliée par n/n* = (1+r1)/(1-r1)
  lorsque l'autocorrélation d'ordre 1 des résidus désaisonnalisés est positive et
  significative (taille d'échantillon effective, Yue & Wang 2004). Approximation documentée.
- Séries insuffisantes : statut "insufficient", aucun résultat chiffré inventé.
"""
from __future__ import annotations
import numpy as np
from scipy.stats import norm

DEFAULTS = {"alpha": 0.05, "min_years": 10, "min_obs_per_month": 8}


def _decimal_year(years, months):
    return years + (months - 1) / 12.0


def _lag1(resid: np.ndarray) -> float:
    x = resid[~np.isnan(resid)]
    if len(x) < 24:
        return 0.0
    x = x - x.mean()
    den = float((x ** 2).sum())
    return float((x[:-1] * x[1:]).sum() / den) if den > 0 else 0.0


def analyze(years, months, values, alpha=0.05, min_years=10, min_obs_per_month=8) -> dict:
    years = np.asarray(years, dtype=int)
    months = np.asarray(months, dtype=int)
    values = np.asarray(values, dtype=float)
    ok = ~np.isnan(values)
    n_obs = int(ok.sum())
    span_years = (years.max() - years.min() + 1) if len(years) else 0
    if n_obs == 0 or span_years < min_years:
        return {"status": "insufficient", "n_obs": n_obs, "reason": f"période < {min_years} ans ou aucune donnée"}

    S, V, slopes, seasons = 0.0, 0.0, [], 0
    for m in range(1, 13):
        sel = (months == m) & ok
        y, x = years[sel], values[sel]
        n = len(x)
        if n < min_obs_per_month:
            continue
        seasons += 1
        iu = np.triu_indices(n, 1)
        d = (x[None, :] - x[:, None])[iu]
        t = (y[None, :] - y[:, None])[iu]
        S += float(np.sign(d).sum())
        slopes.append(d / t)
        _, cnt = np.unique(x, return_counts=True)
        ties = sum(c * (c - 1) * (2 * c + 5) for c in cnt if c > 1)
        V += (n * (n - 1) * (2 * n + 5) - ties) / 18.0
    if seasons < 6 or V <= 0:
        return {"status": "insufficient", "n_obs": n_obs, "reason": "trop peu de mois exploitables"}

    slopes = np.concatenate(slopes)
    sen = float(np.median(slopes))

    # résidus désaisonnalisés et détendancés → autocorrélation d'ordre 1
    tdec = _decimal_year(years, months)
    month_med = {m: np.nanmedian(values[(months == m) & ok]) for m in range(1, 13) if ((months == m) & ok).any()}
    deseas = np.array([v - month_med.get(m, np.nan) for v, m in zip(values, months)])
    resid = deseas - sen * (tdec - np.nanmean(tdec[ok]))
    r1 = _lag1(resid)
    n_eff_ratio = 1.0
    if r1 > 1.96 / np.sqrt(max(n_obs, 1)):
        n_eff_ratio = min((1 + r1) / (1 - r1), 10.0)
    Vc = V * n_eff_ratio

    z = 0.0 if S == 0 else (S - np.sign(S)) / np.sqrt(Vc)
    p = float(2 * norm.sf(abs(z)))

    # IC de la pente de Sen (Hirsch et al. 1982), avec variance corrigée
    N = len(slopes)
    c = norm.ppf(1 - alpha / 2) * np.sqrt(Vc)
    srt = np.sort(slopes)
    lo = float(np.interp(np.clip((N - c) / 2 - 1, 0, N - 1), np.arange(N), srt))
    hi = float(np.interp(np.clip((N + c) / 2, 0, N - 1), np.arange(N), srt))

    # régression linéaire (visualisation, complémentaire)
    A = np.vstack([tdec[ok] - tdec[ok].mean(), np.ones(n_obs)]).T
    ols, icpt = np.linalg.lstsq(A, values[ok], rcond=None)[0]
    ss_res = float(((values[ok] - (A @ [ols, icpt])) ** 2).sum())
    ss_tot = float(((values[ok] - values[ok].mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    significant = p < alpha
    direction = ("up" if sen > 0 else "down") if significant and sen != 0 else "none"
    span = (tdec[ok].max() - tdec[ok].min()) + 1 / 12
    return {
        "status": "ok", "n_obs": n_obs, "n_seasons": seasons,
        "sen_slope": sen, "ci_low": lo, "ci_high": hi,
        "mk_S": S, "mk_z": float(z), "p_value": p,
        "autocorr_r1": r1, "variance_inflation": float(n_eff_ratio),
        "significant": bool(significant), "direction": direction,
        "total_change": float(sen * span), "span_years": float(span),
        "ols_slope": float(ols), "ols_r2": float(r2),
        "level": float(values[ok].mean()), "t_mid": float(tdec[ok].mean()),
    }


def bh_adjust(p) -> np.ndarray:
    """P-values ajustées de Benjamini-Hochberg (contrôle du taux de fausses découvertes, FDR)."""
    p = np.asarray(p, dtype=float)
    n = len(p)
    o = np.argsort(p)
    adj = np.minimum.accumulate((p[o] * n / np.arange(1, n + 1))[::-1])[::-1]
    out = np.empty(n)
    out[o] = np.clip(adj, 0, 1)
    return out


def mk_sen_annual(years, values, alpha=0.05) -> dict:
    """Mann-Kendall classique (correction des ex aequo) + pente de Sen + IC 95 % sur une série annuelle.
    Utilisée comme analyse de sensibilité sur années complètes ; aucune correction d'autocorrélation (n trop faible pour l'estimer)."""
    y = np.asarray(years, float); x = np.asarray(values, float)
    ok = ~np.isnan(x); y, x = y[ok], x[ok]; n = len(x)
    if n < 8:
        return {"status": "insufficient", "n_obs": n}
    iu = np.triu_indices(n, 1)
    d = (x[None, :] - x[:, None])[iu]; t = (y[None, :] - y[:, None])[iu]
    S = float(np.sign(d).sum()); slopes = d / t
    _, cnt = np.unique(x, return_counts=True)
    V = (n * (n - 1) * (2 * n + 5) - sum(c * (c - 1) * (2 * c + 5) for c in cnt if c > 1)) / 18.0
    z = 0.0 if S == 0 else (S - np.sign(S)) / np.sqrt(V)
    N = len(slopes); c = norm.ppf(1 - alpha / 2) * np.sqrt(V); srt = np.sort(slopes)
    lo = float(np.interp(np.clip((N - c) / 2 - 1, 0, N - 1), np.arange(N), srt))
    hi = float(np.interp(np.clip((N + c) / 2, 0, N - 1), np.arange(N), srt))
    return {"status": "ok", "n_obs": n, "sen_slope": float(np.median(slopes)), "ci_low": lo, "ci_high": hi,
            "mk_S": S, "mk_z": float(z), "p_value": float(2 * norm.sf(abs(z)))}
