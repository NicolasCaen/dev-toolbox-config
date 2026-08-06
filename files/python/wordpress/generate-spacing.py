#!/usr/bin/env python3
"""
Générateur spacingSizes JSON pour WordPress/Gutenberg.
- Valeurs fixes et clamp mélangées dans une seule saisie
- Format name : "slug | rem" (ex: "4 | .25", "16-56 | 1->3.5")
- Peut écrire directement dans un fichier theme.json
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
    intercept_str = format_rem(intercept)
    slope_vw_str = format_vw(slope_vw)

    if intercept >= 0:
        preferred = f"{intercept_str}rem + {slope_vw_str}vw"
    else:
        preferred = f"-{format_rem(abs(intercept))} + {slope_vw_str}vw"

    return f"clamp({min_str}, {preferred}, {max_str})"

def make_fixed(slug, px, prefix=""):
    rem_short = format_rem_short(px_to_rem(px))
    full_slug = f"{prefix}{slug}" if prefix else str(slug)
    return {
        "slug": full_slug,
        "name": f"{full_slug} | {rem_short}",
        "size": rem_short + "rem" if px != 0 else "0"
    }

def make_fluid(slug, min_px, max_px, min_vp=500, max_vp=1500, prefix=""):
    min_short = format_rem_short(px_to_rem(min_px))
    max_short = format_rem_short(px_to_rem(max_px))
    clamp_val = calc_clamp(min_px, max_px, min_vp, max_vp)
    full_slug = f"{prefix}{slug}" if prefix else str(slug)
    return {
        "slug": full_slug,
        "name": f"{full_slug} | {min_short}->{max_short}",
        "size": clamp_val
    }

def make_special(slug, name, size):
    return {"slug": slug, "name": name, "size": size}

def parse_entry(entry):
    """Parse : '16' = fixe, '16-56' = clamp, 'h-16-56' = clamp h-."""
    prefix = ""
    if entry.startswith("h-"):
        prefix = "h-"
        entry = entry[2:]

    if "-" in entry:
        parts = entry.split("-")
        if len(parts) == 2:
            try:
                return ("fluid", int(parts[0]), int(parts[1]), prefix)
            except ValueError:
                return None
    else:
        try:
            return ("fixed", int(entry), None, prefix)
        except ValueError:
            return None
    return None

def generate_spacing_sizes(raw, min_vp, max_vp, specials):
    """Génère la liste spacingSizes à partir de la saisie."""
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

    fixed = [(px, pfx) for kind, px, _, pfx in entries if kind == "fixed"]
    fluid = [(mn, mx, pfx) for kind, mn, mx, pfx in entries if kind == "fluid"]

    normal_fixed = [(px, pfx) for px, pfx in fixed if not pfx]
    h_fixed = [(px, pfx) for px, pfx in fixed if pfx]
    normal_fluid = [(mn, mx, pfx) for mn, mx, pfx in fluid if not pfx]
    h_fluid = [(mn, mx, pfx) for mn, mx, pfx in fluid if pfx]

    spacing_sizes = []

    for px, _ in normal_fixed:
        spacing_sizes.append(make_fixed(px, px))

    if normal_fluid:
        normal_fluid.sort(key=lambda x: (x[0], x[1]))
        for min_px, group in groupby(normal_fluid, key=lambda x: x[0]):
            for mn, mx, _ in group:
                slug = f"{mn}-{mx}"
                spacing_sizes.append(make_fluid(slug, mn, mx, min_vp, max_vp))

    for px, _ in h_fixed:
        spacing_sizes.append(make_fixed(px, px, prefix="h-"))

    if h_fluid:
        h_fluid.sort(key=lambda x: (x[0], x[1]))
        for min_px, group in groupby(h_fluid, key=lambda x: x[0]):
            for mn, mx, _ in group:
                slug = f"{mn}-{mx}"
                spacing_sizes.append(make_fluid(slug, mn, mx, min_vp, max_vp, prefix="h-"))

    for slug, name, size in specials:
        spacing_sizes.append(make_special(slug, name, size))

    return spacing_sizes

def merge_into_theme_json(theme_path, spacing_sizes):
    """Remplace spacingSizes dans un fichier theme.json."""
    with open(theme_path, 'r', encoding='utf-8') as f:
        theme = json.load(f)

    if "settings" not in theme:
        theme["settings"] = {}
    if "spacing" not in theme["settings"]:
        theme["settings"]["spacing"] = {}

    theme["settings"]["spacing"]["spacingSizes"] = spacing_sizes

    with open(theme_path, 'w', encoding='utf-8') as f:
        json.dump(theme, f, indent=4, ensure_ascii=False)
        f.write("\n")

    print(f"✅ theme.json mis à jour : {theme_path}")

def main():
    print("=" * 60)
    print("  Générateur spacingSizes pour WordPress/Gutenberg")
    print("=" * 60)

    print("\n--- VALEURS ---")
    print("Entrez les valeurs séparées par des virgules.")
    print("  Fixe  : 0, 4, 8, 16, 32")
    print("  Clamp : 16-56, 56-120 (min-max en px)")
    print("  Hauteur : h-16, h-16-56 (préfixe h-)")
    print("Exemple : 0,4,8,16,24,32,40,56,72,80,120,160,200,240,16-24,16-32,16-40,16-56,16-72,16-120,16-160,24-32,24-40,24-56,24-72,32-40,32-56,32-72,40-56,40-72,40,80,40-120,40-160,40-200,40-240,56-72,56-80,56-120,56-160,56-200,56-240,72-80,72-120,72-160,72-200-240")
    raw = input("\nValeurs : ").strip()
    if not raw:
        raw = "0,4,8,16,24,32,40,56,72,80,120,160,200,240,16-24,16-32,16-40,16-56,16-72,16-120,16-160,24-32,24-40,24-56,24-72,32-40,32-56,32-72,40-56,40-72,40,80,40-120,40-160,40-200,40-240,56-72,56-80,56-120,56-160,56-200,56-240,72-80,72-120,72-160,72-200,72-240"

    print("\n--- PARAMÈTRES CLAMP ---")
    min_vp_input = input("Viewport min en px (défaut 500) : ").strip()
    max_vp_input = input("Viewport max en px (défaut 1500) : ").strip()
    min_vp = int(min_vp_input) if min_vp_input else 500
    max_vp = int(max_vp_input) if max_vp_input else 1500

    print("\n--- VALEURS SPÉCIALES ---")
    print("Laisser vide pour terminer.")
    specials = []
    while True:
        slug = input("  Slug (ex: headerheight) : ").strip()
        if not slug:
            break
        name = input("  Nom (ex: headerheight | Header Height) : ").strip()
        size = input("  Size (ex: var(--header-height)) : ").strip()
        specials.append((slug, name, size))

    # Génération
    spacing_sizes = generate_spacing_sizes(raw, min_vp, max_vp, specials)

    # Output JSON standalone
    output = json.dumps({"spacingSizes": spacing_sizes}, indent=4, ensure_ascii=False)
    print("\n" + "=" * 60)
    print(output)

    # Sauvegarde
    print("\n" + "=" * 60)
    print("Sauvegarde :")
    print("  - Chemin vers theme.json → remplace spacingSizes dans le fichier")
    print("  - Autre nom de fichier → sauvegarde le JSON standalone")
    print("  - Entrée → affichage uniquement")
    save = input("\nFichier de destination : ").strip()

    if not save:
        return

    if save.endswith('.json') and os.path.isfile(save):
        # Vérifier si c'est un theme.json
        with open(save, 'r', encoding='utf-8') as f:
            content = f.read()
        try:
            data = json.loads(content)
            if "settings" in data and "version" in data:
                # C'est un theme.json
                merge_into_theme_json(save, spacing_sizes)
                return
        except json.JSONDecodeError:
            pass

    # Sauvegarde standalone
    with open(save, 'w', encoding='utf-8') as f:
        f.write(output)
        f.write("\n")
    print(f"✅ Sauvegardé dans {save}")

if __name__ == "__main__":
    main()