#!/usr/bin/env python3
"""
Générateur color/gradient palette pour WordPress/Gutenberg.
- Saisie : "nom | valeur" séparés par des virgules
- Sets par défaut : primary, secondary, neutral (light/medium/dark)
- Couleurs fixes : error, success, warning
- Gradients proposés : chaque couleur vers blanc et vers noir
"""

import json
import os
import re


def slugify(text):
    """Convertit un nom en slug (minuscules, espaces -> -, caractères spéciaux supprimés)."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def make_color(name, value):
    return {
        "slug": slugify(name),
        "name": name,
        "color": value
    }


def make_gradient(name, slug, value):
    return {
        "slug": slug,
        "name": name,
        "gradient": value
    }


def make_duotone(name, slug, colors):
    return {
        "slug": slug,
        "name": name,
        "colors": colors
    }


def parse_color_entry(token):
    """Parse : 'nom | valeur'."""
    if "|" not in token:
        return None
    parts = token.split("|", 1)
    name = parts[0].strip()
    value = parts[1].strip()
    if not name or not value:
        return None
    return (name, value)


def parse_duotone_entry(token):
    """Parse : 'nom | couleur1,couleur2'."""
    if "|" not in token:
        return None
    parts = token.split("|", 1)
    name = parts[0].strip()
    colors_raw = parts[1].strip()
    if not name or not colors_raw:
        return None
    colors = [c.strip() for c in colors_raw.split(",")]
    if len(colors) != 2 or not colors[0] or not colors[1]:
        return None
    return (name, colors)


def merge_into_theme_json(theme_path, palette, gradients, duotones):
    """Remplace palette, gradients et duotone dans un fichier theme.json."""
    with open(theme_path, 'r', encoding='utf-8') as f:
        theme = json.load(f)

    if "settings" not in theme:
        theme["settings"] = {}
    if "color" not in theme["settings"]:
        theme["settings"]["color"] = {}

    theme["settings"]["color"]["palette"] = palette
    theme["settings"]["color"]["gradients"] = gradients
    theme["settings"]["color"]["duotone"] = duotones

    with open(theme_path, 'w', encoding='utf-8') as f:
        json.dump(theme, f, indent=4, ensure_ascii=False)
        f.write("\n")

    print(f"✅ theme.json mis à jour : {theme_path}")


def generate_css(palette, gradients, duotones, color_prefix="--wp--preset--color--", gradient_prefix="--wp--preset--gradient--"):
    """Génère un bloc :root avec des variables CSS."""
    lines = [':root {']
    for entry in palette:
        lines.append(f"  {color_prefix}{entry['slug']}: {entry['color']};")
    for entry in gradients:
        lines.append(f"  {gradient_prefix}{entry['slug']}: {entry['gradient']};")
    if duotones:
        lines.append("  /* Duotones */")
        for entry in duotones:
            c1, c2 = entry['colors']
            lines.append(f"  /* duotone-{entry['slug']}: {c1} / {c2} */")
    lines.append("}")
    return "\n".join(lines)


def main():
    print("=" * 60)
    print("  Générateur color/gradient palette WordPress/Gutenberg")
    print("=" * 60)

    print("\n--- COULEURS MANUELLES ---")
    print("Entrez les couleurs au format \"nom | valeur\", séparées par des virgules.")
    print("  Exemple : primary light | #DBEAFE, primary medium | #3B82F6, primary dark | #1E3A8A")
    raw = input("\nCouleurs : ").strip()

    palette = []

    if raw:
        for token in raw.split(","):
            token = token.strip()
            if not token:
                continue
            parsed = parse_color_entry(token)
            if parsed:
                name, value = parsed
                palette.append(make_color(name, value))
            else:
                print(f"  ⚠️ Ignoré : '{token}' (format invalide)")

    default_sets = {
        "primary": {
            "light": "#DBEAFE",
            "medium": "#3B82F6",
            "dark": "#1E3A8A"
        },
        "secondary": {
            "light": "#FCE7F3",
            "medium": "#EC4899",
            "dark": "#9D174D"
        },
        "neutral": {
            "light": "#F3F4F6",
            "medium": "#6B7280",
            "dark": "#111827"
        }
    }

    # Type de palette
    print("\n--- TYPE DE PALETTE ---")
    print("  0 : tout (choisir manuellement)")
    print("  1 : bas (base, accent, contrast)")
    print("  2 : primary (primary, secondary, neutral)")
    palette_type = input("Type de palette (0/1/2) [défaut 0] : ").strip().lower()
    if not palette_type:
        palette_type = "0"

    if palette_type == "1":
        palette.extend([
            {"slug": "base", "name": "Base", "color": "#ffffff"},
            {"slug": "contrast", "name": "Contrast", "color": "#1e1e1e"},
            {"slug": "accent", "name": "Accent", "color": "#c5a3ff"}
        ])
    elif palette_type == "2":
        for set_name, shades in default_sets.items():
            for shade, value in shades.items():
                name = f"{set_name} {shade}"
                palette.append(make_color(name, value))
    else:
        # Sets par défaut
        print("\n--- SETS PAR DÉFAUT ---")
        for set_name, shades in default_sets.items():
            add = input(f"  Ajouter le set {set_name} (light/medium/dark) ? (o/n) : ").strip().lower()
            if add in ("o", "oui", "y", "yes"):
                for shade, value in shades.items():
                    name = f"{set_name} {shade}"
                    palette.append(make_color(name, value))

        # Couleurs de base
        print("\n--- COULEURS DE BASE ---")
        base_colors = [
            ("base", "Base", "#ffffff"),
            ("base-2", "Base 2", "#f2f2f2"),
            ("base-3", "Base 3", "#d9d9d9"),
            ("contrast", "Contrast", "#1e1e1e"),
            ("contrast-2", "Contrast 2", "#636363"),
            ("contrast-3", "Contrast 3", "#a4a4a4"),
            ("accent", "Accent", "#c5a3ff"),
            ("accent-2", "Accent 2", "#f2c94c"),
            ("accent-3", "Accent 3", "#ff7b7b")
        ]
        for slug, name, value in base_colors:
            add = input(f"  Ajouter '{name}' ({value}) ? (o/n) : ").strip().lower()
            if add in ("o", "oui", "y", "yes"):
                palette.append({"slug": slug, "name": name, "color": value})

    # Couleurs fixes
    print("\n--- COULEURS FIXES ---")
    hardcoded = [
        ("error", "Error", "#EF4444"),
        ("success", "Success", "#10B981"),
        ("warning", "Warning", "#F59E0B")
    ]
    for slug, name, value in hardcoded:
        add = input(f"  Ajouter '{name}' ({value}) ? (o/n) : ").strip().lower()
        if add in ("o", "oui", "y", "yes"):
            palette.append({"slug": slug, "name": name, "color": value})

    # Personnalisation des couleurs
    if palette:
        print("\n--- PERSONNALISATION DES COULEURS ---")
        for entry in palette:
            new_color = input(f"  {entry['name']} ({entry['color']}) → nouvelle valeur (Entrée pour garder) : ").strip()
            if new_color:
                entry["color"] = new_color

    # Gradients
    gradients = []
    if palette:
        print("\n--- GRADIENTS ---")
        print("  0 : aucun")
        print("  1 : générer tous les dégradés")
        print("  2 : manuel")
        grad_choice = input("Générer les gradients (0/1/2) [défaut 0] : ").strip().lower()
        if not grad_choice:
            grad_choice = "0"

        if grad_choice == "1":
            for entry in palette:
                slug = entry["slug"]
                name = entry["name"]
                color = entry["color"]
                gradients.append(make_gradient(f"{name} to white", f"{slug}-to-white", f"linear-gradient(135deg, {color} 0%, #ffffff 100%)"))
                gradients.append(make_gradient(f"white to {name}", f"white-to-{slug}", f"linear-gradient(135deg, #ffffff 0%, {color} 100%)"))
                gradients.append(make_gradient(f"{name} to black", f"{slug}-to-black", f"linear-gradient(135deg, {color} 0%, #000000 100%)"))
                gradients.append(make_gradient(f"black to {name}", f"black-to-{slug}", f"linear-gradient(135deg, #000000 0%, {color} 100%)"))
        elif grad_choice == "2":
            for entry in palette:
                slug = entry["slug"]
                name = entry["name"]
                color = entry["color"]

                add_white = input(f"  Ajouter les dégradés blancs pour '{name}' ? (o/n) : ").strip().lower()
                if add_white in ("o", "oui", "y", "yes"):
                    gradients.append(make_gradient(f"{name} to white", f"{slug}-to-white", f"linear-gradient(135deg, {color} 0%, #ffffff 100%)"))
                    gradients.append(make_gradient(f"white to {name}", f"white-to-{slug}", f"linear-gradient(135deg, #ffffff 0%, {color} 100%)"))

                add_black = input(f"  Ajouter les dégradés noirs pour '{name}' ? (o/n) : ").strip().lower()
                if add_black in ("o", "oui", "y", "yes"):
                    gradients.append(make_gradient(f"{name} to black", f"{slug}-to-black", f"linear-gradient(135deg, {color} 0%, #000000 100%)"))
                    gradients.append(make_gradient(f"black to {name}", f"black-to-{slug}", f"linear-gradient(135deg, #000000 0%, {color} 100%)"))

    # Duotones
    duotones = []
    if palette:
        print("\n--- DUOTONES ---")
        print("  0 : aucun")
        print("  1 : générer tous les duotones")
        print("  2 : manuel")
        duo_choice = input("Générer les duotones (0/1/2) [défaut 0] : ").strip().lower()
        if not duo_choice:
            duo_choice = "0"

        if duo_choice in ("1", "2"):
            print("\nEntrez les duotones personnalisés au format \"nom | couleur1,couleur2\", séparés par des points-virgules.")
            print("  Exemple : Noir et blanc | #000000,#ffffff; Violet et jaune | #8c00b7,#fcff41")
            raw_duos = input("Duotones : ").strip()
            if raw_duos:
                for token in raw_duos.split(";"):
                    token = token.strip()
                    if not token:
                        continue
                    parsed = parse_duotone_entry(token)
                    if parsed:
                        name, colors = parsed
                        duotones.append(make_duotone(name, slugify(name), colors))
                    else:
                        print(f"  ⚠️ Ignoré : '{token}' (format invalide)")

            duotone_presets = [
                ("black-and-white", "Noir et blanc", ["#000000", "#ffffff"]),
                ("purple-yellow", "Violet et jaune", ["#8c00b7", "#fcff41"])
            ]
            if duo_choice == "1":
                for slug, name, colors in duotone_presets:
                    duotones.append(make_duotone(name, slug, colors))
            elif duo_choice == "2":
                for slug, name, colors in duotone_presets:
                    add = input(f"  Ajouter '{name}' ({colors[0]}, {colors[1]}) ? (o/n) : ").strip().lower()
                    if add in ("o", "oui", "y", "yes"):
                        duotones.append(make_duotone(name, slug, colors))

            if duo_choice == "1":
                for entry in palette:
                    slug = entry["slug"]
                    name = entry["name"]
                    color = entry["color"]
                    duotones.append(make_duotone(f"{name} and white", f"{slug}-and-white", [color, "#ffffff"]))
                    duotones.append(make_duotone(f"white and {name}", f"white-and-{slug}", ["#ffffff", color]))
                    duotones.append(make_duotone(f"{name} and black", f"{slug}-and-black", [color, "#000000"]))
                    duotones.append(make_duotone(f"black and {name}", f"black-and-{slug}", ["#000000", color]))
            elif duo_choice == "2":
                for entry in palette:
                    slug = entry["slug"]
                    name = entry["name"]
                    color = entry["color"]

                    add_white = input(f"  Duotones '{name}' + blanc ? (o/n) : ").strip().lower()
                    if add_white in ("o", "oui", "y", "yes"):
                        duotones.append(make_duotone(f"{name} and white", f"{slug}-and-white", [color, "#ffffff"]))
                        duotones.append(make_duotone(f"white and {name}", f"white-and-{slug}", ["#ffffff", color]))

                    add_black = input(f"  Duotones '{name}' + noir ? (o/n) : ").strip().lower()
                    if add_black in ("o", "oui", "y", "yes"):
                        duotones.append(make_duotone(f"{name} and black", f"{slug}-and-black", [color, "#000000"]))
                        duotones.append(make_duotone(f"black and {name}", f"black-and-{slug}", ["#000000", color]))

    # Format de sortie
    print("\n--- FORMAT ---")
    print("  json : génère un objet JSON (theme.json)")
    print("  css  : génère des variables CSS dans :root")
    format_choice = input("Format (json/css) [défaut json] : ").strip().lower()
    if not format_choice:
        format_choice = "json"

    if format_choice == "css":
        output = generate_css(palette, gradients, duotones)
    else:
        output = json.dumps({"palette": palette, "gradients": gradients, "duotones": duotones}, indent=4, ensure_ascii=False)

    # Affichage
    print("\n" + "=" * 60)
    print(output)

    # Sauvegarde
    print("\n" + "=" * 60)
    print("Sauvegarde :")
    if format_choice == "css":
        print("  - Chemin vers fichier .css")
        print("  - Autre nom → sauvegarde le CSS")
    else:
        print("  - Chemin vers theme.json → remplace palette/gradients/duotone dans le fichier")
        print("  - Autre nom → sauvegarde le JSON standalone")
    print("  - Entrée → affichage uniquement")
    save = input("\nFichier de destination : ").strip()

    if not save:
        return

    if format_choice == "css":
        with open(save, 'w', encoding='utf-8') as f:
            f.write(output)
            f.write("\n")
        print(f"✅ CSS sauvegardé dans {save}")
        return

    if save.endswith('.json') and os.path.isfile(save):
        with open(save, 'r', encoding='utf-8') as f:
            content = f.read()
        try:
            data = json.loads(content)
            if "settings" in data and "version" in data:
                merge_into_theme_json(save, palette, gradients, duotones)
                return
        except json.JSONDecodeError:
            pass

    # Sauvegarde standalone JSON
    with open(save, 'w', encoding='utf-8') as f:
        f.write(output)
        f.write("\n")
    print(f"✅ JSON sauvegardé dans {save}")


if __name__ == "__main__":
    main()
