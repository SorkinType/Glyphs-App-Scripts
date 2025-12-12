#MenuTitle: Add Missing Glyphs from Source Font
# -*- coding: utf-8 -*-
"""
Compare glyph set with another font and add missing glyphs to the current font.
Save this file in your Glyphs Scripts folder:
~/Library/Application Support/Glyphs 3/Scripts/

Usage:
1. Open your font
2. Run this script from Scripts menu
3. Choose a source font file
4. Missing glyphs will be added to your font
"""

import os
from AppKit import NSOpenPanel, NSFileHandlingPanelOKButton, NSAlert

try:
    from fontTools.ttLib import TTFont
    FONTTOOLS_AVAILABLE = True
except ImportError:
    FONTTOOLS_AVAILABLE = False
    print("Warning: fontTools not available. Install with: pip3 install fonttools")

try:
    import defcon
    DEFCON_AVAILABLE = True
except ImportError:
    DEFCON_AVAILABLE = False
    print("Warning: defcon not available. Install with: pip3 install defcon")


def get_glyph_list_from_glyphs_file(source_path):
    """Get list of glyph names from a Glyphs file."""
    source_font = GSFont(source_path)
    return [glyph.name for glyph in source_font.glyphs]


def get_glyph_list_from_ufo(source_path):
    """Get list of glyph names from a UFO."""
    if not DEFCON_AVAILABLE:
        raise ImportError("defcon is required for UFO files. Install with: pip3 install defcon")
    
    font = defcon.Font(source_path)
    return [glyph.name for glyph in font]


def get_glyph_list_from_binary(source_path):
    """Get list of glyph names from a compiled font (TTF/OTF)."""
    if not FONTTOOLS_AVAILABLE:
        raise ImportError("fontTools is required for TTF/OTF files. Install with: pip3 install fonttools")
    
    font = TTFont(source_path)
    return font.getGlyphOrder()


def get_glyph_data_from_glyphs_file(source_path, glyph_names):
    """Get glyph data (including unicode, category, subcategory) from Glyphs file."""
    source_font = GSFont(source_path)
    glyph_data = {}
    
    for glyph_name in glyph_names:
        source_glyph = source_font.glyphs[glyph_name]
        if source_glyph:
            glyph_data[glyph_name] = {
                'unicode': source_glyph.unicode,
                'category': source_glyph.category,
                'subCategory': source_glyph.subCategory,
                'script': source_glyph.script
            }
    
    return glyph_data


def get_glyph_data_from_ufo(source_path, glyph_names):
    """Get glyph data from UFO (limited info available)."""
    if not DEFCON_AVAILABLE:
        raise ImportError("defcon is required for UFO files")
    
    font = defcon.Font(source_path)
    glyph_data = {}
    
    for glyph_name in glyph_names:
        if glyph_name in font:
            source_glyph = font[glyph_name]
            # UFO has limited metadata
            unicode_val = None
            if source_glyph.unicodes:
                unicode_val = format(source_glyph.unicodes[0], '04X')
            
            glyph_data[glyph_name] = {
                'unicode': unicode_val,
                'category': None,
                'subCategory': None,
                'script': None
            }
    
    return glyph_data


def get_glyph_data_from_binary(source_path, glyph_names):
    """Get glyph data from binary font (very limited info)."""
    if not FONTTOOLS_AVAILABLE:
        raise ImportError("fontTools is required for TTF/OTF files")
    
    font = TTFont(source_path)
    glyph_data = {}
    
    # Get unicode mappings from cmap
    unicode_map = {}
    if 'cmap' in font:
        for table in font['cmap'].tables:
            if table.isUnicode():
                unicode_map.update(table.cmap)
    
    # Reverse the map to get unicode for each glyph
    glyph_to_unicode = {}
    for unicode_val, glyph_name in unicode_map.items():
        if glyph_name not in glyph_to_unicode:
            glyph_to_unicode[glyph_name] = format(unicode_val, '04X')
    
    for glyph_name in glyph_names:
        glyph_data[glyph_name] = {
            'unicode': glyph_to_unicode.get(glyph_name),
            'category': None,
            'subCategory': None,
            'script': None
        }
    
    return glyph_data


def get_glyphs_and_data(source_path):
    """Get glyph names and metadata from various font formats."""
    ext = os.path.splitext(source_path)[1].lower()
    
    if ext in ['.glyphs', '.glyphx']:
        glyph_names = get_glyph_list_from_glyphs_file(source_path)
        glyph_data = get_glyph_data_from_glyphs_file(source_path, glyph_names)
    elif ext == '.ufo' or os.path.isdir(source_path):
        glyph_names = get_glyph_list_from_ufo(source_path)
        glyph_data = get_glyph_data_from_ufo(source_path, glyph_names)
    elif ext in ['.ttf', '.otf']:
        glyph_names = get_glyph_list_from_binary(source_path)
        glyph_data = get_glyph_data_from_binary(source_path, glyph_names)
    else:
        raise ValueError(f"Unsupported format: {ext}")
    
    return glyph_names, glyph_data


def choose_source_file():
    """Show file picker and return selected path."""
    panel = NSOpenPanel.openPanel()
    panel.setCanChooseFiles_(True)
    panel.setCanChooseDirectories_(True)  # For UFO
    panel.setAllowedFileTypes_(["glyphs", "glyphx", "ufo", "ttf", "otf"])
    panel.setTitle_("Choose Source Font")
    panel.setPrompt_("Select")
    
    if panel.runModal() == NSFileHandlingPanelOKButton:
        return panel.URL().path()
    return None


def add_glyph_to_font(font, glyph_name, glyph_info):
    """Add a new glyph to the font with metadata."""
    new_glyph = GSGlyph(glyph_name)
    
    # Set unicode if available
    if glyph_info.get('unicode'):
        new_glyph.unicode = glyph_info['unicode']
    
    # Set category if available
    if glyph_info.get('category'):
        new_glyph.category = glyph_info['category']
    
    # Set subcategory if available
    if glyph_info.get('subCategory'):
        new_glyph.subCategory = glyph_info['subCategory']
    
    # Set script if available
    if glyph_info.get('script'):
        new_glyph.script = glyph_info['script']
    
    font.glyphs.append(new_glyph)
    
    return new_glyph


# Main execution
def main():
    # Check if a font is open
    font = Glyphs.font
    if not font:
        Message("No Font Open", "Please open a font first.")
        return
    
    print(f"\n=== Add Missing Glyphs from Source Font ===")
    
    # Get current glyph set with case-insensitive mapping
    current_glyphs = set([glyph.name for glyph in font.glyphs])
    # Create a lowercase to actual name mapping
    current_glyphs_lower_map = {name.lower(): name for name in current_glyphs}
    print(f"Current font has {len(current_glyphs)} glyphs")
    
    # Choose source file
    source_path = choose_source_file()
    
    if not source_path:
        print("Cancelled by user")
        return
    
    print(f"\nReading glyph list from: {os.path.basename(source_path)}")
    
    try:
        # Get source glyphs and their data
        source_glyphs, glyph_data = get_glyphs_and_data(source_path)
        source_glyph_set = set(source_glyphs)
        print(f"Source font has {len(source_glyph_set)} glyphs")
        
        # Find missing glyphs (case-insensitive check to avoid duplicates)
        missing_glyphs = []
        skipped_case_conflicts = []
        
        for glyph_name in source_glyphs:
            # Check if this glyph exists in any case variation
            if glyph_name.lower() in current_glyphs_lower_map:
                existing_name = current_glyphs_lower_map[glyph_name.lower()]
                if existing_name != glyph_name:
                    skipped_case_conflicts.append(f"{glyph_name} (exists as {existing_name})")
            else:
                missing_glyphs.append(glyph_name)
        
        if skipped_case_conflicts:
            print(f"\nSkipping {len(skipped_case_conflicts)} glyphs due to case conflicts:")
            for conflict in skipped_case_conflicts[:10]:
                print(f"  {conflict}")
            if len(skipped_case_conflicts) > 10:
                print(f"  ...and {len(skipped_case_conflicts) - 10} more")
        
        if not missing_glyphs:
            Message("No Missing Glyphs", "Your font already contains all glyphs from the source font.")
            print("\n✓ No missing glyphs - your font is complete!")
            return
        
        print(f"\nFound {len(missing_glyphs)} missing glyphs")
        
        # Sort for consistent ordering
        missing_glyphs_sorted = sorted(missing_glyphs)
        
        # Show preview
        preview_count = 20
        preview_list = missing_glyphs_sorted[:preview_count]
        remaining = len(missing_glyphs_sorted) - preview_count
        
        preview_text = ", ".join(preview_list)
        if remaining > 0:
            preview_text += f"\n...and {remaining} more"
        
        # Ask for confirmation
        response = Glyphs.showMacroWindow()
        
        message = f"Add {len(missing_glyphs)} missing glyphs?\n\n{preview_text}"
        result = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(
            "Add Missing Glyphs",
            "Add Glyphs",
            "Cancel",
            None,
            message
        ).runModal()
        
        if result != 1:  # 1 = default button (Add Glyphs)
            print("Cancelled by user")
            return
        
        # Add missing glyphs with error handling
        added_count = 0
        failed_glyphs = []
        
        for glyph_name in missing_glyphs_sorted:
            try:
                # Double-check the glyph doesn't exist before adding
                if font.glyphs[glyph_name] is not None:
                    print(f"  Skipping {glyph_name} - already exists")
                    continue
                
                info = glyph_data.get(glyph_name, {})
                add_glyph_to_font(font, glyph_name, info)
                added_count += 1
                
                # Print details
                details = []
                if info.get('unicode'):
                    details.append(f"U+{info['unicode']}")
                if info.get('category'):
                    details.append(info['category'])
                
                detail_str = f" ({', '.join(details)})" if details else ""
                print(f"  Added: {glyph_name}{detail_str}")
                
            except Exception as e:
                failed_glyphs.append((glyph_name, str(e)))
                print(f"  Failed to add {glyph_name}: {e}")
        
        if failed_glyphs:
            print(f"\nFailed to add {len(failed_glyphs)} glyphs:")
            for name, error in failed_glyphs[:5]:
                print(f"  {name}: {error}")
            if len(failed_glyphs) > 5:
                print(f"  ...and {len(failed_glyphs) - 5} more")
        
        # Show success message
        success_msg = f"✓ Successfully added {added_count} glyphs to your font"
        Message("Success", success_msg)
        print(f"\n{success_msg}")
        print(f"New total: {len(font.glyphs)} glyphs")
        
    except Exception as e:
        error_msg = str(e)
        Message("Error", f"Failed to add glyphs:\n{error_msg}")
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()


# Run the script
main()