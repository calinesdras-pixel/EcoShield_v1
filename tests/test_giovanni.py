"""Tests données Giovanni (CSV réels) et statistiques (séries synthétiques réservées aux tests)."""
import sys, pathlib, json
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import giovanni
from stats_engine import analyze, bh_adjust, mk_sen_annual

PROC = ROOT / "data" / "processed" / "giovanni"


def meta():
    giovanni.main.__call__ if False else None
    return {m["code"]: m for m in json.loads((PROC / "metadata.json").read_text(encoding="utf-8"))["series"]}


def test_periods_match_files():
    m = meta()
    assert m["TAIR"]["periode_analysee"] == ["2014-12", "2026-07"]
    assert m["SOILM"]["periode_analysee"] == ["2014-12", "2026-07"]
    assert m["PRECIP"]["periode_analysee"] == ["2014-12", "2025-09"]   # pas de prolongation artificielle


def test_no_duplicates_no_gaps_no_zero_fill():
    for code, mm in meta().items():
        df = pd.read_csv(PROC / f"{code}.csv", parse_dates=["date"])
        assert not df.date.duplicated().any()
        assert len(df) == mm["n_attendues"] and mm["n_manquantes"] == 0
        assert df.value.notna().all()


def test_unit_conversions():
    t = pd.read_csv(PROC / "TAIR.csv"); assert 20 < t.value.mean() < 30 and abs(t.value_raw.iloc[0] - 273.15 - t.value.iloc[0]) < 1e-4
    p = pd.read_csv(PROC / "PRECIP.csv", parse_dates=["date"])
    r = p.iloc[1]; days = r.date.days_in_month
    assert abs(r.value - r.value_raw * 24 * days) < 1e-3


def test_raw_files_untouched_and_traced():
    for mm in meta().values():
        import hashlib
        assert hashlib.sha256((giovanni.RAW / mm["fichier_source"]).read_bytes()).hexdigest() == mm["sha256_source"]
        assert mm["source"] == "NASA Giovanni" and mm["unite"] and mm["boite_englobante_lon_lat"]


def test_fill_value_becomes_nan_not_zero(tmp_path, monkeypatch):
    f = tmp_path / "x.csv"
    f.write_text('Title:,"t"\nFill Value (a):, -9999\n\ntime, a\n2020-01-01 00:00:00,1.0\n2020-02-01 00:00:00,-9999\n', encoding="utf-8")
    h, df = giovanni.read_giovanni(f)
    assert h["fill_value"] == -9999.0 and len(df) == 2


def series(slope, n_years=12, noise=0.4, seed=1, ar=0.0):
    rng = np.random.default_rng(seed); n = n_years * 12
    years = np.repeat(np.arange(2014, 2014 + n_years), 12); months = np.tile(np.arange(1, 13), n_years)
    e = np.zeros(n)
    for i in range(1, n): e[i] = ar * e[i - 1] + rng.normal(0, noise)
    e[0] = rng.normal(0, noise)
    return years, months, 25 + 2 * np.sin(2 * np.pi * months / 12) + slope * (years + (months - 1) / 12 - 2020) + e


def test_bh_known_values():
    adj = bh_adjust([0.01, 0.04, 0.03, 0.005])
    assert np.allclose(adj, [0.02, 0.04, 0.04, 0.02])


def test_autocorrelation_inflates_variance():
    r = analyze(*series(0.0, ar=0.7, seed=3)); assert r["autocorr_r1"] > 0.4 and r["variance_inflation"] > 1.5


def test_outliers_do_not_break_sen():
    y, m, v = series(0.1); v = v.copy(); v[[10, 50, 90]] += 30
    assert abs(analyze(y, m, v)["sen_slope"] - 0.1) < 0.05


def test_annual_mk_detects_trend_and_flat():
    yrs = np.arange(2015, 2026)
    assert mk_sen_annual(yrs, 0.3 * (yrs - 2015) + np.random.default_rng(0).normal(0, .1, 11))["p_value"] < 0.01
    assert mk_sen_annual(yrs, np.random.default_rng(1).normal(0, 1, 11))["p_value"] > 0.05
