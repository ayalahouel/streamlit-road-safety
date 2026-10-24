"""I/O: download raw BAAC files from data.gouv.fr (with a local cache) and read
them robustly, whatever the year's quirks (separator, encoding, BOM, quotes,
renamed id column)."""

from __future__ import annotations

import hashlib
import io
import json
import time
from pathlib import Path

import pandas as pd
import requests

from utils.constants import DATASET_API, REDIRECT_URL, RESOURCE_IDS, TABLES, YEARS

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

# Canonical column names (the files mix cases and renamed the id in 2022).
CANONICAL = {
    "num_acc": "Num_Acc",
    "accident_id": "Num_Acc",
    "id_vehicule": "id_vehicule",
    "num_veh": "num_veh",
}


def raw_path(table: str, year: int, raw_dir: Path = RAW_DIR) -> Path:
    return raw_dir / f"{table}-{year}.csv"


def _discover_url(table: str, year: int) -> str | None:
    """Fallback: look the resource up by title through the data.gouv.fr API."""
    keys = {
        "caract": ("caract", "carcteristiques", "caracteristiques"),
        "lieux": ("lieux",),
        "vehicules": ("vehicules",),
        "usagers": ("usagers",),
    }[table]
    try:
        meta = requests.get(DATASET_API, timeout=30).json()
    except Exception:
        return None
    for res in meta.get("resources", []):
        title = (res.get("title") or "").lower()
        if str(year) in title and any(k in title for k in keys) and "immatric" not in title:
            return res.get("url")
    return None


def download_raw(years=YEARS, raw_dir: Path = RAW_DIR, force: bool = False, log=print) -> dict:
    """Download the 4 tables for each year. Files already on disk are reused
    (this is the cache). Returns a manifest {file: {url, sha256, bytes}}."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for year in years:
        for table in TABLES:
            dest = raw_path(table, year, raw_dir)
            if dest.exists() and not force:
                log(f"  cached   {dest.name}")
            else:
                urls = [REDIRECT_URL.format(rid=RESOURCE_IDS[year][table])]
                last_err = None
                for attempt in range(3):
                    url = urls[-1]
                    try:
                        r = requests.get(url, timeout=120)
                        r.raise_for_status()
                        dest.write_bytes(r.content)
                        log(f"  fetched  {dest.name} ({len(r.content)/1e6:.1f} MB)")
                        break
                    except Exception as err:  # network hiccup or moved resource
                        last_err = err
                        alt = _discover_url(table, year)
                        if alt and alt not in urls:
                            urls.append(alt)
                        time.sleep(2 * (attempt + 1))
                else:
                    raise RuntimeError(f"Could not download {table} {year}: {last_err}")
            data = dest.read_bytes()
            manifest[dest.name] = {
                "url": REDIRECT_URL.format(rid=RESOURCE_IDS[year][table]),
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
    (raw_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def read_baac_csv(path: Path) -> pd.DataFrame:
    """Read one BAAC csv as strings. Tries ';' then ',' and utf-8 then latin-1."""
    raw = Path(path).read_bytes()
    last_err = None
    for enc in ("utf-8-sig", "latin-1"):
        try:
            text = raw.decode(enc)
        except UnicodeDecodeError as err:
            last_err = err
            continue
        for sep in (";", ",", "\t"):
            try:
                df = pd.read_csv(io.StringIO(text), sep=sep, dtype=str, keep_default_na=False)
            except Exception as err:
                last_err = err
                continue
            if df.shape[1] >= 4:
                cols = [c.strip().strip('"').strip("﻿").strip().lower() for c in df.columns]
                df.columns = [CANONICAL.get(c, c) for c in cols]
                for c in df.columns:
                    df[c] = df[c].str.strip().str.strip('"').str.strip()
                df = df.replace({"": pd.NA, " ": pd.NA})
                return df
    raise ValueError(f"Unreadable file {path}: {last_err}")
