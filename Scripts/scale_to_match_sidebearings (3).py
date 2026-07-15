#MenuTitle: Scale to Match Side Bearings 3

# encoding: utf-8
"""

─────────────────────────────────────────────────────────────────────────────
Horizontally scales selected glyphs in the SOURCE font so their outlines fit
within the existing advance width, matching the side-bearing proportions found
in a TARGET font.

For every matched master pair the script:
  • Keeps the advance width of the source glyph unchanged.
  • Derives a horizontal scale factor from the target glyph's side bearings.
  • Scales all contour nodes, components, and anchors in place.

Matching order: Unicode → glyph name fallback.
Supports multiple masters with an editable master-mapping UI.
"""

import objc
from Foundation import NSPoint, NSAffineTransform, NSAffineTransformStruct
from GlyphsApp import *
from GlyphsApp.UI import *
from vanilla import *


# ─────────────────────────────────────────────────────────────────────────────
# Helper utilities
# ─────────────────────────────────────────────────────────────────────────────

def get_glyph_by_unicode_or_name(font, ref_glyph):
    """Find a glyph in *font* matching *ref_glyph* by unicode first, then name."""
    if ref_glyph.unicode:
        for g in font.glyphs:
            if g.unicode == ref_glyph.unicode:
                return g
    if ref_glyph.name in font.glyphs:
        return font.glyphs[ref_glyph.name]
    return None


def scale_layer(layer, scale_x, center_x):
    """Horizontally scale all paths, components and anchors in *layer* around
    *center_x* by *scale_x*.  The advance width is never touched."""

    # ── Paths / nodes ─────────────────────────────────────────────────────
    for path in layer.paths:
        for node in path.nodes:
            x = center_x + (node.position.x - center_x) * scale_x
            node.position = NSPoint(x, node.position.y)

    # ── Components ────────────────────────────────────────────────────────
    for comp in layer.components:
        # comp.transform is an NSAffineTransform in Glyphs 3.
        # We read/write via its transformStruct (NSAffineTransformStruct).
        t = comp.transform.transformStruct   # named tuple: m11 m12 m21 m22 tX tY

        new_tX = center_x + (t.tX - center_x) * scale_x

        new_struct = NSAffineTransformStruct(
            t.m11 * scale_x,   # x-scale column
            t.m12,
            t.m21 * scale_x,   # x-shear column
            t.m22,
            new_tX,
            t.tY
        )
        new_transform = NSAffineTransform.transform()
        new_transform.setTransformStruct_(new_struct)
        comp.transform = new_transform

    # ── Anchors ───────────────────────────────────────────────────────────
    for anchor in layer.anchors:
        x = center_x + (anchor.position.x - center_x) * scale_x
        anchor.position = NSPoint(x, anchor.position.y)


def compute_scale_and_center(src_layer, tgt_layer):
    """Return (scale_x, center_x) so the source layer's side-bearing
    *proportions* match those of the target, keeping the advance width fixed.

    Returns (None, None) if the operation is not applicable.
    """
    src_adv = src_layer.width
    tgt_adv  = tgt_layer.width

    if src_adv <= 0 or tgt_adv <= 0:
        return None, None

    tgt_lsb     = tgt_layer.LSB
    tgt_rsb     = tgt_layer.RSB
    tgt_shape_w = tgt_adv - tgt_lsb - tgt_rsb

    if tgt_shape_w <= 0:
        return None, None

    # Bearing proportions from the target
    lsb_ratio = tgt_lsb / float(tgt_adv)
    rsb_ratio = tgt_rsb / float(tgt_adv)

    # Apply those proportions to the source advance width
    new_lsb     = lsb_ratio * src_adv
    new_shape_w = src_adv - new_lsb - rsb_ratio * src_adv

    src_lsb     = src_layer.LSB
    src_shape_w = src_adv - src_lsb - src_layer.RSB

    if src_shape_w == 0:
        return None, None

    scale_x = new_shape_w / float(src_shape_w)

    if abs(1.0 - scale_x) < 1e-9:
        return 1.0, src_adv / 2.0

    # Solve for the pivot so the left bbox edge lands on new_lsb:
    #   center_x + (src_lsb - center_x) * scale_x  =  new_lsb
    center_x = (new_lsb - src_lsb * scale_x) / (1.0 - scale_x)
    return scale_x, center_x


# ─────────────────────────────────────────────────────────────────────────────
# Master-matching helper
# ─────────────────────────────────────────────────────────────────────────────

def auto_match_masters(src_font, tgt_font):
    """Return [(src_master_index, tgt_master_index), …] using name heuristics."""
    pairs    = []
    used_tgt = set()

    def tokens(m):
        return set(m.name.lower().replace('-', ' ').replace('_', ' ').split())

    for si, sm in enumerate(src_font.masters):
        best_score, best_ti = -1, 0
        for ti, tm in enumerate(tgt_font.masters):
            if ti in used_tgt:
                continue
            score = len(tokens(sm) & tokens(tm))
            if score > best_score:
                best_score, best_ti = score, ti
        pairs.append([si, best_ti])
        used_tgt.add(best_ti)

    return pairs


# ─────────────────────────────────────────────────────────────────────────────
# Vanilla UI
# ─────────────────────────────────────────────────────────────────────────────

class ScaleSideBearingsUI(object):

    WINDOW_W = 600
    ROW_H    = 24
    PAD      = 16
    LABEL_W  = 160

    def __init__(self):
        fonts = Glyphs.fonts
        if len(fonts) < 2:
            Message(
                "Please open at least two fonts before running this script.",
                title="Scale to Match Side Bearings"
            )
            return

        self.fonts = list(fonts)
        self.src_idx = 0
        self.tgt_idx = 1
        self.master_pairs = auto_match_masters(self.fonts[0], self.fonts[1])
        self._master_rows = []   # list of (lbl_attr, arrow_attr, popup_attr)

        self._build_window()

    # ── Window construction ───────────────────────────────────────────────

    def _build_window(self):
        W = self.WINDOW_W
        P = self.PAD

        n_masters = max(len(f.masters) for f in self.fonts)
        body_h = (
            P + 26 + P           # title
            + 28 + 28 + P        # font selectors
            + 20 + P             # section label
            + n_masters * (self.ROW_H + 6) + P   # master rows
            + 24 + P             # warning
            + 32 + P             # buttons
        )

        self.w = Window(
            (W, body_h),
            "Scale to Match Side Bearings",
            minSize=(W, body_h),
            maxSize=(W, body_h),
        )
        w = self.w
        y = P

        # Title
        w.title = TextBox((P, y, -P, 22),
                          "Scale Selected Glyphs to Match Side Bearings",
                          sizeStyle="regular")
        y += 26 + P

        # Source font selector
        font_names = [f.familyName or "Untitled" for f in self.fonts]
        w.srcLabel = TextBox((P, y + 4, self.LABEL_W, 20),
                             "Font to change:", sizeStyle="small")
        w.srcPopup = PopUpButton((P + self.LABEL_W, y, -P, 22),
                                 font_names,
                                 callback=self._on_font_change,
                                 sizeStyle="small")
        w.srcPopup.set(self.src_idx)
        y += 28

        # Target font selector
        w.tgtLabel = TextBox((P, y + 4, self.LABEL_W, 20),
                             "Reference font:", sizeStyle="small")
        w.tgtPopup = PopUpButton((P + self.LABEL_W, y, -P, 22),
                                 font_names,
                                 callback=self._on_font_change,
                                 sizeStyle="small")
        w.tgtPopup.set(self.tgt_idx)
        y += 28 + P

        # Master-mapping section
        w.masterSectionLabel = TextBox(
            (P, y, -P, 18),
            "Master mapping  (source master  →  reference master):",
            sizeStyle="small"
        )
        y += 20 + P

        self._master_section_y = y
        self._render_master_rows(y)
        y = self._master_section_bottom + P

        # Warning
        w.warningLabel = TextBox(
            (P, y, -P, 20),
            "⚠  Advance widths are preserved — only outlines, components & anchors are scaled.",
            sizeStyle="mini"
        )
        y += 22 + P

        # Buttons
        btn_w = 120
        w.cancelBtn = Button((P, y, btn_w, 26), "Cancel",
                             callback=self._on_cancel)
        w.applyBtn  = Button((-P - btn_w, y, btn_w, 26), "Apply",
                             callback=self._on_apply)
        w.applyBtn._nsObject.setKeyEquivalent_("\r")

        w.open()

    # ── Master row rendering ──────────────────────────────────────────────

    def _render_master_rows(self, start_y):
        w   = self.w
        P   = self.PAD
        W   = self.WINDOW_W
        ROW = self.ROW_H

        # Tear down any existing rows
        for lbl_a, arr_a, pop_a in self._master_rows:
            for attr in (lbl_a, arr_a, pop_a):
                try:
                    delattr(w, attr)
                except Exception:
                    pass
        self._master_rows = []

        src_names = [m.name for m in self.fonts[self.src_idx].masters]
        tgt_names = [m.name for m in self.fonts[self.tgt_idx].masters]

        col_lbl   = P
        col_arrow = P + (W - 2 * P) // 2 - 20
        col_tgt   = col_arrow + 44
        y         = start_y

        for i, (si, ti) in enumerate(self.master_pairs):
            lbl_a = "_mrow_lbl_%d"   % i
            arr_a = "_mrow_arrow_%d" % i
            pop_a = "_mrow_popup_%d" % i

            setattr(w, lbl_a,
                    TextBox((col_lbl, y + 4, col_arrow - col_lbl - 8, ROW),
                            src_names[si] if si < len(src_names) else "—",
                            sizeStyle="small"))
            setattr(w, arr_a,
                    TextBox((col_arrow, y + 4, 40, ROW), "→", sizeStyle="small"))

            popup = PopUpButton((col_tgt, y, W - col_tgt - P, ROW),
                                tgt_names, sizeStyle="small")
            popup.set(ti if ti < len(tgt_names) else 0)
            setattr(w, pop_a, popup)

            self._master_rows.append((lbl_a, arr_a, pop_a))
            y += ROW + 6

        self._master_section_bottom = y

    # ── Callbacks ─────────────────────────────────────────────────────────

    def _on_font_change(self, sender):
        self.src_idx = self.w.srcPopup.get()
        self.tgt_idx = self.w.tgtPopup.get()
        if self.src_idx == self.tgt_idx:
            self.tgt_idx = (self.tgt_idx + 1) % len(self.fonts)
            self.w.tgtPopup.set(self.tgt_idx)
        self.master_pairs = auto_match_masters(
            self.fonts[self.src_idx], self.fonts[self.tgt_idx]
        )
        self._render_master_rows(self._master_section_y)

    def _on_cancel(self, sender):
        self.w.close()

    def _on_apply(self, sender):
        # Snapshot popup values BEFORE closing the window
        final_pairs = []
        for i, (si, _) in enumerate(self.master_pairs):
            pop_a  = "_mrow_popup_%d" % i
            popup  = getattr(self.w, pop_a, None)
            ti_val = popup.get() if popup is not None else self.master_pairs[i][1]
            final_pairs.append((si, ti_val))

        self.w.close()
        self._run(final_pairs)

    # ── Core logic ────────────────────────────────────────────────────────

    def _run(self, final_pairs):
        src_font   = self.fonts[self.src_idx]
        tgt_font   = self.fonts[self.tgt_idx]
        src_masters = src_font.masters
        tgt_masters = tgt_font.masters

        selected_glyphs = [g for g in src_font.glyphs if g.selected]
        if not selected_glyphs:
            Message("No glyphs are selected in the source font.",
                    title="Scale to Match Side Bearings")
            return

        changed   = 0
        skipped   = 0
        log_lines = []

        src_font.disableUpdateInterface()
        try:
            for src_glyph in selected_glyphs:
                tgt_glyph = get_glyph_by_unicode_or_name(tgt_font, src_glyph)
                if tgt_glyph is None:
                    skipped += 1
                    log_lines.append("  SKIP (no match): %s" % src_glyph.name)
                    continue

                glyph_changed = False
                for si, ti in final_pairs:
                    if si >= len(src_masters) or ti >= len(tgt_masters):
                        continue

                    src_layer = src_glyph.layers[src_masters[si].id]
                    tgt_layer = tgt_glyph.layers[tgt_masters[ti].id]

                    if src_layer is None or tgt_layer is None:
                        log_lines.append("  SKIP layer (%s / %s): layer not found"
                                         % (src_glyph.name, src_masters[si].name))
                        continue

                    scale_x, center_x = compute_scale_and_center(src_layer, tgt_layer)

                    if scale_x is None:
                        log_lines.append("  SKIP layer (%s / %s): cannot compute scale"
                                         % (src_glyph.name, src_masters[si].name))
                        continue

                    if abs(scale_x - 1.0) < 1e-6:
                        continue   # nothing to do

                    scale_layer(src_layer, scale_x, center_x)
                    log_lines.append("  OK  %-30s [%s]  scale_x=%.4f"
                                     % (src_glyph.name, src_masters[si].name, scale_x))
                    glyph_changed = True

                if glyph_changed:
                    changed += 1

        finally:
            src_font.enableUpdateInterface()

        summary = (
            "Done.\n\n"
            "Glyphs changed : %d\n"
            "Glyphs skipped : %d\n\n"
            "Log:\n%s"
        ) % (changed, skipped, "\n".join(log_lines) if log_lines else "  (none)")

        Message(summary, title="Scale to Match Side Bearings — Complete")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ScaleSideBearingsUI()
