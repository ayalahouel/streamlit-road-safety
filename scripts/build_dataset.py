"""Download (with cache) + clean + validate the BAAC data, then write the
pre-aggregated parquet files the app reads.

Usage (from the project root):
    python scripts/build_dataset.py            # download if needed, then build
    python scripts/build_dataset.py --force    # re-download everything
    python scripts/build_dataset.py --raw-dir path/to/csvs --skip-download
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.constants import YEARS  # noqa: E402
from utils.io import PROCESSED_DIR, RAW_DIR, download_raw  # noqa: E402
from utils.prep import build_tables, save_tables  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-download raw files")
    ap.add_argument("--skip-download", action="store_true")
    ap.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    ap.add_argument("--out-dir", type=Path, default=PROCESSED_DIR)
    args = ap.parse_args()

    if not args.skip_download:
        print("Downloading raw files from data.gouv.fr ...")
        download_raw(YEARS, args.raw_dir, force=args.force)
    accidents, users, quality = build_tables(YEARS, args.raw_dir)
    save_tables(accidents, users, quality, args.out_dir)
    t = quality["totals"]
    print(f"Done: {t['accidents']:,} accidents, {t['people']:,} people, "
          f"{t['killed']:,} killed -> {args.out_dir}")


if __name__ == "__main__":
    main()
