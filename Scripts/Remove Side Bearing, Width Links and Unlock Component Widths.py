#MenuTitle: Remove Side Bearing, Width Links and Unlock Component Widths
# -*- coding: utf-8 -*-
"""
Remove Side Bearing, Width Links & Unlock Component Widths
────────────────────────────────────────────────────────────
Removes LSB, RSB, and Width links from all selected glyphs across every
master, AND (optionally) unlocks the width of composite glyphs by
disabling automatic alignment on their components.

Sidebearing/width links in Glyphs can exist at two levels:
  • Glyph level  — glyph.leftMetricsKey / glyph.rightMetricsKey / glyph.widthMetricsKey
                   This is the most common case: one link applies to all masters.
  • Layer level  — layer.leftMetricsKey / layer.rightMetricsKey / layer.widthMetricsKey
                   A per-master override used when a single master needs a
                   different link (or an explicit override of the glyph-level one).

Both levels are scanned and cleared.

Component width lock:
  When a layer is made up only of automatically-aligned components, its
  width field is greyed out / "Auto" in the UI, because Glyphs keeps
  recomputing the layer from the components' own metrics. Setting
  component.disableAlignment = True on each component stops that
  automatic recompute, which unlocks the width field so it can be
  edited (or so links can safely be removed without snapping back).
  This is applied per-layer (masters and any alternate/brace layers).
"""

import traceback

from GlyphsApp import Glyphs, Message
from vanilla import Window, TextBox, Button, HorizontalLine, List, CheckBox


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


METRIC_ATTRS = (
    ("leftMetricsKey",  "LSB"),
    ("rightMetricsKey", "RSB"),
    ("widthMetricsKey", "Width"),
)


def collect_links(font, glyph_names):
    """
    Scan every named glyph for LSB, RSB, and Width links at both glyph
    and layer level.

    Returns a list of dicts:
        Category   — "Metric Link"
        Glyph      — glyph name
        Master     — master name, or "(all masters)" for glyph-level keys
        Detail     — "LSB", "RSB", or "Width"
        Value      — the link string, e.g. "=H" or "=n+20"
        Level      — "glyph" or "layer" (used internally during removal)
    """
    rows = []

    for name in glyph_names:
        glyph = font.glyphs[name]
        if glyph is None:
            continue

        # ── Glyph-level keys ──────────────────────────────────────────────────
        for attr, side in METRIC_ATTRS:
            val = getattr(glyph, attr, None)
            if has_link(val):
                rows.append({
                    "Category": "Metric Link",
                    "Glyph":    name,
                    "Master":   "(all masters)",
                    "Detail":   side,
                    "Value":    val,
                    "Level":    "glyph",
                })

        # ── Layer-level keys (per-master overrides) ───────────────────────────
        for master in font.masters:
            layer = glyph.layers[master.id]
            if layer is None:
                continue
            for attr, side in METRIC_ATTRS:
                val = getattr(layer, attr, None)
                if has_link(val):
                    rows.append({
                        "Category": "Metric Link",
                        "Glyph":    name,
                        "Master":   master.name,
                        "Detail":   side,
                        "Value":    val,
                        "Level":    "layer",
                    })

    return rows


def collect_auto_aligned_components(font, glyph_names):
    """
    Scan every named glyph, on every layer (masters + alternate/brace
    layers), for components that are still automatically aligned
    (component.disableAlignment == False). These are the components
    responsible for locking the layer's width field.

    Returns a list of dicts:
        Category — "Component Alignment"
        Glyph    — glyph name
        Master   — layer name (master name, or brace/alternate layer name)
        Detail   — "Component"
        Value    — component name (the referenced glyph)
    """
    rows = []

    for name in glyph_names:
        glyph = font.glyphs[name]
        if glyph is None:
            continue

        for layer in glyph.layers:
            if not layer.components:
                continue
            for component in layer.components:
                if not component.disableAlignment:
                    rows.append({
                        "Category": "Component Alignment",
                        "Glyph":    name,
                        "Master":   layer.name,
                        "Detail":   "Component",
                        "Value":    component.componentName,
                    })

    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Dialog
# ─────────────────────────────────────────────────────────────────────────────

class RemoveSideBearingLinksDialog:

    PADDING = 16
    ROW_H   = 22
    WIN_W   = 620
    LIST_H  = 240

    def __init__(self):
        self.font = Glyphs.font
        if not self.font:
            Message("No font open", "Please open a font before running this script.")
            return

        self.glyph_names = selected_glyph_names(self.font)
        if not self.glyph_names:
            Message("No glyphs selected", "Please select glyphs in the font first.")
            return

        self.links      = collect_links(self.font, self.glyph_names)
        self.components = collect_auto_aligned_components(self.font, self.glyph_names)

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
            + rh + 4        # checkbox 1
            + rh + 10       # checkbox 2
            + 1 + 12        # divider
            + (rh + 4)      # buttons
            + p
        )

        self.w = Window(
            (w, win_h),
            "Remove Side Bearing & Width Links / Unlock Component Widths",
            autosaveName="com.remove_sb_links_unlock_widths.dialog",
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

        link_count = len(self.links)
        comp_count = len(self.components)
        self.w.previewLabel = TextBox(
            (p, y, -p, rh),
            "%d metric link(s) and %d auto-aligned component(s) found:" % (link_count, comp_count),
            sizeStyle="small",
        )
        y += rh + 6

        list_rows = [
            {
                "Category": r["Category"],
                "Glyph":    r["Glyph"],
                "Master":   r["Master"],
                "Detail":   r["Detail"],
                "Value":    r["Value"],
            }
            for r in (self.links + self.components)
        ]

        self.w.linkList = List(
            (p, y, -p, lh),
            list_rows,
            columnDescriptions=[
                {"title": "Category", "key": "Category", "width": 130},
                {"title": "Glyph",    "key": "Glyph",    "width": 120},
                {"title": "Master",   "key": "Master",   "width": 110},
                {"title": "Detail",   "key": "Detail",   "width": 80},
                {"title": "Value",    "key": "Value"},
            ],
            allowsMultipleSelection=False,
            drawFocusRing=False,
        )
        y += lh + 8

        self.w.removeLinksCheckbox = CheckBox(
            (p, y, -p, rh),
            "Remove LSB / RSB / Width links (%d found)" % link_count,
            value=link_count > 0,
        )
        self.w.removeLinksCheckbox.enable(link_count > 0)
        y += rh + 4

        self.w.unlockWidthsCheckbox = CheckBox(
            (p, y, -p, rh),
            "Unlock widths by disabling auto-alignment on components (%d found)" % comp_count,
            value=comp_count > 0,
        )
        self.w.unlockWidthsCheckbox.enable(comp_count > 0)
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
            "Apply",
            callback=self._remove,
        )
        self.w.removeButton.enable(link_count > 0 or comp_count > 0)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _cancel(self, sender):
        self.w.close()

    def _remove(self, sender):
        do_links   = self.w.removeLinksCheckbox.get()
        do_unlock  = self.w.unlockWidthsCheckbox.get()
        self.w.close()

        font    = self.font
        removed = []
        unlocked = []
        errors  = []

        for name in self.glyph_names:
            glyph = font.glyphs[name]
            if glyph is None:
                continue
            try:
                if do_links:
                    # ── Glyph-level keys ──────────────────────────────────────
                    for attr, side in METRIC_ATTRS:
                        val = getattr(glyph, attr, None)
                        if has_link(val):
                            removed.append((name, "(all masters)", side, val))
                            setattr(glyph, attr, None)

                    # ── Layer-level keys ──────────────────────────────────────
                    for master in font.masters:
                        layer = glyph.layers[master.id]
                        if layer is None:
                            continue
                        for attr, side in METRIC_ATTRS:
                            val = getattr(layer, attr, None)
                            if has_link(val):
                                removed.append((name, master.name, side, val))
                                setattr(layer, attr, None)

                if do_unlock:
                    for layer in glyph.layers:
                        if not layer.components:
                            continue
                        for component in layer.components:
                            if not component.disableAlignment:
                                unlocked.append((name, layer.name, component.componentName))
                                component.disableAlignment = True

            except Exception:
                errors.append(
                    (name, traceback.format_exc().strip().splitlines()[-1])
                )

        # ── Report ────────────────────────────────────────────────────────────
        lines = [
            "Font: %s" % font_label(font),
            "",
        ]

        if do_links:
            lines.append("Links removed: %d" % len(removed))
            for name, master, side, expr in removed:
                lines.append("      %s  [%s]  %s  was: %s" % (name, master, side, expr))
            lines.append("")

        if do_unlock:
            lines.append("Components unlocked (auto-alignment disabled): %d" % len(unlocked))
            for name, master, comp in unlocked:
                lines.append("      %s  [%s]  component: %s" % (name, master, comp))
            lines.append("")

        if errors:
            lines += ["Errors (%d):" % len(errors)]
            for name, msg in errors:
                lines += ["      %s: %s" % (name, msg)]

        report = "\n".join(lines).rstrip()
        print(report)
        Message("Remove Side Bearing & Width Links / Unlock Widths — done", report)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

RemoveSideBearingLinksDialog()
