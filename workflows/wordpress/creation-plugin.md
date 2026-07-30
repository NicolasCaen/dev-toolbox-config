# Workflow de création de plugin WordPress

## Principes généraux
- **Auteur par défaut**
  Utiliser `Author: GEHIN Nicolas` dans l’en-tête du plugin.
- **Version initiale**
  Lors de la création, définir `Version: 0.1.0`.
- **Le nom du plugin**
  le nom du plugin devra toujours être prefixer par up-
- **Fichier README**
  Créer un `README.md` à la racine du plugin contenant au minimum un bloc **Description**, un bloc **Installation** et un bloc **Changelog**.
- **Mise à jour systématique**
  À chaque évolution du plugin, mettre à jour à la fois la version dans l’en-tête principal et le changelog du `README.md`.

## Étapes de création
- **[Préparer le dossier]**
  Créer un dossier `wp-content/plugins/mon-plugin/` (remplacer `mon-plugin` par le slug souhaité).
- **[Fichier principal]**
  Ajouter `mon-plugin.php` avec l’en-tête standard :
  ```php
  <?php
  /**
   * Plugin Name: Mon Plugin
   * Description: Résumé court.
   * Version: 0.1.0
   * Author: GEHIN Nicolas
   */
  ```
- **[README initial]**
  Créer `README.md` avec la structure suivante :
  ```markdown
  # Mon Plugin

  ## Description
  Décrire la finalité.

  ## Installation
  1. Télécharger le plugin.
  2. Le déposer dans `wp-content/plugins/`.
  3. L’activer dans l’administration WordPress.

  ## Changelog
  - 2025-01-01 · v0.1.0 · Création du plugin.
  ```
- **[Organisation complémentaire]**
  Ajouter les sous-dossiers nécessaires (`/assets`, `/includes`, etc.) et préparer le bootstrap minimal.

## Règles de versioning
Le schéma suit quatre niveaux `MAJEUR.MINOR.FONCTION.PATCH`. Lors de la création, seul `v0.1.0` est affiché, mais la logique d’évolution repose sur les quatre segments.
- **Nouvelle fonctionnalité**
  Incrémenter le segment *FONCTION* : `v0.1.0` → `v0.1.1.0`, puis `v0.1.2.0`, etc.
- **Grosse nouvelle fonctionnalité / refonte**
  Incrémenter le segment *MINOR* : `v0.1.2.0` → `v0.2.0.0`.
- **Correction de bug ou itération mineure**
  Incrémenter le segment *PATCH* : `v0.1.2.0` → `v0.1.2.1`, `v0.1.2.2`, etc.
- **Refonte majeure**
  Lorsque le plugin change radicalement, incrémenter le segment *MAJEUR* : `v0.2.3.4` → `v1.0.0.0`.

> Astuce : lors de l’édition de l’en-tête, afficher seulement les segments non nuls pour conserver des versions lisibles (ex. `0.1.0`, `0.1.2.0`, `0.2.0.0`).

## Gestion du changelog
- **[Nouvelle entrée]**
  Ajouter une ligne ou un bloc daté pour chaque modification, en suivant un format constant (`YYYY-MM-DD · vX.Y.Z.W · Résumé` ou en sections Markdown).
- **[Lien avec la version]**
  Chaque entrée de changelog doit correspondre à une version incrémentée selon les règles ci-dessus.
- **[Transparence]**
  Mentionner les principales nouveautés, corrections et améliorations pour faciliter le suivi des évolutions.

## Checklist rapide
- **[ ]** Créer le dossier et le fichier principal avec l’en-tête standard.
- **[ ]** Initialiser `README.md` avec sections Description, Installation, Changelog.
- **[ ]** Définir la version initiale à `0.1.0` et l’auteur à `GEHIN Nicolas`.
- **[ ]** Mettre à jour version + changelog à chaque nouvelle fonctionnalité, correction ou refonte.
- **[ ]** Respecter la logique `MAJEUR.MINOR.FONCTION.PATCH` pour les incréments.
---
description: Création de plugin
auto_execution_mode: 1
---
