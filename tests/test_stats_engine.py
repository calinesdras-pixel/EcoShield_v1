"""Tests du moteur statistique sur séries synthétiques à tendance connue (cahier des charges §9.2)."""
import sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from stats_engine import analyze


def make(slope, n_years=25, noise=0.4, seed=1, seasonal=2.0):
    rng = np.random.default_rng(seed)
    years = np.repeat(np.arange(2001, 2001 + n_years), 12)
    months = np.tile(np.arange(1, 13), n_years)
    t = years + (months - 1) / 12
    v = 25 + seasonal * np.sin(2 * np.pi * (months - 3) / 12) + slope * (t - t.mean()) + rng.normal(0, noise, len(t))
    return years, months, v


def test_detects_known_positive_trend():
    r = analyze(*make(0.05))
    assert r["status"] == "ok" and r["direction"] == "up" and r["significant"]
    assert abs(r["sen_slope"] - 0.05) < 0.01
    assert r["ci_low"] <= 0.05 <= r["ci_high"]


def test_detects_known_negative_trend():
    r = analyze(*make(-0.08))
    assert r["direction"] == "down" and abs(r["sen_slope"] + 0.08) < 0.015


def test_no_trend_not_significant_for_most_seeds():
    false_pos = sum(analyze(*make(0.0, seed=s))["significant"] for s in range(40))
    assert false_pos <= 6  # ~5 % attendu, marge de tolérance


def test_insufficient_series():
    assert analyze(*make(0.05, n_years=6))["status"] == "insufficient"


def test_missing_values_are_ignored_not_zero():
    y, m, v = make(0.05)
    v = v.copy(); v[::7] = np.nan
    r = analyze(y, m, v)
    assert r["status"] == "ok" and abs(r["sen_slope"] - 0.05) < 0.015


def test_seasonality_alone_gives_no_trend():
    r = analyze(*make(0.0, seasonal=8.0, noise=0.2, seed=7))
    assert not r["significant"]
