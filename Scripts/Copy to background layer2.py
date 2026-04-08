#MenuTitle: Copy Outlines to Background 2
# -*- coding: utf-8 -*-
"""
copy_to_background.py

Copies outlines from selected glyphs in a source font into the background
layer of the matching glyphs in a target font.

• Only glyphs selected in the source font's Edit tab (or Font tab) are processed.
• Glyphs are matched by name, with a normalisation fallback so that the
  suffixes .sc and .smcp are treated as equivalent (e.g. "gimel-hb.sc" will
  match "gimel-hb.smcp" in the target and vice versa).
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


# Suffix pairs that should be treated as equivalent.
# Each tuple is (suffix_a, suffix_b). Matching is case-sensitive and only
# applies to the final suffix (i.e. the last dot-separated token).
EQUIVALENT_SUFFIXES = [
    (".sc", ".smcp"),
]


def normalise_name(name):
    """
    Return a canonical version of *name* with equivalent suffixes collapsed.
    ".smcp" is rewritten to ".sc" so both sides of a match share the same key.
    Only the final suffix is rewritten; the rest of the name is untouched.
    """
    for a, b in EQUIVALENT_SUFFIXES:
        if name.endswith(b):
            return name[: -len(b)] + a
        # No need to rewrite "a" — it is already canonical.
    return name


def build_dst_map(dst_font):
    """
    Build two lookup dicts for target glyphs:
      exact_map  : glyph.name  → GSGlyph   (direct hit)
      normal_map : normalise_name(glyph.name) → GSGlyph  (normalised fallback)

    When both dicts contain the same normalised key, the first glyph wins
    (i.e. if a font has both "a.sc" and "a.smcp", "a.sc" takes priority as
    it is already the canonical form).
    """
    exact_map  = {}
    normal_map = {}
    for g in dst_font.glyphs:
        exact_map[g.name] = g
        key = normalise_name(g.name)
        if key not in normal_map:          # canonical form wins
            normal_map[key] = g
    return exact_map, normal_map


def resolve_dst_glyph(name, exact_map, normal_map):
    """
    Find the best matching target glyph for *name*.
    1. Try an exact name match first.
    2. Fall back to the normalised key so .sc ↔ .smcp are bridged.
    Returns (glyph, match_type) where match_type is "exact" or "normalised",
    or (None, None) if no match is found.
    """
    if name in exact_map:
        return exact_map[name], "exact"
    key = normalise_name(name)
    if key in normal_map:
        return normal_map[key], "normalised"
    return None, None


def master_id_for_name(font, master_name):
    """
    Return the masterID string for the master whose name matches master_name.
    Falls back to the first master's ID if none match.
    """
    for master in font.masters:
        if master.name == master_name:
            return master.id
    return font.masters[0].id if font.masters else None


def layer_for_master_id(glyph, master_id):
    """
    Return the layer whose associatedMasterId matches master_id.
    Falls back to layerId match, then layer[0].
    """
    for layer in glyph.layers:
        if layer.associatedMasterId == master_id:
            return layer
    for layer in glyph.layers:
        if layer.layerId == master_id:
            return layer
    return glyph.layers[0] if glyph.layers else None


def selected_glyph_names(font):
    """
    Return the names of glyphs currently selected in *font*.
    Tries three sources in order so RTL glyphs and edge cases are all caught:
      1. font.selection  (Font tab)
      2. currentTab.selectedLayers  (Edit tab, individually selected)
      3. currentTab.layers  (entire Edit tab contents, if nothing individually selected)
    """
    names = []
    seen  = set()

    def add(name):
        if name and name not in seen:
            seen.add(name)
            names.append(name)

    if font.selection:
        for g in font.selection:
            if hasattr(g, "name"):
                add(g.name)

    if not names and font.currentTab:
        for layer in font.currentTab.selectedLayers:
            if layer.parent:
                add(layer.parent.name)

    if not names and font.currentTab:
        for layer in font.currentTab.layers:
            if layer.parent:
                add(layer.parent.name)

    return names


def copy_shapes(src_layer, dst_layer):
    """
    Replace the background of dst_layer with a copy of the shapes in src_layer.
    Uses direct list assignment to clear, compatible with Glyphs 3 GSBackgroundLayer.
    """
    bg = dst_layer.background

    bg.paths      = []
    bg.components = []

    for path in src_layer.paths:
        bg.paths.append(path.copy())

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

        self._col_cb   = p
        self._col_src  = p + 24
        self._col_arr  = self._col_src + 160
        self._col_dst  = self._col_arr + 22

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
        rh = self.ROW_H

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

            cb_attr = "_row_cb_%d" % i
            setattr(self.w, cb_attr,
                CheckBox((self._col_cb, y + 1, 22, rh), "", value=True, sizeStyle="regular")
            )

            lbl_attr = "_row_lbl_%d" % i
            setattr(self.w, lbl_attr,
                TextBox((self._col_src, y, 155, rh), src_name, sizeStyle="regular")
            )

            arr_attr = "_row_arr_%d" % i
            setattr(self.w, arr_attr,
                TextBox((self._col_arr, y, 20, rh), "→", sizeStyle="regular")
            )

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
                "src_master_name": src_name,
                "cb_attr":         cb_attr,
                "popup_attr":      popup_attr,
                "dst_names":       dst_master_names,
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
                src_mn  = row["src_master_name"]
                dst_mn  = row["dst_names"][popup.get()]
                src_mid = master_id_for_name(src_font, src_mn)
                dst_mid = master_id_for_name(dst_font, dst_mn)
                master_pairs.append((src_mn, src_mid, dst_mn, dst_mid))

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

        print("Selected glyphs (%d): %s" % (len(glyph_names), ", ".join(glyph_names)))

        # ── Build target glyph lookup (exact + normalised) ────────────────────
        exact_map, normal_map = build_dst_map(dst_font)

        total_copied    = 0
        pair_reports    = []

        for src_mn, src_mid, dst_mn, dst_mid in master_pairs:
            copied       = []
            no_match     = []
            empty_source = []
            errors       = []
            sc_smcp_hits = []   # track .sc ↔ .smcp bridged matches for the report

            for name in glyph_names:
                src_glyph = src_font.glyphs[name]
                if src_glyph is None:
                    no_match.append(name)
                    continue

                src_layer = layer_for_master_id(src_glyph, src_mid)
                if src_layer is None:
                    no_match.append(name)
                    continue

                print("DEBUG: master=%s  glyph=%s  paths=%d  comps=%d  layerID=%s  masterID=%s" % (
                    src_mn, name,
                    len(src_layer.paths), len(src_layer.components),
                    src_layer.layerId, src_mid,
                ))

                if not src_layer.paths and not src_layer.components:
                    empty_source.append(name)
                    continue

                dst_glyph, match_type = resolve_dst_glyph(name, exact_map, normal_map)
                if dst_glyph is None:
                    no_match.append(name)
                    continue

                if match_type == "normalised":
                    sc_smcp_hits.append("%s → %s" % (name, dst_glyph.name))

                dst_layer = layer_for_master_id(dst_glyph, dst_mid)
                if dst_layer is None:
                    errors.append((name, "Could not find target layer."))
                    continue

                try:
                    copy_shapes(src_layer, dst_layer)
                    copied.append(name)
                except Exception:
                    errors.append((name, traceback.format_exc().strip().splitlines()[-1]))

            total_copied += len(copied)
            pair_reports.append((src_mn, dst_mn, copied, no_match, empty_source, errors, sc_smcp_hits))

        # ── Report ────────────────────────────────────────────────────────────
        lines = [
            "Source : %s" % font_label(src_font),
            "Target : %s" % font_label(dst_font),
            "",
            "✅  Total glyphs copied across all masters : %d" % total_copied,
        ]

        for src_mn, dst_mn, copied, no_match, empty_source, errors, sc_smcp_hits in pair_reports:
            lines += [
                "",
                "── %s  →  %s" % (src_mn, dst_mn),
                "   Copied : %d" % len(copied),
            ]
            if sc_smcp_hits:
                lines.append("   🔀  .sc/.smcp bridged (%d): %s" % (
                    len(sc_smcp_hits), ", ".join(sc_smcp_hits)
                ))
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
