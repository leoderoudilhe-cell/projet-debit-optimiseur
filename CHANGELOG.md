# Changelog — Débit Optimiseur

## 2026-06-28 — Migration de l'hébergement sur le VPS (Docker + Caddy)

### Déploiement
- L'app n'est plus hébergée sur Railway/Render : elle tourne désormais en **Docker sur
  le VPS Hostinger** (conteneur `optim`, port interne **8000** mappé sur **8002** côté hôte),
  exposée via **Caddy** (TLS automatique) sur **https://tomoptimisateur.duckdns.org**.
- Suppression des fichiers spécifiques aux PaaS : `render.yaml`, `railway.toml`, `Procfile`.
  Le `Dockerfile` (image portable) reste la base du déploiement.

## 2026-06-25 (c) — Retours atelier de Tom (3 correctifs)

### Coupe depuis le HAUT du panneau (`pdf/layout.py`)
- Tom coupe à la scie à panneaux **du haut vers le bas** (il enlève chaque bande ;
  sinon la chute reste au-dessus et bloque la lame). Le plan empilait depuis le bas.
  Corrigé : **axe Y inversé au rendu** → 1ʳᵉ bande en haut, chute en bas, coupes
  H1, H2… numérotées et mesurées **depuis le haut**.

### Légende des petites pièces — bug corrigé (`pdf/layout.py`)
- Les pièces trop petites pour afficher leurs cotes devaient basculer en légende de
  bas de page, mais la légende était construite à partir d'un **dict vide** (rempli
  seulement plus tard, pendant le rendu du flowable) → cotes jamais affichées.
  Constaté par Tom (panneau 9/13, n° 520 et 603). Corrigé : la légende est
  **pré-calculée** avant le rendu (même logique de fit, via `pdfmetrics`). Vérifié
  sur les vraies données : n°520=1454×80 et n°603=470×50 apparaissent désormais.

### Collage depuis Excel (`parser/cadwork_csv.py`)
- Tom ne peut copier-coller son débit que depuis Excel — or Excel met le presse-papier
  en **tabulations**, pas en `;`, donc le collé échouait. Ajout d'une **détection
  automatique du séparateur** (`;`, tab, `,`) sur la ligne d'en-tête.

### Tests
- +`test_parser.py` (séparateurs, encodage) et +`test_layout.py` (légende, flip Y).
  Suite totale : **33 tests** verts.

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
