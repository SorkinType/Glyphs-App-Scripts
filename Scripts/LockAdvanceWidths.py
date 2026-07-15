#MenuTitle: Lock Advance Widths (Add = Prefix)
# -*- coding: utf-8 -*-
__doc__ = """
Locks the advance width of all selected glyphs by prefixing their
width metric key with '=' so the value stays constant even when
outlines or components change.

If a glyph has no width key set, it reads the current layer width
and writes it as =<value>. If a key already exists and doesn't
start with '=', it prepends '='.
"""

from GlyphsApp import Glyphs, Message

font = Glyphs.font

if font is None:
    Message("No font open.", "Lock Advance Widths")
else:
    selectedGlyphs = [layer.parent for layer in font.selectedLayers]

    if not selectedGlyphs:
        Message("No glyphs selected.", "Lock Advance Widths")
    else:
        modified = []
        skipped = []

        for glyph in selectedGlyphs:
            # Work on every master layer of the glyph
            for layer in glyph.layers:
                # Only process master layers (not backup / special layers)
                if layer.associatedMasterId != layer.layerId and not layer.isMasterLayer:
                    continue

                currentKey = layer.widthMetricsKey  # may be None

                if currentKey is not None:
                    key = currentKey.strip()
                    if key.startswith("="):
                        # Already locked — leave it alone
                        skipped.append(f"{glyph.name} [{layer.name}]: already locked ({key})")
                    else:
                        # Prepend = to the existing key expression
                        layer.widthMetricsKey = "=" + key
                        modified.append(f"{glyph.name} [{layer.name}]: '{key}' → '={key}'")
                else:
                    # No key set — read the current advance width and lock it
                    width = int(round(layer.width))
                    layer.widthMetricsKey = "=" + str(width)
                    modified.append(f"{glyph.name} [{layer.name}]: (none) → '={width}'")

        # Build a summary report
        lines = []
        if modified:
            lines.append(f"✅ Locked {len(modified)} layer(s):")
            lines.extend(f"   {m}" for m in modified)
        if skipped:
            lines.append(f"\n⚠️  Skipped {len(skipped)} already-locked layer(s):")
            lines.extend(f"   {s}" for s in skipped)
        if not modified and not skipped:
            lines.append("Nothing to do — no master layers found on selected glyphs.")

        print("\n".join(lines))
        Message("\n".join(lines), "Lock Advance Widths")
