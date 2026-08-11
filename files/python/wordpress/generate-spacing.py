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

def px_to_rem(px, root_px=16):
    return px / root_px

def format_number(value, decimals=4):
    """Formate un nombre comme la fonction formatNumber de l'extension Chrome.
    Garde le 0 initial (ex: 0.25 → '0.25', 1.0 → '1', 3.5 → '3.5')."""
    s = f"{value:.{decimals}f}"
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return s

def format_rem_short(value):
    """Formate rem sans suffixe (ex: 0.25 → '0.25', 1.0 → '1', 3.5 → '3.5')."""
    return format_number(value)

def format_rem(value):
    return format_rem_short(value) + "rem"

def format_vw(value):
    """Formate une valeur vw sans suffixe (ex: 0.175 → '0.175', 1.0 → '1')."""
    return format_number(value, decimals=6)

def calc_clamp(min_px, max_px, min_vp=500, max_vp=1500, root_px=16, zoom_friendly=True):
    """Calcule clamp(min, preferred, max) avec interpolation linéaire.
    
    Méthodes de calcul (comme l'extension Chrome) :
    - zoom_friendly=True : intercept en rem (scales avec le font-size du navigateur)
    - zoom_friendly=False : intercept en px (reste fixe regardless du font-size)
    """
    # Calcul en px (comme l'extension Chrome)
    slope = (max_px - min_px) / (max_vp - min_vp)
    vw_coeff = slope * 100
    intercept_px = min_px - slope * min_vp

    min_rem = px_to_rem(min_px, root_px)
    max_rem = px_to_rem(max_px, root_px)
    intercept_rem = px_to_rem(intercept_px, root_px)

    min_str = format_rem(min_rem)
    max_str = format_rem(max_rem)
    slope_vw_str = format_vw(vw_coeff)

    if zoom_friendly:
        # Zoom friendly : intercept en rem (scales avec browser font size)
        intercept_str = format_rem_short(intercept_rem)
        if intercept_rem >= 0:
            preferred = f"{intercept_str}rem + {slope_vw_str}vw"
        else:
            preferred = f"-{format_rem_short(abs(intercept_rem))}rem + {slope_vw_str}vw"
    else:
        # Standard : intercept en px (fixe regardless du font-size)
        intercept_str = format_number(intercept_px)
        if intercept_px >= 0:
            preferred = f"{intercept_str}px + {slope_vw_str}vw"
        else:
            preferred = f"-{format_number(abs(intercept_px))}px + {slope_vw_str}vw"

    return f"clamp({min_str}, {preferred}, {max_str})"

def make_fixed(slug, px, prefix="", root_px=16):
    rem_short = format_rem_short(px_to_rem(px, root_px))
    full_slug = f"{prefix}{slug}" if prefix else str(slug)
    return {
        "slug": full_slug,
        "name": f"{full_slug} | {rem_short}",
        "size": rem_short + "rem" if px != 0 else "0"
    }

def make_fluid(slug, min_px, max_px, min_vp=500, max_vp=1500, prefix="", root_px=16, zoom_friendly=True):
    min_short = format_rem_short(px_to_rem(min_px, root_px))
    max_short = format_rem_short(px_to_rem(max_px, root_px))
    clamp_val = calc_clamp(min_px, max_px, min_vp, max_vp, root_px, zoom_friendly)
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

def generate_spacing_sizes(raw, min_vp, max_vp, specials, root_px=16, zoom_friendly=True):
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
        spacing_sizes.append(make_fixed(px, px, root_px=root_px))

    if normal_fluid:
        normal_fluid.sort(key=lambda x: (x[0], x[1]))
        for min_px, group in groupby(normal_fluid, key=lambda x: x[0]):
            for mn, mx, _ in group:
                slug = f"{mn}-{mx}"
                spacing_sizes.append(make_fluid(slug, mn, mx, min_vp, max_vp, root_px=root_px, zoom_friendly=zoom_friendly))

    for px, _ in h_fixed:
        spacing_sizes.append(make_fixed(px, px, prefix="h-", root_px=root_px))

    if h_fluid:
        h_fluid.sort(key=lambda x: (x[0], x[1]))
        for min_px, group in groupby(h_fluid, key=lambda x: x[0]):
            for mn, mx, _ in group:
                slug = f"{mn}-{mx}"
                spacing_sizes.append(make_fluid(slug, mn, mx, min_vp, max_vp, prefix="h-", root_px=root_px, zoom_friendly=zoom_friendly))

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

def generate_css(spacing_sizes, prefix="--wp--preset--size--"):
    """Génère un bloc :root avec des variables CSS."""
    lines = [":root {"]
    for entry in spacing_sizes:
        slug = entry["slug"]
        size = entry["size"]
        lines.append(f"  {prefix}{slug}: {size};")
    lines.append("}")
    return "\n".join(lines)

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
    root_px_input = input("Root font-size en px (défaut 16) : ").strip()
    root_px = int(root_px_input) if root_px_input else 16

    min_vp_input = input("Viewport min en px (défaut 500) : ").strip()
    max_vp_input = input("Viewport max en px (défaut 1500) : ").strip()
    min_vp = int(min_vp_input) if min_vp_input else 500
    max_vp = int(max_vp_input) if max_vp_input else 1500

    print("\n--- MÉTHODE DE CALCUL ---")
    print("  zoom  : intercept en rem (scales avec le font-size du navigateur)")
    print("  px    : intercept en px (fixe, standard)")
    method_input = input("Méthode (zoom/px) [défaut zoom] : ").strip().lower()
    zoom_friendly = method_input != "px"

    print("\n--- VALEURS SPÉCIALES ---")
    specials = []
    special_presets = [
        ("headerheight", "Header height", "var(--headerheight)"),
        ("root-left", "Root padding left", "var(--wp--style--root--padding-left)"),
        ("root-right", "Root padding right", "var(--wp--style--root--padding-right)")
    ]
    for slug, name, size in special_presets:
        response = input(f"  Ajouter '{name}' ({slug}) ? (o/n) : ").strip().lower()
        if response in ("o", "oui", "y", "yes"):
            specials.append((slug, name, size))

    # Génération
    spacing_sizes = generate_spacing_sizes(raw, min_vp, max_vp, specials, root_px=root_px, zoom_friendly=zoom_friendly)

    # Format de sortie
    print("\n--- FORMAT ---")
    print("  json : génère un objet JSON (theme.json/size.json)")
    print("  css  : génère des variables CSS dans :root")
    format_choice = input("Format (json/css) [défaut json] : ").strip().lower()
    if not format_choice:
        format_choice = "json"

    if format_choice == "css":
        prefix = input("Préfixe CSS (défaut --wp--preset--size--) : ").strip()
        if not prefix:
            prefix = "--wp--preset--size--"
        output = generate_css(spacing_sizes, prefix)
    else:
        output = json.dumps({"spacingSizes": spacing_sizes}, indent=4, ensure_ascii=False)

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
        print("  - Chemin vers theme.json → remplace spacingSizes dans le fichier")
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
                merge_into_theme_json(save, spacing_sizes)
                return
        except json.JSONDecodeError:
            pass

    # Sauvegarde standalone JSON
    with open(save, 'w', encoding='utf-8') as f:
        f.write(output)
        f.write("\n")
    print(f"✅ JSON sauvegardé dans {save}")

if __name__ == "__main__":
    main()#!/usr/bin/env python3
"""
Générateur spacingSizes JSON pour WordPress/Gutenberg.
- Valeurs fixes et clamp mélangées dans une seule saisie
- Format name : "slug | rem" (ex: "4 | .25", "16-56 | 1->3.5")
- Peut écrire directement dans un fichier theme.json
"""

import json
import os
from itertools import groupby

def px_to_rem(px, root_px=16):
    return px / root_px

def format_number(value, decimals=4):
    """Formate un nombre comme la fonction formatNumber de l'extension Chrome.
    Garde le 0 initial (ex: 0.25 → '0.25', 1.0 → '1', 3.5 → '3.5')."""
    s = f"{value:.{decimals}f}"
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return s

def format_rem_short(value):
    """Formate rem sans suffixe (ex: 0.25 → '0.25', 1.0 → '1', 3.5 → '3.5')."""
    return format_number(value)

def format_rem(value):
    return format_rem_short(value) + "rem"

def format_vw(value):
    """Formate une valeur vw sans suffixe (ex: 0.175 → '0.175', 1.0 → '1')."""
    return format_number(value, decimals=6)

def calc_clamp(min_px, max_px, min_vp=500, max_vp=1500, root_px=16, zoom_friendly=True):
    """Calcule clamp(min, preferred, max) avec interpolation linéaire.
    
    Méthodes de calcul (comme l'extension Chrome) :
    - zoom_friendly=True : intercept en rem (scales avec le font-size du navigateur)
    - zoom_friendly=False : intercept en px (reste fixe regardless du font-size)
    """
    # Calcul en px (comme l'extension Chrome)
    slope = (max_px - min_px) / (max_vp - min_vp)
    vw_coeff = slope * 100
    intercept_px = min_px - slope * min_vp

    min_rem = px_to_rem(min_px, root_px)
    max_rem = px_to_rem(max_px, root_px)
    intercept_rem = px_to_rem(intercept_px, root_px)

    min_str = format_rem(min_rem)
    max_str = format_rem(max_rem)
    slope_vw_str = format_vw(vw_coeff)

    if zoom_friendly:
        # Zoom friendly : intercept en rem (scales avec browser font size)
        intercept_str = format_rem_short(intercept_rem)
        if intercept_rem >= 0:
            preferred = f"{intercept_str}rem + {slope_vw_str}vw"
        else:
            preferred = f"-{format_rem_short(abs(intercept_rem))}rem + {slope_vw_str}vw"
    else:
        # Standard : intercept en px (fixe regardless du font-size)
        intercept_str = format_number(intercept_px)
        if intercept_px >= 0:
            preferred = f"{intercept_str}px + {slope_vw_str}vw"
        else:
            preferred = f"-{format_number(abs(intercept_px))}px + {slope_vw_str}vw"

    return f"clamp({min_str}, {preferred}, {max_str})"

def make_fixed(slug, px, prefix="", root_px=16):
    rem_short = format_rem_short(px_to_rem(px, root_px))
    full_slug = f"{prefix}{slug}" if prefix else str(slug)
    return {
        "slug": full_slug,
        "name": f"{full_slug} | {rem_short}",
        "size": rem_short + "rem" if px != 0 else "0"
    }

def make_fluid(slug, min_px, max_px, min_vp=500, max_vp=1500, prefix="", root_px=16, zoom_friendly=True):
    min_short = format_rem_short(px_to_rem(min_px, root_px))
    max_short = format_rem_short(px_to_rem(max_px, root_px))
    clamp_val = calc_clamp(min_px, max_px, min_vp, max_vp, root_px, zoom_friendly)
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

def generate_spacing_sizes(raw, min_vp, max_vp, specials, root_px=16, zoom_friendly=True):
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
        spacing_sizes.append(make_fixed(px, px, root_px=root_px))

    if normal_fluid:
        normal_fluid.sort(key=lambda x: (x[0], x[1]))
        for min_px, group in groupby(normal_fluid, key=lambda x: x[0]):
            for mn, mx, _ in group:
                slug = f"{mn}-{mx}"
                spacing_sizes.append(make_fluid(slug, mn, mx, min_vp, max_vp, root_px=root_px, zoom_friendly=zoom_friendly))

    for px, _ in h_fixed:
        spacing_sizes.append(make_fixed(px, px, prefix="h-", root_px=root_px))

    if h_fluid:
        h_fluid.sort(key=lambda x: (x[0], x[1]))
        for min_px, group in groupby(h_fluid, key=lambda x: x[0]):
            for mn, mx, _ in group:
                slug = f"{mn}-{mx}"
                spacing_sizes.append(make_fluid(slug, mn, mx, min_vp, max_vp, prefix="h-", root_px=root_px, zoom_friendly=zoom_friendly))

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

def generate_css(spacing_sizes, prefix="--wp--preset--size--"):
    """Génère un bloc :root avec des variables CSS."""
    lines = [":root {"]
    for entry in spacing_sizes:
        slug = entry["slug"]
        size = entry["size"]
        lines.append(f"  {prefix}{slug}: {size};")
    lines.append("}")
    return "\n".join(lines)

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
    root_px_input = input("Root font-size en px (défaut 16) : ").strip()
    root_px = int(root_px_input) if root_px_input else 16

    min_vp_input = input("Viewport min en px (défaut 500) : ").strip()
    max_vp_input = input("Viewport max en px (défaut 1500) : ").strip()
    min_vp = int(min_vp_input) if min_vp_input else 500
    max_vp = int(max_vp_input) if max_vp_input else 1500

    print("\n--- MÉTHODE DE CALCUL ---")
    print("  zoom  : intercept en rem (scales avec le font-size du navigateur)")
    print("  px    : intercept en px (fixe, standard)")
    method_input = input("Méthode (zoom/px) [défaut zoom] : ").strip().lower()
    zoom_friendly = method_input != "px"

    print("\n--- VALEURS SPÉCIALES ---")
    specials = []
    special_presets = [
        ("headerheight", "Header height", "var(--headerheight)"),
        ("root-left", "Root padding left", "var(--wp--style--root--padding-left)"),
        ("root-right", "Root padding right", "var(--wp--style--root--padding-right)")
    ]
    for slug, name, size in special_presets:
        response = input(f"  Ajouter '{name}' ({slug}) ? (o/n) : ").strip().lower()
        if response in ("o", "oui", "y", "yes"):
            specials.append((slug, name, size))

    # Génération
    spacing_sizes = generate_spacing_sizes(raw, min_vp, max_vp, specials, root_px=root_px, zoom_friendly=zoom_friendly)

    # Format de sortie
    print("\n--- FORMAT ---")
    print("  json : génère un objet JSON (theme.json/size.json)")
    print("  css  : génère des variables CSS dans :root")
    format_choice = input("Format (json/css) [défaut json] : ").strip().lower()
    if not format_choice:
        format_choice = "json"

    if format_choice == "css":
        prefix = input("Préfixe CSS (défaut --wp--preset--size--) : ").strip()
        if not prefix:
            prefix = "--wp--preset--size--"
        output = generate_css(spacing_sizes, prefix)
    else:
        output = json.dumps({"spacingSizes": spacing_sizes}, indent=4, ensure_ascii=False)

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
        print("  - Chemin vers theme.json → remplace spacingSizes dans le fichier")
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
                merge_into_theme_json(save, spacing_sizes)
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