#!/usr/bin/env python3
"""
Générateur fontSizes JSON pour WordPress/Gutenberg, à partir d'un export de
variables Figma "Responsive" (collection avec 2 modes : desktop / mobile).

- Détecte automatiquement les fichiers de variables Figma dans un dossier.
- Extrait les variables FLOAT dont le nom contient "font/size" (ex:
  "typography/font/size/body/xsmall", "typography/font/size/title/large").
- Pour chaque variable, résout la valeur desktop (max) et mobile (min) en px.
- Si les deux valeurs sont identiques : taille fixe en rem.
- Si elles diffèrent : génère un clamp() fluide avec la même méthode de
  calcul que generate-spacing.py (calc_clamp / format_vw).
- Peut écrire directement dans settings.typography.fontSizes d'un theme.json
  existant, ou sauvegarder un JSON standalone {"fontSizes": [...]}.
"""

import json
import os
import re


# ---------------------------------------------------------------------------
# Utilitaires clamp (identiques à generate-spacing.py)
# ---------------------------------------------------------------------------

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
        intercept_str = format_rem_short(intercept_rem)
        if intercept_rem >= 0:
            preferred = f"{intercept_str}rem + {slope_vw_str}vw"
        else:
            preferred = f"-{format_rem_short(abs(intercept_rem))}rem + {slope_vw_str}vw"
    else:
        intercept_str = format_number(intercept_px)
        if intercept_px >= 0:
            preferred = f"{intercept_str}px + {slope_vw_str}vw"
        else:
            preferred = f"-{format_number(abs(intercept_px))}px + {slope_vw_str}vw"

    return f"clamp({min_str}, {preferred}, {max_str})"


# ---------------------------------------------------------------------------
# Slug / nom
# ---------------------------------------------------------------------------

def slugify(text):
    text = text.lower().strip()
    trans = str.maketrans("àâäçéèêëîïôöùûüÿñ", "aaaceeeeiioouuuyn")
    text = text.translate(trans)
    text = text.replace("/", "-")
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def slug_from_variable_name(name, marker="font/size/"):
    """Extrait un slug à partir d'un nom de variable Figma.
    'typography/font/size/body/xsmall' -> 'body-xsmall'"""
    idx = name.lower().find(marker)
    if idx != -1:
        tail = name[idx + len(marker):]
    else:
        tail = name
    return slugify(tail)


# ---------------------------------------------------------------------------
# Extraction Figma
# ---------------------------------------------------------------------------

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


def extract_font_size_variables(data, mobile_mode_id, desktop_mode_id, marker="font/size/"):
    """Retourne une liste de dicts {slug, name, mobile_px, desktop_px}
    pour les variables FLOAT dont le nom contient `marker`."""
    results = []
    for var in data.get("variables", []):
        if var.get("type") != "FLOAT":
            continue
        name = var.get("name", "")
        if marker not in name.lower():
            continue

        by_mode = var.get("resolvedValuesByMode", {})
        mobile_rv = by_mode.get(mobile_mode_id)
        desktop_rv = by_mode.get(desktop_mode_id)
        if not mobile_rv or not desktop_rv:
            continue

        mobile_val = mobile_rv.get("resolvedValue")
        desktop_val = desktop_rv.get("resolvedValue")
        if mobile_val is None or desktop_val is None:
            continue

        results.append({
            "slug": slug_from_variable_name(name, marker),
            "label": name,
            "mobile_px": float(mobile_val),
            "desktop_px": float(desktop_val),
        })
    return results


def choose_modes(data):
    """Détermine les mode_id mobile / desktop.
    Détection automatique par nom de mode ('mobile'/'desktop'), sinon demande à l'utilisateur."""
    modes = data.get("modes", {})
    mode_items = list(modes.items())  # [(mode_id, mode_name), ...]

    mobile_id = None
    desktop_id = None
    for mode_id, mode_name in mode_items:
        lname = mode_name.lower()
        if "mobile" in lname or "phone" in lname:
            mobile_id = mode_id
        elif "desktop" in lname or "web" in lname:
            desktop_id = mode_id

    if mobile_id and desktop_id:
        return mobile_id, desktop_id

    print("\n  Modes disponibles :")
    for i, (mode_id, mode_name) in enumerate(mode_items, start=1):
        print(f"    {i}. {mode_name}")

    raw_mobile = input("  Numéro du mode MOBILE (min) : ").strip()
    raw_desktop = input("  Numéro du mode DESKTOP (max) : ").strip()

    try:
        mobile_id = mode_items[int(raw_mobile) - 1][0]
        desktop_id = mode_items[int(raw_desktop) - 1][0]
    except (ValueError, IndexError):
        return None, None

    return mobile_id, desktop_id


# ---------------------------------------------------------------------------
# Génération fontSizes
# ---------------------------------------------------------------------------

def make_font_size(slug, mobile_px, desktop_px, min_vp=500, max_vp=1500,
                    root_px=16, zoom_friendly=True):
    mobile_short = format_rem_short(px_to_rem(mobile_px, root_px))
    desktop_short = format_rem_short(px_to_rem(desktop_px, root_px))

    if mobile_px == desktop_px:
        return {
            "slug": slug,
            "name": f"{slug} | {desktop_short}",
            "size": format_rem(px_to_rem(desktop_px, root_px))
        }

    clamp_val = calc_clamp(mobile_px, desktop_px, min_vp, max_vp, root_px, zoom_friendly)
    return {
        "slug": slug,
        "name": f"{slug} | {mobile_short}->{desktop_short}",
        "size": clamp_val
    }


def merge_into_theme_json(theme_path, font_sizes):
    """Remplace fontSizes dans settings.typography d'un fichier theme.json."""
    with open(theme_path, "r", encoding="utf-8") as f:
        theme = json.load(f)

    if "settings" not in theme:
        theme["settings"] = {}
    if "typography" not in theme["settings"]:
        theme["settings"]["typography"] = {}

    theme["settings"]["typography"]["fontSizes"] = font_sizes

    with open(theme_path, "w", encoding="utf-8") as f:
        json.dump(theme, f, indent=4, ensure_ascii=False)
        f.write("\n")

    print(f"✅ theme.json mis à jour : {theme_path}")


def generate_css(font_sizes, prefix="--wp--preset--font-size--"):
    lines = [":root {"]
    for entry in font_sizes:
        lines.append(f"  {prefix}{entry['slug']}: {entry['size']};")
    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Programme principal
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  Figma -> WordPress/Gutenberg : fontSizes (typography)")
    print("=" * 60)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_figma_folder = os.path.join(script_dir, "figma_json__typo")
    default_theme_json = os.path.join(script_dir, "theme.json")

    print("\n--- SOURCE FIGMA ---")
    folder = input(
        f"Dossier contenant le fichier de variables responsive exporté depuis Figma "
        f"[défaut: {default_figma_folder}] : "
    ).strip().strip('"')
    if not folder:
        folder = default_figma_folder

    files = scan_figma_files(folder)
    if not files:
        print(f"  ⚠️ Aucun fichier de variables Figma valide trouvé dans '{folder}'.")
        return

    print(f"\nFichiers détectés dans '{folder}' :")
    for i, (fname, _, data) in enumerate(files, start=1):
        nb_vars = sum(1 for v in data.get("variables", []) if v.get("type") == "FLOAT")
        modes = list(data.get("modes", {}).values())
        print(f"  {i}. {fname}  ({nb_vars} variables FLOAT, modes: {', '.join(modes)})")

    if len(files) == 1:
        chosen_idx = 1
    else:
        raw = input(f"\nFichier à utiliser (numéro) [défaut: 1] : ").strip()
        chosen_idx = int(raw) if raw.isdigit() and 1 <= int(raw) <= len(files) else 1

    fname, path, data = files[chosen_idx - 1]
    print(f"  ✅ Fichier sélectionné : {fname}")

    mobile_id, desktop_id = choose_modes(data)
    if not mobile_id or not desktop_id:
        print("  ⚠️ Modes mobile/desktop non déterminés, abandon.")
        return

    print("\n--- FILTRE ---")
    marker = input(
        "Motif à rechercher dans le nom des variables [défaut: font/size/] : "
    ).strip()
    if not marker:
        marker = "font/size/"

    variables = extract_font_size_variables(data, mobile_id, desktop_id, marker)
    if not variables:
        print(f"  ⚠️ Aucune variable FLOAT trouvée avec le motif '{marker}'.")
        return

    print(f"\n  ✅ {len(variables)} variable(s) de taille de police trouvée(s) :")
    for v in variables:
        print(f"    - {v['label']}  (mobile: {v['mobile_px']}px, desktop: {v['desktop_px']}px) -> slug '{v['slug']}'")

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

    font_sizes = []
    seen_slugs = set()
    for v in variables:
        slug = v["slug"]
        if slug in seen_slugs:
            print(f"  ⚠️ Doublon de slug ignoré : '{slug}' ({v['label']})")
            continue
        seen_slugs.add(slug)
        font_sizes.append(
            make_font_size(slug, v["mobile_px"], v["desktop_px"], min_vp, max_vp, root_px, zoom_friendly)
        )

    print("\n--- FORMAT ---")
    print("  json : génère un objet JSON (ou met à jour un theme.json existant)")
    print("  css  : génère des variables CSS dans :root")
    format_choice = input("Format (json/css) [défaut json] : ").strip().lower()
    if not format_choice:
        format_choice = "json"

    if format_choice == "css":
        output = generate_css(font_sizes)
    else:
        output = json.dumps({"fontSizes": font_sizes}, indent=4, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(output)

    print("\n" + "=" * 60)
    print("Sauvegarde :")
    if format_choice == "css":
        print("  - Chemin vers fichier .css")
    else:
        print("  - Chemin vers theme.json → remplace settings.typography.fontSizes dans le fichier")
        print("  - Autre nom → sauvegarde le JSON standalone")
    print("  - Entrée → affichage uniquement")
    save = input(f"\nFichier de destination [défaut: {default_theme_json}] : ").strip()

    if not save:
        save = default_theme_json if format_choice != "css" else ""
        if not save:
            return

    if format_choice == "css":
        with open(save, "w", encoding="utf-8") as f:
            f.write(output)
            f.write("\n")
        print(f"✅ CSS sauvegardé dans {save}")
        return

    if save.endswith(".json") and os.path.isfile(save):
        with open(save, "r", encoding="utf-8") as f:
            content = f.read()
        try:
            existing = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"\n❌ '{save}' existe mais n'est pas un JSON valide : {e}")
            print("   Aucune écriture effectuée (le fichier aurait été écrasé).")
            return
        if "settings" in existing and "version" in existing:
            merge_into_theme_json(save, font_sizes)
            return
        else:
            print(f"\n❌ '{save}' est un JSON existant mais ne ressemble pas à un theme.json.")
            print("   Aucune écriture effectuée pour éviter d'écraser le fichier.")
            return

    if os.path.isfile(save):
        confirm = input(
            f"\n⚠️ '{save}' existe déjà et va être ÉCRASÉ. Confirmer ? (o/n) [défaut: n] : "
        ).strip().lower()
        if confirm not in ("o", "oui", "y", "yes"):
            print("   Annulé, aucune écriture effectuée.")
            return

    with open(save, "w", encoding="utf-8") as f:
        f.write(output)
        f.write("\n")
    print(f"✅ JSON sauvegardé dans {save}")


if __name__ == "__main__":
    main()
