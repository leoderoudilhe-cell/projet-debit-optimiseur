# Stack technique

## Choix retenus

| Composant | Choix | Pourquoi |
|---|---|---|
| Backend | Python — FastAPI | Permet d'utiliser rectpack directement, écosystème PDF mature, léger |
| Moteur de calcul | `rectpack` (PyPI) | Librairie de bin-packing 2D mature, testée, gère Skyline/MaxRects/Guillotine. Voir limites notées dans la spec fonctionnelle. |
| Génération PDF | ReportLab ou WeasyPrint | À trancher en développement selon la facilité de contrôle fin du rendu (positionnement précis des rectangles + texte adaptatif) |
| Frontend | Application web simple (HTML/JS, ou framework léger si Claude Code le juge pertinent) | Usage desktop unique, pas besoin de complexité |
| Base de données | PostgreSQL | Pour les métadonnées d'historique (nom projet, date, liens fichiers) |
| Stockage fichiers PDF | Volume Railway ou stockage objet simple | Pas besoin de complexité S3 à ce stade, un stockage disque suffit pour le volume d'usage attendu |
| Hébergement | Railway | Cohérent avec l'infra existante du commanditaire (autre projet bot déjà hébergé là-bas) |

## Pas de contraintes
- Pas de besoin offline / hors-ligne
- Utilisateur unique pour l'instant — pas de système d'authentification multi-utilisateur nécessaire en V1 (à voir si un accès basique par mot de passe simple est suffisant pour éviter un accès public non désiré, étant donné que ce sera hébergé sur une URL Railway accessible)

## Note sur la dépendance critique : rectpack + contrainte de rotation mixte

Avant de t'engager sur l'architecture finale du module de calcul, valide rapidement (avec un script de test isolé, pas en intégration complète) que l'approche "deux passes" décrite dans la spec fonctionnelle fonctionne bien avec rectpack — sinon il faudra peut-être évaluer une alternative ou une modification plus profonde de la logique de packing. Ne pas découvrir ce blocage potentiel après avoir construit toute l'UI autour.
