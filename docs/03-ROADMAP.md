# Roadmap

## Étape 0 — Prérequis avant de coder quoi que ce soit
- [ ] Exemple réel de fiche de débit Cadwork déposé dans `exemple-donnees/`
- [ ] Confirmer le mapping de colonnes réel vs. l'hypothèse posée dans la spec fonctionnelle

**Ne pas commencer le développement du parseur d'import avant d'avoir cet exemple.** Le reste du projet (moteur de calcul, PDF, UI) peut démarrer en parallèle avec des données factices.

## Étape 1 — Setup projet
- Structure du repo (backend / frontend séparés ou monorepo léger, au choix de Claude Code selon la stack retenue)
- Dépendances de base installées (voir `04-STACK-TECHNIQUE.md`)
- Un "hello world" qui tourne en local et déployable sur Railway dès le début (éviter de découvrir des problèmes de déploiement à la fin)

## Étape 2 — Moteur de calcul (cœur du projet, priorité absolue)
- Implémenter le bin-packing 2D avec rectpack sur des données factices (un débit simple inventé, pas besoin du vrai format encore)
- Implémenter la couche de contrainte fil du bois par-dessus
- **Tester unitairement ce module isolément avant de toucher à l'UI** — c'est la partie la plus risquée techniquement, elle doit être validée seule
- Implémenter le regroupement par épaisseur/matériau
- Implémenter le calcul de taux de chute (pas de classification réutilisable/déchet — toute zone non utilisée est simplement « chute », point final)

## Étape 3 — Parsing de l'import (une fois l'exemple Cadwork disponible)
- Écrire le parseur sur la base du format réel, pas de l'hypothèse
- Implémenter la détection automatique du fil obligatoire par mot-clé matériau
- Permettre la correction manuelle pièce par pièce avant calcul

## Étape 4 — Génération PDF
- Document 1 (fiche récap) — le plus simple des deux, à faire en premier
- Document 2 (plans de calepinage) — implémenter d'abord le rendu simple (texte toujours dans le rectangle), puis ajouter la logique de bascule en légende quand le texte ne rentre pas
- Tester le rendu sur plusieurs tailles de pièces différentes (très petites, très grandes, ratios extrêmes) pour valider que la bascule légende fonctionne dans tous les cas, pas seulement le cas de démo

## Étape 5 — Interface web
- Écran principal (collage + bouton Optimiser) sur la base de la maquette fournie
- Écran de résultat avec stats + aperçu + export
- Respecter la charte graphique (`02-DA-CHARTE-GRAPHIQUE.md`)

## Étape 6 — Historique
- Stockage des métadonnées d'export (nom projet, date) + fichiers PDF générés
- Page de consultation en lecture seule

## Étape 7 — Déploiement Railway
- Variables d'environnement, base de données Postgres provisionnée
- Test de bout en bout en conditions réelles

## Hors scope V1 — pistes pour plus tard, ne pas anticiper dans le code actuel
- Regroupement des pièces adjacentes pour continuité visuelle du fil (façades de tiroirs, etc.)
- Gestion de stock de chutes réutilisables dans le temps (entre plusieurs débits)
- Export machine / post-processeur CNC
- Comptes utilisateurs multiples
