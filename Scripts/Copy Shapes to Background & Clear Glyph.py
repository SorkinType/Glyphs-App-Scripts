#MenuTitle: Copy Shapes to Background, Then Clear
# -*- coding: utf-8 -*-
"""
Copies all paths and components from each layer's foreground into its
background layer, then removes them from the foreground — preserving
the advance width and stripping any linked sidebearings.

Works on:
  • All glyphs in the font (when nothing is selected, or via Script menu)
  • Only selected glyphs (when run from the Edit view with a selection)

Compatible with Glyphs 2 and Glyphs 3.
"""

from __future__ import print_function
import copy

__doc__ = __file__


def run():
    font = Glyphs.font
    if font is None:
        Message("No font open.", "Copy to Background")
        return

    # Decide which glyphs to process
    # In Glyphs 3 the selectedLayers attribute lives on the font's
    # currentTab; in G2 it's on the font directly. Fall back gracefully.
    selected_layers = []
    try:
        tab = font.currentTab
        if tab and tab.selectedLayers:
            selected_layers = list(tab.selectedLayers)
    except Exception:
        pass

    if not selected_layers:
        # Fall back: process every glyph in the font
        glyphs_to_process = font.glyphs
    else:
        # Collect the unique glyphs touched by the selection
        seen = set()
        glyphs_to_process = []
        for layer in selected_layers:
            if layer.parent not in seen:
                seen.add(layer.parent)
                glyphs_to_process.append(layer.parent)

    processed = 0
    font.disableUpdateInterface()
    try:
        for glyph in glyphs_to_process:
            for layer in glyph.layers:
                # Skip non-master layers that are purely backup/brace/bracket
                # layers — only process layers that have a master counterpart
                # or are themselves master layers.
                if not layer.isMasterLayer and not layer.isSpecialLayer:
                    continue

                # ── 1. Remember the current advance width ─────────────────
                advance_width = layer.width

                # ── 2. Get (or create) the background layer ───────────────
                background = layer.background  # always available in G2 & G3

                # ── 3. Clear whatever was already in the background ───────
                background.clear()  # removes paths + components

                # ── 4. Copy paths from foreground → background ────────────
                for path in layer.paths:
                    background.paths.append(copy.deepcopy(path))

                # ── 5. Copy components from foreground → background ───────
                for component in layer.components:
                    background.components.append(copy.deepcopy(component))

                # ── 6. Strip linked sidebearings from the foreground ──────
                #       LSB link
                if hasattr(layer, "leftMetricsKey") and layer.leftMetricsKey:
                    layer.leftMetricsKey = None
                #       RSB link
                if hasattr(layer, "rightMetricsKey") and layer.rightMetricsKey:
                    layer.rightMetricsKey = None
                #       Width link (Glyphs 3)
                if hasattr(layer, "widthMetricsKey") and layer.widthMetricsKey:
                    layer.widthMetricsKey = None

                # Also clear glyph-level metrics keys so they don't re-link
                if hasattr(glyph, "leftMetricsKey") and glyph.leftMetricsKey:
                    glyph.leftMetricsKey = None
                if hasattr(glyph, "rightMetricsKey") and glyph.rightMetricsKey:
                    glyph.rightMetricsKey = None
                if hasattr(glyph, "widthMetricsKey") and glyph.widthMetricsKey:
                    glyph.widthMetricsKey = None

                # ── 7. Clear paths and components from the foreground ─────
                layer.clear()  # removes paths + components

                # ── 8. Restore advance width ──────────────────────────────
                layer.width = advance_width

                processed += 1

    finally:
        font.enableUpdateInterface()

    print(
        "Done. Processed %d layer(s) across %d glyph(s)."
        % (processed, len(list(glyphs_to_process)))
    )
    Message(
        "Processed %d layer(s) in %d glyph(s).\n\n"
        "Shapes are now in the background; foreground is empty.\n"
        "Advance widths and sidebearing links have been preserved/removed."
        % (processed, len(list(glyphs_to_process))),
        "Copy to Background — Done",
    )


run()