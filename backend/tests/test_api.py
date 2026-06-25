"""Tests d'intégration de l'API (parse → optimize → history → download).

Couvre la chaîne HTTP complète, y compris la génération PDF et la persistance
SQLite (fallback automatique). Le stockage PDF est redirigé vers un dossier
temporaire pour ne rien laisser traîner.
"""
import pytest
from fastapi.testclient import TestClient

# CSV Cadwork minimal mais réaliste (séparateur ;, en-tête détecté via "Larg.")
SAMPLE_CSV = (
    "Export débit\n"
    "Projet test\n"
    "No. LP;Nom;Matériau;Qté;Haut.;Larg.;Long.\n"
    "1;Panneau A;MDF;2;19;600;800\n"
    "2;Côté gauche;Aggloméré plaqué chêne;1;19;300;1200\n"
    "3;Quincaillerie;Sys32;4;19;50;50\n"   # filtré (matériau ignoré)
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "storage_path", str(tmp_path))
    from app.main import app
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_parse_detects_materials_and_grain(client):
    r = client.post("/api/parse", data={"paste": SAMPLE_CSV})
    assert r.status_code == 200
    body = r.json()
    mats = {m["material"]: m for m in body["materials"]}
    assert "Sys32" not in mats                       # matériau ignoré filtré
    assert mats["MDF"]["grain_locked"] is False      # MDF = rotation libre
    assert mats["Aggloméré plaqué chêne"]["grain_locked"] is True  # chêne = fil
    assert body["piece_count"] == 3                  # 2 MDF + 1 chêne (Sys32 exclu)
    assert body["raw_b64"]


def test_parse_rejects_empty(client):
    r = client.post("/api/parse", data={"paste": "n'importe quoi sans colonnes"})
    assert r.status_code == 422


def test_optimize_end_to_end(client):
    r = client.post("/api/optimize", data={"paste": SAMPLE_CSV, "project_name": "Test"})
    assert r.status_code == 200
    body = r.json()
    assert body["total_panels"] >= 1
    assert body["total_pieces"] == 3
    assert 0 <= body["global_waste_ratio"] <= 100
    export_id = body["export_id"]

    # historique listé
    h = client.get("/api/history")
    assert h.status_code == 200
    assert any(e["id"] == export_id for e in h.json())

    # PDFs téléchargeables
    for kind in ("recap", "layout"):
        d = client.get(f"/api/history/{export_id}/{kind}")
        assert d.status_code == 200
        assert d.headers["content-type"] == "application/pdf"
        assert d.content[:4] == b"%PDF"


def test_optimize_grain_override(client):
    # On force le chêne en rotation libre via override → accepté sans erreur
    import json
    r = client.post("/api/optimize", data={
        "paste": SAMPLE_CSV,
        "grain_overrides": json.dumps({"Aggloméré plaqué chêne": False}),
    })
    assert r.status_code == 200


def test_optimize_rejects_bad_panel_params(client):
    r = client.post("/api/optimize", data={"paste": SAMPLE_CSV, "panel_width": "0"})
    assert r.status_code == 422


def test_optimize_rejects_margin_too_large(client):
    r = client.post("/api/optimize", data={
        "paste": SAMPLE_CSV, "panel_width": "100", "border_margin": "60",
    })
    assert r.status_code == 422


def test_download_missing_export_404(client):
    r = client.get("/api/history/999999/recap")
    assert r.status_code == 404
