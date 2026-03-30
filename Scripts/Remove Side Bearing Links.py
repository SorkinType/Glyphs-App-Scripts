#MenuTitle: Remove Side Bearing Links and Width Links
# -*- coding: utf-8 -*-
"""
Remove Side Bearing Links
─────────────────────────
Removes LSB, RSB, and Width links from all selected glyphs across every master.
 
Sidebearing/width links in Glyphs can exist at two levels:
  • Glyph level  — glyph.leftMetricsKey / glyph.rightMetricsKey / glyph.widthMetricsKey
                   This is the most common case: one link applies to all masters.
  • Layer level  — layer.leftMetricsKey / layer.rightMetricsKey / layer.widthMetricsKey
                   A per-master override used when a single master needs a
                   different link (or an explicit override of the glyph-level one).
 
All three levels are scanned and cleared.
"""
 
import traceback
 
from GlyphsApp import Glyphs, Message
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
 
 
def has_link(value):
    """True if a metricsKey value is a non-empty string (i.e. a link expression)."""
    return isinstance(value, str) and value.strip() != ""
 
 
def collect_links(font, glyph_names):
    """
    Scan every named glyph for LSB, RSB, and Width links at both glyph
    and layer level.
 
    Returns a list of dicts:
        Glyph      — glyph name
        Master     — master name, or "(all masters)" for glyph-level keys
        Side       — "LSB", "RSB", or "Width"
        Expression — the link string, e.g. "=H" or "=n+20"
        Level      — "glyph" or "layer" (used internally during removal)
    """
    rows = []
 
    for name in glyph_names:
        glyph = font.glyphs[name]
        if glyph is None:
            continue
 
        # ── Glyph-level keys ──────────────────────────────────────────────────
        for attr, side in (
            ("leftMetricsKey",  "LSB"),
            ("rightMetricsKey", "RSB"),
            ("widthMetricsKey", "Width"),
        ):
            val = getattr(glyph, attr, None)
            if has_link(val):
                rows.append({
                    "Glyph":      name,
                    "Master":     "(all masters)",
                    "Side":       side,
                    "Expression": val,
                    "Level":      "glyph",
                })
 
        # ── Layer-level keys (per-master overrides) ───────────────────────────
        for master in font.masters:
            layer = glyph.layers[master.id]
            if layer is None:
                continue
            for attr, side in (
                ("leftMetricsKey",  "LSB"),
                ("rightMetricsKey", "RSB"),
                ("widthMetricsKey", "Width"),
            ):
                val = getattr(layer, attr, None)
                if has_link(val):
                    rows.append({
                        "Glyph":      name,
                        "Master":     master.name,
                        "Side":       side,
                        "Expression": val,
                        "Level":      "layer",
                    })
 
    return rows
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Dialog
# ─────────────────────────────────────────────────────────────────────────────
 
class RemoveSideBearingLinksDialog:
 
    PADDING = 16
    ROW_H   = 22
    WIN_W   = 580
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
 
        self.links = collect_links(self.font, self.glyph_names)
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
            + rh + 6        # font info label
            + 1 + 10        # divider
            + rh + 6        # preview label
            + lh + 8        # list
            + rh + 10       # note label
            + 1 + 12        # divider
            + (rh + 4)      # buttons
            + p
        )
 
        self.w = Window(
            (w, win_h),
            "Remove Side Bearing & Width Links",
            autosaveName="com.remove_sb_links.dialog",
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
 
        count = len(self.links)
        self.w.previewLabel = TextBox(
            (p, y, -p, rh),
            "%d link(s) found (LSB / RSB / Width) — these will be removed:" % count
            if count else "No LSB, RSB, or Width links found in the selected glyphs.",
            sizeStyle="small",
        )
        y += rh + 6
 
        list_rows = [
            {
                "Glyph":      r["Glyph"],
                "Master":     r["Master"],
                "Side":       r["Side"],
                "Expression": r["Expression"],
            }
            for r in self.links
        ]
 
        self.w.linkList = List(
            (p, y, -p, lh),
            list_rows,
            columnDescriptions=[
                {"title": "Glyph",      "key": "Glyph",      "width": 160},
                {"title": "Master",     "key": "Master",      "width": 130},
                {"title": "Side",       "key": "Side",        "width": 60},
                {"title": "Expression", "key": "Expression"},
            ],
            allowsMultipleSelection=False,
            drawFocusRing=False,
        )
        y += lh + 8
 
        self.w.noteLabel = TextBox(
            (p, y, -p, rh),
            "Glyph-level links apply to all masters. Layer-level links are per-master overrides."
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
            "Remove Links",
            callback=self._remove,
        )
        self.w.removeButton.enable(count > 0)
 
    # ── Callbacks ─────────────────────────────────────────────────────────────
 
    def _cancel(self, sender):
        self.w.close()
 
    def _remove(self, sender):
        self.w.close()
 
        font    = self.font
        removed = []
        errors  = []
 
        for name in self.glyph_names:
            glyph = font.glyphs[name]
            if glyph is None:
                continue
            try:
                # ── Glyph-level keys ──────────────────────────────────────────
                for attr, side in (
                    ("leftMetricsKey",  "LSB"),
                    ("rightMetricsKey", "RSB"),
                    ("widthMetricsKey", "Width"),
                ):
                    val = getattr(glyph, attr, None)
                    if has_link(val):
                        removed.append((name, "(all masters)", side, val))
                        setattr(glyph, attr, None)
 
                # ── Layer-level keys ──────────────────────────────────────────
                for master in font.masters:
                    layer = glyph.layers[master.id]
                    if layer is None:
                        continue
                    for attr, side in (
                        ("leftMetricsKey",  "LSB"),
                        ("rightMetricsKey", "RSB"),
                        ("widthMetricsKey", "Width"),
                    ):
                        val = getattr(layer, attr, None)
                        if has_link(val):
                            removed.append((name, master.name, side, val))
                            setattr(layer, attr, None)
 
            except Exception:
                errors.append(
                    (name, traceback.format_exc().strip().splitlines()[-1])
                )
 
        # ── Report ────────────────────────────────────────────────────────────
        lines = [
            "Font: %s" % font_label(font),
            "",
            "Links removed: %d" % len(removed),
        ]
        for name, master, side, expr in removed:
            lines.append("      %s  [%s]  %s  was: %s" % (name, master, side, expr))
 
        if errors:
            lines += ["", "Errors (%d):" % len(errors)]
            for name, msg in errors:
                lines += ["      %s: %s" % (name, msg)]
 
        report = "\n".join(lines)
        print(report)
        Message("Remove Side Bearing & Width Links — done", report)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────