#MenuTitle: Remove Glyphs Not in Reference Font
# -*- coding: utf-8 -*-
"""
remove_glyphs_not_in_reference.py

Compares two open fonts and removes glyphs from a target font that are
not present in a reference font.

Workflow:
  1. Pick the TARGET font  — glyphs will be deleted from this one.
  2. Pick the REFERENCE font — only glyphs whose names appear here are kept.
  3. A preview list shows exactly which glyphs will be deleted before anything
     is touched. Confirm to proceed.

Matching is by glyph name only.
"""

import traceback

from GlyphsApp import Glyphs, Message
from vanilla import Window, PopUpButton, TextBox, Button, HorizontalLine, List


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def font_label(font):
    name = font.familyName or "(untitled)"
    if font.filepath:
        import os
        name += "  [%s]" % os.path.basename(font.filepath)
    return name


# ─────────────────────────────────────────────────────────────────────────────
# Dialog
# ─────────────────────────────────────────────────────────────────────────────

class RemoveGlyphsDialog:

    PADDING = 16
    ROW_H   = 22
    LABEL_W = 130
    POPUP_W = 260
    WIN_W   = 460
    WIN_H   = 560

    def __init__(self):
        self.fonts = Glyphs.fonts
        if len(self.fonts) < 2:
            Message(
                "Not enough fonts open",
                "Please open at least two fonts in Glyphs before running this script.",
            )
            return

        self._glyphs_to_delete = []
        self._build_window()
        self.w.open()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_window(self):
        p  = self.PADDING
        rh = self.ROW_H
        lw = self.LABEL_W
        pw = self.POPUP_W
        w  = self.WIN_W

        self.w = Window(
            (w, self.WIN_H),
            "Remove Glyphs Not in Reference Font",
            autosaveName="com.remove_glyphs_not_in_reference.dialog",
        )

        y = p

        # ── Target font ───────────────────────────────────────────────────────
        self.w.targetSectionLabel = TextBox(
            (p, y, -p, rh),
            "TARGET  (glyphs may be deleted from this font)",
            sizeStyle="small",
        )
        y += rh + 6

        self.w.targetFontLabel = TextBox(
            (p, y, lw, rh), "Font:", sizeStyle="regular"
        )
        self.w.targetFontPopup = PopUpButton(
            (p + lw, y, pw, rh),
            [font_label(f) for f in self.fonts],
            callback=self._selection_changed,
            sizeStyle="regular",
        )
        y += rh + 12

        self.w.divider1 = HorizontalLine((p, y, -p, 1))
        y += 12

        # ── Reference font ────────────────────────────────────────────────────
        self.w.referenceSectionLabel = TextBox(
            (p, y, -p, rh),
            "REFERENCE  (only glyphs found here are kept in the target)",
            sizeStyle="small",
        )
        y += rh + 6

        self.w.referenceFontLabel = TextBox(
            (p, y, lw, rh), "Font:", sizeStyle="regular"
        )
        self.w.referenceFontPopup = PopUpButton(
            (p + lw, y, pw, rh),
            [font_label(f) for f in self.fonts],
            callback=self._selection_changed,
            sizeStyle="regular",
        )
        # Default reference to second open font
        if len(self.fonts) > 1:
            self.w.referenceFontPopup.set(1)
        y += rh + 12

        self.w.divider2 = HorizontalLine((p, y, -p, 1))
        y += 12

        # ── Preview list ──────────────────────────────────────────────────────
        self.w.previewLabel = TextBox(
            (p, y, -p, rh),
            "Glyphs that will be deleted from the target:",
            sizeStyle="small",
        )
        y += rh + 4

        list_h = 180
        self.w.previewList = List(
            (p, y, -p, list_h),
            [],
            columnDescriptions=[
                {"title": "Glyph name", "key": "name", "width": 200},
                {"title": "Unicode",    "key": "unicode", "width": 80},
                {"title": "Category",   "key": "category"},
            ],
            allowsMultipleSelection=False,
            drawFocusRing=False,
        )
        y += list_h + 6

        self.w.previewNote = TextBox(
            (p, y, -p, rh),
            "— press Compare to populate the list —",
            sizeStyle="small",
        )
        y += rh + 12

        self.w.divider3 = HorizontalLine((p, y, -p, 1))
        y += 12

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_w = 120
        self.w.cancelButton = Button(
            (p, y, btn_w, rh + 4),
            "Cancel",
            callback=self._cancel,
        )
        self.w.compareButton = Button(
            (p + btn_w + 8, y, btn_w, rh + 4),
            "Compare",
            callback=self._compare,
        )
        self.w.deleteButton = Button(
            (-p - btn_w, y, btn_w, rh + 4),
            "Delete Glyphs",
            callback=self._delete,
        )
        self.w.deleteButton.enable(False)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _selection_changed(self, sender):
        # Reset preview whenever the user changes a font popup
        self.w.previewList.set([])
        self.w.previewNote.set("— press Compare to populate the list —")
        self.w.deleteButton.enable(False)
        self._glyphs_to_delete = []

    def _cancel(self, sender):
        self.w.close()

    def _compare(self, sender):
        target_font    = self.fonts[self.w.targetFontPopup.get()]
        reference_font = self.fonts[self.w.referenceFontPopup.get()]

        if target_font is reference_font:
            Message("Same font selected", "Target and reference fonts must be different.")
            return

        reference_names = {g.name for g in reference_font.glyphs}

        self._glyphs_to_delete = [
            g for g in target_font.glyphs
            if g.name not in reference_names
        ]
        self._glyphs_to_delete.sort(key=lambda g: g.name)

        rows = []
        for g in self._glyphs_to_delete:
            uni = g.unicode or ""
            if isinstance(uni, (list, tuple)):
                uni = ", ".join(uni)
            rows.append({
                "name":     g.name,
                "unicode":  uni,
                "category": (g.category or ""),
            })

        self.w.previewList.set(rows)

        count = len(self._glyphs_to_delete)
        if count:
            self.w.previewNote.set(
                "%d glyph(s) will be deleted. Review the list, then press Delete Glyphs." % count
            )
            self.w.deleteButton.enable(True)
        else:
            self.w.previewNote.set("✅  All glyphs in the target are present in the reference. Nothing to delete.")
            self.w.deleteButton.enable(False)

    def _delete(self, sender):
        if not self._glyphs_to_delete:
            return

        target_font = self.fonts[self.w.targetFontPopup.get()]
        count       = len(self._glyphs_to_delete)

        deleted  = []
        errors   = []

        for glyph in self._glyphs_to_delete:
            try:
                target_font.removeGlyph_(glyph)
                deleted.append(glyph.name)
            except Exception:
                errors.append(
                    (glyph.name, traceback.format_exc().strip().splitlines()[-1])
                )

        self.w.close()

        # ── Report ────────────────────────────────────────────────────────────
        lines = [
            "Target    : %s" % font_label(target_font),
            "Reference : %s" % font_label(self.fonts[self.w.referenceFontPopup.get()]),  # still readable after close
            "",
            "✅  Deleted : %d glyph(s)" % len(deleted),
        ]

        if errors:
            lines += ["", "❌  Errors (%d):" % len(errors)]
            lines += ["      %s: %s" % (n, msg) for n, msg in errors]

        report = "\n".join(lines)
        print(report)
        Message("Remove Glyphs — done", report)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

RemoveGlyphsDialog()