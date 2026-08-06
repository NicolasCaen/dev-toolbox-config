#!/usr/bin/env python3
"""
Génère automatiquement un tableau spacingSizes JSON pour WordPress/Gutenberg.
- Valeurs fixes : conversion px → rem
- Valeurs fluides : clamp(min, preferred, max) avec interpolation linéaire
"""
 
import json
import sys
 
def px_to_rem(px):
    """Convertit des pixels en rem (1rem = 16px)."""
    return px / 16
 
def format_rem(value):
    """Formate une valeur rem de façon propre (évite 1.0rem → 1rem)."""
    if value == int(value):
        return f"{int(value)}rem"
    return f"{round(value, 4)}rem".rstrip('0').rstrip('.') + "rem"
 
def calc_clamp(min_px, max_px, min_vp=500, max_vp=1500):
    """
    Calcule clamp(min, preferred, max).
    En dessous de min_vp → valeur = min_px
    Au dessus de max_vp → valeur = max_px
    Entre les deux → interpolation linéaire.
    """
    min_rem = px_to_rem(min_px)
    max_rem = px_to_rem(max_px)
 
    # Calcul de la droite : y = a*x + b (x en px, y en rem)
    # À x = min_vp : y = min_rem
    # À x = max_vp : y = max_rem
    slope = (max_rem - min_rem) / (max_vp - min_vp)  # rem/px
    intercept = min_rem - slope * min_vp             # rem
 
    # Conversion en vw (1vw = viewport/100 px)
    slope_vw = slope * 100  # rem/vw
 
    min_str = format_rem(min_rem)
    max_str = format_rem(max_rem)
 
    # preferred = intercept + slope_vw * 1vw
    intercept_str = format_rem(intercept)
    slope_vw_str = format_rem(slope_vw)
 
    # Construire le preferred
    if intercept >= 0:
        preferred = f"{intercept_str} + {slope_vw_str}vw"
    else:
        preferred = f"-{format_rem(abs(intercept))} + {slope_vw_str}vw"
 
    return f"clamp({min_str}, {preferred}, {max_str})"
 
def make_fixed(slug, px):
    """Crée une entrée fixe."""
    rem = format_rem(px_to_rem(px))
    return {
        "slug": str(slug),
        "name": f"{rem} ({px}px)",
        "size": rem if px != 0 else "0"
    }
 
def make_fluid(slug, min_px, max_px, min_vp=500, max_vp=1500, prefix=""):
    """Crée une entrée fluide avec clamp."""
    min_rem = format_rem(px_to_rem(min_px))
    max_rem = format_rem(px_to_rem(max_px))
    clamp_val = calc_clamp(min_px, max_px, min_vp, max_vp)
    name_prefix = f"{prefix} | " if prefix else ""
    return {
        "slug": f"{prefix}{slug}" if prefix else str(slug),
        "name": f"{name_prefix}{min_rem} ({min_px}px) \u2192 {max_rem} ({max_px}px)",
        "size": clamp_val
    }
 
def make_special(slug, name, size):
    """Crée une entrée spéciale (var, etc.)."""
    return {
        "slug": slug,
        "name": name,
        "size": size
    }
 
def main():
    print("=" * 60)
    print("  Générateur spacingSizes pour WordPress/Gutenberg")
    print("=" * 60)
 
    # --- Valeurs fixes ---
    print("\n--- VALEURS FIXES ---")
    print("Entrez les valeurs en px séparées par des virgules.")
    print("Exemple : 0,4,8,12,16,24,32,40,48,56,72,80")
    raw = input("Valeurs fixes (px) : ").strip()
    if not raw:
        raw = "0,4,8,12,16,24,32,40,48,56,72,80"
    fixed_px = [int(x.strip()) for x in raw.split(",")]
 
    # --- Paramètres clamp ---
    print("\n--- PARAMÈTRES CLAMP ---")
    min_vp_input = input("Viewport min en px (défaut 500) : ").strip()
    max_vp_input = input("Viewport max en px (défaut 1500) : ").strip()
    min_vp = int(min_vp_input) if min_vp_input else 500
    max_vp = int(max_vp_input) if max_vp_input else 1500
 
    # --- Valeurs fluides ---
    print("\n--- VALEURS FLUIDES (clamp) ---")
    print("Format : min_px-max_px (ex: 16-32, 16-48, 40-80)")
    print("Laisser vide pour terminer.")
    print("Préfixe 'h-' pour les hauteurs : tapez 'h-' devant (ex: h-16-40)")
 
    fluid_entries = []
    while True:
        entry = input(f"  Valeur fluide (min-max{', ou h-min-max pour hauteur'}) : ").strip()
        if not entry:
            break
        prefix = ""
        if entry.startswith("h-"):
            prefix = "h-"
            entry = entry[2:]
        parts = entry.split("-")
        if len(parts) == 2:
            try:
                min_px, max_px = int(parts[0]), int(parts[1])
                fluid_entries.append((min_px, max_px, prefix))
            except ValueError:
                print("  ⚠️ Format invalide. Exemple : 16-32")
        else:
            print("  ⚠️ Format invalide. Exemple : 16-32")
 
    # --- Valeurs spéciales ---
    print("\n--- VALEURS SPÉCIALES ---")
    print("Laisser vide pour terminer.")
    specials = []
    while True:
        slug = input("  Slug (ex: headerheight) : ").strip()
        if not slug:
            break
        name = input("  Nom (ex: Header Height) : ").strip()
        size = input("  Size (ex: var(--header-height)) : ").strip()
        specials.append((slug, name, size))
 
    # --- Génération ---
    print("\n" + "=" * 60)
    print("  Génération du JSON...")
    print("=" * 60)
 
    spacing_sizes = []
 
    # Fixes
    for px in fixed_px:
        spacing_sizes.append(make_fixed(px, px))
 
    # Fluides - groupées par min_px
    if fluid_entries:
        # Séparer normales et h-
        normal_fluids = [(mn, mx, p) for mn, mx, p in fluid_entries if not p]
        h_fluids = [(mn, mx, p) for mn, mx, p in fluid_entries if p]
 
        # Trier par min puis max
        normal_fluids.sort(key=lambda x: (x[0], x[1]))
        h_fluids.sort(key=lambda x: (x[0], x[1]))
 
        # Regrouper par min_px
        from itertools import groupby
        for min_px, group in groupby(normal_fluids, key=lambda x: x[0]):
            for mn, mx, pfx in group:
                slug = f"{mn}-{mx}"
                spacing_sizes.append(make_fluid(slug, mn, mx, min_vp, max_vp))
 
        # H | fixes d'abord (si pas déjà dans fixed_px)
        h_fixed_added = False
        for mn, mx, pfx in h_fluids:
            if not h_fixed_added and mn not in fixed_px:
                spacing_sizes.append(make_fixed(f"h-{mn}", mn))
            h_fixed_added = True
 
        # H | fluides
        for min_px, group in groupby(h_fluids, key=lambda x: x[0]):
            for mn, mx, pfx in group:
                slug = f"{mn}-{mx}"
                spacing_sizes.append(make_fluid(slug, mn, mx, min_vp, max_vp, prefix="h-"))
 
    # Spéciales
    for slug, name, size in specials:
        spacing_sizes.append(make_special(slug, name, size))
 
    # Output JSON
    output = json.dumps({"spacingSizes": spacing_sizes}, indent=4, ensure_ascii=False)
 
    print("\n" + output)
 
    # Sauvegarde optionnelle
    save = input("\nSauvegarder dans un fichier ? (nom/chemin ou Entrée pour ignorer) : ").strip()
    if save:
        with open(save, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"✅ Sauvegardé dans {save}")
 
if __name__ == "__main__":
    main()