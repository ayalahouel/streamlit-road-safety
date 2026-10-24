"""Offline tests: build a synthetic fixture in the raw BAAC format, run the
real pipeline on it, then run the full app headlessly with Streamlit AppTest."""

import os
from pathlib import Path

import pandas as pd
import pytest

from tests.make_fixture import make
from utils.prep import build_tables, normalise_dep, parse_hour, save_tables, wilson_ci

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    raw = make(tmp_path_factory.mktemp("raw"), n_acc=400)
    out = tmp_path_factory.mktemp("processed")
    acc, users, q = build_tables(raw_dir=raw, log=lambda *_: None)
    save_tables(acc, users, q, out)
    return acc, users, q, out


def test_tables_consistent(built):
    acc, users, q, _ = built
    assert acc["acc_uid"].is_unique
    assert set(users["acc_uid"]) <= set(acc["acc_uid"])
    assert acc["n_killed"].sum() == users["killed"].sum()
    assert acc["hour"].dropna().between(0, 23).all()


def test_quality_checks_catch_planted_issues(built):
    _, _, q, _ = built
    for chk in q["checks"].values():
        assert chk["metro_coords_outside_france"] >= 1
        assert chk["lieux_duplicate_ids"] >= 1
        assert chk["implausible_speed_limits"] >= 1


def test_helpers():
    assert list(normalise_dep(pd.Series(["1", "2A", "590", "971"]))) == ["01", "2A", "59", "971"]
    assert list(parse_hour(pd.Series(["08:15", "1730", "99:00"])).fillna(-1)) == [8, 17, -1]
    lo, hi = wilson_ci([5], [100])
    assert 0 < lo[0] < 0.05 < hi[0] < 0.2


def test_app_runs(built):
    from streamlit.testing.v1 import AppTest
    os.environ["ROADSAFETY_DATA_DIR"] = str(built[3])
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    assert not at.exception
    at.sidebar.multiselect[2].set_value(["Cyclist"]).run()
    assert not at.exception
