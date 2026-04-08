#MenuTitle: Remove Duplicate Nodes
# -*- coding: utf-8 -*-
"""
Remove Duplicate Nodes
───────────────────────
Finds and removes nodes that are stacked exactly on top of another node
in the same path, across all selected glyphs and all masters.

A node is considered a duplicate if it shares the same (x, y) coordinates
as the immediately adjacent node in the path. Two non-adjacent nodes at the
same position are not collapsed (that would change path topology).

A dialog shows a preview of what will be removed before anything is changed.
"""

import traceback

from GlyphsApp import Glyphs, Message, GSOFFCURVE
from vanilla import Window, TextBox, Button, HorizontalLine, List


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def font_label(font):
    name = font.familyName or "(untitled)"
    if font.filepath:
        import os
        name += "  [%s]" % os.path.basename(font.filepath)
    return name


def selected_glyph_names(font):
    """Return glyph names selected in the Font tab or Edit tab."""
    names = []
    if font.selection:
        for g in font.selection:
            if hasattr(g, "name") and g.name not in names:
                names.append(g.name)
    if not names and font.currentTab:
        for layer in font.currentTab.selectedLayers:
            if layer.parent and layer.parent.name not in names:
                names.append(layer.parent.name)
    return names


def coords(node):
    return (int(round(node.x)), int(round(node.y)))


def find_duplicate_indices(path):
    """
    Return the indices of nodes that are at the same position as their
    predecessor in the path (wrapping around for closed paths).

    We walk every consecutive pair. When a duplicate is found we mark the
    *second* node (the one to remove) so the first is always kept.
    Only oncurve–oncurve and offcurve–offcurve pairs are collapsed;
    a degenerate oncurve/offcurve pair at the same spot is also caught.
    """
    nodes = path.nodes
    n = len(nodes)
    if n < 2:
        return []

    to_remove = []
    # For a closed path the last node wraps back to index 0
    pairs = list(range(n - 1))
    if path.closed:
        pairs.append(n - 1)   # pair (nodes[-1], nodes[0])

    for i in pairs:
        a = nodes[i]
        b = nodes[(i + 1) % n]
        if coords(a) == coords(b):
            # Mark the second node for removal
            idx = (i + 1) % n
            if idx not in to_remove:
                to_remove.append(idx)

    return sorted(to_remove, reverse=True)   # reverse so removal doesn't shift indices


def scan_layer(layer, glyph_name, master_name):
    """Return preview rows for duplicates found in this layer."""
    rows = []
    for pi, path in enumerate(layer.paths):
        dupes = find_duplicate_indices(path)
        for idx in dupes:
            node = path.nodes[idx]
            rows.append({
                "Glyph":  glyph_name,
                "Master": master_name,
                "Path":   str(pi),
                "Node":   str(idx),
                "Coords": "(%g, %g)" % (node.x, node.y),
            })
    return rows


def collect_duplicates(font, glyph_names):
    rows = []
    for name in glyph_names:
        glyph = font.glyphs[name]
        if glyph is None:
            continue
        for master in font.masters:
            layer = glyph.layers[master.id]
            if layer is None:
                continue
            rows.extend(scan_layer(layer, name, master.name))
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Dialog
# ─────────────────────────────────────────────────────────────────────────────

class RemoveDuplicateNodesDialog:

    PADDING = 16
    ROW_H   = 22
    WIN_W   = 560
    LIST_H  = 220

    def __init__(self):
        self.font = Glyphs.font
        if not self.font:
            Message("No font open", "Please open a font before running this script.")
            return

        self.glyph_names = selected_glyph_names(self.font)
        if not self.glyph_names:
            Message("No glyphs selected", "Please select glyphs in the font first.")
            return

        self.duplicates = collect_duplicates(self.font, self.glyph_names)
        self._build_window()
        self.w.open()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_window(self):
        p  = self.PADDING
        rh = self.ROW_H
        lh = self.LIST_H
        w  = self.WIN_W

        win_h = (
            p
            + rh + 6        # font info
            + 1 + 10        # divider
            + rh + 6        # preview label
            + lh + 8        # list
            + rh + 10       # note
            + 1 + 12        # divider
            + (rh + 4)      # buttons
            + p
        )

        self.w = Window(
            (w, win_h),
            "Remove Duplicate Nodes",
            autosaveName="com.remove_duplicate_nodes.dialog",
        )

        y = p

        self.w.fontLabel = TextBox(
            (p, y, -p, rh),
            "Font: %s   |   %d glyph(s) selected   |   %d master(s)" % (
                font_label(self.font),
                len(self.glyph_names),
                len(self.font.masters),
            ),
            sizeStyle="small",
        )
        y += rh + 6

        self.w.divider1 = HorizontalLine((p, y, -p, 1))
        y += 10

        count = len(self.duplicates)
        self.w.previewLabel = TextBox(
            (p, y, -p, rh),
            "%d duplicate node(s) found — these will be removed:" % count
            if count else "No duplicate nodes found in the selected glyphs.",
            sizeStyle="small",
        )
        y += rh + 6

        self.w.nodeList = List(
            (p, y, -p, lh),
            self.duplicates,
            columnDescriptions=[
                {"title": "Glyph",  "key": "Glyph",  "width": 160},
                {"title": "Master", "key": "Master",  "width": 120},
                {"title": "Path",   "key": "Path",    "width": 40},
                {"title": "Node",   "key": "Node",    "width": 45},
                {"title": "Coords", "key": "Coords"},
            ],
            allowsMultipleSelection=False,
            drawFocusRing=False,
        )
        y += lh + 8

        self.w.noteLabel = TextBox(
            (p, y, -p, rh),
            "Only adjacent duplicate nodes are removed. The first of each pair is kept."
            if count else "",
            sizeStyle="small",
        )
        y += rh + 10

        self.w.divider2 = HorizontalLine((p, y, -p, 1))
        y += 12

        btn_w = 140
        self.w.cancelButton = Button(
            (p, y, 100, rh + 4),
            "Cancel",
            callback=self._cancel,
        )
        self.w.removeButton = Button(
            (-p - btn_w, y, btn_w, rh + 4),
            "Remove Nodes",
            callback=self._remove,
        )
        self.w.removeButton.enable(count > 0)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _cancel(self, sender):
        self.w.close()

    def _remove(self, sender):
        self.w.close()

        font    = self.font
        removed = 0
        errors  = []

        for name in self.glyph_names:
            glyph = font.glyphs[name]
            if glyph is None:
                continue
            for master in font.masters:
                layer = glyph.layers[master.id]
                if layer is None:
                    continue
                try:
                    for path in layer.paths:
                        indices = find_duplicate_indices(path)
                        for idx in indices:   # already sorted high→low
                            path.removeNodeAtIndex_(idx)
                            removed += 1
                except Exception:
                    errors.append(
                        (name, master.name,
                         traceback.format_exc().strip().splitlines()[-1])
                    )

        lines = [
            "Font: %s" % font_label(font),
            "",
            "Duplicate nodes removed: %d" % removed,
        ]
        if errors:
            lines += ["", "Errors (%d):" % len(errors)]
            for name, master, msg in errors:
                lines += ["      %s [%s]: %s" % (name, master, msg)]

        report = "\n".join(lines)
        print(report)
        Message("Remove Duplicate Nodes — done", report)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

RemoveDuplicateNodesDialog()