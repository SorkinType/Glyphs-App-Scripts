#MenuTitle: Color Glyphs by Content Type (Extended)
# -*- coding: utf-8 -*-
"""
Mark glyphs with colors based on their content and case:
- Dark Blue (7):    Uppercase paths only (Latin, Greek, Cyrillic, Coptic, Armenian)
- Light Blue (6):   Lowercase paths only (Latin, Greek, Cyrillic, Coptic, Armenian)
- Pink (9):         Small caps (.sc/.c2sc) paths only
- Light Green (4):  Other glyphs with paths only
- Dark Green (5):   Contains only components
- Purple (8):       Contains both paths and components
- No color:         Empty glyphs

Save this file in your Glyphs Scripts folder:
~/Library/Application Support/Glyphs 3/Scripts/

Usage:
1. Open a font file
2. Run this script from Scripts menu
3. All glyphs will be automatically colored based on their content
"""

def is_uppercase_glyph(glyph_name):
    """
    Check if a glyph is uppercase for Latin, Greek, Cyrillic, Coptic, or Armenian.
    """
    # Latin uppercase
    latin_upper = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    
    # Greek uppercase Unicode ranges and common names
    greek_upper_names = {
        'Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta', 'Eta', 'Theta',
        'Iota', 'Kappa', 'Lambda', 'Mu', 'Nu', 'Xi', 'Omicron', 'Pi', 'Rho',
        'Sigma', 'Tau', 'Upsilon', 'Phi', 'Chi', 'Psi', 'Omega'
    }
    
    # Cyrillic uppercase names (common ones)
    cyrillic_upper_names = {
        'A-cy', 'Be-cy', 'Ve-cy', 'Ghe-cy', 'De-cy', 'Ie-cy', 'Zhe-cy', 'Ze-cy',
        'I-cy', 'Ka-cy', 'El-cy', 'Em-cy', 'En-cy', 'O-cy', 'Pe-cy', 'Er-cy',
        'Es-cy', 'Te-cy', 'U-cy', 'Ef-cy', 'Ha-cy', 'Tse-cy', 'Che-cy', 'Sha-cy',
        'Shcha-cy', 'Hardsign-cy', 'Yeru-cy', 'Softsign-cy', 'E-cy', 'Yu-cy', 'Ya-cy',
        'Io-cy', 'Dje-cy', 'Gje-cy', 'Ie-cy.loclBGR', 'Dze-cy', 'Dzhe-cy', 'Yi-cy',
        'Je-cy', 'Lje-cy', 'Nje-cy', 'Tshe-cy', 'Kje-cy', 'Ushort-cy', 'Dzhe-cy'
    }
    
    # Coptic uppercase names
    coptic_upper_names = {
        'Alfa-coptic', 'Vida-coptic', 'Gamma-coptic', 'Dalda-coptic', 'Ei-coptic',
        'Sou-coptic', 'Zata-coptic', 'Hate-coptic', 'Thethe-coptic', 'Iauda-coptic',
        'Kapa-coptic', 'Laula-coptic', 'Mi-coptic', 'Ni-coptic', 'Ksi-coptic',
        'O-coptic', 'Pi-coptic', 'Ro-coptic', 'Sima-coptic', 'Tau-coptic',
        'Ua-coptic', 'Fi-coptic', 'Khi-coptic', 'Psi-coptic', 'Oou-coptic',
        'Shei-coptic', 'Fei-coptic', 'Khei-coptic', 'Hori-coptic', 'Gangia-coptic',
        'Shima-coptic', 'Dei-coptic', 'Ti-coptic'
    }
    
    # Armenian uppercase names
    armenian_upper_names = {
        'Ayb-arm', 'Ben-arm', 'Gim-arm', 'Da-arm', 'Ech-arm', 'Za-arm', 'Eh-arm',
        'Et-arm', 'To-arm', 'Zhe-arm', 'Ini-arm', 'Liwn-arm', 'Xeh-arm', 'Ca-arm',
        'Ken-arm', 'Ho-arm', 'Ja-arm', 'Ghad-arm', 'Cheh-arm', 'Men-arm', 'Yi-arm',
        'Now-arm', 'Sha-arm', 'Vo-arm', 'Cha-arm', 'Peh-arm', 'Jheh-arm', 'Ra-arm',
        'Seh-arm', 'Vew-arm', 'Tiwn-arm', 'Reh-arm', 'Co-arm', 'Yiwn-arm', 'Piwr-arm',
        'Keh-arm', 'Oh-arm', 'Feh-arm', 'Ech_yiwn-arm', 'Men_now-arm', 'Men_ech-arm',
        'Men_ini-arm', 'Vew_now-arm', 'Men_xeh-arm'
    }
    
    # Check if it's a single Latin uppercase letter
    if len(glyph_name) == 1 and glyph_name in latin_upper:
        return True
    
    # Check Greek, Cyrillic, Coptic, Armenian by name
    if glyph_name in greek_upper_names or glyph_name in cyrillic_upper_names:
        return True
    if glyph_name in coptic_upper_names or glyph_name in armenian_upper_names:
        return True
    
    # Check for suffixed versions (e.g., A.alt, Alpha.ss01)
    base_name = glyph_name.split('.')[0]
    if base_name in greek_upper_names or base_name in cyrillic_upper_names:
        return True
    if base_name in coptic_upper_names or base_name in armenian_upper_names:
        return True
    
    return False


def is_lowercase_glyph(glyph_name):
    """
    Check if a glyph is lowercase for Latin, Greek, Cyrillic, Coptic, or Armenian.
    """
    # Latin lowercase
    latin_lower = set('abcdefghijklmnopqrstuvwxyz')
    
    # Greek lowercase names
    greek_lower_names = {
        'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta',
        'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi', 'omicron', 'pi', 'rho',
        'sigma', 'tau', 'upsilon', 'phi', 'chi', 'psi', 'omega', 'finalsigma'
    }
    
    # Cyrillic lowercase names
    cyrillic_lower_names = {
        'a-cy', 'be-cy', 've-cy', 'ghe-cy', 'de-cy', 'ie-cy', 'zhe-cy', 'ze-cy',
        'i-cy', 'ka-cy', 'el-cy', 'em-cy', 'en-cy', 'o-cy', 'pe-cy', 'er-cy',
        'es-cy', 'te-cy', 'u-cy', 'ef-cy', 'ha-cy', 'tse-cy', 'che-cy', 'sha-cy',
        'shcha-cy', 'hardsign-cy', 'yeru-cy', 'softsign-cy', 'e-cy', 'yu-cy', 'ya-cy',
        'io-cy', 'dje-cy', 'gje-cy', 'ie-cy.loclBGR', 'dze-cy', 'dzhe-cy', 'yi-cy',
        'je-cy', 'lje-cy', 'nje-cy', 'tshe-cy', 'kje-cy', 'ushort-cy', 'dzhe-cy'
    }
    
    # Coptic lowercase names (as specified)
    coptic_lower_names = {
        'shei-coptic', 'fei-coptic', 'khei-coptic', 'hori-coptic', 'gangia-coptic',
        'shima-coptic', 'dei-coptic'
    }
    
    # Armenian lowercase names (as specified)
    armenian_lower_names = {
        'ayb-arm', 'ben-arm', 'gim-arm', 'da-arm', 'ech-arm', 'za-arm', 'eh-arm',
        'et-arm', 'to-arm', 'zhe-arm', 'ini-arm', 'liwn-arm', 'xeh-arm', 'ca-arm',
        'ken-arm', 'ho-arm', 'ja-arm', 'ghad-arm', 'cheh-arm', 'men-arm', 'yi-arm',
        'now-arm', 'sha-arm', 'vo-arm', 'cha-arm', 'peh-arm', 'jheh-arm', 'ra-arm',
        'seh-arm', 'vew-arm', 'tiwn-arm', 'reh-arm', 'co-arm', 'yiwn-arm', 'piwr-arm',
        'keh-arm', 'oh-arm', 'feh-arm', 'ech_yiwn-arm', 'men_now-arm', 'men_ech-arm',
        'men_ini-arm', 'vew_now-arm', 'men_xeh-arm'
    }
    
    # Check if it's a single Latin lowercase letter
    if len(glyph_name) == 1 and glyph_name in latin_lower:
        return True
    
    # Check Greek, Cyrillic, Coptic, Armenian by name
    if glyph_name in greek_lower_names or glyph_name in cyrillic_lower_names:
        return True
    if glyph_name in coptic_lower_names or glyph_name in armenian_lower_names:
        return True
    
    # Check for suffixed versions (e.g., a.alt, alpha.ss01)
    # But NOT small caps suffixes
    if '.sc' not in glyph_name and '.c2sc' not in glyph_name:
        base_name = glyph_name.split('.')[0]
        if base_name in greek_lower_names or base_name in cyrillic_lower_names:
            return True
        if base_name in coptic_lower_names or base_name in armenian_lower_names:
            return True
    
    return False


def is_small_caps_glyph(glyph_name):
    """
    Check if a glyph is a small caps variant (.sc or .c2sc suffix).
    """
    return '.sc' in glyph_name or '.c2sc' in glyph_name


def analyze_glyph_content(glyph):
    """
    Analyze a glyph's content across all master/special layers only.
    Returns: 'paths_only', 'both', 'components_only', or 'empty'
    """
    has_paths = False
    has_components = False
    
    for layer in glyph.layers:
        # Skip non-master layers (brace/bracket layers, backups, etc.)
        if not layer.isMasterLayer and not layer.isSpecialLayer:
            continue
        
        if len(layer.paths) > 0:
            has_paths = True
        if len(layer.components) > 0:
            has_components = True
        
        # Early exit once we know it's a mix
        if has_paths and has_components:
            return 'both'
    
    if has_paths and not has_components:
        return 'paths_only'
    elif has_components and not has_paths:
        return 'components_only'
    else:
        return 'empty'


def color_glyphs():
    """Main function to color glyphs based on their content."""
    font = Glyphs.font
    
    if not font:
        Message("No Font Open", "Please open a font first.")
        return
    
    print("\n" + "=" * 60)
    print("COLOR GLYPHS BY CONTENT TYPE (EXTENDED)")
    print("=" * 60)
    
    # Official Glyphs color palette indices (0–11):
    #  0 = Red,        1 = Orange,  2 = Brown,      3 = Yellow
    #  4 = Light Green, 5 = Dark Green, 6 = Cyan,   7 = Blue
    #  8 = Purple,     9 = Pink,    10 = Light Gray, 11 = Dark Gray
    DARK_BLUE   = 7   # Uppercase paths only
    LIGHT_BLUE  = 6   # Lowercase paths only
    PINK        = 9   # Small caps paths only
    LIGHT_GREEN = 4   # Other paths only
    DARK_GREEN  = 5   # Components only
    PURPLE      = 8   # Mixed (paths + components)
    
    counters = {
        'uppercase_paths':    0,
        'lowercase_paths':    0,
        'smallcaps_paths':    0,
        'other_paths':        0,
        'both':               0,
        'components_only':    0,
        'empty':              0,
    }
    
    for glyph in font.glyphs:
        content_type = analyze_glyph_content(glyph)
        glyph_name = glyph.name
        
        if content_type == 'paths_only':
            # Determine which category of paths-only
            if is_small_caps_glyph(glyph_name):
                glyph.color = PINK
                counters['smallcaps_paths'] += 1
                print(f"  {glyph_name}: Pink (small caps paths only)")
            elif is_uppercase_glyph(glyph_name):
                glyph.color = DARK_BLUE
                counters['uppercase_paths'] += 1
                print(f"  {glyph_name}: Dark Blue (uppercase paths only)")
            elif is_lowercase_glyph(glyph_name):
                glyph.color = LIGHT_BLUE
                counters['lowercase_paths'] += 1
                print(f"  {glyph_name}: Light Blue (lowercase paths only)")
            else:
                glyph.color = LIGHT_GREEN
                counters['other_paths'] += 1
                print(f"  {glyph_name}: Light Green (other paths only)")
        
        elif content_type == 'both':
            glyph.color = PURPLE
            counters['both'] += 1
            print(f"  {glyph_name}: Purple (paths + components)")
        
        elif content_type == 'components_only':
            glyph.color = DARK_GREEN
            counters['components_only'] += 1
            print(f"  {glyph_name}: Dark Green (components only)")
        
        elif content_type == 'empty':
            glyph.color = None
            counters['empty'] += 1
            print(f"  {glyph_name}: No color (empty)")
    
    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"Dark Blue   (uppercase paths):        {counters['uppercase_paths']}")
    print(f"Light Blue  (lowercase paths):        {counters['lowercase_paths']}")
    print(f"Pink        (small caps paths):       {counters['smallcaps_paths']}")
    print(f"Light Green (other paths):            {counters['other_paths']}")
    print(f"Dark Green  (components only):        {counters['components_only']}")
    print(f"Purple      (paths + components):     {counters['both']}")
    print(f"No color    (empty):                  {counters['empty']}")
    print(f"{'=' * 60}")
    print(f"Total glyphs processed:               {len(font.glyphs)}")
    print(f"{'=' * 60}\n")
    
    Message(
        "Coloring Complete",
        f"Glyphs colored:\n\n"
        f"● {counters['uppercase_paths']} dark blue    (uppercase paths)\n"
        f"● {counters['lowercase_paths']} light blue   (lowercase paths)\n"
        f"● {counters['smallcaps_paths']} pink         (small caps paths)\n"
        f"● {counters['other_paths']} light green  (other paths)\n"
        f"● {counters['both']} purple       (paths + components)\n"
        f"● {counters['components_only']} dark green   (components only)\n"
        f"● {counters['empty']} unmarked     (empty)",
    )


# Run the script
color_glyphs()