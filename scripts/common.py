from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "processed" / "sci_archive.sqlite"


COUNTRY_ALIASES = [
    ("UNITED STATES", "United States"),
    ("USA", "United States"),
    ("ENGLAND", "United Kingdom"),
    ("SCOTLAND", "United Kingdom"),
    ("WALES", "United Kingdom"),
    ("NORTHERN IRELAND", "United Kingdom"),
    ("UNITED KINGDOM", "United Kingdom"),
    ("GERMANY", "Germany"),
    ("NETHERLANDS", "Netherlands"),
    ("PEOPLES R CHINA", "China"),
    ("PEOPLE'S R CHINA", "China"),
    ("CHINA", "China"),
    ("JAPAN", "Japan"),
    ("FRANCE", "France"),
    ("SWITZERLAND", "Switzerland"),
    ("ITALY", "Italy"),
    ("SPAIN", "Spain"),
    ("INDIA", "India"),
    ("CANADA", "Canada"),
    ("AUSTRALIA", "Australia"),
    ("BRAZIL", "Brazil"),
    ("SOUTH KOREA", "South Korea"),
    ("KOREA", "South Korea"),
    ("SINGAPORE", "Singapore"),
    ("POLAND", "Poland"),
    ("TURKIYE", "Turkiye"),
    ("TURKEY", "Turkiye"),
    ("AUSTRIA", "Austria"),
    ("SWEDEN", "Sweden"),
    ("DENMARK", "Denmark"),
    ("NORWAY", "Norway"),
    ("FINLAND", "Finland"),
    ("BELGIUM", "Belgium"),
    ("IRELAND", "Ireland"),
    ("PORTUGAL", "Portugal"),
    ("GREECE", "Greece"),
    ("CZECH REPUBLIC", "Czech Republic"),
    ("CZECHIA", "Czech Republic"),
    ("HUNGARY", "Hungary"),
    ("ROMANIA", "Romania"),
    ("RUSSIA", "Russia"),
    ("SOUTH AFRICA", "South Africa"),
    ("NEW ZEALAND", "New Zealand"),
    ("MEXICO", "Mexico"),
    ("ARGENTINA", "Argentina"),
    ("CHILE", "Chile"),
    ("MALAYSIA", "Malaysia"),
    ("THAILAND", "Thailand"),
    ("IRAN", "Iran"),
    ("EGYPT", "Egypt"),
    ("SAUDI ARABIA", "Saudi Arabia"),
    ("PAKISTAN", "Pakistan"),
]


BIOMED_KEYWORDS = {
    "medicine",
    "medical",
    "clinical",
    "biomedical",
    "biology",
    "biochemistry",
    "molecular",
    "cell",
    "genetics",
    "genomics",
    "pharmacology",
    "pharmacy",
    "toxicology",
    "immunology",
    "microbiology",
    "virology",
    "oncology",
    "cancer",
    "neuroscience",
    "neurology",
    "psychiatry",
    "public health",
    "health care",
    "dentistry",
    "nursing",
    "veterinary",
    "physiology",
    "pathology",
    "surgery",
    "cardiac",
    "cardiovascular",
    "endocrinology",
    "gastroenterology",
    "hematology",
    "dermatology",
    "radiology",
    "reproductive",
    "urology",
    "pediatrics",
    "obstetrics",
    "gynecology",
    "infectious",
    "nutrition",
}


BIOMED_CATEGORIES = {
    "ALLERGY",
    "ANATOMY & MORPHOLOGY",
    "ANDROLOGY",
    "ANESTHESIOLOGY",
    "AUDIOLOGY & SPEECH-LANGUAGE PATHOLOGY",
    "BIOCHEMICAL RESEARCH METHODS",
    "BIOCHEMISTRY & MOLECULAR BIOLOGY",
    "BIOLOGY",
    "BIOPHYSICS",
    "BIOTECHNOLOGY & APPLIED MICROBIOLOGY",
    "ECOLOGY",
    "ENTOMOLOGY",
    "CARDIAC & CARDIOVASCULAR SYSTEMS",
    "CELL & TISSUE ENGINEERING",
    "CELL BIOLOGY",
    "CLINICAL NEUROLOGY",
    "CRITICAL CARE MEDICINE",
    "DENTISTRY, ORAL SURGERY & MEDICINE",
    "DERMATOLOGY",
    "DEVELOPMENTAL BIOLOGY",
    "EMERGENCY MEDICINE",
    "ENDOCRINOLOGY & METABOLISM",
    "ENGINEERING, BIOMEDICAL",
    "EVOLUTIONARY BIOLOGY",
    "FISHERIES",
    "FOOD SCIENCE & TECHNOLOGY",
    "MARINE & FRESHWATER BIOLOGY",
    "MATERIALS SCIENCE, BIOMATERIALS",
    "MATHEMATICAL & COMPUTATIONAL BIOLOGY",
    "GASTROENTEROLOGY & HEPATOLOGY",
    "GENETICS & HEREDITY",
    "GERIATRICS & GERONTOLOGY",
    "HEALTH CARE SCIENCES & SERVICES",
    "HEALTH POLICY & SERVICES",
    "HEMATOLOGY",
    "IMMUNOLOGY",
    "INFECTIOUS DISEASES",
    "INTEGRATIVE & COMPLEMENTARY MEDICINE",
    "MEDICAL ETHICS",
    "MEDICAL INFORMATICS",
    "MEDICAL LABORATORY TECHNOLOGY",
    "MEDICINE, GENERAL & INTERNAL",
    "MEDICINE, LEGAL",
    "MEDICINE, RESEARCH & EXPERIMENTAL",
    "MICROBIOLOGY",
    "MULTIDISCIPLINARY SCIENCES",
    "MYCOLOGY",
    "NEUROIMAGING",
    "NEUROSCIENCES",
    "NURSING",
    "NUTRITION & DIETETICS",
    "OBSTETRICS & GYNECOLOGY",
    "ONCOLOGY",
    "OPHTHALMOLOGY",
    "ORTHOPEDICS",
    "OTORHINOLARYNGOLOGY",
    "PARASITOLOGY",
    "PATHOLOGY",
    "PEDIATRICS",
    "PERIPHERAL VASCULAR DISEASE",
    "PHARMACOLOGY & PHARMACY",
    "PHYSIOLOGY",
    "PLANT SCIENCES",
    "PRIMARY HEALTH CARE",
    "PSYCHIATRY",
    "PUBLIC, ENVIRONMENTAL & OCCUPATIONAL HEALTH",
    "RADIOLOGY, NUCLEAR MEDICINE & MEDICAL IMAGING",
    "REHABILITATION",
    "REPRODUCTIVE BIOLOGY",
    "RESPIRATORY SYSTEM",
    "RHEUMATOLOGY",
    "SPORT SCIENCES",
    "SUBSTANCE ABUSE",
    "SURGERY",
    "TOXICOLOGY",
    "TRANSPLANTATION",
    "TROPICAL MEDICINE",
    "UROLOGY & NEPHROLOGY",
    "VETERINARY SCIENCES",
    "VIROLOGY",
    "ZOOLOGY",
}


def category_names(categories: str | None) -> list[str]:
    if not categories:
        return []
    names = []
    for part in categories.replace(" | ", ";").split(";"):
        name = part.split("|")[0].strip().upper()
        if name:
            names.append(name)
    return names


def derive_country(address: str | None) -> str | None:
    if not address:
        return None
    text = re.sub(r"\s+", " ", address).upper()
    for alias, country in COUNTRY_ALIASES:
        if re.search(rf"(^|[^A-Z]){re.escape(alias)}([^A-Z]|$)", text):
            return country
    return None


def normalize_title(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"&", " and ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def clean_issn(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip().upper()
    if not value:
        return None
    compact = re.sub(r"[^0-9X]", "", value)
    if len(compact) == 8:
        return f"{compact[:4]}-{compact[4:]}"
    return value


def parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = value.strip().replace(",", "")
    if not cleaned or cleaned.upper() in {"N/A", "NA", "NOT AVAILABLE"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def detect_index_type(*values: str | None) -> str:
    text = " ".join(v or "" for v in values).upper()
    if "ESCI" in text or "EMERGING SOURCES CITATION INDEX" in text:
        return "ESCI"
    if "SCIE" in text or "SCIENCE CITATION INDEX EXPANDED" in text:
        return "SCIE"
    return "UNKNOWN"


def first_present(row: dict[str, str], aliases: Iterable[str]) -> str | None:
    lowered = {k.strip().lower(): v for k, v in row.items() if k is not None}
    for alias in aliases:
        value = lowered.get(alias.lower())
        if value is not None and value.strip():
            return value.strip()
    return None


def parse_partial_date(year: str | None, month: str | None = None, day: str | None = None) -> str | None:
    if not year:
        return None
    month_map = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }
    try:
        y = int(year)
        if month:
            month_clean = month.strip()[:3].lower()
            m = month_map[month_clean] if month_clean in month_map else int(month)
        else:
            m = 1
        d = int(day) if day else 1
        return date(y, m, d).isoformat()
    except ValueError:
        return None
