"""Tests du parser Cadwork : séparateurs (;, tab Excel, ,), encodage, filtres."""
from app.parser.cadwork_csv import parse_cadwork_csv

HEADER_COLS = ["No. LP", "Nom", "Matériau", "Qté", "Haut.", "Larg.", "Long."]
ROWS = [
    ["1", "Façade", "Aggloméré plaqué chêne", "2", "19", "600", "800"],
    ["2", "Étagère", "MDF", "3", "19", "300", "1200"],
    ["3", "Quinc.", "Sys32", "5", "19", "50", "50"],   # filtré
]


def _build(sep: str) -> str:
    lines = ["Export débit", sep.join(HEADER_COLS)]
    lines += [sep.join(r) for r in ROWS]
    return "\n".join(lines)


def test_parse_semicolon():
    pieces = parse_cadwork_csv(_build(";"))
    assert {p.material for p in pieces} == {"Aggloméré plaqué chêne", "MDF"}
    assert sum(p.quantity for p in pieces) == 5      # Sys32 (5) filtré


def test_parse_tab_excel_paste():
    # Un copier-coller depuis Excel arrive TABULÉ — doit marcher (retour Tom).
    pieces = parse_cadwork_csv(_build("\t"))
    assert len(pieces) == 2
    chene = next(p for p in pieces if "chêne" in p.material.lower())
    assert chene.quantity == 2 and chene.grain_locked is True
    mdf = next(p for p in pieces if p.material == "MDF")
    assert mdf.grain_locked is False


def test_parse_comma():
    pieces = parse_cadwork_csv(_build(","))
    assert len(pieces) == 2


def test_parse_utf8_bytes_with_accents():
    # Collage navigateur = UTF-8 : les accents ne doivent pas casser la détection.
    raw = _build(";").encode("utf-8")
    pieces = parse_cadwork_csv(raw)
    assert any("chêne" in p.material.lower() for p in pieces)


def test_parse_cp1252_bytes_fallback():
    # Fichier Cadwork = windows-1252 : repli d'encodage.
    raw = _build(";").encode("windows-1252")
    pieces = parse_cadwork_csv(raw)
    assert any("chêne" in p.material.lower() for p in pieces)


def test_dimensions_parsed():
    p = next(p for p in parse_cadwork_csv(_build("\t")) if p.lp_number == "1")
    assert (p.thickness, p.width, p.length) == (19, 600, 800)
