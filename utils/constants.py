"""Constants: data sources, code dictionaries (from the official ONISR data
dictionary) and the department -> region lookup.

Everything that defines the data scope lives here so the pipeline is
deterministic: same years, same resources, same labels on every run.
"""

DATASET_TITLE = (
    "Bases de données annuelles des accidents corporels de la circulation "
    "routière (BAAC) — ONISR / Ministère de l'Intérieur"
)
DATASET_PAGE = "https://www.data.gouv.fr/datasets/53698f4ca3a729239d2036df/"
DATASET_API = "https://www.data.gouv.fr/api/1/datasets/53698f4ca3a729239d2036df/"
DATA_DICTIONARY = (
    "https://static.data.gouv.fr/resources/bases-de-donnees-annuelles-des-"
    "accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2024/"
    "20251021-115933/description-des-bases-de-donnees-annuelles.pdf"
)
LICENSE = "Licence Ouverte / Open Licence v2.0 (Etalab)"

# Scope: 2021-2024 share exactly the same schema (id_usager / id_vehicule,
# e-scooter categories), which keeps year-on-year comparisons honest.
YEARS = [2021, 2022, 2023, 2024]
TABLES = ["caract", "lieux", "vehicules", "usagers"]

# data.gouv.fr resource ids. The /api/1/datasets/r/<id> endpoint always
# redirects to the latest version of a resource, so it is the most stable link.
RESOURCE_IDS = {
    2021: {
        "caract": "85cfdc0c-23e4-4674-9bcd-79a970d7269b",
        "lieux": "8a4935aa-38cd-43af-bf10-0209d6d17434",
        "vehicules": "0bb5953a-25d8-46f8-8c25-b5c2f5ba905e",
        "usagers": "ba5a1956-7e82-41b7-a602-89d7dd484d7a",
    },
    2022: {
        "caract": "5fc299c0-4598-4c29-b74c-6a67b0cc27e7",
        "lieux": "a6ef711a-1f03-44cb-921a-0ce8ec975995",
        "vehicules": "c9742921-4427-41e5-81bc-f13af8bc31a0",
        "usagers": "62c20524-d442-46f5-bfd8-982c59763ec8",
    },
    2023: {
        "caract": "104dbb32-704f-4e99-a71e-43563cb604f2",
        "lieux": "8bef19bf-a5e4-46b3-b5f9-a145da4686bc",
        "vehicules": "146a42f5-19f0-4b3e-a887-5cd8fbef057b",
        "usagers": "68848e2a-28dd-4efc-9d5f-d512f7dbe66f",
    },
    2024: {
        "caract": "83f0fb0e-e0ef-47fe-93dd-9aaee851674a",
        "lieux": "228b3cda-fdfb-4677-bd54-ab2107028d2d",
        "vehicules": "fd30513c-6b11-4a56-b6dc-5ac87728794b",
        "usagers": "f57b1f58-386d-4048-8f78-2ebe435df868",
    },
}
REDIRECT_URL = "https://www.data.gouv.fr/api/1/datasets/r/{rid}"

# ---------------------------------------------------------------- code labels
GRAV = {1: "Unhurt", 2: "Killed", 3: "Hospitalised", 4: "Slightly injured"}
LUM = {
    1: "Daylight",
    2: "Dusk / dawn",
    3: "Night, no street lighting",
    4: "Night, lighting off",
    5: "Night, lighting on",
}
AGG = {1: "Rural (outside built-up area)", 2: "Urban (built-up area)"}
ATM = {
    1: "Normal",
    2: "Light rain",
    3: "Heavy rain",
    4: "Snow / hail",
    5: "Fog / smoke",
    6: "Strong wind / storm",
    7: "Dazzling",
    8: "Overcast",
    9: "Other",
}
CATR = {
    1: "Motorway",
    2: "National road",
    3: "Departmental road",
    4: "Municipal road",
    5: "Off public network",
    6: "Car park",
    7: "Metropolitan urban road",
    9: "Other",
}
SEXE = {1: "Male", 2: "Female"}
CATU = {1: "Driver", 2: "Passenger", 3: "Pedestrian"}

# Vehicle category (catv) -> road-user mode used throughout the story.
MODE_BY_CATV = {}
for c in (1, 80):
    MODE_BY_CATV[c] = "Cyclist"
for c in (50, 60):
    MODE_BY_CATV[c] = "E-scooter / PMD"
for c in (2, 30, 31, 32, 33, 34, 41, 42, 43):
    MODE_BY_CATV[c] = "Motorised 2-3 wheeler"
for c in (3, 7):
    MODE_BY_CATV[c] = "Car"
MODE_BY_CATV[10] = "Van"
for c in (13, 14, 15, 16, 17, 37, 38):
    MODE_BY_CATV[c] = "HGV / bus"
MODES = [
    "Pedestrian",
    "Cyclist",
    "E-scooter / PMD",
    "Motorised 2-3 wheeler",
    "Car",
    "Van",
    "HGV / bus",
    "Other / unknown",
]
VULNERABLE = {"Pedestrian", "Cyclist", "E-scooter / PMD", "Motorised 2-3 wheeler"}

AGE_BINS = [0, 18, 25, 35, 45, 65, 75, 120]
AGE_LABELS = ["0-17", "18-24", "25-34", "35-44", "45-64", "65-74", "75+"]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ------------------------------------------------------------ geography
REGIONS = {
    "Auvergne-Rhône-Alpes": ["01", "03", "07", "15", "26", "38", "42", "43", "63", "69", "73", "74"],
    "Bourgogne-Franche-Comté": ["21", "25", "39", "58", "70", "71", "89", "90"],
    "Bretagne": ["22", "29", "35", "56"],
    "Centre-Val de Loire": ["18", "28", "36", "37", "41", "45"],
    "Corse": ["2A", "2B"],
    "Grand Est": ["08", "10", "51", "52", "54", "55", "57", "67", "68", "88"],
    "Hauts-de-France": ["02", "59", "60", "62", "80"],
    "Île-de-France": ["75", "77", "78", "91", "92", "93", "94", "95"],
    "Normandie": ["14", "27", "50", "61", "76"],
    "Nouvelle-Aquitaine": ["16", "17", "19", "23", "24", "33", "40", "47", "64", "79", "86", "87"],
    "Occitanie": ["09", "11", "12", "30", "31", "32", "34", "46", "48", "65", "66", "81", "82"],
    "Pays de la Loire": ["44", "49", "53", "72", "85"],
    "Provence-Alpes-Côte d'Azur": ["04", "05", "06", "13", "83", "84"],
    "Overseas": ["971", "972", "973", "974", "975", "976", "977", "978", "986", "987", "988"],
}
REGION_BY_DEP = {d: r for r, deps in REGIONS.items() for d in deps}

DEP_NAMES = {
    "01": "Ain", "02": "Aisne", "03": "Allier", "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes", "06": "Alpes-Maritimes", "07": "Ardèche", "08": "Ardennes",
    "09": "Ariège", "10": "Aube", "11": "Aude", "12": "Aveyron",
    "13": "Bouches-du-Rhône", "14": "Calvados", "15": "Cantal", "16": "Charente",
    "17": "Charente-Maritime", "18": "Cher", "19": "Corrèze", "2A": "Corse-du-Sud",
    "2B": "Haute-Corse", "21": "Côte-d'Or", "22": "Côtes-d'Armor", "23": "Creuse",
    "24": "Dordogne", "25": "Doubs", "26": "Drôme", "27": "Eure",
    "28": "Eure-et-Loir", "29": "Finistère", "30": "Gard", "31": "Haute-Garonne",
    "32": "Gers", "33": "Gironde", "34": "Hérault", "35": "Ille-et-Vilaine",
    "36": "Indre", "37": "Indre-et-Loire", "38": "Isère", "39": "Jura",
    "40": "Landes", "41": "Loir-et-Cher", "42": "Loire", "43": "Haute-Loire",
    "44": "Loire-Atlantique", "45": "Loiret", "46": "Lot", "47": "Lot-et-Garonne",
    "48": "Lozère", "49": "Maine-et-Loire", "50": "Manche", "51": "Marne",
    "52": "Haute-Marne", "53": "Mayenne", "54": "Meurthe-et-Moselle", "55": "Meuse",
    "56": "Morbihan", "57": "Moselle", "58": "Nièvre", "59": "Nord",
    "60": "Oise", "61": "Orne", "62": "Pas-de-Calais", "63": "Puy-de-Dôme",
    "64": "Pyrénées-Atlantiques", "65": "Hautes-Pyrénées", "66": "Pyrénées-Orientales",
    "67": "Bas-Rhin", "68": "Haut-Rhin", "69": "Rhône", "70": "Haute-Saône",
    "71": "Saône-et-Loire", "72": "Sarthe", "73": "Savoie", "74": "Haute-Savoie",
    "75": "Paris", "76": "Seine-Maritime", "77": "Seine-et-Marne", "78": "Yvelines",
    "79": "Deux-Sèvres", "80": "Somme", "81": "Tarn", "82": "Tarn-et-Garonne",
    "83": "Var", "84": "Vaucluse", "85": "Vendée", "86": "Vienne",
    "87": "Haute-Vienne", "88": "Vosges", "89": "Yonne", "90": "Territoire de Belfort",
    "91": "Essonne", "92": "Hauts-de-Seine", "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne", "95": "Val-d'Oise", "971": "Guadeloupe", "972": "Martinique",
    "973": "Guyane", "974": "La Réunion", "975": "Saint-Pierre-et-Miquelon",
    "976": "Mayotte", "977": "Saint-Barthélemy", "978": "Saint-Martin",
    "986": "Wallis-et-Futuna", "987": "Polynésie française", "988": "Nouvelle-Calédonie",
}

# Bounding box used to validate GPS coordinates for mainland France + Corsica.
METRO_BBOX = {"lat": (41.0, 51.6), "lon": (-5.6, 9.9)}

# Colour-blind-safe palette (Okabe & Ito) used for every categorical chart.
PALETTE = {
    "Pedestrian": "#E69F00",
    "Cyclist": "#56B4E9",
    "E-scooter / PMD": "#CC79A7",
    "Motorised 2-3 wheeler": "#D55E00",
    "Car": "#0072B2",
    "Van": "#009E73",
    "HGV / bus": "#555555",
    "Other / unknown": "#999999",
    "Rural (outside built-up area)": "#009E73",
    "Urban (built-up area)": "#0072B2",
}
ACCENT = "#D55E00"
NEUTRAL = "#0072B2"
