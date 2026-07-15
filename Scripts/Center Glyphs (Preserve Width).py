#MenuTitle: Center Glyphs (Preserve Width)
# -*- coding: utf-8 -*-
"""
Centers the paths/components of selected glyphs within their existing advance
width, without changing the advance width or the glyph width.
 
Works on the currently active master of each selected glyph.
"""
 
from __future__ import division, print_function
import GlyphsApp
 
font = Glyphs.font
if not font:
    Message("No font open.", "Center Glyphs")
else:
    # Collect layers to process: either selected layers in Edit view,
    # or all masters of glyphs selected in Font view.
    layers = font.selectedLayers
 
    if not layers:
        Message("No glyphs selected.", "Center Glyphs")
    else:
        font.disableUpdateInterface()
        try:
            for layer in layers:
                # Bounding box of all paths + components combined.
                bounds = layer.completeBoundingBox()
 
                # Skip empty layers (no outlines, no components).
                if bounds is None:
                    continue
 
                content_width  = bounds.size.width
                content_origin = bounds.origin.x   # left edge of content
                advance_width  = layer.width        # RSB + LSB + content
 
                if advance_width <= 0:
                    continue
 
                # X position the content must move to so it sits centred
                # inside the advance width.
                target_origin = (advance_width - content_width) / 2.0
 
                # How far every node / anchor / component must shift.
                delta_x = target_origin - content_origin
 
                if abs(delta_x) < 0.01:   # already centred – nothing to do
                    continue
 
                # --- Move paths ---
                for path in layer.paths:
                    for node in path.nodes:
                        node.x += delta_x
 
                # --- Move components ---
                for component in layer.components:
                    pos = component.position
                    component.position = NSPoint(pos.x + delta_x, pos.y)
 
                # --- Move anchors ---
                for anchor in layer.anchors:
                    pos = anchor.position
                    anchor.position = NSPoint(pos.x + delta_x, pos.y)
 
                # Advance width is intentionally NOT changed.
 
        finally:
            font.enableUpdateInterface()
 
        print("Done: centered %d layer(s)." % len(layers))