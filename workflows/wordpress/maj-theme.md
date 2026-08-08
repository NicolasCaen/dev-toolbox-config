# Workflow de mise à jour de thème WordPress

## Principes généraux
- **Fichiers concernés**
  La version du thème est définie dans **deux** fichiers qui doivent rester synchronisés :
  - `style.css` (en-tête du thème, ligne `Version:`)
  - `assets/scss/style.scss` (en-tête source SCSS, ligne `Version:`)
- **Changelog**
  À chaque mise à jour, ajouter une entrée datée dans la section `## Changelog` du `README.md` du thème.
- **Cohérence**
  La version affichée dans `style.css`, `style.scss` et le changelog du `README.md` doit être identique.

## Étapes de mise à jour
- **[Identifier le type de mise à jour]**
  Déterminer le segment à incrémenter selon les règles de versioning (voir ci-dessous).
- **[Bumper la version dans `style.css`]**
  Modifier la ligne `Version: X.Y.Z.W` dans l'en-tête du fichier `style.css` à la racine du thème.
- **[Bumper la version dans `style.scss`]**
  Modifier la ligne `Version: X.Y.Z.W` dans l'en-tête du fichier `assets/scss/style.scss`.
- **[Mettre à jour le changelog]**
  Ajouter une ligne dans la section `## Changelog` du `README.md` au format :
  ```
  - YYYY-MM-DD · vX.Y.Z.W · Résumé de la modification.
  ```
- **[Recompiler si nécessaire]**
  Si des modifications SCSS ont été faites, recompiler `style.css` à partir de `assets/scss/style.scss`.

## Règles de versioning
Le schéma suit quatre niveaux `MAJEUR.MINOR.FONCTION.PATCH`.
- **Nouvelle fonctionnalité**
  Incrémenter le segment *FONCTION* : `v0.1.0` → `v0.1.1.0`, puis `v0.1.2.0`, etc.
- **Grosse nouvelle fonctionnalité / refonte**
  Incrémenter le segment *MINOR* : `v0.1.2.0` → `v0.2.0.0`.
- **Correction de bug ou itération mineure**
  Incrémenter le segment *PATCH* : `v0.1.2.0` → `v0.1.2.1`, `v0.1.2.2`, etc.
- **Refonte majeure**
  Lorsque le thème change radicalement, incrémenter le segment *MAJEUR* : `v0.2.3.4` → `v1.0.0.0`.

> Astuce : lors de l'édition de l'en-tête, afficher seulement les segments non nuls pour conserver des versions lisibles (ex. `0.1.0`, `0.1.2.0`, `0.2.0.0`).

## Gestion du changelog
- **[Nouvelle entrée]**
  Ajouter une ligne datée pour chaque modification, au format `YYYY-MM-DD · vX.Y.Z.W · Résumé`.
- **[Lien avec la version]**
  Chaque entrée de changelog doit correspondre à la version incrémentée dans `style.css` et `style.scss`.
- **[Transparence]**
  Mentionner les principales nouveautés, corrections et améliorations pour faciliter le suivi des évolutions.

## Checklist rapide
- **[ ]** Identifier le type de mise à jour (fonction, minor, patch, majeur).
- **[ ]** Bumper la version dans `style.css`.
- **[ ]** Bumper la version dans `assets/scss/style.scss` (version identique).
- **[ ]** Ajouter une entrée datée dans la section `## Changelog` du `README.md`.
- **[ ]** Recompiler le SCSS si des modifications de styles ont été faites.
- **[ ]** Vérifier la cohérence des versions entre les trois fichiers.
---
description: Mise à jour de thème
auto_execution_mode: 1
---
