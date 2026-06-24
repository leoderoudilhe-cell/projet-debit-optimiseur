# Spec fonctionnelle — Optimiseur de débit

## 1. Entrée

### Source
Copier-coller direct depuis une fiche de débit Cadwork, ou import CSV/Excel équivalent.

⚠️ **Format exact non confirmé à ce stade.** Hypothèse de travail tant que l'exemple réel n'est pas fourni :

| Colonne | Description |
|---|---|
| N° LP | Numéro de position (identifiant unique de la pièce dans le débit) |
| Longueur | en mm |
| Largeur | en mm |
| Épaisseur | en mm |
| Matériau / essence | texte libre (ex. "Chêne massif", "Mélaminé blanc") |
| Quantité | nombre d'occurrences de cette pièce |

**Avant de coder le parseur définitif : comparer cette hypothèse à l'exemple réel déposé dans `exemple-donnees/`. Adapter le mapping de colonnes si nécessaire — ne pas forcer les vraies données dans ce moule si elles diffèrent.**

### Détection automatique du fil obligatoire
- Si une colonne dédiée existe dans l'export réel → l'utiliser directement.
- Sinon, déduire par mot-clé sur le champ matériau :
  - Fil obligatoire (pas de rotation) : "chêne", "hêtre", "noyer", "frêne", "placage", et toute essence de bois massif identifiable
  - Rotation libre : "MDF", "mélaminé", "stratifié sans fil", "contreplaqué brut"
- Dans tous les cas, **correction manuelle possible pièce par pièce** dans l'interface avant calcul (au cas où la détection automatique se trompe).

## 2. Moteur de calcul

### Base technique
Utiliser la librairie **rectpack** (Python) comme moteur de bin-packing 2D. Elle implémente trois familles d'algorithmes (Skyline, MaxRects, Guillotine) pour le placement de rectangles dans un nombre minimal de bacs (= panneaux).

📌 **Limite connue, vérifiée par recherche** : rectpack ne gère pas nativement de contrainte de rotation par pièce — son paramètre de rotation est global (autorisée ou interdite pour tout le run), pas individuel. Cette contrainte doit être ajoutée comme couche logique au-dessus de la librairie.

### Couche maison à coder : contrainte de fil du bois
- Avant l'appel à rectpack, séparer les pièces en deux groupes : `fil_obligatoire` et `rotation_libre`.
- Pour les pièces `fil_obligatoire` : fixer leur orientation (grande longueur = sens du fil du panneau) et les passer à rectpack avec rotation désactivée pour ce sous-groupe.
- Pour les pièces `rotation_libre` : autoriser la rotation à 90° normalement.
- **Point d'incertitude technique à valider en développement** : rectpack ne permet probablement pas de mixer ces deux comportements dans un seul run sur un même bac. Il faudra peut-être : (a) placer d'abord les pièces à fil obligatoire dans une passe contrainte, (b) combler les espaces restants avec les pièces à rotation libre dans une seconde passe. À tester et ajuster — ne pas supposer que ça fonctionnera du premier coup.

### Règles dimensionnelles fixes
- Panneau standard par défaut : **2800 × 2070 mm** (modifiable dans les réglages avancés)
- Épaisseur de lame de scie (kerf) : **3 mm**, à intégrer comme espacement entre chaque pièce adjacente
- Marge de bord de panneau : **5 mm sur chaque côté** (zone non utilisable, à soustraire de la surface exploitable avant calcul)
- Alignement : la **plus grande longueur des pièces s'aligne en haut du panneau**, parce que la machine de l'atelier coupe d'abord en bandes (sens horizontal) puis refend ensuite — donc l'algorithme de placement doit privilégier des bandes horizontales cohérentes plutôt qu'un placement totalement libre, même quand ça n'est pas l'optimum mathématique pur de chute.

### Regroupement
- **Jamais de mélange d'épaisseur ou de matériau sur un même panneau.** Grouper les pièces par couple (épaisseur, matériau) avant de lancer le calcul, et traiter chaque groupe comme un sous-problème de bin-packing indépendant.
- Si un groupe nécessite plusieurs panneaux, le moteur détermine automatiquement le nombre de panneaux requis.

### Chutes
- Toute zone de panneau non utilisée après placement de toutes les pièces du groupe = chute, point final.
- **Aucune distinction réutilisable / déchet à faire.** L'outil n'évalue pas si une chute est exploitable ou non — c'est à l'atelier de juger sur place s'ils gardent un reste ou pas. Ne pas implémenter de seuil de taille ni de classification.
- Calculer un taux de chute = (surface chute / surface panneau total utilisé) × 100, par panneau et en cumulé sur tout le débit.

## 3. Sortie — deux documents PDF distincts

### Document 1 : Fiche récapitulative (1 page)
Contenu :
- Nom du projet (si saisi) + date
- Liste complète des pièces du débit (n° LP, dimensions, épaisseur, matériau, quantité)
- Nombre de panneaux utilisés, regroupés par couple épaisseur/matériau
- Taux de chute global et métrage de matière consommée (m²)

### Document 2 : Plans de calepinage (1 page A4 par panneau)
Pour chaque panneau utilisé, une page contenant :
- En-tête : numéro du panneau (ex. "Panneau 1/3"), matériau, épaisseur, dimensions du panneau
- Indicateur visuel si le panneau est en "fil obligatoire" (tag visible)
- Schéma coté à l'échelle du panneau avec chaque pièce placée
- Sur chaque pièce : son n° de position + ses dimensions (L × l), affichés **à l'intérieur du rectangle**

**Règle d'affichage texte dans les rectangles — comportement à coder précisément :**
1. Calculer si le texte (n° + dimensions) tient dans le rectangle de la pièce avec une police lisible à l'impression (seuil minimum proposé : **6pt**), sans chevauchement avec le bord de la pièce ni les pièces voisines.
2. Si oui → afficher le texte complet dans le rectangle, en ajustant la taille de police au maximum disponible dans la limite du rectangle (police adaptative, pas une taille fixe).
3. Si non (texte ne rentre pas proprement même à la police minimale, ou chevauchement) → basculer en **mode légende** : le rectangle affiche uniquement le n° de position en grand, et une légende en bas de page liste la correspondance n° → dimensions pour toutes les pièces concernées par ce mode dégradé sur cette page.
4. Ce calcul se fait **pièce par pièce**, pas globalement pour toute la page — certaines pièces d'un même panneau peuvent afficher leurs cotes en entier, d'autres basculer en légende, selon leur taille individuelle.

- Zones de chute clairement identifiées visuellement sur le schéma (distinctes des pièces placées).
- Indication visuelle du sens du fil sur les pièces concernées (ex. hachures fines dans la direction du fil).

### Pas d'étiquettes individuelles
Aucun document d'étiquettes séparées à imprimer/découper/coller. Toute l'information nécessaire à l'atelier est sur le plan de calepinage lui-même.

## 4. Interface utilisateur

### Écran principal
- Champ "Nom du projet" (texte libre, optionnel)
- Zone de collage du tableau de débit (zone de texte large acceptant un copier-coller direct depuis Cadwork/Excel)
- Réglages avancés repliés par défaut (panneau standard, lame, marge — modifiables si besoin, mais invisibles à l'écran principal pour ne pas surcharger l'utilisateur)
- Un seul bouton d'action : **Optimiser**

### Écran de résultat
- Indicateurs clés visibles immédiatement : nombre de panneaux utilisés, taux de chute global, nombre de matériaux distincts, nombre de pièces placées
- Aperçu visuel de la fiche récap et des plans de calepinage
- Bouton d'export / téléchargement des 2 PDF

### Historique
- Page séparée listant les exports précédents
- Chaque entrée : nom de projet (si saisi, sinon date/heure automatique), date, lien de retéléchargement des PDF générés
- **Lecture seule** — pas de modification, pas de relance de calcul depuis l'historique. Pour modifier un débit, l'utilisateur recolle et relance un nouveau calcul, qui crée une nouvelle entrée d'historique.

## 5. Recherche & limites (contexte de cadrage, pas à reproduire dans le code)

Veille effectuée avant de cadrer ce projet :
- Les logiciels du marché (OptiCoupe, Cutlist Plus, CutList Optimizer, SmartCut) gèrent tous nativement le sens du fil, la largeur de lame et l'export atelier — ce sont des fonctionnalités standards du secteur, pas avancées.
- OptiCoupe regroupe les pièces adjacentes (ex. façades de tiroirs) pour garantir la continuité visuelle du fil au moment de la découpe — fonctionnalité avancée non incluse dans le scope V1, mais à garder en tête comme piste d'évolution.
- Aucun solveur de production, commercial ou open source, ne gère élégamment le bin-packing 2D avec contrainte de rotation mixte par défaut — confirmé par la documentation technique de plusieurs solveurs (OptaPlanner, etc.). C'est pour ça qu'une couche maison est nécessaire plutôt qu'une simple option de configuration existante.
- La librairie **rectpack** a un cas d'usage documenté de découpe de pièces rectangulaires sur panneaux CNC — c'est une base solide et testée, mais sans gestion de fil de bois native.
