# Dev Toolbox Config

Dépôt de configuration pour l'extension VS Code **Dev Toolbox**. Contient les ressources personnelles : workflows, templates, snippets et documentation.

## Installation

1. Cloner ce dépôt.
2. Dans VS Code (ou Devin), ouvrir les **Settings** et configurer les chemins absolus :

```json
{
    "devToolbox.workflowsDirectory": "/chemin/vers/dev-toolbox-config/workflows",
    "devToolbox.templatesDirectory": "/chemin/vers/dev-toolbox-config/templates",
    "devToolbox.snippetsDirectory": "/chemin/vers/dev-toolbox-config/snippets",
    "devToolbox.documentationDirectory": "/chemin/vers/dev-toolbox-config/documentation",
    "devToolbox.author": "Votre Nom"
}
```

3. L'icône **Dev Toolbox** dans la barre d'activité donne accès à toutes les ressources.

---

## Structure

```
dev-toolbox-config/
├── workflows/          → Fichiers Markdown de workflows
├── templates/          → Templates de projets (un sous-dossier par template)
├── snippets/           → Snippets de code au format JSON VS Code
├── documentation/      → Documentation en Markdown
└── plugins/            → Réservé pour les plugins futurs
```

---

## Workflows

### Emplacement

`workflows/`

### Format

Fichiers `.md` organisés en sous-dossiers. Chaque sous-dossier devient une **catégorie** automatiquement.

### Variables disponibles

| Variable         | Description                          | Source                              |
|------------------|--------------------------------------|-------------------------------------|
| `{{author}}`     | Auteur                               | Setting `devToolbox.author`         |
| `{{version}}`    | Version                              | Setting `devToolbox.initialVersion` |
| `{{date}}`       | Date du jour (format ISO)            | Automatique                         |
| `{{year}}`       | Année courante                       | Automatique                         |
| `{{workspaceName}}` | Nom du workspace VS Code          | Automatique                         |
| `{{projectName}}`   | Nom du projet/dossier cible       | Automatique                         |

### Exemple

`workflows/deploy/deploy-workflow.md` :

```markdown
---
description: Workflow de déploiement standard
---

# Déploiement de {{projectName}}

1. Vérifier que la branche `main` est à jour
2. Lancer les tests : `npm run check`
3. Build : `npm run compile`
4. Créer le tag : `git tag v{{version}}`

- **Auteur** : {{author}}
- **Date** : {{date}}
```

### Utilisation

- **Clic droit** sur un dossier dans l'Explorer → **Dev Toolbox: Ajouter un workflow**
- Ou via la **Command Palette** (`Cmd+Shift+P`) → **Dev Toolbox: Ajouter un workflow**
- Le fichier rendu est écrit dans `.devin/workflows/` du projet cible

---

## Templates

### Emplacement

`templates/`

### Format

Un **sous-dossier par template**. Tout ce qui est dans le sous-dossier fait partie du template. L'arborescence complète est recopiée lors de la création.

### Variables disponibles

Mêmes variables que les workflows (`{{author}}`, `{{version}}`, `{{date}}`, `{{year}}`, `{{workspaceName}}`, `{{projectName}}`). Les variables sont remplacées dans :
- Le contenu des fichiers texte (UTF-8)
- Les chemins relatifs
- Les fichiers binaires sont copiés **sans modification**

### Exemple

```
templates/
└── vite-react/
    ├── package.json      → {{projectName}}, {{version}}, {{author}}
    ├── index.html        → {{projectName}}
    └── src/
        └── main.tsx      → {{projectName}}, {{author}}
```

`templates/vite-react/package.json` :

```json
{
  "name": "{{projectName}}",
  "version": "{{version}}",
  "author": "{{author}}",
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  }
}
```

### Utilisation

- **Clic droit** sur un dossier de destination → **Dev Toolbox: Créer un template**
- Ou via la **Command Palette** → **Dev Toolbox: Créer un template**
- Chaque variable manquante est demandée une seule fois

---

## Snippets

### Emplacement

`snippets/`

### Format

Fichiers `.json` au format snippet VS Code. Organisés en sous-dossiers :
- Le sous-dossier devient la **catégorie**
- Le nom du sous-dossier définit le **langage par défaut** (ex: `php/` → langage `php`)

### Structure d'un snippet

```json
{
  "Nom du snippet": {
    "prefix": "raccourci",
    "body": "Code avec ${1:placeholder} et ${2:tab}.",
    "description": "Description affichée dans la QuickPick",
    "scope": "javascript,typescript"
  }
}
```

### Champs

| Champ           | Requis | Description                                                                 |
|-----------------|--------|-----------------------------------------------------------------------------|
| `prefix`        | Non    | Raccourci(s) déclencheur(s). String ou tableau.                             |
| `body`          | Oui    | Corps du snippet. String ou tableau de lignes. Supporte `${1:label}`, `$0`.|
| `description`   | Non    | Description humaine affichée dans la QuickPick.                             |
| `scope`         | Non    | Langage(s) cible(s). String ou tableau. Si omis : tous les langages.        |

### Exemple

`snippets/typescript/console.json` :

```json
{
  "Console Log": {
    "prefix": "cl",
    "body": "console.log(${1:value});",
    "description": "Affiche une valeur dans la console"
  },
  "Console Error": {
    "prefix": "ce",
    "body": "console.error(${1:message});",
    "description": "Affiche une erreur dans la console"
  }
}
```

`snippets/php/debug.json` :

```json
{
  "Var Dump": {
    "prefix": "vd",
    "body": "var_dump(${1:variable}); die();",
    "description": "Affiche le contenu d'une variable et stoppe l'exécution"
  }
}
```

### Utilisation

- **Clic droit** dans l'éditeur → **Dev Toolbox: Insérer un snippet**
- Ou via la **Command Palette** → **Dev Toolbox: Insérer un snippet**
- La liste est **filtrée par le langage** de l'éditeur actif
- Ou cliquer directement sur un snippet dans la **bibliothèque** Dev Toolbox

---

## Documentation

### Emplacement

`documentation/`

### Format

Fichiers `.md` organisés en sous-dossiers (catégories automatiques).

### Exemple

`documentation/readme-template.md` :

```markdown
# {{projectName}}

## Description

Description du projet.

## Auteur

{{author}} - {{date}}
```

### Utilisation

- Cliquer sur un document dans la **bibliothèque** Dev Toolbox pour ouvrir son aperçu Markdown

---

## Bibliothèque Dev Toolbox

L'icône **Dev Toolbox** dans la barre d'activité affiche une vue arborescente avec :

- **Workflows** → clic pour installer
- **Templates** → clic pour créer un projet
- **Snippets** → clic pour insérer dans l'éditeur
- **Documentation** → clic pour ouvrir l'aperçu
- **Favoris** → visible si `devToolbox.showFavorites` est activé

Bouton **refresh** pour recharger les ressources après modification des fichiers.

---

## Paramètres disponibles

| Paramètre                        | Description                                  |
|----------------------------------|----------------------------------------------|
| `devToolbox.author`              | Auteur utilisé dans les variables            |
| `devToolbox.pluginPrefix`        | Préfixe pour les extensions générées         |
| `devToolbox.workflowsDirectory`  | Chemin absolu du dossier workflows           |
| `devToolbox.templatesDirectory`  | Chemin absolu du dossier templates           |
| `devToolbox.documentationDirectory` | Chemin absolu du dossier documentation    |
| `devToolbox.snippetsDirectory`   | Chemin absolu du dossier snippets            |
| `devToolbox.initialVersion`      | Version par défaut (ex: `1.0.0`)             |
| `devToolbox.notificationsEnabled`| Affiche les notifications                    |
| `devToolbox.showFavorites`       | Affiche la section Favoris                   |
