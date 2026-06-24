# Changelog — Débit Optimiseur

## 2026-06-25 — Optimisation moteur + durcissement sécurité

### Optimisation (calepinage)
- **Correctif FFDH** (`engine/shelf.py`) : une pièce libre (rotation autorisée)
  ouvre désormais un nouveau « shelf » sur son **côté court** (orientation qui
  minimise la hauteur), cohérent avec le tri du packer. Avant, une pièce étroite
  et longue (ex. 100×2000) ouvrait un shelf de ~2000 de haut et gaspillait le
  reste du panneau. Le flag `rotated` est aussi désormais exact (placement direct
  sans re-dérivation d'orientation).
- Test de non-régression ajouté (`tests/test_engine.py::TestFreePieceShelfHeight`).
  Suite : **16 tests** verts.

### Sécurité / robustesse
- **Race condition supprimée** (`engine/packer.py` + `routes/optimize.py`) : les
  paramètres panneau (largeur/hauteur/kerf/marge) sont passés en **arguments** à
  `optimize()` au lieu de muter le singleton global `settings` (fuite possible
  entre requêtes concurrentes).
- **Validation des entrées** (`routes/optimize.py`) : rejet (422) des dimensions
  ≤ 0 et des marges incohérentes (2·marge ≥ panneau).
- **CORS restreint** (`main.py`) : allowlist via `ALLOWED_ORIGINS` (défaut
  localhost) au lieu de `*`.

### Outillage
- Dépôt git initialisé + `.gitignore` (exclut `.venv/`, `__pycache__/`, `.env`,
  artefacts `storage/`).
