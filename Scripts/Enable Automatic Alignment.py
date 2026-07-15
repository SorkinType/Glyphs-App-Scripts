#MenuTitle: Enable Automatic Alignment
# -*- coding: utf-8 -*-
"""
Enable Automatic Alignment
────────────────────────────────
Re-enables automatic alignment (component.disableAlignment = False) for
all components in the selected glyphs, either just in the current
master, or across every master of the font.

This is the counterpart to scripts that unlock composite widths by
disabling alignment — use this one to put components back into
"Auto" mode once you're done editing.
"""

import traceback

from GlyphsApp import Glyphs, Message
from vanilla import Window, TextBox, Button, HorizontalLine, List, RadioGroup


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


def current_master_name(font):
    master = font.selectedFontMaster
    return master.name if master else None


def collect_disabled_components(font, glyph_names, master_id):
    """
    Scan the given glyphs for components with disableAlignment == True.

    If master_id is None, every layer belonging to a master is checked
    (all masters). If master_id is given, only that master's layer is
    checked for each glyph.

    Returns a list of dicts:
        Glyph     — glyph name
        Master    — master/layer name
        Component — referenced glyph name
        MasterID  — the layer's associated master id (for applying later)
    """
    rows = []

    for name in glyph_names:
        glyph = font.glyphs[name]
        if glyph is None:
            continue

        if master_id is None:
            layers = [glyph.layers[m.id] for m in font.masters]
        else:
            layers = [glyph.layers[master_id]]

        for layer in layers:
            if layer is None or not layer.components:
                continue
            for component in layer.components:
                if component.disableAlignment:
                    rows.append({
                        "Glyph":     name,
                        "Master":    layer.name,
                        "Component": component.componentName,
                        "MasterID":  layer.associatedMasterId,
                    })

    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Dialog
# ─────────────────────────────────────────────────────────────────────────────

class EnableAutomaticAlignmentDialog:

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

        self.current_master = self.font.selectedFontMaster
        self.scope_options = ["Current master only (%s)" % (current_master_name(self.font) or "—"), "All masters"]

        self._build_window()
        self._refresh_list()
        self.w.open()

    # ── Data ──────────────────────────────────────────────────────────────────

    def _current_scope_master_id(self):
        # index 0 == current master only, index 1 == all masters
        if self.w.scopeRadio.get() == 0:
            return self.current_master.id if self.current_master else None
        return None  # None == all masters

    def _refresh_list(self, sender=None):
        master_id = self._current_scope_master_id()
        self.rows = collect_disabled_components(self.font, self.glyph_names, master_id)

        list_rows = [
            {"Glyph": r["Glyph"], "Master": r["Master"], "Component": r["Component"]}
            for r in self.rows
        ]
        self.w.componentList.set(list_rows)

        count = len(self.rows)
        self.w.previewLabel.set(
            "%d component(s) with alignment disabled will be re-enabled:" % count
            if count else "No components with disabled alignment found in this scope."
        )
        self.w.applyButton.enable(count > 0)

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
            + rh + 6        # scope label
            + rh + 10       # radio group
            + rh + 6        # preview label
            + lh + 10       # list
            + 1 + 12        # divider
            + (rh + 4)      # buttons
            + p
        )

        self.w = Window(
            (w, win_h),
            "Enable Automatic Alignment",
            autosaveName="com.enable_automatic_alignment.dialog",
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

        self.w.scopeLabel = TextBox((p, y, -p, rh), "Scope:", sizeStyle="small")
        y += rh + 6

        self.w.scopeRadio = RadioGroup(
            (p, y, -p, rh),
            self.scope_options,
            isVertical=False,
            callback=self._refresh_list,
        )
        self.w.scopeRadio.set(0)
        y += rh + 10

        self.w.previewLabel = TextBox((p, y, -p, rh), "", sizeStyle="small")
        y += rh + 6

        self.w.componentList = List(
            (p, y, -p, lh),
            [],
            columnDescriptions=[
                {"title": "Glyph",     "key": "Glyph",     "width": 160},
                {"title": "Master",    "key": "Master",    "width": 140},
                {"title": "Component", "key": "Component"},
            ],
            allowsMultipleSelection=False,
            drawFocusRing=False,
        )
        y += lh + 10

        self.w.divider2 = HorizontalLine((p, y, -p, 1))
        y += 12

        btn_w = 140
        self.w.cancelButton = Button(
            (p, y, 100, rh + 4),
            "Cancel",
            callback=self._cancel,
        )
        self.w.applyButton = Button(
            (-p - btn_w, y, btn_w, rh + 4),
            "Enable Alignment",
            callback=self._apply,
        )

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _cancel(self, sender):
        self.w.close()

    def _apply(self, sender):
        rows = list(self.rows)  # snapshot before closing
        self.w.close()

        font = self.font
        enabled = []
        errors  = []

        for row in rows:
            try:
                glyph = font.glyphs[row["Glyph"]]
                if glyph is None:
                    continue
                layer = glyph.layers[row["MasterID"]]
                if layer is None:
                    continue
                for component in layer.components:
                    if component.componentName == row["Component"] and component.disableAlignment:
                        component.disableAlignment = False
                        enabled.append((row["Glyph"], layer.name, row["Component"]))
                        break
            except Exception:
                errors.append(
                    (row["Glyph"], traceback.format_exc().strip().splitlines()[-1])
                )

        lines = [
            "Font: %s" % font_label(font),
            "",
            "Components with automatic alignment re-enabled: %d" % len(enabled),
        ]
        for name, master, comp in enabled:
            lines.append("      %s  [%s]  component: %s" % (name, master, comp))

        if errors:
            lines += ["", "Errors (%d):" % len(errors)]
            for name, msg in errors:
                lines += ["      %s: %s" % (name, msg)]

        report = "\n".join(lines).rstrip()
        print(report)
        Message("Enable Automatic Alignment — done", report)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

EnableAutomaticAlignmentDialog()
