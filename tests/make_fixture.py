"""Generate a SMALL SYNTHETIC fixture in the exact BAAC raw format (separator,
quoting, comma decimals, the 2022 'Accident_Id' rename, a latin-1 file, '-1'
codes, duplicate rows...). Used only by the automated tests so the pipeline
and the app can be checked offline. It is never used by the app itself.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.constants import DEP_NAMES, YEARS  # noqa: E402

SEED = 42


def _q(v):
    return f'"{v}"'


def make(out_dir: Path, n_acc: int = 1500, years=YEARS):
    rng = np.random.default_rng(SEED)
    out_dir.mkdir(parents=True, exist_ok=True)
    deps = [d for d in DEP_NAMES if len(d) == 2] + ["971", "974"]
    centre = {d: (rng.uniform(42.5, 50.5), rng.uniform(-4, 7.5)) for d in deps}
    centre["971"], centre["974"] = (16.2, -61.5), (-21.1, 55.5)
    for year in years:
        enc = "latin-1" if year == 2021 else "utf-8"
        idcol = "Accident_Id" if year == 2022 else "Num_Acc"
        car = [";".join([idcol, "jour", "mois", "an", "hrmn", "lum", "dep", "com", "agg",
                         "int", "atm", "col", "adr", "lat", "long"])]
        lie = ["Num_Acc;catr;voie;v1;v2;circ;nbv;vosp;prof;pr;pr1;plan;lartpc;larrout;surf;infra;situ;vma"]
        veh = ["Num_Acc;id_vehicule;num_veh;senc;catv;obs;obsm;choc;manv;motor;occutc"]
        usa = ["Num_Acc;id_usager;id_vehicule;num_veh;place;catu;grav;sexe;an_nais;trajet;"
               "secu1;secu2;secu3;locp;actp;etatp"]
        vid = 100000
        for i in range(n_acc):
            aid = f"{year}00{i:06d}"
            dep = deps[rng.integers(len(deps))] if i != 5 else "75"
            rural = rng.random() < 0.35
            hour = int(rng.choice(24, p=np.r_[np.full(6, .015), np.full(12, .06), np.full(6, .025)]
                                  / np.r_[np.full(6, .015), np.full(12, .06), np.full(6, .025)].sum()))
            night = hour < 6 or hour >= 21
            lum = int(rng.choice([3, 5])) if night else 1
            la, lo = centre[dep]
            lat = f"{la + rng.normal(0, .2):.7f}".replace(".", ",")
            lon = f"{lo + rng.normal(0, .2):.7f}".replace(".", ",")
            if i == 5:
                lat, lon = "0,0", "0,0"  # invalid coordinate to be caught
            car.append(";".join(_q(x) for x in [aid, rng.integers(1, 29), rng.integers(1, 13), year,
                                                 f"{hour:02d}:{rng.integers(0, 60):02d}", lum, dep,
                                                 dep + "001", 1 if rural else 2, 1,
                                                 int(rng.choice([1, 2, 8, -1])), 3, "RUE X", lat, lon]))
            catr = 3 if rural else 4
            vma = int(rng.choice([80, 90])) if rural else int(rng.choice([30, 50]))
            if i == 7:
                vma = 900
            line = ";".join(_q(x) for x in [aid, catr, "", "", "", 2, 2, 0, 1, "", "", 1, "", "", 1, 0, 1, vma])
            lie.append(line)
            if i % 300 == 0:
                lie.append(line)  # duplicate lieux row
            nveh = int(rng.integers(1, 3))
            for k in range(nveh):
                vid += 1
                num = chr(65 + k)
                catv = int(rng.choice([7, 7, 7, 33, 1, 10, 50, 15, 2]))
                veh.append(";".join(_q(x) for x in [aid, f"{vid // 1000} {vid % 1000:03d}", num, 1,
                                                     f"{catv:02d}", 0, 2, 1, 1, 1, ""]))
                ped = k == 0 and not rural and rng.random() < .08
                people = [(1, "driver")] + ([(3, "ped")] if ped else [])
                if rng.random() < .3:
                    people.append((2, "pass"))
                for catu, _ in people:
                    vuln = catv in (33, 1, 50, 2) or catu == 3
                    p_kill = .004 + .03 * rural + .02 * night + .03 * vuln
                    r = rng.random()
                    grav = 2 if r < p_kill else 3 if r < p_kill + .15 else 4 if r < .6 else 1
                    an = int(year - rng.integers(16, 90)) if rng.random() > .01 else 1850
                    usa.append(";".join(_q(x) for x in [aid, f"{rng.integers(1e5, 9e5)}",
                                                         f"{vid // 1000} {vid % 1000:03d}", num, 1, catu,
                                                         grav, int(rng.integers(1, 3)), an, 5, 1, 0, -1,
                                                         -1, -1, -1]))
        for name, rows in [("caract", car), ("lieux", lie), ("vehicules", veh), ("usagers", usa)]:
            data = "\n".join(rows) + "\n"
            prefix = "﻿" if (name == "caract" and year == 2023) else ""
            (out_dir / f"{name}-{year}.csv").write_bytes((prefix + data).encode(enc))
    return out_dir


if __name__ == "__main__":
    make(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tests/fixture_raw"))
