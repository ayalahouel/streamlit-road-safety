"""Cleaning, validation and feature engineering.

Output: two analysis tables + a data-quality report.
  * accidents.parquet : one row per accident (time, place, conditions, toll)
  * users.parquet     : one row per person involved (mode, age, severity)
  * quality.json      : every check run during cleaning, shown in the app
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from utils.constants import (
    AGE_BINS, AGE_LABELS, AGG, ATM, CATR, CATU, DEP_NAMES, GRAV, LUM,
    METRO_BBOX, MODE_BY_CATV, REGION_BY_DEP, SEXE, WEEKDAYS, YEARS,
)
from utils.io import PROCESSED_DIR, RAW_DIR, raw_path, read_baac_csv

KEY_COLS = {
    "caract": ["Num_Acc", "jour", "mois", "an", "hrmn", "lum", "dep", "agg", "atm", "lat", "long"],
    "lieux": ["Num_Acc", "catr", "vma"],
    "vehicules": ["Num_Acc", "id_vehicule", "num_veh", "catv"],
    "usagers": ["Num_Acc", "id_vehicule", "num_veh", "catu", "grav", "sexe", "an_nais"],
}


def _num(s: pd.Series) -> pd.Series:
    """String -> number; BAAC codes '-1' / blank mean 'not recorded'."""
    out = pd.to_numeric(s.astype("string").str.replace(",", ".", regex=False), errors="coerce")
    return out.where(out != -1)


def _missing_profile(df: pd.DataFrame, cols: list[str]) -> dict:
    prof = {}
    for c in cols:
        if c not in df.columns:
            prof[c] = 100.0
            continue
        s = df[c].astype("string")
        miss = s.isna() | s.isin(["-1", " -1", "NA", "nan"])
        prof[c] = round(100 * miss.mean(), 2)
    return prof


def normalise_dep(s: pd.Series) -> pd.Series:
    s = s.astype("string").str.strip().str.upper()
    # pre-2019 style '590' -> '59' (defensive; harmless for 2021+)
    legacy = s.str.fullmatch(r"\d{2}0") & ~s.str.startswith("97") & ~s.str.startswith("98")
    s = s.where(~legacy, s.str[:2])
    s = s.where(~s.str.fullmatch(r"\d"), s.str.zfill(2))
    return s


def parse_hour(s: pd.Series) -> pd.Series:
    s = s.astype("string").str.strip()
    hh = s.str.split(":").str[0]
    no_colon = ~s.str.contains(":", na=False)
    hh = hh.where(~no_colon, s.str.zfill(4).str[:2])
    h = pd.to_numeric(hh, errors="coerce")
    return h.where((h >= 0) & (h <= 23))


def build_tables(years=YEARS, raw_dir: Path = RAW_DIR, log=print):
    acc_frames, user_frames = [], []
    q = {"years": list(years), "files": {}, "checks": {}, "missing_pct": {}}

    for year in years:
        log(f"Cleaning {year} ...")
        t = {tb: read_baac_csv(raw_path(tb, year, raw_dir)) for tb in KEY_COLS}
        for tb, df in t.items():
            q["files"][f"{tb}-{year}"] = {"rows": int(len(df)), "cols": int(df.shape[1])}
            q["missing_pct"][f"{tb}-{year}"] = _missing_profile(df, KEY_COLS[tb])
            absent = [c for c in KEY_COLS[tb] if c not in df.columns]
            if absent:
                raise ValueError(f"{tb}-{year}: expected columns missing {absent}; got {list(df.columns)}")

        chk = {}
        # ---------------------------------------------------- accidents
        c = t["caract"].copy()
        chk["caract_duplicate_ids"] = int(c["Num_Acc"].duplicated().sum())
        c = c.drop_duplicates("Num_Acc")
        a = pd.DataFrame({"acc_id": c["Num_Acc"].astype("string")})
        yr = _num(c["an"])
        yr = yr.where(yr > 100, yr + 2000)
        chk["caract_year_mismatch"] = int((yr != year).sum())
        a["year"] = year
        a["month"] = _num(c["mois"]).astype("Int64")
        a["day"] = _num(c["jour"]).astype("Int64")
        a["date"] = pd.to_datetime(
            dict(year=a["year"], month=a["month"], day=a["day"]), errors="coerce"
        )
        chk["invalid_dates"] = int(a["date"].isna().sum())
        a["weekday"] = pd.Categorical(
            a["date"].dt.dayofweek.map(dict(enumerate(WEEKDAYS))), categories=WEEKDAYS, ordered=True
        )
        a["hour"] = parse_hour(c["hrmn"]).astype("Int64")
        chk["invalid_hours"] = int(a["hour"].isna().sum())
        a["dep"] = normalise_dep(c["dep"])
        a["dep_name"] = a["dep"].map(DEP_NAMES)
        a["region"] = a["dep"].map(REGION_BY_DEP)
        chk["unknown_department"] = int(a["region"].isna().sum())
        a["metro"] = a["region"].ne("Overseas") & a["region"].notna()
        a["lighting"] = _num(c["lum"]).map(LUM).fillna("Not recorded")
        a["night"] = _num(c["lum"]).isin([3, 4, 5])
        a["area"] = _num(c["agg"]).map(AGG).fillna("Not recorded")
        a["weather"] = _num(c["atm"]).map(ATM).fillna("Not recorded")
        lat, lon = _num(c["lat"]), _num(c["long"])
        in_box = lat.between(*METRO_BBOX["lat"]) & lon.between(*METRO_BBOX["lon"])
        bad_metro = a["metro"] & ~in_box
        chk["metro_coords_outside_france"] = int(bad_metro.sum())
        a["lat"] = lat.where(~bad_metro)
        a["lon"] = lon.where(~bad_metro)

        l = t["lieux"].copy()
        chk["lieux_duplicate_ids"] = int(l["Num_Acc"].duplicated().sum())
        l = l.drop_duplicates("Num_Acc")  # one road description per accident
        l = pd.DataFrame({
            "acc_id": l["Num_Acc"].astype("string"),
            "road": _num(l["catr"]).map(CATR).fillna("Not recorded"),
            "speed_limit": _num(l["vma"]),
        })
        bad_vma = ~l["speed_limit"].between(10, 130) & l["speed_limit"].notna()
        chk["implausible_speed_limits"] = int(bad_vma.sum())
        l.loc[bad_vma, "speed_limit"] = np.nan
        a = a.merge(l, on="acc_id", how="left")
        a["road"] = a["road"].fillna("Not recorded")

        # ---------------------------------------------------- people
        v = t["vehicules"][["Num_Acc", "id_vehicule", "num_veh", "catv"]].copy()
        v["catv"] = _num(v["catv"])
        u = t["usagers"].copy()
        chk["usagers_exact_duplicates"] = int(u.duplicated().sum())
        u = u.drop_duplicates()
        u = u.merge(v[["Num_Acc", "id_vehicule", "catv"]].drop_duplicates(["Num_Acc", "id_vehicule"]),
                    on=["Num_Acc", "id_vehicule"], how="left")
        # fallback join on num_veh for rows without id_vehicule match
        miss = u["catv"].isna()
        if miss.any():
            alt = u.loc[miss, ["Num_Acc", "num_veh"]].merge(
                v[["Num_Acc", "num_veh", "catv"]].drop_duplicates(["Num_Acc", "num_veh"]),
                on=["Num_Acc", "num_veh"], how="left")
            u.loc[miss, "catv"] = alt["catv"].to_numpy()
        chk["users_without_vehicle_match"] = int(u["catv"].isna().sum())
        orphan = ~u["Num_Acc"].isin(a["acc_id"])
        chk["users_orphan_accident"] = int(orphan.sum())
        u = u[~orphan]

        p = pd.DataFrame({"acc_id": u["Num_Acc"].astype("string"), "year": year})
        catu = _num(u["catu"])
        p["role"] = catu.map(CATU).fillna("Not recorded")
        mode = u["catv"].map(MODE_BY_CATV).fillna("Other / unknown")
        p["mode"] = mode.where(catu != 3, "Pedestrian")
        g = _num(u["grav"])
        chk["unknown_severity"] = int(g.isna().sum())
        p["severity"] = g.map(GRAV).fillna("Not recorded")
        p["killed"] = g.eq(2)
        p["hospitalised"] = g.eq(3)
        p["injured"] = g.isin([2, 3, 4])
        p["sex"] = _num(u["sexe"]).map(SEXE).fillna("Not recorded")
        age = year - _num(u["an_nais"])
        bad_age = age.notna() & ~age.between(0, 105)
        chk["implausible_ages"] = int(bad_age.sum())
        p["age"] = age.where(~bad_age)
        p["age_group"] = pd.cut(p["age"], AGE_BINS, labels=AGE_LABELS, right=False)

        # accident-level toll
        toll = p.groupby("acc_id").agg(
            n_people=("acc_id", "size"),
            n_killed=("killed", "sum"),
            n_hosp=("hospitalised", "sum"),
            n_injured=("injured", "sum"),
        ).reset_index()
        a = a.merge(toll, on="acc_id", how="left")
        for col in ["n_people", "n_killed", "n_hosp", "n_injured"]:
            a[col] = a[col].fillna(0).astype(int)
        chk["accidents_without_people"] = int((a["n_people"] == 0).sum())
        a["fatal"] = a["n_killed"] > 0

        # people inherit accident context (for filtering)
        ctx = ["acc_id", "dep", "dep_name", "region", "metro", "area", "night", "hour",
               "weekday", "month", "road"]
        p = p.merge(a[ctx], on="acc_id", how="left")

        q["checks"][str(year)] = chk
        acc_frames.append(a)
        user_frames.append(p)

    accidents = pd.concat(acc_frames, ignore_index=True)
    users = pd.concat(user_frames, ignore_index=True)
    accidents["acc_uid"] = accidents["year"].astype(str) + "_" + accidents["acc_id"].astype(str)
    users["acc_uid"] = users["year"].astype(str) + "_" + users["acc_id"].astype(str)
    for df in (accidents, users):
        for col in ["region", "dep", "dep_name", "area", "road"]:
            df[col] = df[col].astype("string")
    q["totals"] = {
        "accidents": int(len(accidents)),
        "people": int(len(users)),
        "killed": int(users["killed"].sum()),
        "hospitalised": int(users["hospitalised"].sum()),
    }
    return accidents, users, q


def save_tables(accidents, users, quality, out_dir: Path = PROCESSED_DIR):
    out_dir.mkdir(parents=True, exist_ok=True)
    accidents.to_parquet(out_dir / "accidents.parquet", index=False)
    users.to_parquet(out_dir / "users.parquet", index=False)
    (out_dir / "quality.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False))


# ------------------------------------------------------------ analytics helpers
def wilson_ci(k, n, z: float = 1.96):
    """95% Wilson interval for a proportion k/n (vectorised)."""
    k, n = np.asarray(k, float), np.asarray(n, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        p = k / n
        den = 1 + z**2 / n
        centre = (p + z**2 / (2 * n)) / den
        half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / den
    return centre - half, centre + half


def dep_summary(acc: pd.DataFrame) -> pd.DataFrame:
    g = acc.groupby(["dep", "dep_name", "region"], dropna=True).agg(
        accidents=("acc_uid", "size"),
        fatal_accidents=("fatal", "sum"),
        killed=("n_killed", "sum"),
        hospitalised=("n_hosp", "sum"),
        lat=("lat", "median"),
        lon=("lon", "median"),
    ).reset_index()
    g["fatal_share"] = 100 * g["fatal_accidents"] / g["accidents"]
    lo, hi = wilson_ci(g["fatal_accidents"], g["accidents"])
    g["ci_low"], g["ci_high"] = 100 * lo, 100 * hi
    g["killed_per_100_acc"] = 100 * g["killed"] / g["accidents"]
    return g
