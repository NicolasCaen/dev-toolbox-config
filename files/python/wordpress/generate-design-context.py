#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère un contexte design (palette, tailles, spacing, dégradés)
à destination d'une IA pour produire des blocs WordPress/Gutenberg
respectant strictement les tokens du theme.json.
"""

import json
import os
import re
from pathlib import Path

THEME_DIR = Path(__file__).parent
THEME_JSON = THEME_DIR / "theme.json"
OUTPUT = THEME_DIR / "ai-design-context.md"


def to_px(value: str) -> float | None:
    """Convertit une valeur CSS (px, rem, em, clamp) en px approximatif."""
    value = value.strip()
    if not value:
        return None

    # clamp(...) -> on prend la valeur max (dernier argument)
    clamp_match = re.match(r"clamp\s*\([^,]+,\s*[^,]+,\s*([^)]+)\)", value, re.I)
    if clamp_match:
        return to_px(clamp_match.group(1))

    # Valeur chiffre simple (typiquement en rem)
    bare_match = re.match(r"^([\d.]+)$", value)
    if bare_match:
        return float(bare_match.group(1)) * 16.0

    # Valeur avec unité
    unit_match = re.match(r"^([\d.]+)\s*(px|rem|em)$", value, re.I)
    if unit_match:
        num = float(unit_match.group(1))
        unit = unit_match.group(2).lower()
        if unit == "px":
            return num
        return num * 16.0

    return None


def format_size(value: str) -> str:
    px = to_px(value)
    if px is None:
        return value
    return f"{value} (≈ {px:.1f}px)"


def resolve_color_reference(value: str, palette: dict) -> str:
    """Remplace var:preset|color|xxx par sa valeur hex quand c'est possible."""
    if not isinstance(value, str):
        return value
    match = re.match(r"var:preset\|color\|([^\|]+)", value)
    if match and match.group(1) in palette:
        return palette[match.group(1)]
    return value


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    data = load_json(THEME_JSON)
    settings = data.get("settings", {})
    color = settings.get("color", {})
    typography = settings.get("typography", {})
    spacing = settings.get("spacing", {})
    custom = settings.get("custom", {})
    layout = settings.get("layout", {})

    # Palette
    palette_items = color.get("palette", [])
    palette = {p["slug"]: p["color"] for p in palette_items}

    # Gradients
    gradients = color.get("gradients", [])

    # Font sizes
    font_sizes = typography.get("fontSizes", [])
    for fs in font_sizes:
        fs["_px"] = to_px(fs.get("size", "")) or 0
    font_sizes_sorted = sorted(font_sizes, key=lambda x: x["_px"], reverse=True)

    # Spacing
    spacing_sizes = spacing.get("spacingSizes", [])
    for s in spacing_sizes:
        s["_px"] = to_px(s.get("size", "")) or 0
    spacing_sorted = sorted(spacing_sizes, key=lambda x: x["_px"], reverse=True)

    # Radius sizes
    border = settings.get("border", {})
    radius_sizes = border.get("radiusSizes", [])
    for r in radius_sizes:
        r["_px"] = to_px(r.get("size", "")) or 0
    radius_sorted = sorted(radius_sizes, key=lambda x: x["_px"], reverse=True)

    # Custom colors
    custom_colors = custom.get("color", {})
    resolved_custom_colors = {
        k: resolve_color_reference(v, palette) for k, v in custom_colors.items()
    }

    # Custom styles
    custom_styles = custom.get("style", {})

    # Shadows
    shadows = settings.get("shadow", {}).get("presets", [])

    lines = [
        "# Contexte design – Up Sylphane",
        "",
        "Ce document résume les tokens de design du thème WordPress `up-sylphane`.",
        "Il est destiné à une IA chargée de générer du HTML/JSON pour des blocs Gutenberg.",
        "Toutes les valeurs doivent être utilisées **exactement** telles qu'elles apparaissent ci-dessous.",
        "",
        "---",
        "",
        "## 1. Palette de couleurs",
        "",
        "Utiliser les slugs avec le format `var:preset|color|<slug>` ou `var(--wp--preset--color--<slug>)`.",
        "",
        "> **Règle fondamentale** : les couleurs ne sont **jamais** définies directement sur les blocs enfants (texte, titre, paragraphe, bouton, etc.).",
        "> C'est le **groupe parent** (la section) qui définit le style de section, lequel propage automatiquement les couleurs vers tous ses enfants via les CSS variables du thème.",
        "> Les blocs enfants héritent donc des couleurs de fond, de texte, de lien, de bouton, etc. en fonction du style de section appliqué au parent.",
        "> Voir la section **8. Styles de section** ci-dessous pour comprendre quel style appliquer à quel groupe parent.",
        "",
        "| Slug | Nom | Couleur |",
        "|------|-----|---------|",
    ]
    for p in palette_items:
        lines.append(f"| `{p['slug']}` | {p.get('name', p['slug'])} | {p['color']} |")

    lines.extend([
        "",
        "### Couleurs sémantiques / custom",
        "",
        "Ces tokens sont également disponibles dans le design. Ils pointent souvent vers des presets :",
        "",
        "| Token | Valeur résolue |",
        "|-------|----------------|",
    ])
    for key, val in resolved_custom_colors.items():
        lines.append(f"| `{key}` | {val} |")

    lines.extend([
        "",
        "## 2. Dégradés",
        "",
        "Utiliser les slugs avec `var:preset|gradient|<slug>` ou la valeur CSS directement.",
        "",
        "| Slug | Nom | Dégradé |",
        "|------|-----|---------|",
    ])
    for g in gradients:
        lines.append(f"| `{g['slug']}` | {g.get('name', g['slug'])} | `{g['gradient']}` |")

    lines.extend([
        "",
        "## 3. Tailles de police",
        "",
        "Ordre de la plus grande à la plus petite. Utiliser `var:preset|font-size|<slug>`.",
        "",
        "| Slug | Nom | Taille |",
        "|------|-----|--------|",
    ])
    for fs in font_sizes_sorted:
        lines.append(f"| `{fs['slug']}` | {fs.get('name', fs['slug'])} | {format_size(fs['size'])} |")

    lines.extend([
        "",
        "### Utilisation typographique attendue",
        "",
        "| Usage | Token |",
        "|-------|-------|",
        "| H1 | `var:preset|font-size|title-large` |",
        "| H2 | `var:preset|font-size|title-medium` |",
        "| H3 | `var:preset|font-size|title-small` |",
        "| H4 | `var:preset|font-size|body-huge` |",
        "| H5 | `var:preset|font-size|body-large` |",
        "| Body par défaut | `var:preset|font-size|body-default` |",
        "| Petit texte | `var:preset|font-size|body-small` |",
        "| Très petit | `var:preset|font-size|body-xsmall` |",
        "",
        "## 4. Spacing",
        "",
        "Ordre du plus grand au plus petit. Utiliser `var:preset|spacing|<slug>`.",
        "",
        "| Slug | Nom | Taille |",
        "|------|-----|--------|",
    ])
    for s in spacing_sorted:
        lines.append(f"| `{s['slug']}` | {s.get('name', s['slug'])} | {format_size(s['size'])} |")

    lines.extend([
        "",
        "## 5. Border radius",
        "",
        "| Slug | Nom | Valeur |",
        "|------|-----|--------|",
    ])
    for r in radius_sorted:
        lines.append(f"| `{r['slug']}` | {r.get('name', r['slug'])} | {format_size(r['size'])} |")

    lines.extend([
        "",
        "## 6. Ombres",
        "",
        "| Slug | Nom | Valeur |",
        "|------|-----|--------|",
    ])
    for sh in shadows:
        lines.append(f"| `{sh['slug']}` | {sh.get('name', sh['slug'])} | `{sh['shadow']}` |")

    lines.extend([
        "",
        "## 7. Layout",
        "",
        f"- **contentSize** : `{layout.get('contentSize', '')}`",
        f"- **wideSize** : `{layout.get('wideSize', '')}`",
        "",
        "## 8. Styles de section",
        "",
        "Le theme.json définit plusieurs styles de section (`1`, `2`, `3`, `default`).",
        "Chaque style définit un ensemble cohérent de couleurs pour le fond, le texte, les titres, les liens, les boutons, les inputs et les éléments décoratifs.",
        "",
        "### Principe de fonctionnement",
        "",
        "1. **Le groupe parent (section) reçoit le style** : on applique la classe `is-style-1`, `is-style-2`, `is-style-3` ou pas de classe (style `default`) sur le bloc groupe/section parent.",
        "2. **Les enfants n'ont aucune couleur explicite** : les blocs enfants (titres, paragraphes, boutons, liens, inputs) ne définissent **aucune couleur** dans leurs attributs. Ils héritent automatiquement des couleurs du style de section parent.",
        "3. **Les CSS variables font le pont** : le thème génère des variables CSS (`--wp--custom--color--text`, `--wp--custom--color--background`, `--wp--custom--color--button-background`, etc.) qui changent en fonction du style de section appliqué.",
        "",
        "### Quand utiliser quel style ?",
        "",
        "| Style | Classe | Fond | Texte | Titre | Idéal pour |",
        "|-------|--------|------|-------|-------|------------|",
        "| `default` | *(aucune)* | `primary-light` (#FFF7E8) | `neutral-dark` (#1A1D16) | `neutral-dark` | Sections par défaut, fond clair |",
        "| `1` | `is-style-1` | `primary-light` (#FFF7E8) | `neutral-dark` (#1A1D16) | `primary-dark` (#29251E) | Sections claires avec titres foncés |",
        "| `2` | `is-style-2` | `primary-default` (#CBBDA2) | `neutral-dark` (#1A1D16) | `primary-dark` (#29251E) | Sections beige moyen, contraste doux |",
        "| `3` | `is-style-3` | `secondary-dark` (#35392D) | `neutral-light` (#FFFFFF) | `primary-light` (#FFF7E8) | Sections foncées, texte clair |",
        "",
        "### Exemple de structure Gutenberg",
        "",
        "```html",
        "<!-- Groupe parent avec style de section 3 (fond foncé) -->",
        "<div class=\"wp-block-group is-style-3\">",
        "  <!-- Les enfants n'ont AUCUNE couleur définie -->",
        "  <h2>Titre hérité (clair sur fond foncé)</h2>",
        "  <p>Texte hérité (clair sur fond foncé)</p>",
        "  <!-- Le bouton hérite aussi des couleurs du style 3 -->",
        "  <div class=\"wp-block-button\">",
        "    <a class=\"wp-block-button__link\">Bouton hérité</a>",
        "  </div>",
        "</div>",
        "```",
        "",
        "> **Important** : ne jamais ajouter `style=\"{\"color\":{\"text\":\"var:preset|color|xxx\"}}\"` sur un bloc enfant. La couleur vient toujours du parent.",
        "",
    ])
    for style_name, style in custom_styles.items():
        lines.append(f"### Style `{style_name}`")
        lines.append(f"```json")
        lines.append(json.dumps(style, indent=4, ensure_ascii=False))
        lines.append(f"```")
        lines.append("")

    lines.extend([
        "",
        "## 9. Directives de génération de blocs",
        "",
        "Lorsque tu génères du JSON/HTML pour Gutenberg :",
        "",
        "1. **Couleurs** : **JAMAIS de couleur directement sur un bloc enfant**. Les couleurs sont définies par le style de section du groupe parent (voir section 8). N'appliquer une couleur explicite que sur le groupe parent si nécessaire.",
        "2. **Dégradés** : utilise `var:preset|gradient|<slug>` pour les fonds dégradés.",
        "3. **Tailles** : n'utilise jamais de valeurs fixes en px/rem ; utilise `var:preset|font-size|<slug>` pour le texte.",
        "4. **Spacing** : utilise `var:preset|spacing|<slug>` pour marges, padding et gaps.",
        "5. **Radius** : utilise `var:preset|radius|<slug>` pour les bordures arrondies.",
        "6. **Ombres** : utilise `var:preset|shadow|<slug>` pour les ombres portées.",
        "7. **Classes utilitaires** : tu peux ajouter `is-style-<style>` si le style est enregistré dans le thème.",
        "8. **Accessibilité** : respecte les contrastes implicites des styles 1, 2, 3 (texte clair sur fond foncé, etc.).",
        "",
        "---",
        "",
        "Fichier généré automatiquement depuis `theme.json`.",
    ])

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Contexte généré : {OUTPUT}")


if __name__ == "__main__":
    main()
