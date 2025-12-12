#MenuTitle: Color Glyphs by Content Type
# -*- coding: utf-8 -*-
"""
Mark glyphs with colors based on their content:
- Green: Contains vector paths only
- Yellow: Contains both paths and components
- No color: Contains only components (or is empty)
Save this file in your Glyphs Scripts folder:
~/Library/Application Support/Glyphs 3/Scripts/
Usage:
1. Open a font file
2. Run this script from Scripts menu
3. All glyphs will be automatically colored based on their content
"""

def analyze_glyph_content(glyph):
    """
    Analyze a glyph's content across all layers.
    Returns: 'paths_only', 'both', 'components_only', or 'empty'
    """
    has_paths = False
    has_components = False
    
    # Check all layers in the glyph
    for layer in glyph.layers:
        if len(layer.paths) > 0:
            has_paths = True
        if len(layer.components) > 0:
            has_components = True
        
        # Early exit if we've found both
        if has_paths and has_components:
            return 'both'
    
    if has_paths and not has_components:
        return 'paths_only'
    elif has_components and not has_paths:
        return 'components_only'
    elif not has_paths and not has_components:
        return 'empty'
    else:
        return 'both'

def color_glyphs():
    """Main function to color glyphs based on their content."""
    
    font = Glyphs.font
    
    if not font:
        Message("No Font Open", "Please open a font first.")
        return
    
    print("\n" + "="*60)
    print("COLOR GLYPHS BY CONTENT TYPE")
    print("="*60)
    
    # Define color indices (0-11 are the predefined Glyphs colors)
    GREEN = 5      # Dark green for paths only
    YELLOW = 3     # Yellow for both paths and components
    
    # Counters
    paths_only_count = 0
    both_count = 0
    components_only_count = 0
    empty_count = 0
    
    # Process all glyphs
    for glyph in font.glyphs:
        content_type = analyze_glyph_content(glyph)
        
        if content_type == 'paths_only':
            glyph.color = GREEN
            paths_only_count += 1
            print(f"  {glyph.name}: GREEN (paths only)")
        
        elif content_type == 'both':
            glyph.color = YELLOW
            both_count += 1
            print(f"  {glyph.name}: YELLOW (paths + components)")
        
        elif content_type == 'components_only':
            # Remove color (set to None)
            glyph.color = None
            components_only_count += 1
            print(f"  {glyph.name}: No color (components only)")
        
        elif content_type == 'empty':
            # Remove color
            glyph.color = None
            empty_count += 1
            print(f"  {glyph.name}: No color (empty)")
    
    # Show summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"GREEN (paths only):           {paths_only_count}")
    print(f"YELLOW (paths + components):  {both_count}")
    print(f"No color (components only):   {components_only_count}")
    print(f"No color (empty):             {empty_count}")
    print(f"{'='*60}")
    print(f"Total glyphs processed:       {len(font.glyphs)}")
    print(f"{'='*60}\n")
    
    # Show success message
    Message("Coloring Complete", 
            f"Glyphs colored:\n\n"
            f"● {paths_only_count} green (paths only)\n"
            f"● {both_count} yellow (paths + components)\n"
            f"● {components_only_count + empty_count} unmarked (components only or empty)")

# Run the script
color_glyphs()