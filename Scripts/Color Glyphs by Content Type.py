#MenuTitle: Color Glyphs by Content Type
# -*- coding: utf-8 -*-
"""
Mark glyphs with colors based on their content:
- Light green (4):  Contains vector paths only
- Dark green (5):   Contains only components
- Purple (8):       Contains both paths and components
- No color:         Empty glyphs

Save this file in your Glyphs Scripts folder:
~/Library/Application Support/Glyphs 3/Scripts/

Usage:
1. Open a font file
2. Run this script from Scripts menu
3. All glyphs will be automatically colored based on their content
"""


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
    print("COLOR GLYPHS BY CONTENT TYPE")
    print("=" * 60)

    # Official Glyphs color palette indices (0–11):
    #  0 = Red,        1 = Orange,  2 = Brown,      3 = Yellow
    #  4 = Light Green, 5 = Dark Green, 6 = Cyan,   7 = Blue
    #  8 = Purple,     9 = Pink,    10 = Light Gray, 11 = Dark Gray
    LIGHT_GREEN = 4   # Paths only                (light green)
    DARK_GREEN  = 5   # Components only            (dark green)
    PURPLE      = 8   # Mixed (paths + components) (purple)

    counters = {
        'paths_only':      0,
        'both':            0,
        'components_only': 0,
        'empty':           0,
    }

    for glyph in font.glyphs:
        content_type = analyze_glyph_content(glyph)
        counters[content_type] += 1

        if content_type == 'paths_only':
            glyph.color = LIGHT_GREEN
            print(f"  {glyph.name}: Light Green (paths only)")

        elif content_type == 'both':
            glyph.color = PURPLE
            print(f"  {glyph.name}: Purple (paths + components)")

        elif content_type == 'components_only':
            glyph.color = DARK_GREEN
            print(f"  {glyph.name}: Dark Green (components only)")

        elif content_type == 'empty':
            glyph.color = None
            print(f"  {glyph.name}: No color (empty)")

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"Light Green (paths only):          {counters['paths_only']}")
    print(f"Dark Green  (components only):     {counters['components_only']}")
    print(f"Purple      (paths + components):  {counters['both']}")
    print(f"No color    (empty):               {counters['empty']}")
    print(f"{'=' * 60}")
    print(f"Total glyphs processed:            {len(font.glyphs)}")
    print(f"{'=' * 60}\n")

    Message(
        "Coloring Complete",
        f"Glyphs colored:\n\n"
        f"● {counters['paths_only']} light green  (paths only)\n"
        f"● {counters['both']} purple        (paths + components)\n"
        f"● {counters['components_only']} dark green   (components only)\n"
        f"● {counters['empty']} unmarked      (empty)",
    )


# Run the script
color_glyphs()
