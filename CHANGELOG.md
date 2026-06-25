# Changelog — Débit Optimiseur

## 2026-06-25 (b) — Audit global, correctifs, optimisation validée, déploiement

### Bug critique corrigé — encodage du copier-coller
- **`parser/cadwork_csv.py`** : le texte collé depuis le navigateur arrive en
  **UTF-8**, mais le parser décodait en windows-1252 (et le repli ne se
  déclenchait jamais, cp1252 n'échouant quasi pas). Résultat : tout débit collé
  contenant des accents (« Chêne », « Aggloméré », « Mélaminé »…) cassait
  silencieusement → aucune pièce reconnue. **C'était la méthode d'entrée
  principale de la spec.** Corrigé : UTF-8 strict d'abord, repli windows-1252
  pour les fichiers Cadwork. Le fichier exemple cp1252 parse toujours (151 pièces).

### Optimisation moteur (recherche + bancs d'essai)
- Recherche open-source approfondie + mesures sur données réelles : BFDH,
  multi-tri, regroupement par classe de hauteur et **knapsack-par-niveau** ont
  tous été testés. Tous font aussi bien ou **PIRE** (knapsack : 22 panneaux vs 13).
  Le FFDH actuel est **quasi-optimal** : 13 panneaux pour un plancher-surface
  théorique de 12 (borne basse inatteignable). La chute restante est structurelle
  (5 groupes matière × ≥1 panneau + pièces grain-locked non-tuilables).
- Ajout d'un **multi-start best-of** (`engine/packer.py`) : chaque groupe est packé
  avec plusieurs ordres de tri, on garde le résultat au moins de panneaux.
  **Garanti jamais pire** que le FFDH (qui est dans le pool). Données réelles
  inchangées (13 panneaux), gain possible sur d'autres débits.

### Robustesse / cas limites
- **Garde-fous d'entrée** (`routes/optimize.py`) : rejet des uploads > 8 Mo (413)
  et des débits > 50 000 pièces (422) — empêche une bombe mémoire via une colonne
  Qté aberrante.

### Nettoyage code mort
- Suppression de `engine/maxrects.py` (jamais importé) et de la dépendance
  `rectpack` (jamais utilisée — moteur 100% maison).
- Suppression de `_read_raw` (mort) et `_sort_key` (mort/redondant) ;
  `import base64` propre au lieu de `__import__("base64")` ; imports inutiles
  retirés.

### Tests
- Nouveau **`tests/test_api.py`** : couverture HTTP de bout en bout (parse →
  optimize → historique → téléchargement PDF, overrides fil, validations).
  Suite totale : **24 tests** verts.

### Déploiement
- `Dockerfile` universel (Railway / Render / Fly / HF Spaces) + `.dockerignore`,
  `backend/requirements.txt`, `Procfile`, `render.yaml` (offre gratuite Render).
- `railway.toml` bascule en builder Docker. Healthcheck `/api/health`.

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
