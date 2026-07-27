---
description: Workflow de déploiement standard
---

# Déploiement de {{projectName}}

## Étapes

1. Vérifier que la branche `main` est à jour
2. Lancer les tests : `npm run check`
3. Build : `npm run compile`
4. Créer le tag : `git tag v{{version}}`
5. Pousser le tag : `git push origin v{{version}}`

## Informations

- **Auteur** : {{author}}
- **Date** : {{date}}
- **Workspace** : {{workspaceName}}
