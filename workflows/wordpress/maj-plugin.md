# Workflow de mise à jour d'un plugin WordPress

## Principes généraux
- **Auteur**
  Conserver `Author: GEHIN Nicolas` dans l'en-tête du plugin (ne pas modifier sauf changement explicite de propriétaire).
- **Nom du plugin**
  Vérifier que le nom conserve le préfixe `up-` (ne pas renommer sans raison explicite).
- **Fichier README**
  S'assurer que `README.md` existe toujours à la racine avec les blocs **Description**, **Installation** et **Changelog**. Le créer s'il est manquant, en reconstituant l'historique depuis les commentaires du code ou l'en-tête si possible.
- **Mise à jour systématique**
  Toute évolution du plugin implique obligatoirement :
  1. l'incrémentation de la version dans l'en-tête principal,
  2. l'ajout d'une entrée correspondante dans le changelog du `README.md`.
  Aucune modification fonctionnelle ne doit être livrée sans ces deux mises à jour.

## Étapes de mise à jour
- **[Identifier la version actuelle]**
  Lire la ligne `Version:` dans l'en-tête du fichier principal du plugin pour connaître le point de départ.
- **[Déterminer la nature du changement]**
  Qualifier la modification à apporter : nouvelle fonctionnalité, grosse fonctionnalité/refonte partielle, correction de bug, ou refonte majeure (voir *Règles de versioning*).
- **[Appliquer les modifications]**
  Développer/corriger le code dans les fichiers concernés (`/includes`, `/assets`, fichier principal, etc.).
- **[Mettre à jour l'en-tête]**
  Modifier la ligne `Version:` du fichier principal selon la règle d'incrément correspondante.
- **[Mettre à jour le README]**
  Ajouter une nouvelle entrée datée dans la section **Changelog**, avec le même numéro de version que l'en-tête.
- **[Vérification finale]**
  Contrôler la cohérence : version identique entre l'en-tête et le changelog, description à jour si la finalité du plugin a évolué, instructions d'installation toujours valides.

## Règles de versioning
Le schéma suit quatre niveaux `MAJEUR.MINOR.FONCTION.PATCH`.
- **Nouvelle fonctionnalité**
  Incrémenter le segment *FONCTION* : `v0.1.0` → `v0.1.1.0`, puis `v0.1.2.0`, etc.
- **Grosse nouvelle fonctionnalité / refonte partielle**
  Incrémenter le segment *MINOR* : `v0.1.2.0` → `v0.2.0.0`.
- **Correction de bug ou itération mineure**
  Incrémenter le segment *PATCH* : `v0.1.2.0` → `v0.1.2.1`, `v0.1.2.2`, etc.
- **Refonte majeure**
  Lorsque le plugin change radicalement, incrémenter le segment *MAJEUR* : `v0.2.3.4` → `v1.0.0.0`.

> Astuce : afficher seulement les segments non nuls pour conserver des versions lisibles (ex. `0.1.0`, `0.1.2.0`, `0.2.0.0`).

## Gestion du changelog
- **[Nouvelle entrée]**
  Ajouter une ligne ou un bloc daté pour chaque mise à jour, en respectant le format déjà utilisé dans le fichier (`YYYY-MM-DD · vX.Y.Z.W · Résumé` ou sections Markdown).
- **[Lien avec la version]**
  Chaque entrée de changelog doit correspondre exactement à la version affichée dans l'en-tête après modification.
- **[Transparence]**
  Résumer clairement ce qui a changé (ajout, correction, suppression, refonte) pour faciliter le suivi par les autres contributeurs.
- **[Non-régression]**
  Ne jamais supprimer ou réécrire les entrées précédentes du changelog : uniquement ajouter de nouvelles entrées.

## Checklist rapide
- **[ ]** Identifier la version actuelle dans l'en-tête du fichier principal.
- **[ ]** Qualifier la nature du changement (fonctionnalité, refonte, correction, refonte majeure).
- **[ ]** Appliquer les modifications de code nécessaires.
- **[ ]** Incrémenter la version dans l'en-tête selon la bonne règle.
- **[ ]** Ajouter une entrée datée et versionnée dans le changelog du `README.md`.
- **[ ]** Vérifier la cohérence version/changelog/description avant de considérer la mise à jour terminée.
---
description: Mise à jour de plugin
auto_execution_mode: 1
---