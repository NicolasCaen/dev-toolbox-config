#!/usr/bin/env python3
"""
Générateur color/gradient/duotone palette + styles de sections pour WordPress/Gutenberg,
à partir d'exports de variables Figma (Colors.json, Token.json, Styles.json, ...).

- Demande un dossier contenant les fichiers JSON exportés depuis Figma
  (variable collections : clés "modes" + "variables").
- Détecte automatiquement les fichiers valides et affiche leur nom / nb de variables.
- Permet de choisir quel(s) fichier(s) et quel(s) mode(s) (Light/Dark/...) inclure.
- Convertit les valeurs RGBA (0-1) en hex (#RRGGBB / #RRGGBBAA).
- Permet d'ajouter des couleurs manuelles ("nom | valeur") et des couleurs fixes
  (error/success/warning) comme dans le script d'origine.
- Génère les dégradés (chaque couleur -> blanc / noir, dans les 2 sens).
- Génère les duotones (presets + combinaisons avec blanc/noir + duotones manuels).
- Génère les styles de sections : pour chaque mode d'un fichier de styles Figma,
  crée des variables custom.style.N dans theme.json, un fichier styleN.json
  dans styles/sections/, et un fichier styleN.js pour l'enregistrement.
- Sortie :
    - CSS : bloc :root avec variables --wp--preset--color--* / --gradient--*
    - JSON : soit un objet standalone {palette, gradients, duotones},
             soit une mise à jour de settings.color.palette/gradients/duotone
             dans un theme.json existant (détecté automatiquement).
"""

import json
import os
import re


# ---------------------------------------------------------------------------
# Utilitaires génériques
# ---------------------------------------------------------------------------

def slugify(text):
    """Convertit un nom en slug (minuscules, / et espaces -> -, caractères spéciaux supprimés)."""
    text = text.lower().strip()
    text = text.replace("/", " ")
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


# ---------------------------------------------------------------------------
# Extraction des couleurs Figma
# ---------------------------------------------------------------------------

def figma_rgba_to_hex(v):
    """Convertit un objet couleur Figma {r,g,b,a} (0-1) en hex."""
    r = round(v.get("r", 0) * 255)
    g = round(v.get("g", 0) * 255)
    b = round(v.get("b", 0) * 255)
    a = v.get("a", 1)
    hexcode = "#{:02X}{:02X}{:02X}".format(r, g, b)
    if a < 1:
        hexcode += "{:02X}".format(round(a * 255))
    return hexcode


def scan_figma_files(folder):
    """Cherche les .json du dossier qui ressemblent à des exports de variables Figma."""
    found = []
    try:
        entries = sorted(os.listdir(folder))
    except FileNotFoundError:
        return found

    for fname in entries:
        if not fname.lower().endswith(".json"):
            continue
        path = os.path.join(folder, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, dict) and "variables" in data and "modes" in data:
            found.append((fname, path, data))
    return found


def extract_colors_from_file(data, selected_mode_ids):
    """
    Extrait les couleurs résolues d'un fichier de variables Figma.
    Retourne une liste de (nom, hex).
    Si plusieurs modes sont sélectionnés, le nom du mode est ajouté au nom
    de la variable pour éviter les collisions (ex: "Text/title Dark").
    """
    modes = data.get("modes", {})
    multi_mode = len(selected_mode_ids) > 1
    results = []

    for var in data.get("variables", []):
        if var.get("type") != "COLOR":
            continue
        for mode_id in selected_mode_ids:
            rv = var.get("resolvedValuesByMode", {}).get(mode_id)
            if not rv:
                continue
            val = rv.get("resolvedValue")
            if not val:
                continue
            hexcode = figma_rgba_to_hex(val)
            if multi_mode:
                mode_name = modes.get(mode_id, mode_id)
                name = f"{var['name']} {mode_name}"
            else:
                name = var["name"]
            results.append((name, hexcode))
    return results


def choose_figma_source(folder):
    """
    Flux interactif : liste les fichiers Figma valides trouvés dans le dossier,
    laisse choisir lesquels inclure, puis pour chacun quel(s) mode(s).
    Retourne une liste de (nom, hex) prêtes à devenir des entrées de palette.
    """
    files = scan_figma_files(folder)
    if not files:
        print(f"  ⚠️ Aucun fichier de variables Figma valide trouvé dans '{folder}'.")
        return []

    print(f"\nFichiers détectés dans '{folder}' :")
    for i, (fname, _, data) in enumerate(files, start=1):
        nb_vars = len(data.get("variables", []))
        modes = list(data.get("modes", {}).values())
        print(f"  {i}. {fname}  ({nb_vars} variables, modes: {', '.join(modes)})")

    raw = input(
        "\nFichiers à inclure (numéros séparés par des virgules, "
        "'a' = tous) [défaut: tous] : "
    ).strip().lower()

    if not raw or raw == "a":
        selected_indices = list(range(1, len(files) + 1))
    else:
        selected_indices = []
        for token in raw.split(","):
            token = token.strip()
            if token.isdigit() and 1 <= int(token) <= len(files):
                selected_indices.append(int(token))

    extracted = []
    for idx in selected_indices:
        fname, path, data = files[idx - 1]
        modes = data.get("modes", {})
        mode_items = list(modes.items())  # [(mode_id, mode_name), ...]

        if len(mode_items) <= 1:
            selected_mode_ids = [m[0] for m in mode_items]
        else:
            print(f"\n  Modes disponibles pour '{fname}' :")
            for i, (mode_id, mode_name) in enumerate(mode_items, start=1):
                print(f"    {i}. {mode_name}")
            raw_modes = input(
                f"  Mode(s) à inclure pour '{fname}' (numéros séparés par des "
                f"virgules, 'a' = tous) [défaut: 1] : "
            ).strip().lower()
            if not raw_modes:
                selected_mode_ids = [mode_items[0][0]]
            elif raw_modes == "a":
                selected_mode_ids = [m[0] for m in mode_items]
            else:
                selected_mode_ids = []
                for token in raw_modes.split(","):
                    token = token.strip()
                    if token.isdigit() and 1 <= int(token) <= len(mode_items):
                        selected_mode_ids.append(mode_items[int(token) - 1][0])

        colors = extract_colors_from_file(data, selected_mode_ids)
        print(f"  ✅ {len(colors)} couleur(s) extraite(s) de '{fname}'.")
        extracted.extend(colors)

    return extracted


# ---------------------------------------------------------------------------
# theme.json / CSS
# ---------------------------------------------------------------------------

def merge_into_theme_json(theme_path, palette, gradients, duotones, custom_colors=None):
    """Remplace palette, gradients et duotone dans un fichier theme.json.
    Si custom_colors est fourni ({slug: hex}), ajoute dans settings.custom.color."""
    with open(theme_path, "r", encoding="utf-8") as f:
        theme = json.load(f)

    if "settings" not in theme:
        theme["settings"] = {}
    if "color" not in theme["settings"]:
        theme["settings"]["color"] = {}

    theme["settings"]["color"]["palette"] = palette
    theme["settings"]["color"]["gradients"] = gradients
    theme["settings"]["color"]["duotone"] = duotones

    if custom_colors:
        if "custom" not in theme["settings"]:
            theme["settings"]["custom"] = {}
        if "color" not in theme["settings"]["custom"]:
            theme["settings"]["custom"]["color"] = {}
        for slug, hex_val in custom_colors.items():
            theme["settings"]["custom"]["color"][slug] = hex_val

    with open(theme_path, "w", encoding="utf-8") as f:
        json.dump(theme, f, indent=4, ensure_ascii=False)
        f.write("\n")

    print(f"✅ theme.json mis à jour : {theme_path}")
    if custom_colors:
        print(f"✅ custom.color : {len(custom_colors)} couleur(s)")


def generate_css(palette, gradients, duotones,
                  color_prefix="--wp--preset--color--",
                  gradient_prefix="--wp--preset--gradient--"):
    """Génère un bloc :root avec des variables CSS."""
    lines = [":root {"]
    for entry in palette:
        lines.append(f"  {color_prefix}{entry['slug']}: {entry['color']};")
    for entry in gradients:
        lines.append(f"  {gradient_prefix}{entry['slug']}: {entry['gradient']};")
    if duotones:
        lines.append("  /* Duotones */")
        for entry in duotones:
            c1, c2 = entry["colors"]
            lines.append(f"  /* duotone-{entry['slug']}: {c1} / {c2} */")
    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Programme principal
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  Figma -> WordPress/Gutenberg : palette, gradients, duotones")
    print("=" * 60)

    palette = []
    token_slugs = {}  # {variable_name: slug} pour résoudre les alias dans les styles
    custom_colors = {}  # {slug: hex} pour custom.color (optionnel)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_figma_folder = os.path.join(script_dir, "figma_json")
    default_theme_json = os.path.join(script_dir, "theme.json")

    # --- Source Figma -------------------------------------------------
    print("\n--- SOURCE FIGMA ---")
    folder = input(
        f"Dossier contenant les fichiers exportés depuis Figma "
        f"[défaut: {default_figma_folder}] : "
    ).strip().strip('"')
    if not folder:
        folder = default_figma_folder

    if folder and os.path.isdir(folder):
        files = scan_figma_files(folder)

        # Séparer les fichiers Token (palette) des autres
        token_files = []
        other_files = []
        for fname, path, data in files:
            if is_style_file(data):
                other_files.append((fname, path, data))
            else:
                # Détecter les fichiers Token (variables avec alias vers Colors)
                has_alias = any(
                    var.get("type") == "COLOR" and
                    any(rv.get("alias") for rv in var.get("resolvedValuesByMode", {}).values())
                    for var in data.get("variables", [])
                )
                if has_alias:
                    token_files.append((fname, path, data))
                else:
                    other_files.append((fname, path, data))

        # --- Token -> palette ---
        if token_files:
            print(f"\nFichiers Token détectés (pour la palette) :")
            for i, (fname, _, data) in enumerate(token_files, start=1):
                nb_vars = sum(1 for v in data.get("variables", []) if v.get("type") == "COLOR")
                modes = list(data.get("modes", {}).values())
                print(f"  {i}. {fname}  ({nb_vars} couleurs, modes: {', '.join(modes)})")

            raw = input(
                "\nFichiers Token à inclure dans la palette (numéros séparés par des virgules, "
                "'a' = tous) [défaut: tous] : "
            ).strip().lower()

            if not raw or raw == "a":
                selected_token_indices = list(range(1, len(token_files) + 1))
            else:
                selected_token_indices = []
                for token in raw.split(","):
                    token = token.strip()
                    if token.isdigit() and 1 <= int(token) <= len(token_files):
                        selected_token_indices.append(int(token))

            for idx in selected_token_indices:
                fname, path, data = token_files[idx - 1]
                modes = data.get("modes", {})
                mode_items = list(modes.items())

                if len(mode_items) <= 1:
                    selected_mode_ids = [m[0] for m in mode_items]
                else:
                    print(f"\n  Modes disponibles pour '{fname}' :")
                    for i, (mode_id, mode_name) in enumerate(mode_items, start=1):
                        print(f"    {i}. {mode_name}")
                    raw_modes = input(
                        f"  Mode(s) à inclure (numéros, 'a' = tous) [défaut: 1] : "
                    ).strip().lower()
                    if not raw_modes:
                        selected_mode_ids = [mode_items[0][0]]
                    elif raw_modes == "a":
                        selected_mode_ids = [m[0] for m in mode_items]
                    else:
                        selected_mode_ids = []
                        for token in raw_modes.split(","):
                            token = token.strip()
                            if token.isdigit() and 1 <= int(token) <= len(mode_items):
                                selected_mode_ids.append(mode_items[int(token) - 1][0])

                colors = extract_colors_from_file(data, selected_mode_ids)
                for name, value in colors:
                    palette.append(make_color(name, value))

                # Construire token_slugs à partir du premier mode sélectionné
                for mode_id in selected_mode_ids:
                    token_slugs.update(build_token_slugs(data, mode_id))

                print(f"  ✅ {len(colors)} couleur(s) extraite(s) de '{fname}'.")
        else:
            print("  ⚠️ Aucun fichier Token trouvé.")

        # --- Autres fichiers -> custom.color (optionnel) ---
        if other_files:
            print(f"\nAutres fichiers détectés (Colors, Styles, ...) :")
            for i, (fname, _, data) in enumerate(other_files, start=1):
                nb_vars = sum(1 for v in data.get("variables", []) if v.get("type") == "COLOR")
                modes = list(data.get("modes", {}).values())
                print(f"  {i}. {fname}  ({nb_vars} couleurs, modes: {', '.join(modes)})")

            do_custom = input(
                "\nMettre ces couleurs dans custom.color (variables CSS) ? (o/n) [défaut: n] : "
            ).strip().lower()

            if do_custom in ("o", "oui", "y", "yes"):
                raw = input(
                    "Fichiers à inclure (numéros séparés par des virgules, "
                    "'a' = tous) [défaut: tous] : "
                ).strip().lower()

                if not raw or raw == "a":
                    selected_other_indices = list(range(1, len(other_files) + 1))
                else:
                    selected_other_indices = []
                    for token in raw.split(","):
                        token = token.strip()
                        if token.isdigit() and 1 <= int(token) <= len(other_files):
                            selected_other_indices.append(int(token))

                for idx in selected_other_indices:
                    fname, path, data = other_files[idx - 1]
                    modes = data.get("modes", {})
                    mode_items = list(modes.items())

                    if len(mode_items) <= 1:
                        selected_mode_ids = [m[0] for m in mode_items]
                    else:
                        print(f"\n  Modes disponibles pour '{fname}' :")
                        for i, (mode_id, mode_name) in enumerate(mode_items, start=1):
                            print(f"    {i}. {mode_name}")
                        raw_modes = input(
                            f"  Mode(s) à inclure (numéros, 'a' = tous) [défaut: 1] : "
                        ).strip().lower()
                        if not raw_modes:
                            selected_mode_ids = [mode_items[0][0]]
                        elif raw_modes == "a":
                            selected_mode_ids = [m[0] for m in mode_items]
                        else:
                            selected_mode_ids = []
                            for token in raw_modes.split(","):
                                token = token.strip()
                                if token.isdigit() and 1 <= int(token) <= len(mode_items):
                                    selected_mode_ids.append(mode_items[int(token) - 1][0])

                    cc = extract_custom_colors_from_file(data, selected_mode_ids)
                    custom_colors.update(cc)
                    print(f"  ✅ {len(cc)} couleur(s) custom extraites de '{fname}'.")
    else:
        print("  ⚠️ Aucun dossier fourni, extraction Figma ignorée.")

    # --- Couleurs manuelles --------------------------------------------
    print("\n--- COULEURS MANUELLES (optionnel) ---")
    print("Entrez d'éventuelles couleurs supplémentaires au format \"nom | valeur\", "
          "séparées par des virgules.")
    print("  Exemple : primary light | #DBEAFE, primary medium | #3B82F6")
    raw = input("\nCouleurs (Entrée pour ignorer) : ").strip()

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

    # --- Couleurs fixes --------------------------------------------------
    print("\n--- COULEURS FIXES ---")
    hardcoded = [
        ("error", "Error", "#EF4444"),
        ("success", "Success", "#10B981"),
        ("warning", "Warning", "#F59E0B")
    ]
    existing_slugs = {c["slug"] for c in palette}
    for slug, name, value in hardcoded:
        if slug in existing_slugs:
            continue
        add = input(f"  Ajouter '{name}' ({value}) ? (o/n) : ").strip().lower()
        if add in ("o", "oui", "y", "yes"):
            palette.append({"slug": slug, "name": name, "color": value})

    # --- Déduplication des slugs -----------------------------------------
    seen = {}
    deduped = []
    for entry in palette:
        slug = entry["slug"]
        if slug in seen:
            print(f"  ⚠️ Doublon ignoré : '{entry['name']}' (slug '{slug}' déjà utilisé "
                  f"par '{seen[slug]}')")
            continue
        seen[slug] = entry["name"]
        deduped.append(entry)
    palette = deduped

    # --- Personnalisation des couleurs ------------------------------------
    if palette:
        print("\n--- PERSONNALISATION DES COULEURS ---")
        print("(Entrée pour garder la valeur actuelle)")
        for entry in palette:
            new_color = input(
                f"  {entry['name']} ({entry['color']}) → nouvelle valeur : "
            ).strip()
            if new_color:
                entry["color"] = new_color

    if not palette:
        print("\n⚠️ Aucune couleur à traiter. Fin du script.")
        return

    # --- Gradients ---------------------------------------------------------
    gradients = []
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
            gradients.append(make_gradient(f"{name} to white", f"{slug}-to-white",
                                            f"linear-gradient(135deg, {color} 0%, #ffffff 100%)"))
            gradients.append(make_gradient(f"white to {name}", f"white-to-{slug}",
                                            f"linear-gradient(135deg, #ffffff 0%, {color} 100%)"))
            gradients.append(make_gradient(f"{name} to black", f"{slug}-to-black",
                                            f"linear-gradient(135deg, {color} 0%, #000000 100%)"))
            gradients.append(make_gradient(f"black to {name}", f"black-to-{slug}",
                                            f"linear-gradient(135deg, #000000 0%, {color} 100%)"))
    elif grad_choice == "2":
        for entry in palette:
            slug = entry["slug"]
            name = entry["name"]
            color = entry["color"]

            add_white = input(f"  Ajouter les dégradés blancs pour '{name}' ? (o/n) : ").strip().lower()
            if add_white in ("o", "oui", "y", "yes"):
                gradients.append(make_gradient(f"{name} to white", f"{slug}-to-white",
                                                f"linear-gradient(135deg, {color} 0%, #ffffff 100%)"))
                gradients.append(make_gradient(f"white to {name}", f"white-to-{slug}",
                                                f"linear-gradient(135deg, #ffffff 0%, {color} 100%)"))

            add_black = input(f"  Ajouter les dégradés noirs pour '{name}' ? (o/n) : ").strip().lower()
            if add_black in ("o", "oui", "y", "yes"):
                gradients.append(make_gradient(f"{name} to black", f"{slug}-to-black",
                                                f"linear-gradient(135deg, {color} 0%, #000000 100%)"))
                gradients.append(make_gradient(f"black to {name}", f"black-to-{slug}",
                                                f"linear-gradient(135deg, #000000 0%, {color} 100%)"))

    # --- Duotones ------------------------------------------------------------
    duotones = []
    print("\n--- DUOTONES ---")
    print("  0 : aucun")
    print("  1 : générer tous les duotones")
    print("  2 : manuel")
    duo_choice = input("Générer les duotones (0/1/2) [défaut 0] : ").strip().lower()
    if not duo_choice:
        duo_choice = "0"

    if duo_choice in ("1", "2"):
        print("\nEntrez d'éventuels duotones personnalisés au format "
              "\"nom | couleur1,couleur2\", séparés par des points-virgules.")
        print("  Exemple : Noir et blanc | #000000,#ffffff; Violet et jaune | #8c00b7,#fcff41")
        raw_duos = input("Duotones (Entrée pour ignorer) : ").strip()
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

    # --- Format de sortie ---------------------------------------------------
    print("\n--- FORMAT ---")
    print("  json : génère un objet JSON (ou met à jour un theme.json existant)")
    print("  css  : génère des variables CSS dans :root")
    format_choice = input("Format (json/css) [défaut json] : ").strip().lower()
    if not format_choice:
        format_choice = "json"

    if format_choice == "css":
        output = generate_css(palette, gradients, duotones)
    else:
        output = json.dumps(
            {"palette": palette, "gradients": gradients, "duotones": duotones},
            indent=4, ensure_ascii=False
        )

    # --- Affichage -----------------------------------------------------------
    print("\n" + "=" * 60)
    print(output)

    # --- Sauvegarde ------------------------------------------------------------
    print("\n" + "=" * 60)
    print("Sauvegarde :")
    if format_choice == "css":
        print("  - Chemin vers fichier .css")
    else:
        print("  - Chemin vers theme.json → remplace palette/gradients/duotone dans le fichier")
        print("  - Autre nom → sauvegarde le JSON standalone")
    print("  - Entrée → affichage uniquement")
    save = input(f"\nFichier de destination [défaut: {default_theme_json}] : ").strip()

    if not save:
        save = default_theme_json

    if format_choice == "css":
        with open(save, "w", encoding="utf-8") as f:
            f.write(output)
            f.write("\n")
        print(f"✅ CSS sauvegardé dans {save}")
        return

    merged_into_theme = False
    if save.endswith(".json") and os.path.isfile(save):
        with open(save, "r", encoding="utf-8") as f:
            content = f.read()
        try:
            data = json.loads(content)
            if "settings" in data and "version" in data:
                merge_into_theme_json(save, palette, gradients, duotones,
                                      custom_colors=custom_colors if custom_colors else None)
                merged_into_theme = True
        except json.JSONDecodeError:
            pass

    if not merged_into_theme:
        with open(save, "w", encoding="utf-8") as f:
            f.write(output)
            f.write("\n")
        print(f"✅ JSON sauvegardé dans {save}")


    # --- Styles de sections -------------------------------------------------
    print("\n--- STYLES DE SECTIONS ---")
    print("Générer des styles de sections à partir des exports Figma ?")
    print("  Chaque mode (Light, Medium, Dark, ...) devient un style numéroté (style1, style2, ...)")
    print("  Les couleurs sont résolues via les alias Token -> var:preset|color|<slug>")
    do_styles = input("Générer les styles de sections ? (o/n) [défaut: n] : ").strip().lower()

    if do_styles in ("o", "oui", "y", "yes"):
        styles_folder = input(
            f"Dossier contenant les fichiers de styles Figma "
            f"[défaut: {default_figma_folder}] : "
        ).strip().strip('"')
        if not styles_folder:
            styles_folder = default_figma_folder

        # Construire token_slugs si vide (si pas de dossier Figma fourni au départ)
        if not token_slugs and styles_folder and os.path.isdir(styles_folder):
            styles_files = scan_figma_files(styles_folder)
            token_file = next((f for fname, _, f in styles_files if fname == "Token.json"), None)
            if token_file:
                token_slugs = build_token_slugs(token_file)
                print(f"✅ {len(token_slugs)} slugs extraits de Token.json")
            else:
                print("  ⚠️ Token.json non trouvé dans le dossier. Les couleurs seront en hex.")

        theme_path_input = input(
            f"Chemin vers theme.json à mettre à jour "
            f"[défaut: {default_theme_json}] : "
        ).strip().strip('"')
        if not theme_path_input:
            theme_path_input = default_theme_json

        default_sections_dir = os.path.join(script_dir, "styles", "sections")
        sections_dir = input(
            f"Dossier pour les fichiers styleN.json [défaut: {default_sections_dir}] : "
        ).strip().strip('"')
        if not sections_dir:
            sections_dir = default_sections_dir

        generate_section_styles(
            styles_folder, theme_path_input, sections_dir,
            token_slugs=token_slugs if token_slugs else None,
            custom_colors=custom_colors if custom_colors else None
        )


# ---------------------------------------------------------------------------
# Styles de sections (Figma -> theme.json custom.style.N + styleN.json)
# ---------------------------------------------------------------------------

# Mapping entre les noms de variables Figma (Styles.json) et la structure
# custom.style.N du theme.json.
STYLE_VAR_MAPPING = {
    "Background/page":            ("background",),
    "Text/body":                  ("text",),
    "Text/title":                 ("heading", "text"),
    "Text/link":                  ("link", "text"),
    "Text/hover":                 ("link", "hover-text"),
    "Text/accent":                ("accent",),
    "Background/button":          ("button", "background"),
    "Text/button":                ("button", "text"),
    "Border/button":              ("button", "border-color"),
    "Background/button-hover":    ("button", "hover-background"),
    "Text/button-hover":          ("button", "hover-text"),
    "Border/button-hover":        ("button", "hover-border"),
    "Border/decorative":          ("decorative", "border-color"),
    "Text/placeholder":           ("input", "placeholder"),
    "Background/input":           ("input", "background"),
    "Text/error":                 ("error",),
}


def is_style_file(data):
    """Détecte si un fichier Figma contient des variables de style (Background/, Text/, Border/)."""
    if not isinstance(data, dict) or "variables" not in data:
        return False
    for var in data.get("variables", []):
        if var.get("type") == "COLOR" and var.get("name", "") in STYLE_VAR_MAPPING:
            return True
    return False


def extract_style_from_mode(data, mode_id, token_slugs=None):
    """
    Extrait les variables de style pour un mode donné.
    Retourne un dict imbriqué correspondant à la structure custom.style.N.
    Si token_slugs est fourni (dict {alias_name: slug}), génère des références
    var:preset|color|<slug> au lieu de valeurs hex.
    """
    result = {}
    for var in data.get("variables", []):
        if var.get("type") != "COLOR":
            continue
        name = var.get("name", "")
        if name not in STYLE_VAR_MAPPING:
            continue
        rv = var.get("resolvedValuesByMode", {}).get(mode_id)
        if not rv:
            continue

        if token_slugs:
            alias_name = rv.get("aliasName", "")
            if alias_name and alias_name in token_slugs:
                value = f"var:preset|color|{token_slugs[alias_name]}"
            else:
                val = rv.get("resolvedValue")
                if not val or not isinstance(val, dict) or "r" not in val:
                    continue
                value = figma_rgba_to_hex(val)
        else:
            val = rv.get("resolvedValue")
            if not val or not isinstance(val, dict) or "r" not in val:
                continue
            value = figma_rgba_to_hex(val)

        path = STYLE_VAR_MAPPING[name]
        d = result
        for key in path[:-1]:
            if key not in d:
                d[key] = {}
            d = d[key]
        d[path[-1]] = value
    return result


def build_style_json(style_id):
    """Génère le contenu d'un fichier styleN.json pour styles/sections/.
    style_id peut être un entier (1, 2, ...) ou une chaîne ('default')."""
    slug = f"style{style_id}" if isinstance(style_id, int) else f"style-{style_id}"
    prefix = f"var:custom|style|{style_id}"
    return {
        "$schema": "https://schemas.wp.org/trunk/theme.json",
        "version": 3,
        "slug": slug,
        "title": slug,
        "blockTypes": [
            "core/group",
            "core/columns",
            "core/column",
            "core/cover"
        ],
        "styles": {
            "color": {
                "background": f"{prefix}|background",
                "text": f"{prefix}|text"
            },
            "blocks": {
                "core/button": {
                    "color": {
                        "background": f"{prefix}|button|background",
                        "text": f"{prefix}|button|text"
                    },
                    "border": {
                        "color": f"{prefix}|button|border-color",
                        "width": "1px",
                        "radius": "40"
                    }
                }
            },
            "elements": {
                "button": {
                    ":hover": {
                        "color": {
                            "background": f"{prefix}|button|hover-background !important",
                            "text": f"{prefix}|button|hover-text !important"
                        },
                        "border": {
                            "color": f"{prefix}|button|hover-border !important"
                        }
                    }
                },
                "heading": {
                    "color": {
                        "text": f"{prefix}|heading|text"
                    }
                },
                "link": {
                    "color": {
                        "text": f"{prefix}|link|text"
                    },
                    ":hover": {
                        "color": {
                            "text": f"{prefix}|link|hover-text"
                        }
                    },
                    "typography": {
                        "textDecoration": "none"
                    }
                }
            }
        }
    }


def extract_default_style_from_theme(theme_path):
    """
    Extrait les valeurs de style par défaut depuis theme.json
    pour créer l'entrée custom.style.default.
    """
    with open(theme_path, "r", encoding="utf-8") as f:
        theme = json.load(f)

    styles = theme.get("styles", {})
    settings = theme.get("settings", {})
    custom = settings.get("custom", {})

    default_style = {}

    # background et text
    color = styles.get("color", {})
    default_style["background"] = color.get("background", "var:custom|color|background")
    default_style["text"] = color.get("text", "var:custom|color|text")

    # heading (pas de couleur explicite dans le thème de base -> hérite de text)
    default_style["heading"] = {
        "text": styles.get("elements", {}).get("heading", {}).get("color", {}).get("text", default_style["text"])
    }

    # link (pas de couleur explicite -> hérite de text)
    link_el = styles.get("elements", {}).get("link", {})
    default_style["link"] = {
        "text": link_el.get("color", {}).get("text", default_style["text"]),
        "hover-text": link_el.get(":hover", {}).get("color", {}).get("text", "var:preset|color|primary-default")
    }

    # button
    btn_block = styles.get("blocks", {}).get("core/button", {})
    btn_color = btn_block.get("color", {})
    btn_border = btn_block.get("border", {})
    default_style["button"] = {
        "background": btn_color.get("background", "var:preset|color|accent"),
        "hover-background": btn_color.get(":hover", {}).get("background", "var:preset|color|accent-2"),
        "text": btn_color.get("text", "var:custom|color|text"),
        "hover-text": btn_color.get(":hover", {}).get("text", "var:custom|color|text"),
        "border-color": btn_border.get("color", "var:preset|color|accent"),
        "hover-border": btn_border.get(":hover", {}).get("color", "var:preset|color|accent-2")
    }

    # accent
    default_style["accent"] = "var:preset|color|accent"

    # decorative
    default_style["decorative"] = {
        "border-color": "var:preset|color|accent"
    }

    # input
    input_custom = custom.get("input", {})
    default_style["input"] = {
        "placeholder": input_custom.get("color-placeholder", "var:preset|color|neutral-subtle"),
        "background": input_custom.get("color-background", "var:preset|color|neutral-light")
    }

    # error
    default_style["error"] = "var:preset|color|semantic-error"

    return default_style


def merge_styles_into_theme_json(theme_path, styles_data, custom_colors=None):
    """
    Met à jour settings.custom.style dans theme.json avec les styles extraits.
    styles_data est un dict { "1": {...}, "2": {...}, ... }
    custom_colors est un dict optionnel { slug: hex } à placer dans custom.color.
    """
    with open(theme_path, "r", encoding="utf-8") as f:
        theme = json.load(f)

    if "settings" not in theme:
        theme["settings"] = {}
    if "custom" not in theme["settings"]:
        theme["settings"]["custom"] = {}
    if "style" not in theme["settings"]["custom"]:
        theme["settings"]["custom"]["style"] = {}

    for num, style_vars in styles_data.items():
        theme["settings"]["custom"]["style"][str(num)] = style_vars

    if custom_colors:
        if "color" not in theme["settings"]["custom"]:
            theme["settings"]["custom"]["color"] = {}
        for slug, hex_val in custom_colors.items():
            theme["settings"]["custom"]["color"][slug] = hex_val

    with open(theme_path, "w", encoding="utf-8") as f:
        json.dump(theme, f, indent=4, ensure_ascii=False)
        f.write("\n")

    print(f"✅ theme.json mis à jour : custom.style avec {len(styles_data)} style(s)")
    if custom_colors:
        print(f"✅ theme.json mis à jour : custom.color avec {len(custom_colors)} couleur(s)")


def build_token_slugs(token_data, mode_id=None):
    """
    Construit un dict {variable_name: slug} à partir d'un fichier Token Figma.
    Si mode_id est None, prend le premier mode disponible.
    """
    modes = token_data.get("modes", {})
    if mode_id is None:
        mode_id = list(modes.keys())[0] if modes else None
    if not mode_id:
        return {}

    slugs = {}
    for var in token_data.get("variables", []):
        if var.get("type") != "COLOR":
            continue
        name = var.get("name", "")
        rv = var.get("resolvedValuesByMode", {}).get(mode_id)
        if rv:
            slugs[name] = slugify(name)
    return slugs


def extract_custom_colors_from_file(data, selected_mode_ids):
    """
    Extrait les couleurs d'un fichier Figma pour les placer dans custom.color.
    Retourne un dict {slug: hex}.
    Si plusieurs modes sont sélectionnés, le nom du mode est ajouté au slug.
    """
    modes = data.get("modes", {})
    multi_mode = len(selected_mode_ids) > 1
    result = {}

    for var in data.get("variables", []):
        if var.get("type") != "COLOR":
            continue
        for mode_id in selected_mode_ids:
            rv = var.get("resolvedValuesByMode", {}).get(mode_id)
            if not rv:
                continue
            val = rv.get("resolvedValue")
            if not val or not isinstance(val, dict) or "r" not in val:
                continue
            hexcode = figma_rgba_to_hex(val)
            name = var["name"]
            if multi_mode:
                mode_name = modes.get(mode_id, mode_id)
                slug = slugify(f"{name} {mode_name}")
            else:
                slug = slugify(name)
            result[slug] = hexcode
    return result


def generate_section_styles(folder, theme_path, sections_dir, token_slugs=None, custom_colors=None):
    """
    Flux interactif pour générer les styles de sections à partir d'un export Figma.
    - Détecte les fichiers contenant des variables de style (Background/, Text/, Border/)
    - Pour chaque mode sélectionné, crée un style numéroté (style1, style2, ...)
    - Met à jour theme.json avec custom.style.N (références var:preset|color|<slug>)
    - Crée les fichiers styleN.json dans styles/sections/
    """
    files = scan_figma_files(folder)
    style_files = [(fname, path, data) for fname, path, data in files if is_style_file(data)]

    if not style_files:
        print(f"  ⚠️ Aucun fichier de styles Figma valide trouvé dans '{folder}'.")
        return

    print(f"\nFichiers de styles détectés dans '{folder}' :")
    for i, (fname, _, data) in enumerate(style_files, start=1):
        nb_vars = sum(1 for v in data.get("variables", []) if v.get("name", "") in STYLE_VAR_MAPPING)
        modes = list(data.get("modes", {}).values())
        print(f"  {i}. {fname}  ({nb_vars} variables de style, modes: {', '.join(modes)})")

    raw = input(
        "\nFichiers à inclure (numéros séparés par des virgules, "
        "'a' = tous) [défaut: tous] : "
    ).strip().lower()

    if not raw or raw == "a":
        selected_indices = list(range(1, len(style_files) + 1))
    else:
        selected_indices = []
        for token in raw.split(","):
            token = token.strip()
            if token.isdigit() and 1 <= int(token) <= len(style_files):
                selected_indices.append(int(token))

    all_styles = {}  # { "1": {...}, "2": {...}, ... }
    style_counter = 1

    for idx in selected_indices:
        fname, path, data = style_files[idx - 1]
        modes = data.get("modes", {})
        mode_items = list(modes.items())  # [(mode_id, mode_name), ...]

        if len(mode_items) <= 1:
            selected_mode_ids = [m[0] for m in mode_items]
        else:
            print(f"\n  Modes disponibles pour '{fname}' :")
            for i, (mode_id, mode_name) in enumerate(mode_items, start=1):
                print(f"    {i}. {mode_name}")
            raw_modes = input(
                f"  Mode(s) à inclure pour '{fname}' (numéros séparés par des "
                f"virgules, 'a' = tous) [défaut: tous] : "
            ).strip().lower()
            if not raw_modes or raw_modes == "a":
                selected_mode_ids = [m[0] for m in mode_items]
            else:
                selected_mode_ids = []
                for token in raw_modes.split(","):
                    token = token.strip()
                    if token.isdigit() and 1 <= int(token) <= len(mode_items):
                        selected_mode_ids.append(mode_items[int(token) - 1][0])

        for mode_id in selected_mode_ids:
            mode_name = modes.get(mode_id, mode_id)
            style_vars = extract_style_from_mode(data, mode_id, token_slugs=token_slugs)
            if not style_vars:
                continue
            num = str(style_counter)
            all_styles[num] = style_vars
            print(f"  ✅ Style {style_counter} créé depuis '{fname}' mode '{mode_name}' ({len(style_vars)} variables)")
            style_counter += 1

    if not all_styles:
        print("  ⚠️ Aucun style à générer.")
        return

    # --- Ajouter le style default depuis theme.json ---
    if theme_path and os.path.isfile(theme_path):
        default_style = extract_default_style_from_theme(theme_path)
        all_styles["default"] = default_style
        print(f"  ✅ Style default créé depuis theme.json ({len(default_style)} variables)")
    else:
        print("  ⚠️ theme.json introuvable, style default non créé.")

    # --- Mettre à jour theme.json ---
    if theme_path and os.path.isfile(theme_path):
        merge_styles_into_theme_json(theme_path, all_styles, custom_colors=custom_colors)
    else:
        print(f"  ⚠️ theme.json introuvable à '{theme_path}', variables custom.style non écrites.")

    # --- Générer les fichiers styleN.json ---
    if sections_dir:
        os.makedirs(sections_dir, exist_ok=True)
        for num in all_styles:
            if num == "default":
                style_json = build_style_json("default")
                json_path = os.path.join(sections_dir, "style-default.json")
            else:
                style_json = build_style_json(int(num))
                json_path = os.path.join(sections_dir, f"style{num}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(style_json, f, indent=4, ensure_ascii=False)
                f.write("\n")
            print(f"  ✅ {json_path}")
    else:
        print("  ⚠️ Aucun dossier de sections fourni, fichiers styleN.json non créés.")


if __name__ == "__main__":
    main()