import csv
import io
from app.models import Piece

GRAIN_LOCKED_KEYWORDS = {
    "chêne", "hetre", "hêtre", "noyer", "frene", "frêne", "merisier",
    "erable", "érable", "placage", "plaqué", "plaque", "massif",
    "douglas", "pin", "sapin", "aulne", "bouleau", "peuplier",
}

FREE_ROTATION_KEYWORDS = {
    "mdf", "mélaminé", "melamine", "contreplaqué", "contreplaque",
    "stratifié sans fil", "aggloméré brut", "agglomere brut",
}

IGNORED_MATERIALS = {"enveloppe", "sys32"}


def _detect_grain(material: str) -> bool:
    m = material.lower()
    for kw in FREE_ROTATION_KEYWORDS:
        if kw in m:
            return False
    for kw in GRAIN_LOCKED_KEYWORDS:
        if kw in m:
            return True
    return False


def _is_ignored(material: str) -> bool:
    m = material.lower()
    return any(kw in m for kw in IGNORED_MATERIALS)


def parse_cadwork_csv(raw: str | bytes) -> list[Piece]:
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("windows-1252")
        except UnicodeDecodeError:
            raw = raw.decode("utf-8", errors="replace")

    lines = raw.splitlines()

    # Skip header lines until we find the column row (contains "No. LP" or "Larg.")
    data_start = 0
    for i, line in enumerate(lines):
        if "Larg." in line or "No. LP" in line:
            data_start = i
            break

    reader = csv.DictReader(
        io.StringIO("\n".join(lines[data_start:])),
        delimiter=";",
    )

    pieces: list[Piece] = []
    for row in reader:
        try:
            material = (row.get("Matériau") or row.get("Mat\xe9riau") or "").strip()
            if not material or _is_ignored(material):
                continue

            lp = str(row.get("No. LP", "0")).strip()
            name = (row.get("Nom") or "").strip()
            qty_raw = (row.get("Qté") or row.get("Qt\xe9") or "1").strip()
            qty = int(qty_raw) if qty_raw.isdigit() else 1

            thickness = int(float((row.get("Haut.") or "0").strip().replace(",", ".")))
            width = int(float((row.get("Larg.") or "0").strip().replace(",", ".")))
            length = int(float((row.get("Long.") or "0").strip().replace(",", ".")))

            if thickness == 0 or width == 0 or length == 0:
                continue

            pieces.append(Piece(
                lp_number=lp,
                name=name,
                material=material,
                thickness=thickness,
                width=width,
                length=length,
                quantity=qty,
                grain_locked=_detect_grain(material),
            ))
        except (ValueError, KeyError):
            continue

    return pieces
