#MenuTitle: Remove Brace Layers 4
# encoding: utf-8
"""
Removes brace layers ({ }) and orphaned / empty layers from a font source.

Three categories are targeted:

  1. BRACE LAYERS   – name starts with "{" and ends with "}", e.g. {100}
  2. EMPTY-NAME     – layer name is None or an empty string
  3. ORPHANED       – layer is not a master layer (no matching master ID)
                      and is not a brace layer with content — i.e. the
                      "(empty)" entries visible in the Layers panel

Options
───────
• Operate on all glyphs or selected glyphs only.
• Preview how many layers will be removed before committing.
"""

import os
from GlyphsApp import *
from vanilla import Window, TextBox, PopUpButton, Button, HorizontalLine


# ─────────────────────────────────────────────────────────────────────────────
# Core logic
# ─────────────────────────────────────────────────────────────────────────────

def master_ids(font):
    """Return a set of all master IDs in *font*."""
    return {m.id for m in font.masters}


def is_brace_layer(layer):
    """True for named intermediate layers: {100}, {100, 200}, etc."""
    name = layer.name or ""
    return name.startswith("{") and name.endswith("}")


def is_removable(layer, master_id_set):
    """True if this layer should be deleted.

    Removes:
      • Named brace / intermediate layers  ({…})
      • Layers with no name or an empty name
      • Layers whose associatedMasterId does not match any current master
        (orphaned backup / intermediate shells that show as "(empty)")
    Keeps:
      • Layers whose layerId matches a master ID  (the real master layers)
    """
    # Always keep real master layers
    if layer.layerId in master_id_set:
        return False

    # Named brace layers
    if is_brace_layer(layer):
        return True

    # Empty or missing name  →  orphaned shell
    name = layer.name or ""
    if name.strip() == "":
        return True

    # Layer whose associated master no longer exists
    assoc = getattr(layer, "associatedMasterId", None)
    if assoc and assoc not in master_id_set:
        return True

    return False


def collect_removable_layers(font, selected_only):
    """Return list of (glyph_name, display_label) for every removable layer."""
    mids  = master_ids(font)
    found = []
    for glyph in font.glyphs:
        if selected_only and not glyph.selected:
            continue
        for layer in glyph.layers:
            if is_removable(layer, mids):
                label = layer.name if (layer.name or "").strip() else "(empty)"
                found.append((glyph.name, label))
    return found


def remove_target_layers(font, selected_only):
    """Delete all removable layers from *font*.

    Returns list of (glyph_name, label) for every layer removed.
    """
    mids    = master_ids(font)
    removed = []

    font.disableUpdateInterface()
    try:
        for glyph in font.glyphs:
            if selected_only and not glyph.selected:
                continue

            # Snapshot IDs first — never mutate while iterating
            to_delete = [
                layer.layerId
                for layer in glyph.layers
                if is_removable(layer, mids)
            ]
            for lid in to_delete:
                layer = glyph.layers[lid]
                label = layer.name if (layer.name or "").strip() else "(empty)"
                removed.append((glyph.name, label))
                del glyph.layers[lid]

    finally:
        font.enableUpdateInterface()

    return removed


# ─────────────────────────────────────────────────────────────────────────────
# Vanilla UI
# ─────────────────────────────────────────────────────────────────────────────

class RemoveBraceLayersUI(object):

    W  = 520
    P  = 16
    LW = 150

    def __init__(self):
        fonts = Glyphs.fonts
        if not fonts:
            Message(
                "Please open a font before running this script.",
                title="Remove Brace Layers"
            )
            return

        self.fonts = list(fonts)
        self._build_window()

    # ── helpers ───────────────────────────────────────────────────────────

    def _font_label(self, font):
        name = font.familyName or "Untitled"
        try:
            if font.filepath:
                name += "  (%s)" % os.path.basename(str(font.filepath))
        except Exception:
            pass
        return name

    def _update_preview(self, sender=None):
        """Refresh the layer count shown in the UI."""
        font          = self.fonts[self.w.fontPopup.get()]
        selected_only = self.w.scopePopup.get() == 1
        found         = collect_removable_layers(font, selected_only)

        scope = "selected glyphs" if selected_only else "all glyphs"
        if found:
            self.w.previewLabel.set(
                "Found %d layer%s to remove across %d glyph%s (%s)." % (
                    len(found),
                    "s" if len(found) != 1 else "",
                    len(set(g for g, _ in found)),
                    "s" if len(set(g for g, _ in found)) != 1 else "",
                    scope,
                )
            )
        else:
            self.w.previewLabel.set(
                "No removable layers found in %s." % scope
            )

    # ── window ────────────────────────────────────────────────────────────

    def _build_window(self):
        W, P, LW = self.W, self.P, self.LW
        font_labels = [self._font_label(f) for f in self.fonts]

        body_h = (
            P + 22 + 6          # heading
            + 14 + P            # sub note
            + 1  + P            # divider
            + 22 + 4            # font selector row
            + 14 + P            # note under selector
            + 1  + P            # divider
            + 22 + 8            # scope selector row
            + 18 + P            # preview label
            + 1  + P            # divider
            + 28 + P            # buttons
        )

        self.w = Window(
            (W, body_h),
            "Remove Brace Layers",
            minSize=(W, body_h),
            maxSize=(W + 200, body_h),
        )
        w = self.w
        y = P

        # ── Heading ───────────────────────────────────────────────────────
        w.heading = TextBox(
            (P, y, -P, 20),
            "Remove Brace Layers & Orphaned Empty Layers",
            sizeStyle="regular"
        )
        y += 22 + 6

        w.subNote = TextBox(
            (P, y, -P, 14),
            "Removes brace layers {…}, unnamed layers, and orphaned empty layers (shown as \"(empty)\" in the Layers panel).",
            sizeStyle="mini"
        )
        y += 14 + P

        w.div1 = HorizontalLine((P, y, -P, 1))
        y += 1 + P

        # ── Font selector ─────────────────────────────────────────────────
        w.fontLabel = TextBox(
            (P, y + 3, LW, 18),
            "Font to modify:",
            sizeStyle="small"
        )
        w.fontPopup = PopUpButton(
            (P + LW, y, -P, 22),
            font_labels,
            sizeStyle="small",
            callback=self._update_preview
        )
        w.fontPopup.set(0)
        y += 22 + 4

        w.fontNote = TextBox(
            (P + LW, y, -P, 14),
            "Brace layers and empty/orphaned layers will be permanently removed from this font.",
            sizeStyle="mini"
        )
        y += 14 + P

        w.div2 = HorizontalLine((P, y, -P, 1))
        y += 1 + P

        # ── Scope selector ────────────────────────────────────────────────
        w.scopeLabel = TextBox(
            (P, y + 3, LW, 18),
            "Remove from:",
            sizeStyle="small"
        )
        w.scopePopup = PopUpButton(
            (P + LW, y, -P, 22),
            [
                "Whole font  (every glyph)",
                "Selected glyphs only",
            ],
            sizeStyle="small",
            callback=self._update_preview
        )
        w.scopePopup.set(0)
        y += 22 + 8

        w.previewLabel = TextBox(
            (P, y, -P, 18),
            "—",
            sizeStyle="small"
        )
        y += 18 + P

        w.div3 = HorizontalLine((P, y, -P, 1))
        y += 1 + P

        # ── Buttons ───────────────────────────────────────────────────────
        btn_w = 120
        w.cancelBtn = Button(
            (P, y, btn_w, 26), "Cancel",
            callback=self._on_cancel
        )
        w.removeBtn = Button(
            (-P - btn_w, y, btn_w, 26), "Remove",
            callback=self._on_remove
        )
        w.removeBtn._nsObject.setKeyEquivalent_("\r")

        # Populate the preview count straight away
        self._update_preview()

        w.open()

    # ── Callbacks ─────────────────────────────────────────────────────────

    def _on_cancel(self, sender):
        self.w.close()

    def _on_remove(self, sender):
        font_idx      = self.w.fontPopup.get()
        selected_only = self.w.scopePopup.get() == 1   # 0=whole font, 1=selection
        font          = self.fonts[font_idx]
        font_name     = self._font_label(font)

        # Quick pre-check
        preview = collect_removable_layers(font, selected_only)
        if not preview:
            scope = "selected glyphs" if selected_only else "all glyphs"
            Message(
                "No removable layers found in %s of \"%s\"." % (scope, font_name),
                title="Remove Brace Layers"
            )
            return

        self.w.close()

        removed = remove_target_layers(font, selected_only)

        # ── Result report ─────────────────────────────────────────────────
        MAX_LINES = 60
        log_lines = [
            "  %-30s  %s" % (gname, lname)
            for gname, lname in removed[:MAX_LINES]
        ]
        if len(removed) > MAX_LINES:
            log_lines.append("  … and %d more." % (len(removed) - MAX_LINES))

        summary = (
            "Font    :  %s\n\n"
            "Layers removed   : %d\n"
            "Glyphs affected  : %d\n\n"
            "Removed layers:\n%s"
        ) % (
            font_name,
            len(removed),
            len(set(g for g, _ in removed)),
            "\n".join(log_lines) if log_lines else "  (none)",
        )

        Message(summary, title="Remove Brace & Empty Layers — Done")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    RemoveBraceLayersUI()
