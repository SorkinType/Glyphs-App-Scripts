#MenuTitle: Mark Non-Shared Glyphs in Red
# -*- coding: utf-8 -*-
"""
MarkNonSharedGlyphs.py

Compares the glyph sets of two currently open Glyphs source files.
Glyphs that exist in one file but not the other are marked red in both files.
Works with source files that have one, two, or more masters.

Matching strategy (in order):
  1. Unicode value(s)  – glyphs with at least one shared Unicode are considered
                         the same glyph regardless of what they are named.
  2. Glyph name        – for glyphs that carry no Unicode (components, alternates,
                         etc.) the name is used as the identity key.

Usage:
  Run from the Script menu while Glyphs App 3 is open.
  A panel listing all open fonts lets you pick Source A and Source B.
  The script marks mismatched glyphs red and reports a summary.
"""

from __future__ import print_function
import os
import vanilla


# ── unicode helpers ───────────────────────────────────────────────────────────

def unicode_set(glyph):
    """
    Return a frozenset of normalised Unicode hex strings for a GSGlyph.
    Handles the Glyphs 3 .unicodes list (may be None) and the legacy
    .unicode string (single value or comma-separated).
    """
    try:
        values = [str(u).upper() for u in (glyph.unicodes or []) if u]
    except AttributeError:
        values = []

    if not values and glyph.unicode:
        values = [v.strip().upper() for v in glyph.unicode.split(",") if v.strip()]

    return frozenset(values)


def build_identity_maps(font):
    """
    Split a font's glyphs into:
      unicode_to_name   { frozenset_of_unicodes -> glyph_name }
      nameset           { glyph names with no unicode }
      all_unicodes_flat { every individual unicode string in the font }
    """
    unicode_to_name   = {}
    nameset           = set()
    all_unicodes_flat = set()

    for g in font.glyphs:
        uniset = unicode_set(g)
        if uniset:
            unicode_to_name[uniset] = g.name
            all_unicodes_flat |= uniset
        else:
            nameset.add(g.name)

    return unicode_to_name, nameset, all_unicodes_flat


def find_unmatched(font_a, font_b):
    """
    Return (unmatched_a, unmatched_b, n_unicode_matches, n_name_matches).
    unmatched_* are lists of GSGlyph objects with no counterpart in the other font.
    """
    uni_map_b, name_set_b, _ = build_identity_maps(font_b)
    uni_map_a, name_set_a, _ = build_identity_maps(font_a)

    n_unicode = 0
    n_name    = 0
    unmatched_a = []

    for g in font_a.glyphs:
        uniset = unicode_set(g)
        if uniset:
            if any(not uniset.isdisjoint(k) for k in uni_map_b):
                n_unicode += 1
                continue
        else:
            if g.name in name_set_b:
                n_name += 1
                continue
            if any(n == g.name for n in uni_map_b.values()):
                n_name += 1
                continue
        unmatched_a.append(g)

    unmatched_b = []
    for g in font_b.glyphs:
        uniset = unicode_set(g)
        if uniset:
            if any(not uniset.isdisjoint(k) for k in uni_map_a):
                continue
        else:
            if g.name in name_set_a:
                continue
            if any(n == g.name for n in uni_map_a.values()):
                continue
        unmatched_b.append(g)

    return unmatched_a, unmatched_b, n_unicode, n_name


def mark_glyphs_red(glyphs):
    for g in glyphs:
        g.color = 1   # 1 = red


def short_name(font):
    """Return a display name for an open GSFont."""
    if font.filepath:
        return os.path.basename(font.filepath)
    return font.familyName or "(Untitled)"


# ── vanilla panel ─────────────────────────────────────────────────────────────

class FontPickerPanel:
    """
    A small floating panel with two pop-up menus (Source A / Source B)
    and a Run button. Built with vanilla so it integrates naturally with
    Glyphs App's UI.
    """

    WINDOW_W = 340
    WINDOW_H = 162
    PAD       = 16
    ROW_H     = 22
    ROW_GAP   = 10
    LABEL_W   = 70
    BTN_H     = 24

    def __init__(self, fonts):
        if len(fonts) < 2:
            Message(
                "Please open at least two font files before running this script.",
                title="Mark Non-Shared Glyphs"
            )
            return

        self.fonts = fonts
        names = [short_name(f) for f in fonts]

        W, H, P = self.WINDOW_W, self.WINDOW_H, self.PAD
        LW = self.LABEL_W
        RW = W - LW - P * 2 - 8   # popup width
        y  = P

        self.w = vanilla.FloatingWindow(
            (W, H),
            "Mark Non-Shared Glyphs in Red",
            autosaveName="MarkNonSharedGlyphsPanel"
        )

        # ── Source A row ──
        self.w.labelA = vanilla.TextBox(
            (P, y + 3, LW, self.ROW_H),
            "Source A:",
            alignment="right"
        )
        self.w.popupA = vanilla.PopUpButton(
            (P + LW + 8, y, RW, self.ROW_H),
            names,
            callback=self._on_popup_change
        )
        y += self.ROW_H + self.ROW_GAP

        # ── Source B row ──
        self.w.labelB = vanilla.TextBox(
            (P, y + 3, LW, self.ROW_H),
            "Source B:",
            alignment="right"
        )
        self.w.popupB = vanilla.PopUpButton(
            (P + LW + 8, y, RW, self.ROW_H),
            names,
            callback=self._on_popup_change
        )
        # Default: B points to the second open font
        if len(fonts) > 1:
            self.w.popupB.set(1)
        y += self.ROW_H + self.ROW_GAP

        # ── Divider ──
        self.w.divider = vanilla.HorizontalLine(
            (P, y, -P, 1)
        )
        y += 10

        # ── Warning / status line ──
        self.w.status = vanilla.TextBox(
            (P, y, -P, self.ROW_H),
            "",
            alignment="center"
        )
        y += self.ROW_H + self.ROW_GAP

        # ── Buttons ──
        self.w.cancelBtn = vanilla.Button(
            (P, y, 80, self.BTN_H),
            "Cancel",
            callback=self._on_cancel
        )
        self.w.runBtn = vanilla.Button(
            (-P - 80, y, 80, self.BTN_H),
            "Run",
            callback=self._on_run
        )
        self.w.runBtn.enable(True)

        self._on_popup_change(None)   # initial validation
        self.w.open()

    # ── callbacks ─────────────────────────────────────────────────────────────

    def _selected_fonts(self):
        idx_a = self.w.popupA.get()
        idx_b = self.w.popupB.get()
        return idx_a, idx_b, self.fonts[idx_a], self.fonts[idx_b]

    def _on_popup_change(self, sender):
        idx_a, idx_b, _, _ = self._selected_fonts()
        if idx_a == idx_b:
            self.w.status.set("⚠️  Please choose two different files.")
            self.w.runBtn.enable(False)
        else:
            self.w.status.set("")
            self.w.runBtn.enable(True)

    def _on_cancel(self, sender):
        self.w.close()
        print("Cancelled.")

    def _on_run(self, sender):
        self.w.close()

        idx_a, idx_b, font_a, font_b = self._selected_fonts()
        name_a = short_name(font_a)
        name_b = short_name(font_b)

        print("Source A : %s  (%d masters)" % (name_a, len(font_a.masters)))
        print("Source B : %s  (%d masters)" % (name_b, len(font_b.masters)))

        unmatched_a, unmatched_b, n_unicode, n_name = find_unmatched(font_a, font_b)

        print("\nMatching stats:")
        print("  Matched via Unicode : %d" % n_unicode)
        print("  Matched via name    : %d" % n_name)
        print("  Total matched       : %d" % (len(font_a.glyphs) - len(unmatched_a)))

        if not unmatched_a and not unmatched_b:
            Message(
                "Both source files share exactly the same glyph set.\nNo glyphs were marked.",
                title="Mark Non-Shared Glyphs"
            )
            print("\nBoth files have equivalent glyph sets. Nothing to mark.")
            return

        mark_glyphs_red(unmatched_a)
        mark_glyphs_red(unmatched_b)

        font_a.save()
        font_b.save()

        # Console report
        def glyph_label(g):
            uniset = unicode_set(g)
            if uniset:
                codes = " ".join("U+%s" % u for u in sorted(uniset))
                return "%s  [%s]" % (g.name, codes)
            return g.name

        print("\n── Results ───────────────────────────────────────────────")
        print("Glyphs ONLY in '%s'  (%d):" % (name_a, len(unmatched_a)))
        for g in sorted(unmatched_a, key=lambda x: x.name):
            print("  • %s" % glyph_label(g))

        print("\nGlyphs ONLY in '%s'  (%d):" % (name_b, len(unmatched_b)))
        for g in sorted(unmatched_b, key=lambda x: x.name):
            print("  • %s" % glyph_label(g))

        total = len(unmatched_a) + len(unmatched_b)
        print("\nTotal glyphs marked red: %d" % total)
        print("──────────────────────────────────────────────────────────")

        Message(
            (
                "Done!\n\n"
                "Only in '{a}':  {na} glyph(s)\n"
                "Only in '{b}':  {nb} glyph(s)\n\n"
                "Matching used Unicode values where available,\n"
                "glyph names as fallback.\n\n"
                "All unmatched glyphs have been marked \U0001f534 red and saved.\n"
                "See the Macro console for details."
            ).format(
                a=name_a, na=len(unmatched_a),
                b=name_b, nb=len(unmatched_b),
            ),
            title="Mark Non-Shared Glyphs"
        )


# ── entry point ───────────────────────────────────────────────────────────────

FontPickerPanel(list(Glyphs.fonts))