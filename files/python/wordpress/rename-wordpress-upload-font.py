#!/usr/bin/env python3
"""
rename_fonts.py

Scanne un dossier (et ses sous-dossiers) à la recherche de fichiers de polices
(.ttf, .otf, .woff, .woff2) et les renomme selon le schéma :

    nom-de-la-police-graisse-style.ext

Exemples de résultats :
    inter-400-normal.woff2
    inter-700-italic.woff2
    open-sans-600-normal.ttf

Utilisation :
    python3 rename_fonts.py /chemin/vers/dossier
    python3 rename_fonts.py /chemin/vers/dossier --dry-run   (simulation, sans renommer)
    python3 rename_fonts.py /chemin/vers/dossier --copy /chemin/sortie   (copie au lieu de renommer sur place)

Dépendance :
    pip install fonttools --break-system-packages
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

try:
    from fontTools.ttLib import TTFont
    from fontTools.ttLib.woff2 import decompress as woff2_decompress  # noqa: F401 (juste pour vérifier dispo)
except ImportError:
    print("ERREUR : fontTools n'est pas installé.")
    print("Installe-le avec : pip install fonttools --break-system-packages")
    sys.exit(1)

FONT_EXTENSIONS = {".ttf", ".otf", ".woff", ".woff2"}

# Table de correspondance pour les noms de graisses textuels -> valeurs numériques CSS
WEIGHT_NAME_TO_NUMBER = {
    "thin": "100",
    "hairline": "100",
    "extralight": "200",
    "ultralight": "200",
    "light": "300",
    "regular": "400",
    "normal": "400",
    "book": "400",
    "medium": "500",
    "semibold": "600",
    "demibold": "600",
    "bold": "700",
    "extrabold": "800",
    "ultrabold": "800",
    "black": "900",
    "heavy": "900",
}


def slugify(text: str) -> str:
    """Transforme un texte en slug propre : minuscules, tirets, sans accents/symboles."""
    text = text.strip().lower()
    # Remplace les espaces et underscores par des tirets
    text = re.sub(r"[\s_]+", "-", text)
    # Retire tout ce qui n'est pas alphanumérique ou tiret
    text = re.sub(r"[^a-z0-9\-]", "", text)
    # Nettoie les tirets multiples/en bordure
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def get_name_table_value(font: TTFont, name_id: int) -> str | None:
    """Récupère une valeur de la table `name` par son ID, en priorisant l'anglais US."""
    name_table = font.get("name")
    if name_table is None:
        return None

    # Priorité : Windows/English US (3,1,0x409), puis Mac/English (1,0,0), puis n'importe quoi
    for platform_id, plat_enc_id, lang_id in [(3, 1, 0x409), (1, 0, 0)]:
        rec = name_table.getName(name_id, platform_id, plat_enc_id, lang_id)
        if rec:
            try:
                return rec.toUnicode()
            except Exception:
                continue

    # Fallback : première entrée trouvée pour ce name_id
    for rec in name_table.names:
        if rec.nameID == name_id:
            try:
                return rec.toUnicode()
            except Exception:
                continue
    return None


def get_weight_from_os2(font: TTFont) -> str | None:
    """Récupère la graisse numérique (100-900) depuis la table OS/2 si disponible."""
    os2 = font.get("OS/2")
    if os2 is not None and hasattr(os2, "usWeightClass"):
        weight = os2.usWeightClass
        if weight:
            return str(weight)
    return None


def get_style_from_font(font: TTFont, subfamily: str) -> str:
    """Détermine si la police est italic ou normal."""
    subfamily_lower = (subfamily or "").lower()
    if "italic" in subfamily_lower or "oblique" in subfamily_lower:
        return "italic"

    # Fallback : vérifie les flags de la table head
    head = font.get("head")
    if head is not None and hasattr(head, "macStyle"):
        if head.macStyle & 0b10:  # bit 1 = italic
            return "italic"
    return "normal"


def extract_font_info(filepath: Path) -> dict:
    """Extrait nom de famille, graisse et style depuis un fichier de police."""
    font = TTFont(filepath, lazy=True, fontNumber=0)

    # nameID 16 = Typographic Family Name (préféré si présent, gère mieux les familles complexes)
    # nameID 1  = Font Family Name (fallback classique)
    family = get_name_table_value(font, 16) or get_name_table_value(font, 1) or filepath.stem

    # nameID 17 = Typographic Subfamily (Regular, Bold Italic, etc.)
    # nameID 2  = Subfamily classique
    subfamily = get_name_table_value(font, 17) or get_name_table_value(font, 2) or "Regular"

    # Graisse : d'abord OS/2, sinon déduite du texte de la sous-famille
    weight = get_weight_from_os2(font)
    if not weight:
        subfamily_lower = subfamily.lower()
        weight = "400"
        for word, num in WEIGHT_NAME_TO_NUMBER.items():
            if word in subfamily_lower:
                weight = num
                break

    style = get_style_from_font(font, subfamily)

    font.close()

    return {
        "family": family,
        "weight": weight,
        "style": style,
        "subfamily": subfamily,
    }


def build_new_name(info: dict, extension: str) -> str:
    family_slug = slugify(info["family"])
    return f"{family_slug}-{info['weight']}-{info['style']}{extension}"


def scan_and_rename(root: Path, dry_run: bool, copy_to: Path | None) -> list[dict]:
    font_files = [
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in FONT_EXTENSIONS
    ]

    if not font_files:
        print(f"Aucun fichier de police trouvé dans {root}")
        return []

    print(f"{len(font_files)} fichier(s) de police trouvé(s).\n")

    # Pour éviter les collisions de noms (ex : deux fois "inter-400-normal.woff2")
    used_names: dict[str, int] = {}
    fonts: list[dict] = []

    for filepath in sorted(font_files):
        try:
            info = extract_font_info(filepath)
        except Exception as e:
            print(f"⚠️  Impossible de lire {filepath.name} : {e}")
            continue

        new_name = build_new_name(info, filepath.suffix.lower())

        # Gestion des doublons (ex: même famille/graisse/style mais fichiers différents)
        if new_name in used_names:
            used_names[new_name] += 1
            stem, ext = new_name.rsplit(".", 1)
            new_name = f"{stem}-{used_names[new_name]}.{ext}"
        else:
            used_names[new_name] = 0

        new_path = filepath.with_name(new_name)

        print(f"{filepath.name}")
        print(f"  → {new_name}")
        print(f"    (famille: {info['family']!r}, sous-famille: {info['subfamily']!r}, "
              f"graisse: {info['weight']}, style: {info['style']})")

        if not dry_run:
            if copy_to:
                copy_to.mkdir(parents=True, exist_ok=True)
                dest = copy_to / new_name
                shutil.copy2(filepath, dest)
                print(f"    ✅ copié vers {dest}")
            else:
                filepath.rename(new_path)
                print(f"    ✅ renommé")
        else:
            print(f"    (dry-run, rien n'a été modifié)")
        print()

        final_path = dest if copy_to else new_path
        base_for_relative = copy_to if copy_to else root
        relative = final_path.relative_to(base_for_relative)

        fonts.append({
            "family": info["family"],
            "weight": info["weight"],
            "style": info["style"],
            "subfamily": info["subfamily"],
            "old_name": filepath.name,
            "new_name": new_name,
            "ext": filepath.suffix.lower(),
            "relative": relative,
            "final_path": final_path,
        })

    return fonts


def assign_families(fonts: list[dict]) -> dict[str, str]:
    """Demande à l'utilisateur d'assigner primary/secondary/tertiary à chaque famille."""
    families = sorted({f["family"] for f in fonts})
    assignments: dict[str, str] = {}
    used_roles: set[str] = set()

    print("\n--- ASSIGNATION DES POLICES ---")
    print("  0 : aucune")
    print("  1 : primary")
    print("  2 : secondary")
    print("  3 : tertiary")

    for family in families:
        while True:
            choice = input(f"  '{family}' (0/1/2/3) : ").strip().lower()
            if choice == "0" or choice == "":
                break
            if choice in ("1", "2", "3"):
                role = {"1": "primary", "2": "secondary", "3": "tertiary"}[choice]
                if role in used_roles:
                    print(f"    ⚠️ Le rôle {role} est déjà utilisé. Choisissez-en un autre.")
                    continue
                assignments[family] = role
                used_roles.add(role)
                break
            print("    ⚠️ Choix invalide.")

    return assignments


def build_font_families(fonts: list[dict], base_url: str, assignments: dict[str, str]) -> list[dict]:
    """Construit la liste fontFamilies pour theme.json."""
    base_url = base_url.rstrip("/")

    # Regrouper les fontFace par famille
    faces_by_family: dict[str, list[dict]] = {}
    for f in fonts:
        family = f["family"]
        if family not in faces_by_family:
            faces_by_family[family] = []

        rel_path = f["relative"].as_posix()
        src = f"{base_url}/{rel_path}"

        faces_by_family[family].append({
            "fontFamily": family,
            "fontWeight": f["weight"],
            "fontStyle": f["style"],
            "fontStretch": "normal",
            "src": [src],
        })

    role_names = {
        "primary": "Primary",
        "secondary": "Secondary",
        "tertiary": "Tertiary",
    }

    font_families = []
    for family, role in sorted(assignments.items(), key=lambda x: list(role_names.keys()).index(x[1])):
        if family not in faces_by_family:
            continue
        font_families.append({
            "name": role_names[role],
            "slug": role,
            "fontFamily": family,
            "fontFace": faces_by_family[family],
        })

    return font_families


def merge_fonts_into_theme_json(theme_path: str, font_families: list[dict]) -> None:
    """Remplace settings.typography.fontFamilies dans un fichier theme.json."""
    with open(theme_path, 'r', encoding='utf-8') as f:
        theme = json.load(f)

    if "settings" not in theme:
        theme["settings"] = {}
    if "typography" not in theme["settings"]:
        theme["settings"]["typography"] = {}

    theme["settings"]["typography"]["fontFamilies"] = font_families

    with open(theme_path, 'w', encoding='utf-8') as f:
        json.dump(theme, f, indent=4, ensure_ascii=False)
        f.write("\n")

    print(f"✅ theme.json mis à jour : {theme_path}")


def generate_css_fonts(fonts: list[dict], base_url: str) -> str:
    """Génère un bloc CSS @font-face."""
    base_url = base_url.rstrip("/")
    format_map = {
        ".woff2": "woff2",
        ".woff": "woff",
        ".ttf": "truetype",
        ".otf": "opentype",
    }

    lines = []
    for f in fonts:
        rel_path = f["relative"].as_posix()
        src = f"{base_url}/{rel_path}"
        fmt = format_map.get(f["ext"], f["ext"][1:])
        lines.append(f"@font-face {{")
        lines.append(f"  font-family: '{f['family']}';")
        lines.append(f"  font-weight: {f['weight']};")
        lines.append(f"  font-style: {f['style']};")
        lines.append(f"  font-stretch: normal;")
        lines.append(f"  font-display: swap;")
        lines.append(f"  src: url('{src}') format('{fmt}');")
        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip()


def main():
    parser = argparse.ArgumentParser(
        description="Renomme les fichiers de polices selon leurs métadonnées internes."
    )
    parser.add_argument("folder", type=str, nargs="?", default=None, help="Dossier à scanner (récursif)")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simule les renommages sans rien modifier"
    )
    parser.add_argument(
        "--copy", type=str, default=None,
        help="Copie les fichiers renommés dans ce dossier au lieu de renommer sur place"
    )
    args = parser.parse_args()

    if args.folder:
        folder = args.folder
    else:
        folder = input("Chemin du dossier de polices : ").strip()
        if not folder:
            print("ERREUR : aucun dossier fourni.")
            sys.exit(1)

    root = Path(folder).expanduser().resolve()
    if not root.is_dir():
        print(f"ERREUR : {root} n'est pas un dossier valide.")
        sys.exit(1)

    copy_to = Path(args.copy).expanduser().resolve() if args.copy else None

    fonts = scan_and_rename(root, dry_run=args.dry_run, copy_to=copy_to)
    if not fonts:
        return

    # Génération theme.json
    print("\n--- GÉNÉRATION POUR WORDPRESS ---")
    gen_json = input("Générer les fontFamilies dans un theme.json ? (o/n) : ").strip().lower()
    if gen_json in ("o", "oui", "y", "yes"):
        theme_path = input("Chemin du theme.json : ").strip()
        if theme_path:
            theme_path = Path(theme_path).expanduser().resolve()
            if theme_path.is_file():
                base_url = input("URL de base (défaut file:./assets/fonts/) : ").strip()
                if not base_url:
                    base_url = "file:./assets/fonts/"
                assignments = assign_families(fonts)
                if assignments:
                    font_families = build_font_families(fonts, base_url, assignments)
                    merge_fonts_into_theme_json(str(theme_path), font_families)
                else:
                    print("Aucune police assignée, theme.json non modifié.")
            else:
                print(f"ERREUR : {theme_path} n'est pas un fichier valide.")

    # Génération CSS
    gen_css = input("Générer un fichier CSS @font-face ? (o/n) : ").strip().lower()
    if gen_css in ("o", "oui", "y", "yes"):
        css_base = input("URL de base CSS (défaut ./assets/fonts/) : ").strip()
        if not css_base:
            css_base = "./assets/fonts/"
        css_output = input("Fichier CSS de destination : ").strip()
        if css_output:
            css = generate_css_fonts(fonts, css_base)
            with open(css_output, 'w', encoding='utf-8') as f:
                f.write(css)
                f.write("\n")
            print(f"✅ CSS sauvegardé dans {css_output}")


if __name__ == "__main__":
    main()