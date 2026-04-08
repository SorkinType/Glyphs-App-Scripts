#MenuTitle: Copy Outlines to Background
# -*- coding: utf-8 -*-
"""
copy_to_background.py

Copies outlines from selected glyphs in a source font into the background
layer of the matching glyphs in a target font.

• Only glyphs selected in the source font's Edit tab (or Font tab) are processed.
• Glyphs are matched by name.
• The target background is replaced with the copied shapes.
• A Vanilla dialog lets you choose source font and target font, then map
  each source master to a target master. All enabled pairs are processed in
  one run — no need to repeat the script per master.
"""

import traceback

from GlyphsApp import Glyphs, Message
from vanilla import (
    Window, PopUpButton, TextBox, Button, HorizontalLine, CheckBox
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def font_label(font):
    """Human-readable label for a font."""
    name = font.familyName or "(untitled)"
    path = font.filepath
    if path:
        import os
        name += "  [%s]" % os.path.basename(path)
    return name


def selected_glyph_names(font):
    """
    Return the names of glyphs currently selected in *font*.
    Works whether the user is in the Font tab or the Edit tab.
    """
    names = []
    # Font tab selection
    if font.selection:
        for g in font.selection:
            if hasattr(g, "name"):
                names.append(g.name)
    # Edit tab — currentTab.selectedLayers
    if not names and font.currentTab:
        for layer in font.currentTab.selectedLayers:
            if layer.parent and layer.parent.name not in names:
                names.append(layer.parent.name)
    return names


def layer_for_master_name(glyph, master_name):
    """First layer matching master_name; falls back to layer[0]."""
    for layer in glyph.layers:
        if layer.name == master_name:
            return layer
    return glyph.layers[0] if glyph.layers else None


def copy_shapes(src_layer, dst_layer):
    """
    Replace the background of dst_layer with a copy of the shapes in src_layer.
    Uses direct assignment to clear, which is compatible with Glyphs 3
    GSBackgroundLayer (the old removePathAtIndex_ / removeComponentAtIndex_
    ObjC methods no longer exist on that object in Glyphs 3).
    """
    bg = dst_layer.background

    # ── Clear existing background content (Glyphs 3 compatible) ───────────
    bg.paths      = []
    bg.components = []

    # ── Copy paths from source ─────────────────────────────────────────────
    for path in src_layer.paths:
        bg.paths.append(path.copy())

    # ── Copy components from source ────────────────────────────────────────
    for comp in src_layer.components:
        bg.components.append(comp.copy())


# ─────────────────────────────────────────────────────────────────────────────
# Dialog
# ─────────────────────────────────────────────────────────────────────────────

class CopyToBackgroundDialog:

    PADDING = 16
    ROW_H   = 22
    LABEL_W = 120
    POPUP_W = 180
    WIN_W   = 500

    def __init__(self):
        self.fonts = Glyphs.fonts
        if len(self.fonts) < 2:
            Message(
                "Not enough fonts open",
                "Please open at least two fonts in Glyphs before running this script.",
            )
            return

        # Pairing rows state — rebuilt whenever fonts change
        self._pair_rows    = []
        self._pair_start_y = 0

        self._build_window()
        self.w.open()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_window(self):
        p   = self.PADDING
        rh  = self.ROW_H
        lw  = self.LABEL_W
        w   = self.WIN_W

        src_font  = self.fonts[0]
        dst_font  = self.fonts[1] if len(self.fonts) > 1 else self.fonts[0]
        n_masters = len(src_font.masters)

        # Column x positions for master-pair rows
        self._col_cb   = p
        self._col_src  = p + 24
        self._col_arr  = self._col_src + 160
        self._col_dst  = self._col_arr + 22

        # Window height calculation
        header_h = p + rh + 8 + rh + 8 + rh + 10 + 1 + 12 + rh + 6
        rows_h   = n_masters * (rh + 8)
        footer_h = 12 + 1 + 12 + (rh + 4) + p
        win_h    = header_h + rows_h + footer_h

        self.w = Window(
            (w, win_h),
            "Copy Outlines to Background",
            autosaveName="com.copy_to_background.dialog",
        )

        y = p

        # ── Font pickers ──────────────────────────────────────────────────────
        self.w.sourceFontLabel = TextBox((p, y, lw, rh), "Source font:", sizeStyle="regular")
        self.w.sourceFontPopup = PopUpButton(
            (p + lw, y, self.POPUP_W + 40, rh),
            [font_label(f) for f in self.fonts],
            callback=self._source_font_changed,
            sizeStyle="regular",
        )
        y += rh + 8

        self.w.targetFontLabel = TextBox((p, y, lw, rh), "Target font:", sizeStyle="regular")
        self.w.targetFontPopup = PopUpButton(
            (p + lw, y, self.POPUP_W + 40, rh),
            [font_label(f) for f in self.fonts],
            callback=self._target_font_changed,
            sizeStyle="regular",
        )
        self.w.targetFontPopup.set(1)
        y += rh + 8

        self.w.sourceNote = TextBox(
            (p, y, -p, rh),
            "ℹ️  Only glyphs selected in the source font will be copied.",
            sizeStyle="small",
        )
        y += rh + 10

        self.w.divider1 = HorizontalLine((p, y, -p, 1))
        y += 12

        # ── Column headers ────────────────────────────────────────────────────
        self.w.colHeaderEnable = TextBox((self._col_cb,  y, 22,  rh), "✓",             sizeStyle="small")
        self.w.colHeaderSrc    = TextBox((self._col_src, y, 155, rh), "Source master", sizeStyle="small")
        self.w.colHeaderDst    = TextBox((self._col_dst, y, self.POPUP_W, rh), "Target master", sizeStyle="small")
        y += rh + 6

        # ── Master pairing rows ───────────────────────────────────────────────
        self._pair_start_y = y
        self._build_master_rows(src_font, dst_font, start_y=y)
        y += n_masters * (rh + 8)

        # ── Divider + buttons ─────────────────────────────────────────────────
        y += 4
        self.w.divider2 = HorizontalLine((p, y, -p, 1))
        y += 12

        btn_w = 120
        self.w.cancelButton = Button(
            (p, y, btn_w, rh + 4), "Cancel", callback=self._cancel
        )
        self.w.runButton = Button(
            (-p - btn_w, y, btn_w, rh + 4), "Copy", callback=self._run
        )

    # ── Master row builder ────────────────────────────────────────────────────

    def _build_master_rows(self, src_font, dst_font, start_y):
        """
        Create one checkbox + source-label + arrow + target-popup row for
        every master in src_font. Controls are stored as w._row_* attributes.
        """
        rh = self.ROW_H

        # Remove any previously created row controls
        for attr in list(vars(self.w).keys()):
            if attr.startswith("_row_"):
                try:
                    delattr(self.w, attr)
                except Exception:
                    pass

        self._pair_rows = []
        dst_master_names = [m.name for m in dst_font.masters] or ["(no masters)"]

        y = start_y
        for i, master in enumerate(src_font.masters):
            src_name = master.name

            # Checkbox
            cb_attr = "_row_cb_%d" % i
            setattr(self.w, cb_attr,
                CheckBox((self._col_cb, y + 1, 22, rh), "", value=True, sizeStyle="regular")
            )

            # Source master name
            lbl_attr = "_row_lbl_%d" % i
            setattr(self.w, lbl_attr,
                TextBox((self._col_src, y, 155, rh), src_name, sizeStyle="regular")
            )

            # Arrow
            arr_attr = "_row_arr_%d" % i
            setattr(self.w, arr_attr,
                TextBox((self._col_arr, y, 20, rh), "→", sizeStyle="regular")
            )

            # Target master popup — auto-match by name, else use positional index
            default_idx = min(i, len(dst_master_names) - 1)
            for j, dn in enumerate(dst_master_names):
                if dn == src_name:
                    default_idx = j
                    break

            popup_attr = "_row_popup_%d" % i
            setattr(self.w, popup_attr,
                PopUpButton(
                    (self._col_dst, y, self.POPUP_W, rh),
                    dst_master_names,
                    sizeStyle="regular",
                )
            )
            getattr(self.w, popup_attr).set(default_idx)

            self._pair_rows.append({
                "src_master": src_name,
                "cb_attr":    cb_attr,
                "popup_attr": popup_attr,
                "dst_names":  dst_master_names,
            })

            y += rh + 8

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _source_font_changed(self, sender):
        src_font = self.fonts[sender.get()]
        dst_font = self.fonts[self.w.targetFontPopup.get()]
        self._build_master_rows(src_font, dst_font, start_y=self._pair_start_y)

    def _target_font_changed(self, sender):
        src_font = self.fonts[self.w.sourceFontPopup.get()]
        dst_font = self.fonts[sender.get()]
        self._build_master_rows(src_font, dst_font, start_y=self._pair_start_y)

    def _cancel(self, sender):
        self.w.close()

    def _run(self, sender):
        self.w.close()

        src_font = self.fonts[self.w.sourceFontPopup.get()]
        dst_font = self.fonts[self.w.targetFontPopup.get()]

        if src_font is dst_font:
            Message("Same font selected", "Source and target fonts must be different.")
            return

        # ── Collect enabled master pairs ──────────────────────────────────────
        master_pairs = []
        for row in self._pair_rows:
            cb    = getattr(self.w, row["cb_attr"])
            popup = getattr(self.w, row["popup_attr"])
            if cb.get():
                dst_name = row["dst_names"][popup.get()]
                master_pairs.append((row["src_master"], dst_name))

        if not master_pairs:
            Message("No masters enabled", "Please tick at least one master pair and try again.")
            return

        # ── Gather selected glyph names from source ───────────────────────────
        glyph_names = selected_glyph_names(src_font)
        if not glyph_names:
            Message(
                "No glyphs selected",
                "Please select one or more glyphs in the source font and run the script again.",
            )
            return

        # ── Build target glyph lookup ─────────────────────────────────────────
        dst_map = {g.name: g for g in dst_font.glyphs}

        total_copied = 0
        pair_reports = []

        for src_master_name, dst_master_name in master_pairs:
            copied       = []
            no_match     = []
            empty_source = []
            errors       = []

            for name in glyph_names:
                src_glyph = src_font.glyphs[name]
                if src_glyph is None:
                    no_match.append(name)
                    continue

                src_layer = layer_for_master_name(src_glyph, src_master_name)
                if src_layer is None:
                    no_match.append(name)
                    continue

                # Debug to Macro Panel
                print("DEBUG: master=%s  glyph=%s  paths=%d  comps=%d" % (
                    src_master_name, name,
                    len(src_layer.paths), len(src_layer.components)
                ))

                if not src_layer.paths and not src_layer.components:
                    empty_source.append(name)
                    continue

                if name not in dst_map:
                    no_match.append(name)
                    continue

                dst_glyph = dst_map[name]
                dst_layer = layer_for_master_name(dst_glyph, dst_master_name)
                if dst_layer is None:
                    errors.append((name, "Could not find target layer."))
                    continue

                try:
                    copy_shapes(src_layer, dst_layer)
                    copied.append(name)
                except Exception:
                    errors.append((name, traceback.format_exc().strip().splitlines()[-1]))

            total_copied += len(copied)
            pair_reports.append((src_master_name, dst_master_name, copied, no_match, empty_source, errors))

        # ── Report ────────────────────────────────────────────────────────────
        lines = [
            "Source : %s" % font_label(src_font),
            "Target : %s" % font_label(dst_font),
            "",
            "✅  Total glyphs copied across all masters : %d" % total_copied,
        ]

        for src_mn, dst_mn, copied, no_match, empty_source, errors in pair_reports:
            lines += [
                "",
                "── %s  →  %s" % (src_mn, dst_mn),
                "   Copied : %d" % len(copied),
            ]
            if no_match:
                lines.append("   ⚠️  No match (%d): %s" % (len(no_match), ", ".join(sorted(no_match))))
            if empty_source:
                lines.append("   ⚠️  Empty source (%d): %s" % (len(empty_source), ", ".join(sorted(empty_source))))
            if errors:
                lines.append("   ❌  Errors (%d):" % len(errors))
                for n, msg in errors:
                    lines.append("      %s: %s" % (n, msg))

        report = "\n".join(lines)
        print(report)
        Message("Copy to Background — done", report)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

CopyToBackgroundDialog()
