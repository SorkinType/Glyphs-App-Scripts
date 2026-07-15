#MenuTitle: Copy Small Caps to c2sc
# -*- coding: utf-8 -*-
"""
Glyphs 3 Script: Copy .sc / .smcp letters as components into .c2sc glyphs.

For every glyph whose name ends in ".sc" (or ".smcp" as fallback):
  - Derive the base letter name (everything before the suffix).
  - Derive the target glyph name by replacing the suffix with ".c2sc".
  - If the target glyph doesn't exist yet, create it and copy the
    category / subCategory / unicode properties from the source.
  - For every master, clear any existing components/paths in the target
    layer and insert a single component that references the .sc source glyph.

Usage: Scripts menu → run this script while a font is open in Glyphs 3.
"""

import GlyphsApp  # noqa – available in the Glyphs runtime


# ── helpers ──────────────────────────────────────────────────────────────────

def find_sc_glyphs(font):
    """
    Return a list of (sc_glyph, suffix_used) tuples for every glyph that
    carries a '.sc' or '.smcp' suffix.

    Priority: '.sc' is preferred. '.smcp' is only used when no '.sc' variant
    exists for the same base letter.
    """
    sc_map   = {}   # base_name → glyph  (for .sc glyphs)
    smcp_map = {}   # base_name → glyph  (for .smcp glyphs)

    for glyph in font.glyphs:
        name = glyph.name
        if name.endswith(".sc"):
            base = name[:-3]          # strip ".sc"
            sc_map[base] = glyph
        elif name.endswith(".smcp"):
            base = name[:-5]          # strip ".smcp"
            smcp_map[base] = glyph

    results = []
    # Collect all unique base names across both maps
    all_bases = set(sc_map.keys()) | set(smcp_map.keys())

    for base in sorted(all_bases):
        if base in sc_map:
            results.append((sc_map[base], ".sc"))
        else:
            results.append((smcp_map[base], ".smcp"))

    return results


def ensure_c2sc_glyph(font, base_name, source_glyph):
    """
    Return the existing .c2sc glyph for *base_name*, or create and add it.
    Newly created glyphs inherit category, subCategory, and (if available)
    the uppercase Unicode codepoint of the base letter.
    """
    target_name = base_name + ".c2sc"
    glyph = font.glyphs[target_name]

    if glyph is None:
        glyph = GSGlyph(target_name)

        # Copy classification from the source small-cap glyph
        if source_glyph.category:
            glyph.category    = source_glyph.category
        if source_glyph.subCategory:
            glyph.subCategory = source_glyph.subCategory

        # Try to assign the Unicode value of the *uppercase* base letter so
        # the glyph shows up correctly in the font. We look for the uppercase
        # base glyph (e.g. "A" for "a.sc") and borrow its unicode value.
        base_glyph = font.glyphs[base_name]
        if base_glyph is None:
            # Try capitalised form (e.g. base "a" → try "A")
            base_glyph = font.glyphs[base_name.upper()] or \
                         font.glyphs[base_name.capitalize()]
        if base_glyph and base_glyph.unicode:
            glyph.unicode = base_glyph.unicode

        font.glyphs.append(glyph)
        print(f"  ✚ Created glyph: {target_name}")
    else:
        print(f"  ↻ Updating glyph: {target_name}")

    return glyph


def set_component_in_all_masters(font, target_glyph, source_glyph_name):
    """
    For every master layer of *target_glyph*:
      - Remove all existing paths and components.
      - Insert one component referencing *source_glyph_name*.
    """
    for layer in target_glyph.layers:
        # Only process master layers (skip brace / bracket layers)
        if layer.layerId not in [m.id for m in font.masters]:
            continue

        layer.shapes.removeAllObjects()          # clear paths & components
        component = GSComponent(source_glyph_name)
        layer.shapes.append(component)


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    font = Glyphs.font
    if font is None:
        Message("No font is open.", "sc_to_c2sc")
        return

    sc_glyphs = find_sc_glyphs(font)

    if not sc_glyphs:
        Message(
            "No glyphs with '.sc' or '.smcp' suffix were found in this font.",
            "sc_to_c2sc"
        )
        return

    print(f"\n── sc → c2sc  ({len(sc_glyphs)} source glyphs found) ──")

    created  = 0
    updated  = 0

    for source_glyph, suffix in sc_glyphs:
        # Derive the base letter name by stripping the suffix
        base_name   = source_glyph.name[: -len(suffix)]  # e.g. "a"
        target_name = base_name + ".c2sc"

        existed_before = font.glyphs[target_name] is not None

        target_glyph = ensure_c2sc_glyph(font, base_name, source_glyph)
        set_component_in_all_masters(font, target_glyph, source_glyph.name)

        if existed_before:
            updated += 1
        else:
            created += 1

    summary = (
        f"Done.\n\n"
        f"  Source suffix used : .sc / .smcp (priority: .sc)\n"
        f"  Glyphs processed   : {len(sc_glyphs)}\n"
        f"  New glyphs created : {created}\n"
        f"  Existing updated   : {updated}"
    )
    print(summary)
    Message(summary, "sc_to_c2sc – finished")


main()