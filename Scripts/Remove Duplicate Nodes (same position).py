#MenuTitle: Remove Duplicate Nodes (same position)
# -*- coding: utf-8 -*-
__doc__ = """
Scans all glyphs in the frontmost font.
For every path, if two or more consecutive nodes share the same
position, the duplicates are deleted and the path is rebuilt.
Reports how many nodes were removed and from which glyphs.
"""

from GlyphsApp import Glyphs, GSNode


def nodes_equal(a, b):
    """Return True if two nodes share the same x/y position."""
    return round(a.position.x) == round(b.position.x) and \
           round(a.position.y) == round(b.position.y)


def clean_path(path):
    """
    Remove duplicate consecutive nodes from a path by rebuilding its node list.
    Consecutive duplicates wrap around: last node is compared to first.
    Returns the number of nodes removed.
    """
    original_nodes = list(path.nodes)
    count = len(original_nodes)
    if count < 2:
        return 0

    # Build a list of indices to KEEP.
    # A node is a duplicate if it shares its position with the NEXT node (wrapping).
    keep = []
    for i in range(count):
        next_i = (i + 1) % count
        if not nodes_equal(original_nodes[i], original_nodes[next_i]):
            keep.append(i)

    removed = count - len(keep)
    if removed == 0:
        return 0

    # Rebuild the path using only kept nodes.
    # Clone each kept node as a fresh GSNode so we're not referencing stale objects.
    new_nodes = []
    for i in keep:
        old = original_nodes[i]
        n = GSNode()
        n.position = old.position
        n.type = old.type
        n.smooth = old.smooth
        new_nodes.append(n)

    # Replace the path's nodes entirely
    path.nodes = new_nodes

    return removed


def run():
    font = Glyphs.font
    if font is None:
        print("No font open.")
        return

    Glyphs.showMacroWindow()
    print("=" * 60)
    print("Remove Duplicate Nodes (same position)")
    print("Font: {}".format(font.familyName or str(font.filepath) or "(unnamed)"))
    print("=" * 60)

    total_removed = 0
    affected_glyphs = []

    for glyph in font.glyphs:
        glyph_removed = 0

        for layer in glyph.layers:
            if not (layer.isMasterLayer or layer.isSpecialLayer):
                continue

            for path in layer.paths:
                count = clean_path(path)
                glyph_removed += count

        if glyph_removed > 0:
            total_removed += glyph_removed
            affected_glyphs.append((glyph.name, glyph_removed))

    # Report
    if affected_glyphs:
        print(u"\nGlyphs cleaned ({} glyph(s)):".format(len(affected_glyphs)))
        for name, count in affected_glyphs:
            print(u"  {} — {} duplicate node(s) removed".format(name, count))
    else:
        print(u"\nNo duplicate nodes found.")

    print(u"\n" + "=" * 60)
    print(u"Done. {} duplicate node(s) removed across {} glyph(s).".format(
        total_removed, len(affected_glyphs)
    ))
    print("=" * 60)


run()