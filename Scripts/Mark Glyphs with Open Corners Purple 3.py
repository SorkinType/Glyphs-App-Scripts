# MenuTitle: Mark Glyphs with Open Corners Purple 3
# -*- coding: utf-8 -*-

# Define the purple color index in Glyphs (Purple is index 6)
PURPLE_COLOR_INDEX = 6

# Get the current font and selected layers
thisFont = Glyphs.font
selectedLayers = thisFont.selectedLayers

if not selectedLayers:
    print("No glyphs selected. Please select at least one glyph.")
else:
    print("Checking selected glyphs for open corners...")
    
    marked_count = 0
    
    # Iterate through the selected glyphs via their active layers
    for layer in selectedLayers:
        parent_glyph = layer.parent
        has_open_corner = False
        
        # Check all layers of the glyph to find open corners
        for g_layer in parent_glyph.layers:
            for path in g_layer.paths:
                for node in path.nodes:
                    # Safely handle the Objective-C attributes dictionary
                    if hasattr(node, "attributes") and node.attributes:
                        # Check if keys() is available to prevent native selector errors
                        if hasattr(node.attributes, "keys") and "openCorner" in node.attributes.keys():
                            has_open_corner = True
                            break
                if has_open_corner:
                    break
            if has_open_corner:
                break
        
        # If an open corner was found, color the glyph purple
        if has_open_corner:
            parent_glyph.color = PURPLE_COLOR_INDEX
            print(f"Marked: {parent_glyph.name}")
            marked_count += 1

    print(f"\nDone! Marked {marked_count} glyph(s) in purple.")