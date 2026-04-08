#MenuTitle: Remove Duplicate Unicode Glyphs (keep outlined)
# -*- coding: utf-8 -*-
__doc__ = """
Finds glyphs sharing the same Unicode value, then removes whichever
duplicate has no outlines. If both have outlines, or neither has
outlines, the conflict is reported but nothing is deleted.
Operates on the frontmost font.
"""

from GlyphsApp import Glyphs


def has_outlines(glyph):
    for layer in glyph.layers:
        if layer.isMasterLayer or layer.isSpecialLayer:
            if len(layer.shapes) > 0:
                return True
    return False


def unichr_safe(hex_str):
    try:
        return chr(int(hex_str, 16))
    except Exception:
        return "?"


def remove_glyph(font, glyph):
    """Safely remove a glyph from the font (Glyphs 2 & 3 compatible)."""
    font.removeGlyph_(glyph)


def run():
    font = Glyphs.font
    if font is None:
        print("No font open.")
        return

    Glyphs.showMacroWindow()
    print("=" * 60)
    print("Remove Duplicate Unicode Glyphs")
    print("Font: {}".format(font.familyName or str(font.filepath) or "(unnamed)"))
    print("=" * 60)

    unicode_map = {}
    for glyph in font.glyphs:
        unicodes = glyph.unicodes
        if not unicodes:
            continue
        for uval in unicodes:
            uval = uval.upper()
            unicode_map.setdefault(uval, []).append(glyph)

    removed   = []
    conflicts = []
    skipped   = []

    for uval, glyphs in unicode_map.items():
        if len(glyphs) < 2:
            continue

        outlined = [g for g in glyphs if has_outlines(g)]
        empty    = [g for g in glyphs if not has_outlines(g)]
        char_repr = u"U+{} ({})".format(uval, unichr_safe(uval))

        if len(empty) == 0:
            names = u", ".join(g.name for g in glyphs)
            conflicts.append(u"  {} — all have outlines: {}".format(char_repr, names))

        elif len(outlined) == 0:
            glyphs_sorted = sorted(glyphs, key=lambda g: g.name)
            keeper = glyphs_sorted[0]
            to_delete = glyphs_sorted[1:]
            names = u", ".join(g.name for g in to_delete)
            skipped.append(
                u"  {} — all empty, kept '{}', removed: {}".format(
                    char_repr, keeper.name, names)
            )
            for g in to_delete:
                remove_glyph(font, g)

        else:
            for g in empty:
                removed.append(u"  {} — removed empty glyph '{}'".format(char_repr, g.name))
                remove_glyph(font, g)

    if removed:
        print(u"\nRemoved ({} glyph(s)):".format(len(removed)))
        for line in removed:
            print(line)

    if skipped:
        print(u"\nAll-empty duplicates resolved ({} unicode(s)):".format(len(skipped)))
        for line in skipped:
            print(line)

    if conflicts:
        print(u"\nConflicts — NOT removed, please resolve manually ({} unicode(s)):".format(
            len(conflicts)))
        for line in conflicts:
            print(line)

    if not removed and not conflicts and not skipped:
        print(u"\nNo duplicate Unicode values found.")

    print(u"\n" + "=" * 60)
    print(u"Done. {} glyph(s) removed, {} conflict(s) need manual review.".format(
        len(removed) + len(skipped), len(conflicts)
    ))
    print("=" * 60)


run()