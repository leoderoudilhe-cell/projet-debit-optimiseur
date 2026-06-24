# Optimiseur de débit — Brief de démarrage projet

> **Pour Claude Code.** Ce dossier contient tout le contexte nécessaire pour démarrer le développement. Lis les fichiers dans cet ordre :
> 1. `00-README-DEMARRAGE.md` (ce fichier) — vue d'ensemble et objectif
> 2. `docs/01-SPEC-FONCTIONNELLE.md` — ce que l'outil doit faire, précisément
> 3. `docs/02-DA-CHARTE-GRAPHIQUE.md` — direction artistique, couleurs, typographies
> 4. `docs/03-ROADMAP.md` — ordre de construction, priorités
> 5. `docs/04-STACK-TECHNIQUE.md` — choix techniques et architecture
> 6. `maquette-reference/maquette.html` — référence visuelle HTML à utiliser comme base de design
> 7. `exemple-donnees/` — exemple réel de fiche de débit Cadwork (export à coller ici avant de lancer le projet)

---

## Le projet en une phrase

Un outil web pour optimiser le débit de panneaux bois (calepinage), destiné à un menuisier (Tom) qui travaille en atelier de fabrication mobilier en série, pour remplacer un calcul actuellement fait à la main / sur Cadwork avec des corrections manuelles fastidieuses.

## Le problème réel à résoudre

Tom a accès à Cadwork (logiciel CFAO bois) mais son module d'optimisation de débit propose des calepinages qu'il doit reprendre à la main — l'algorithme n'est pas assez pertinent sur ce cas d'usage précis (gestion du fil du bois, regroupement de pièces, minimisation de chute). 

**On ne cherche pas à remplacer Cadwork dans sa globalité** (modélisation 3D, structure bois, etc.) — uniquement à proposer un calcul de calepinage plus juste et plus rapide, avec une interface minimaliste : coller le débit, cliquer, obtenir un résultat exploitable directement en atelier, sans retouche manuelle.

## Qui l'utilise, et comment

- **Utilisateur unique pour l'instant** : Tom, sur PC fixe à l'atelier, via navigateur web
- **Pas de contrainte hors-ligne** — connexion internet disponible
- **Usage attendu** : ouvrir l'outil, coller un tableau de débit, cliquer "Optimiser", récupérer 2 PDF (récap + plans de calepinage), les imprimer pour l'atelier

## Contrainte non négociable : le sens du fil du bois

C'est le cœur technique du projet et la raison d'être de l'outil :

- **Bois massif / simili-massif** (placage, stratifié à fil visible) → la pièce ne peut PAS pivoter à 90°. Sa plus grande longueur doit être alignée avec le sens du fil du panneau.
- **Tout autre matériau** (MDF brut, mélaminé sans fil visible, etc.) → rotation libre à 90° autorisée pour optimiser le placement.

Aucune librairie d'optimisation de bin-packing 2D standard ne gère ça nativement (vérifié en veille — voir `docs/01-SPEC-FONCTIONNELLE.md` section "Recherche & limites"). C'est une couche à coder par-dessus le moteur de packing.

## Ce qui n'est PAS dans le scope V1

- Pas d'édition de projet après export (l'historique est en lecture seule, retéléchargement uniquement)
- Pas de gestion multi-utilisateurs / comptes
- Pas d'export machine CNC / post-processeur
- Pas de gestion de stock de chutes entre débits différents — l'outil ne classe pas les chutes en "réutilisable" ou "déchet", il affiche juste la zone non utilisée ; c'est à l'atelier de juger sur place ce qu'il en fait
- Pas d'étiquettes individuelles à découper-coller — les dimensions sont annotées directement sur le plan de calepinage

## État d'avancement au moment de la transmission

- ✅ Spec fonctionnelle validée avec le commanditaire (voir doc dédié)
- ✅ Direction artistique validée (voir doc dédié)
- ✅ Maquette HTML statique validée comme référence visuelle
- ⏳ **Format exact d'export Cadwork pas encore confirmé** — un exemple réel doit être déposé dans `exemple-donnees/` avant de coder le parseur d'import. Si ce dossier est vide, demander l'exemple avant d'écrire la logique de parsing, ne pas deviner le format.

## Comment travailler sur ce projet

Procède par étapes courtes et valide chaque brique avant de passer à la suite plutôt que de tout générer d'un coup :
1. Setup projet (stack, structure de dossiers, dépendances)
2. Moteur de calcul (packing + contrainte fil du bois) — **teste-le isolément avec des données factices avant de toucher à l'UI**
3. Parsing de l'import (une fois l'exemple réel disponible)
4. Génération des 2 PDF de sortie
5. Interface web (basée sur la maquette fournie)
6. Historique des exports

Pose des questions si un point de la spec semble ambigu ou contradictoire plutôt que de supposer — ce projet a été cadré avec une exigence de précision élevée, pas d'approximation bienvenue.
