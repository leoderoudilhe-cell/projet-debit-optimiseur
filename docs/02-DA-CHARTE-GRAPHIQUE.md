# Direction artistique — Charte graphique

## Intention générale

L'esthétique doit servir la lisibilité industrielle, pas la décoration. Cet outil est utilisé par un menuisier sur un PC d'atelier — l'interface doit lire comme un **plan technique**, pas comme une application SaaS générique. Référentiel : vocabulaire visuel du calepinage, de la cotation, du plan de coupe.

Éviter explicitement les trois patterns visuels par défaut de la génération d'interface actuelle (fond crème + serif + terracotta / fond noir + accent acide unique / style "broadsheet" journalistique) sauf si le résultat ci-dessous y ressemble par nécessité fonctionnelle plutôt que par défaut.

## Palette

| Rôle | Couleur | Hex |
|---|---|---|
| Fond principal (UI) | Anthracite atelier | `#1C1E1B` |
| Fond secondaire (panneaux, cartes) | Anthracite clair | `#24271F` |
| Fond zone "papier" (plans, fiches) | Blanc cassé papier | `#F5F3EE` |
| Bordures zone papier | Beige ligne | `#D8D3C4` |
| Accent principal (actions, focus) | Chêne clair | `#D9A066` |
| Accent profond (texte sur fond clair) | Chêne profond | `#B97F3F` |
| Texte sur fond sombre | Blanc cassé | `#F5F3EE` |
| Texte secondaire / discret | Gris atelier | `#9A9C92` |
| Alerte / erreur | Rouge brique sobre | `#C44536` |
| Validation / état positif | Vert sauge | `#5C8A6E` |

**Règle d'usage :** l'accent chêne (`#D9A066`) est réservé aux actions et aux éléments de données mises en avant (chiffres clés). Ne pas l'utiliser en décoration. Le rouge est strictement réservé aux alertes/erreurs, jamais en décoration ou en accent neutre.

## Typographie

| Rôle | Police | Usage |
|---|---|---|
| Display / titres / cotes / chiffres | **Space Mono** (700) | Titres de section, valeurs chiffrées dans les stats, en-têtes de plans, tout ce qui doit lire comme une donnée technique ou une cote de plan |
| Corps de texte / UI | **Inter** (400, 500, 600) | Labels, descriptions, navigation, contenu courant |

**Pourquoi une mono pour les titres et les chiffres** : ça crée immédiatement une association visuelle avec les outils de mesure et les plans techniques — cohérent avec le métier — plutôt qu'une typo display classique qui évoquerait un produit grand public.

Source : Google Fonts — `Space+Mono:wght@400;700` et `Inter:wght@400;500;600;700`.

## Layout

- Structure simple, une colonne centrale max-width ~1180px, pas de grille marketing complexe
- Barre de navigation haute, minimale : marque + 3 entrées (Nouveau débit / Historique / Réglages)
- Les "stats" de résultat (panneaux utilisés, taux de chute, etc.) en cartes courtes alignées horizontalement, valeur en Space Mono 700 + label discret en dessous
- Les documents de sortie (fiche récap, plans de calepinage) sont rendus comme des "feuilles" visuellement distinctes du reste de l'UI : fond papier clair contrastant avec le fond sombre de l'appli, ratio A4 paysage, ombre portée légère pour suggérer une feuille physique posée sur l'écran

## Signature visuelle

L'élément mémorable de cet outil n'est pas une icône ou une illustration : **c'est le plan de calepinage lui-même**, rendu fidèlement, coté, avec :
- Pièces en aplat chêne clair semi-transparent
- Hachures fines diagonales superposées sur les pièces à fil de bois obligatoire (signal visuel direct, sans avoir besoin de lire un texte pour comprendre la contrainte)
- Chutes en hachures croisées grises, distinctes visuellement des pièces utiles
- Texte des cotes en Space Mono, dans le rectangle si la place le permet, sinon bascule en numéro + légende (voir spec fonctionnelle, section 3)

## Référence de rendu

Voir `maquette-reference/maquette.html` pour l'implémentation concrète de cette charte (CSS inclus, prêt à être repris comme base ou inspiration directe pour les composants réels).

## Ce qui n'est pas figé / marge d'amélioration laissée à Claude Code

- La maquette HTML fournie est une preuve d'intention, pas un design system complet — composants interactifs (états hover, focus clavier visible, responsive mobile) à construire proprement même si l'usage principal est desktop atelier
- Liberté sur les micro-interactions (transitions, feedback de chargement pendant le calcul) tant que l'esprit "outil technique sobre" est respecté — éviter toute animation décorative superflue
