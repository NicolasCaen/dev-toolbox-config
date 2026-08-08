#!/usr/bin/env python3
"""
Générateur radiusSizes JSON pour WordPress/Gutenberg.
- Valeurs fixes et clamp mélangées dans une seule saisie
- Slug = valeur en px (ex: "4", "4-8")
- Valeurs spéciales : full (100%), rounded (10rem)
"""

import json
import os
from itertools import groupby


def px_to_rem(px):
    return px / 16


def format_rem_short(value):
    """Formate rem sans suffixe (ex: 0.25 → '.25', 1.0 → '1', 3.5 → '3.5')."""
    if value == int(value):
        return str(int(value))
    s = f"{round(value, 4)}"
    s = s.rstrip('0').rstrip('.')
    if s.startswith('0.'):
        return s[1:]
    return s


def format_rem(value):
    return format_rem_short(value) + "rem"


def format_vw(value):
    """Formate une valeur vw sans suffixe rem (ex: 0.175 → '.175', 1.0 → '1')."""
    if value == int(value):
        return str(int(value))
    s = f"{round(value, 6)}"
    s = s.rstrip('0').rstrip('.')
    if s.startswith('0.'):
        return s[1:]
    return s


def calc_clamp(min_px, max_px, min_vp=500, max_vp=1500):
    """Calcule clamp(min, preferred, max) avec interpolation linéaire."""
    min_rem = px_to_rem(min_px)
    max_rem = px_to_rem(max_px)

    slope = (max_rem - min_rem) / (max_vp - min_vp)
    intercept = min_rem - slope * min_vp
    slope_vw = slope * 100

    min_str = format_rem(min_rem)
    max_str = format_rem(max_rem)
    intercept_str = format_rem_short(intercept)
    slope_vw_str = format_vw(slope_vw)

    if intercept >= 0:
        preferred = f"{intercept_str}rem + {slope_vw_str}vw"
    else:
        preferred = f"-{format_rem_short(abs(intercept))}rem + {slope_vw_str}vw"

    return f"clamp({min_str}, {preferred}, {max_str})"


def make_fixed(slug, px):
    rem_short = format_rem_short(px_to_rem(px))
    return {
        "slug": str(slug),
        "name": str(slug),
        "size": rem_short + "rem" if px != 0 else "0"
    }


def make_fluid(slug, min_px, max_px, min_vp=500, max_vp=1500):
    clamp_val = calc_clamp(min_px, max_px, min_vp, max_vp)
    return {
        "slug": str(slug),
        "name": str(slug),
        "size": clamp_val
    }


def make_special(slug, name, size):
    return {"slug": slug, "name": name, "size": size}


def parse_entry(entry):
    """Parse : '4' = fixe, '4-8' = clamp."""
    if "-" in entry:
        parts = entry.split("-")
        if len(parts) == 2:
            try:
                return ("fluid", int(parts[0]), int(parts[1]))
            except ValueError:
                return None
    else:
        try:
            return ("fixed", int(entry), None)
        except ValueError:
            return None
    return None


def generate_radius_sizes(raw, min_vp, max_vp, specials):
    """Génère la liste radiusSizes à partir de la saisie."""
    entries = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        parsed = parse_entry(token)
        if parsed:
            entries.append(parsed)
        else:
            print(f"  ⚠️ Ignoré : '{token}' (format invalide)")

    fixed = [px for kind, px, _ in entries if kind == "fixed"]
    fluid = [(mn, mx) for kind, mn, mx in entries if kind == "fluid"]

    radius_sizes = []

    for px in fixed:
        radius_sizes.append(make_fixed(px, px))

    if fluid:
        fluid.sort(key=lambda x: (x[0], x[1]))
        for min_px, group in groupby(fluid, key=lambda x: x[0]):
            for mn, mx in group:
                slug = f"{mn}-{mx}"
                radius_sizes.append(make_fluid(slug, mn, mx, min_vp, max_vp))

    for slug, name, size in specials:
        radius_sizes.append(make_special(slug, name, size))

    return radius_sizes


def merge_into_theme_json(theme_path, radius_sizes):
    """Remplace radiusSizes dans un fichier theme.json."""
    with open(theme_path, 'r', encoding='utf-8') as f:
        theme = json.load(f)

    if "settings" not in theme:
        theme["settings"] = {}
    if "border" not in theme["settings"]:
        theme["settings"]["border"] = {}

    theme["settings"]["border"]["radiusSizes"] = radius_sizes

    with open(theme_path, 'w', encoding='utf-8') as f:
        json.dump(theme, f, indent=4, ensure_ascii=False)
        f.write("\n")

    print(f"✅ theme.json mis à jour : {theme_path}")


def generate_css(radius_sizes, prefix="--wp--preset--radius--"):
    """Génère un bloc :root avec des variables CSS."""
    lines = [":root {"]
    for entry in radius_sizes:
        slug = entry["slug"]
        size = entry["size"]
        lines.append(f"  {prefix}{slug}: {size};")
    lines.append("}")
    return "\n".join(lines)


def main():
    print("=" * 60)
    print("  Générateur radiusSizes pour WordPress/Gutenberg")
    print("=" * 60)

    print("\n--- VALEURS ---")
    print("Entrez les valeurs séparées par des virgules.")
    print("  Fixe : 0, 4, 8, 16, 24")
    print("  Clamp : 4-8, 8-16, 16-24 (min-max en px)")
    print("Exemple : 0,4,8,16,24,4-8,4-16,4-24,8-16,8-24,16-24")
    raw = input("\nValeurs : ").strip()
    if not raw:
        raw = "0,4,8,16,24"

    print("\n--- PARAMÈTRES CLAMP ---")
    min_vp_input = input("Viewport min en px (défaut 500) : ").strip()
    max_vp_input = input("Viewport max en px (défaut 1500) : ").strip()
    min_vp = int(min_vp_input) if min_vp_input else 500
    max_vp = int(max_vp_input) if max_vp_input else 1500

    print("\n--- VALEURS SPÉCIALES ---")
    specials = []
    special_presets = [
        ("full", "full", "100%"),
        ("rounded", "rounded", "10rem")
    ]
    for slug, name, size in special_presets:
        response = input(f"  Ajouter '{name}' ({slug}) ? (o/n) : ").strip().lower()
        if response in ("o", "oui", "y", "yes"):
            specials.append((slug, name, size))

    # Génération
    radius_sizes = generate_radius_sizes(raw, min_vp, max_vp, specials)

    # Format de sortie
    print("\n--- FORMAT ---")
    print("  json : génère un objet JSON (theme.json/size.json)")
    print("  css  : génère des variables CSS dans :root")
    format_choice = input("Format (json/css) [défaut json] : ").strip().lower()
    if not format_choice:
        format_choice = "json"

    if format_choice == "css":
        prefix = input("Préfixe CSS (défaut --wp--preset--radius--) : ").strip()
        if not prefix:
            prefix = "--wp--preset--radius--"
        output = generate_css(radius_sizes, prefix)
    else:
        output = json.dumps({"radiusSizes": radius_sizes}, indent=4, ensure_ascii=False)

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
        print("  - Chemin vers theme.json → remplace radiusSizes dans le fichier")
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
        # Vérifier si c'est un theme.json
        with open(save, 'r', encoding='utf-8') as f:
            content = f.read()
        try:
            data = json.loads(content)
            if "settings" in data and "version" in data:
                # C'est un theme.json
                merge_into_theme_json(save, radius_sizes)
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
