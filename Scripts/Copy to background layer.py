#MenuTitle: Copy Outlines to Background
# -*- coding: utf-8 -*-
"""
copy_to_background.py

Copies outlines from selected glyphs in a source font into the background
layer of the matching glyphs in a target font.

• Only glyphs selected in the source font's Edit tab (or Font tab) are processed.
• Glyphs are matched by name.
• The target background is replaced with the copied shapes.
• A Vanilla dialog lets you choose source font, source master, target font,
  and target master before anything is written.
"""

import traceback

from GlyphsApp import Glyphs, Message
from vanilla import Window, PopUpButton, TextBox, Button, HorizontalLine


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

    The Glyphs background layer is not a normal GSLayer — you cannot assign
    to its .paths list directly. The reliable approach is to:
      1. Get a mutable copy of src_layer as a GSLayer.
      2. Clear the destination background.
      3. Append each path/component individually using the background's own
         append methods, working on the layer object returned by .background.
    """
    bg = dst_layer.background

    # Clear existing background content
    # Iterate over a copy of the list since we are mutating it
    for path in list(bg.paths):
        bg.removePathAtIndex_(0)
    for _ in list(bg.components):
        bg.removeComponentAtIndex_(0)

    # Copy paths
    for path in src_layer.paths:
        new_path = path.copy()
        bg.paths.append(new_path)

    # Copy components
    for comp in src_layer.components:
        new_comp = comp.copy()
        bg.components.append(new_comp)


# ─────────────────────────────────────────────────────────────────────────────
# Dialog
# ─────────────────────────────────────────────────────────────────────────────

class CopyToBackgroundDialog:

    PADDING  = 16
    ROW_H    = 22
    LABEL_W  = 120
    POPUP_W  = 260
    WIN_W    = 440
    WIN_H    = 310

    def __init__(self):
        self.fonts = Glyphs.fonts
        if len(self.fonts) < 2:
            Message(
                "Not enough fonts open",
                "Please open at least two fonts in Glyphs before running this script.",
            )
            return

        self._build_window()
        self.w.open()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_window(self):
        p  = self.PADDING
        rh = self.ROW_H
        lw = self.LABEL_W
        pw = self.POPUP_W
        w  = self.WIN_W

        self.w = Window(
            (w, self.WIN_H),
            "Copy Outlines to Background",
            autosaveName="com.copy_to_background.dialog",
        )

        y = p

        # ── Source section ────────────────────────────────────────────────────
        self.w.sourceSectionLabel = TextBox(
            (p, y, -p, rh),
            "SOURCE  (read outlines from selected glyphs here)",
            sizeStyle="small",
        )
        y += rh + 6

        self.w.sourceFontLabel = TextBox(
            (p, y, lw, rh), "Font:", sizeStyle="regular"
        )
        self.w.sourceFontPopup = PopUpButton(
            (p + lw, y, pw, rh),
            [font_label(f) for f in self.fonts],
            callback=self._source_font_changed,
            sizeStyle="regular",
        )
        y += rh + 8

        self.w.sourceMasterLabel = TextBox(
            (p, y, lw, rh), "Master:", sizeStyle="regular"
        )
        self.w.sourceMasterPopup = PopUpButton(
            (p + lw, y, pw, rh),
            self._master_names(self.fonts[0]),
            sizeStyle="regular",
        )
        y += rh + 8

        self.w.sourceNote = TextBox(
            (p + lw, y, pw, rh),
            "ℹ️  Only selected glyphs will be copied.",
            sizeStyle="small",
        )
        y += rh + 10

        self.w.divider1 = HorizontalLine((p, y, -p, 1))
        y += 12

        # ── Target section ────────────────────────────────────────────────────
        self.w.targetSectionLabel = TextBox(
            (p, y, -p, rh),
            "TARGET  (write into background layers here)",
            sizeStyle="small",
        )
        y += rh + 6

        self.w.targetFontLabel = TextBox(
            (p, y, lw, rh), "Font:", sizeStyle="regular"
        )
        self.w.targetFontPopup = PopUpButton(
            (p + lw, y, pw, rh),
            [font_label(f) for f in self.fonts],
            callback=self._target_font_changed,
            sizeStyle="regular",
        )
        self.w.targetFontPopup.set(1)   # default to second open font
        y += rh + 8

        self.w.targetMasterLabel = TextBox(
            (p, y, lw, rh), "Master:", sizeStyle="regular"
        )
        self.w.targetMasterPopup = PopUpButton(
            (p + lw, y, pw, rh),
            self._master_names(self.fonts[1] if len(self.fonts) > 1 else self.fonts[0]),
            sizeStyle="regular",
        )
        y += rh + 16

        self.w.divider2 = HorizontalLine((p, y, -p, 1))
        y += 12

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_w = 120
        self.w.cancelButton = Button(
            (p, y, btn_w, rh + 4),
            "Cancel",
            callback=self._cancel,
        )
        self.w.runButton = Button(
            (-p - btn_w, y, btn_w, rh + 4),
            "Copy",
            callback=self._run,
        )

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _master_names(self, font):
        return [m.name for m in font.masters] or ["(no masters)"]

    def _source_font_changed(self, sender):
        font = self.fonts[sender.get()]
        self.w.sourceMasterPopup.setItems(self._master_names(font))

    def _target_font_changed(self, sender):
        font = self.fonts[sender.get()]
        self.w.targetMasterPopup.setItems(self._master_names(font))

    def _cancel(self, sender):
        self.w.close()

    def _run(self, sender):
        self.w.close()

        src_font        = self.fonts[self.w.sourceFontPopup.get()]
        src_master_name = self._master_names(src_font)[self.w.sourceMasterPopup.get()]
        dst_font        = self.fonts[self.w.targetFontPopup.get()]
        dst_master_name = self._master_names(dst_font)[self.w.targetMasterPopup.get()]

        if src_font is dst_font:
            Message("Same font selected", "Source and target fonts must be different.")
            return

        # ── Gather selected glyph names from source ───────────────────────────
        glyph_names = selected_glyph_names(src_font)
        if not glyph_names:
            Message(
                "No glyphs selected",
                "Please select one or more glyphs in the source font and run the script again.",
            )
            return

        # ── Build target lookup ───────────────────────────────────────────────
        dst_map = {g.name: g for g in dst_font.glyphs}

        copied       = []
        no_match     = []
        empty_source = []
        errors       = []

        for name in glyph_names:
            # Source glyph and layer
            src_glyph = src_font.glyphs[name]
            if src_glyph is None:
                no_match.append(name)
                continue

            src_layer = layer_for_master_name(src_glyph, src_master_name)
            if src_layer is None:
                no_match.append(name)
                continue

            if not src_layer.paths and not src_layer.components:
                empty_source.append(name)
                continue

            # Target glyph and layer
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

        # ── Report ────────────────────────────────────────────────────────────
        lines = [
            "Source : %s  (master: %s)" % (font_label(src_font), src_master_name),
            "Target : %s  (master: %s)" % (font_label(dst_font), dst_master_name),
            "",
            "✅  Copied to background : %d glyph(s)" % len(copied),
        ]

        if no_match:
            lines += ["", "⚠️  Not found in target or source (%d):" % len(no_match)]
            lines += ["      " + n for n in sorted(no_match)]

        if empty_source:
            lines += ["", "⚠️  Source layer empty – nothing copied (%d):" % len(empty_source)]
            lines += ["      " + n for n in sorted(empty_source)]

        if errors:
            lines += ["", "❌  Errors (%d):" % len(errors)]
            lines += ["      %s: %s" % (n, msg) for n, msg in errors]

        report = "\n".join(lines)
        print(report)
        Message("Copy to Background — done", report)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

CopyToBackgroundDialog()