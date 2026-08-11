# update-with-figma-export

Script Python permettant de générer automatiquement les styles du thème WordPress à partir d'exports Figma.

## Structure des dossiers par défaut

```
up-theme-basic/
├── update-with-figma-export.py    ← le script
├── update-with-figma-export.md    ← cette documentation
├── theme.json                     ← fichier de configuration du thème (mis à jour par le script)
├── figma_json/                    ← déposer ici les fichiers JSON exportés depuis Figma
│   ├── Token.json                 ← couleurs principales (palette du thème)
│   ├── Colors.json                ← couleurs supplémentaires (optionnel, custom.color)
│   └── Styles.json                ← variables de style par mode (Light, Medium, Dark, ...)
└── styles/
    └── sections/                  ← fichiers de styles générés (styleN.json)
        ├── style-default.json     ← style par défaut (valeurs de base du thème)
        ├── style1.json            ← style 1 (ex: mode Light)
        ├── style2.json            ← style 2 (ex: mode Medium)
        └── style3.json            ← style 3 (ex: mode Dark)
```

## Fichiers Figma à déposer

Placer les fichiers JSON exportés depuis Figma dans le dossier `figma_json/` :

| Fichier       | Rôle                                                                 | Obligatoire |
|---------------|----------------------------------------------------------------------|-------------|
| `Token.json`  | Définit la palette de couleurs principale (aliases vers Colors.json) | Oui         |
| `Colors.json` | Couleurs brutes Figma (optionnel, ajouté à `custom.color`)           | Non         |
| `Styles.json` | Variables de style par mode (Background, Text, Button, ...)          | Oui         |

## Utilisation

1. Exporter les variables depuis Figma au format JSON
2. Les déposer dans `figma_json/`
3. Lancer le script :

```bash
python3 update-with-figma-export.py
```

4. Appuyer sur **Entrée** pour accepter tous les chemins par défaut

## Déroulé interactif

Le script pose plusieurs questions dans l'ordre. Toutes acceptent **Entrée** pour le défaut.

### 1. Source Figma

- Dossier contenant les exports Figma (défaut : `figma_json/`)
- Sélection des fichiers `Token.json` à inclure dans la palette
- Optionnel : mettre les couleurs de `Colors.json` / `Styles.json` dans `custom.color`
  - Sélection des fichiers et modes à inclure
  - Les variables de style (`Background/page`, `Text/title`, ...) sont **ignorées** ici
    (elles vont dans `custom.style.N`, pas `custom.color`)

### 2. Variables globales (custom.color sémantique)

Le script demande s'il doit écrire les **variables globales** de `custom.color` — le contrat
sémantique du thème (33 variables : `text`, `background`, `title`, `link`, `link-hover`,
`accent`, `decorative`, `error`, `input-*`, `button-*`, `submit-*`).

Ces variables sont **uniquement des références** (`var:preset|color|...` ou
`var:custom|color|...`), jamais des valeurs hex, pour que changer la palette suffise à
retoner tout le thème.

| Mode | Effet |
|------|-------|
| `0` | N'écrit aucune variable globale |
| `1` (défaut) | Ajoute uniquement les variables manquantes, **conserve** vos valeurs personnalisées |
| `2` | Réinitialise toutes les variables aux valeurs par défaut définies dans le script |

Les couleurs Figma extraites à l'étape 1 **ne peuvent pas écraser** une variable globale
existante : si `Colors.json` contient une variable `background`, elle est ignorée pour
préserver la référence `var:preset|color|primary-light`.

### 3. Couleurs manuelles (optionnel)

Format `nom | valeur`, séparées par des virgules. Exemple :

```
primary light | #DBEAFE, primary medium | #3B82F6
```

### 4. Couleurs fixes

Propose d'ajouter `Error` (#EF4444), `Success` (#10B981), `Warning` (#F59E0B) à la palette.

### 5. Personnalisation des couleurs

Pour chaque couleur de la palette, permet de remplacer la valeur extraite de Figma.

### 6. Gradients

| Choix | Effet |
|-------|-------|
| `0` (défaut) | Aucun — **préserve** les gradients existants dans theme.json |
| `1` | Génère tous les dégradés (combinaisons de la palette) |
| `2` | Sélection manuelle |

### 7. Duotones

| Choix | Effet |
|-------|-------|
| `0` (défaut) | Aucun — **préserve** les duotones existants dans theme.json |
| `1` | Génère tous les duotones (combinaisons de la palette) |
| `2` | Sélection manuelle |

### 8. Format de sortie

| Format | Effet |
|--------|-------|
| `json` (défaut) | Met à jour `theme.json` (fusionne palette/gradients/duotones/custom.color) |
| `css`  | Génère un fichier CSS avec variables `:root` |

### 9. Sauvegarde

- **Chemin vers theme.json** (défaut) → fusionne dans le fichier existant
- **Autre nom** → sauvegarde le JSON standalone `{palette, gradients, duotones}`
- **Entrée vide** → affichage uniquement, aucune écriture

### 10. Styles de sections

Voir section dédiée ci-dessous.

## Ce que fait le script

### Palette de couleurs (Token.json)

- Lit `Token.json` et extrait les couleurs aliases
- Génère la palette dans `theme.json` → `settings.color.palette`
- Les slugs utilisent le format `primary-light`, `primary-dark`, `secondary-default`, etc.

### Couleurs personnalisées (Colors.json)

- Si `Colors.json` est présent et sélectionné, ajoute les couleurs dans `settings.custom.color`
- Ces couleurs ne sont **pas** dans la palette principale, mais disponibles comme variables CSS
- Les variables de style (`Background/page`, `Text/title`, etc.) sont **ignorées** — elles
  vont dans `custom.style.N` via l'étape Styles de sections
- Les variables dont le slug entre en collision avec une clé de variable globale
  (ex: `Error` → `error`) sont ignorées pour préserver la référence existante

### Variables globales (custom.color sémantique)

Le script garantit la présence de 33 variables globales dans `settings.custom.color` :

```
text, background, title, link, link-hover, accent, decorative, error,
input-text, input-placeholder, input-background, input-border, input-focus-border,
button-text, button-link, button-background, button-border,
button-text-hover, button-background-hover, button-border-hover,
button-outline-text, button-outline-link, button-outline-background, button-outline-border,
button-outline-text-hover, button-outline-background-hover, button-outline-border-hover,
submit-text, submit-background, submit-border,
submit-text-hover, submit-background-hover, submit-border-hover
```

Toutes sont des références (`var:preset|color|...` ou `var:custom|color|...`), jamais de hex.
Les valeurs par défaut sont définies dans la constante `GLOBAL_COLOR_VARS` du script.

### Styles de sections

- Détecte les fichiers contenant des variables de style (`Background/`, `Text/`, `Border/`, ...)
- Pour chaque mode Figma (Light, Medium, Dark, ...), crée un style numéroté :
  - `style1` ← premier mode sélectionné
  - `style2` ← deuxième mode
  - `style3` ← troisième mode
- Crée automatiquement un **style default** :
  - Si `custom.style.default` existe déjà dans theme.json → **conservé intact**
  - Sinon → reconstruit en référençant les variables globales
    (`var:custom|color|title`, `var:custom|color|button-background`, etc.)

### Mise à jour de theme.json

Le script fusionne dans `theme.json` (sans écraser le reste du fichier) :

```json
{
  "settings": {
    "color": {
      "palette": [...],
      "gradients": [...],
      "duotone": [...]
    },
    "custom": {
      "color": {
        "creme-50": "#FBF9F6",
        "title": "var:preset|color|primary-dark",
        "button-background": "var:preset|color|secondary-dark",
        ...
      },
      "style": {
        "default": { "background": "var:custom|color|background", ... },
        "1": { "background": "var:preset|color|primary-light", ... },
        "2": { "background": "var:preset|color|primary-default", ... },
        "3": { "background": "var:preset|color|secondary-dark", ... }
      }
    }
  }
}
```

### Fichiers styleN.json

Chaque style génère un fichier dans `styles/sections/` :

- `style-default.json` — références `var:custom|style|default|...`
- `style1.json` — références `var:custom|style|1|...`
- `style2.json` — références `var:custom|style|2|...`
- `style3.json` — références `var:custom|style|3|...`

Ces fichiers sont des **block style variations** applicables sur les blocs :
- `core/group`
- `core/columns`
- `core/column`
- `core/cover`

## Format des références

| Type           | Syntaxe                              | Exemple                              |
|----------------|--------------------------------------|--------------------------------------|
| Couleur preset | `var:preset\|color\|<slug>`          | `var:preset\|color\|primary-light`   |
| Variable custom| `var:custom\|color\|<key>`           | `var:custom\|color\|button-background` |
| Variable style | `var:custom\|style\|<N>\|<key>`      | `var:custom\|style\|1\|background`   |

## Protections contre la perte de données

Le script inclut plusieurs garde-fous :

1. **JSON invalide** : si `theme.json` n'est pas un JSON valide (ex: virgule manquante
   pendant une édition), le script s'arrête sans rien écrire au lieu d'écraser le fichier.

2. **Fichier non-theme.json** : si le fichier de destination existe mais ne contient pas
   les clés `settings` et `version`, le script refuse d'écrire pour éviter d'écraser
   un fichier non-thème.

3. **Confirmation d'écrasement** : pour un fichier existant hors theme.json, demande
   confirmation avant d'écraser.

4. **Listes vides préservées** : répondre `0` aux gradients/duotones **ne supprime pas**
   les gradients/duotones existants dans theme.json. Les listes vides sont ignorées
   lors de la fusion.

5. **Variables globales protégées** : les couleurs Figma extraites ne peuvent pas
   écraser une variable globale existante (ex: `background`, `title`).

## Notes

- Aucun fichier JavaScript n'est généré
- Les chemins par défaut sont relatifs à l'emplacement du script
- Le script peut être relancé sans risque : il met à jour les sections existantes
- Le style `default` est **conservé** s'il existe déjà dans theme.json ;
  sinon il est régénéré en référençant les variables globales
- Les variables globales (`GLOBAL_COLOR_VARS`) sont définies dans le script.
  Pour changer une valeur par défaut (ex: `button-outline-text-hover`), éditer
  la constante dans `update-with-figma-export.py` puis utiliser le mode `2`
  (réinitialiser) au prochain run.
