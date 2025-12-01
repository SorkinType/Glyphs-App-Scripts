#MenuTitle: Copy Widths from Source Font
# -*- coding: utf-8 -*-
"""
Copy glyph widths from a source font to selected glyphs in the current font.
Save this file in your Glyphs Scripts folder:
~/Library/Application Support/Glyphs 3/Scripts/

Usage:
1. Select glyphs in your current font
2. Run this script from Scripts menu
3. Choose a source font file
4. Widths will be copied to selected glyphs
"""

import os
import sys
from AppKit import NSOpenPanel, NSFileHandlingPanelOKButton

# Check Python libraries
try:
    from fontTools.ttLib import TTFont
    FONTTOOLS_AVAILABLE = True
except ImportError:
    FONTTOOLS_AVAILABLE = False

try:
    import defcon
    DEFCON_AVAILABLE = True
except ImportError:
    DEFCON_AVAILABLE = False


def read_widths_from_glyphs_file(source_path):
    """Read glyph widths from another Glyphs file."""
    try:
        source_font = GSFont(source_path)
        widths = {}
        unicode_to_width = {}
        
        # Use the first master
        if not source_font.masters:
            raise ValueError("Source font has no masters")
        
        master = source_font.masters[0]
        
        for glyph in source_font.glyphs:
            try:
                layer = glyph.layers[master.id]
                if layer:
                    widths[glyph.name] = layer.width
                    # Also store by unicode for cross-referencing
                    if glyph.unicode:
                        unicode_to_width[glyph.unicode] = layer.width
            except:
                continue
        
        return widths, unicode_to_width
    except Exception as e:
        raise ValueError(f"Failed to read Glyphs file: {e}")


def read_widths_from_ufo(source_path):
    """Read glyph widths from a UFO source."""
    if not DEFCON_AVAILABLE:
        raise ImportError("defcon library is required for UFO files.\nInstall with: pip3 install defcon")
    
    try:
        font = defcon.Font(source_path)
        widths = {}
        unicode_to_width = {}
        
        for glyph in font:
            widths[glyph.name] = glyph.width
            # Store by unicode if available
            if glyph.unicodes:
                unicode_val = format(glyph.unicodes[0], '04X')
                unicode_to_width[unicode_val] = glyph.width
        
        return widths, unicode_to_width
    except Exception as e:
        raise ValueError(f"Failed to read UFO: {e}")


def read_widths_from_binary(source_path):
    """Read glyph widths from a compiled font (TTF/OTF)."""
    if not FONTTOOLS_AVAILABLE:
        raise ImportError("fontTools library is required for TTF/OTF files.\nInstall with: pip3 install fonttools")
    
    try:
        font = TTFont(source_path)
        widths = {}
        unicode_to_width = {}
        
        if 'hmtx' not in font:
            raise ValueError("Font has no horizontal metrics table")
        
        hmtx = font['hmtx']
        
        # Get unicode mappings from cmap
        unicode_map = {}
        if 'cmap' in font:
            for table in font['cmap'].tables:
                if table.isUnicode():
                    unicode_map.update(table.cmap)
        
        for glyph_name in font.getGlyphOrder():
            try:
                width, lsb = hmtx[glyph_name]
                widths[glyph_name] = width
            except:
                continue
        
        # Build unicode to width mapping
        for unicode_val, glyph_name in unicode_map.items():
            if glyph_name in widths:
                unicode_to_width[format(unicode_val, '04X')] = widths[glyph_name]
        
        return widths, unicode_to_width
    except Exception as e:
        raise ValueError(f"Failed to read binary font: {e}")


def read_widths(source_path):
    """Read glyph widths from various font formats."""
    if not os.path.exists(source_path):
        raise ValueError(f"File not found: {source_path}")
    
    ext = os.path.splitext(source_path)[1].lower()
    
    if ext in ['.glyphs', '.glyphx']:
        return read_widths_from_glyphs_file(source_path)
    elif ext == '.ufo' or os.path.isdir(source_path):
        return read_widths_from_ufo(source_path)
    elif ext in ['.ttf', '.otf']:
        return read_widths_from_binary(source_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}\nSupported: .glyphs, .glyphx, .ufo, .ttf, .otf")


def choose_source_file():
    """Show file picker and return selected path."""
    try:
        panel = NSOpenPanel.openPanel()
        panel.setCanChooseFiles_(True)
        panel.setCanChooseDirectories_(True)  # For UFO
        panel.setAllowedFileTypes_(["glyphs", "glyphx", "ufo", "ttf", "otf"])
        panel.setTitle_("Choose Source Font")
        panel.setPrompt_("Select")
        
        if panel.runModal() == NSFileHandlingPanelOKButton:
            url = panel.URL()
            if url:
                return url.path()
        return None
    except Exception as e:
        print(f"Error showing file picker: {e}")
        return None


# Main execution
def main():
    print("\n" + "="*50)
    print("Copy Widths from Source Font")
    print("="*50)
    
    # Check if a font is open
    font = Glyphs.font
    if not font:
        Message("No Font Open", "Please open a font first.")
        print("ERROR: No font is open")
        return
    
    print(f"Current font: {font.familyName}")
    
    # Check if glyphs are selected
    selected_layers = font.selectedLayers
    if not selected_layers:
        Message("No Selection", "Please select glyphs first.")
        print("ERROR: No glyphs selected")
        return
    
    # Get unique glyph names from selection
    selected_glyph_names = []
    for layer in selected_layers:
        if layer.parent and layer.parent.name:
            selected_glyph_names.append(layer.parent.name)
    
    selected_glyph_names = list(set(selected_glyph_names))
    
    if not selected_glyph_names:
        Message("No Valid Selection", "Please select valid glyphs.")
        print("ERROR: No valid glyphs in selection")
        return
    
    print(f"\nSelected {len(selected_glyph_names)} glyphs:")
    print(f"  {', '.join(sorted(selected_glyph_names)[:10])}")
    if len(selected_glyph_names) > 10:
        print(f"  ...and {len(selected_glyph_names) - 10} more")
    
    # Choose source file
    print("\nOpening file picker...")
    source_path = choose_source_file()
    
    if not source_path:
        print("Cancelled by user")
        return
    
    print(f"\nSource file: {os.path.basename(source_path)}")
    print(f"Full path: {source_path}")
    
    try:
        # Read source widths
        print("\nReading widths from source...")
        source_widths, unicode_to_width = read_widths(source_path)
        print(f"✓ Found {len(source_widths)} glyphs in source")
        print(f"✓ Found {len(unicode_to_width)} glyphs with unicode values")
        
        # Filter to only selected glyphs that exist in source
        # Try to match by name first, then by unicode
        widths_to_copy = {}
        match_info = {}
        
        for name in selected_glyph_names:
            matched = False
            
            # Try direct name match first
            if name in source_widths:
                widths_to_copy[name] = source_widths[name]
                match_info[name] = "name"
                matched = True
            else:
                # Try to match by unicode
                target_glyph = font.glyphs[name]
                if target_glyph and target_glyph.unicode:
                    if target_glyph.unicode in unicode_to_width:
                        widths_to_copy[name] = unicode_to_width[target_glyph.unicode]
                        match_info[name] = f"unicode U+{target_glyph.unicode}"
                        matched = True
            
            if not matched:
                target_glyph = font.glyphs[name]
                unicode_info = f" (U+{target_glyph.unicode})" if target_glyph and target_glyph.unicode else ""
                print(f"  ✗ No match for: {name}{unicode_info}")
        
        if not widths_to_copy:
            msg = "None of the selected glyphs were found in the source font."
            Message("No Matches", msg)
            print(f"\nERROR: {msg}")
            print(f"\nSelected glyphs (first 5):")
            for name in sorted(selected_glyph_names)[:5]:
                target_glyph = font.glyphs[name]
                unicode_info = f" U+{target_glyph.unicode}" if target_glyph and target_glyph.unicode else " (no unicode)"
                print(f"  {name}{unicode_info}")
            print(f"\nSource has (first 5): {', '.join(sorted(list(source_widths.keys())[:5]))}")
            return
        
        print(f"\n✓ Matched {len(widths_to_copy)} glyphs:")
        match_by_name = sum(1 for v in match_info.values() if v == "name")
        match_by_unicode = len(match_info) - match_by_name
        print(f"  {match_by_name} by name, {match_by_unicode} by unicode")
        
        # Apply widths to all masters
        print(f"\nApplying widths to {len(font.masters)} master(s)...")
        updated_count = 0
        changes_made = []
        
        for master in font.masters:
            for glyph_name, width in widths_to_copy.items():
                glyph = font.glyphs[glyph_name]
                if glyph:
                    layer = glyph.layers[master.id]
                    if layer:
                        old_width = layer.width
                        layer.width = width
                        updated_count += 1
                        
                        if old_width != width:
                            changes_made.append(f"{glyph_name}: {old_width} → {width}")
        
        # Report results
        missing = set(selected_glyph_names) - set(widths_to_copy.keys())
        
        print("\nChanges made:")
        for change in changes_made[:20]:
            print(f"  {change}")
        if len(changes_made) > 20:
            print(f"  ...and {len(changes_made) - 20} more changes")
        
        success_msg = f"✓ Updated widths for {len(widths_to_copy)} glyphs across {len(font.masters)} master(s)"
        if missing:
            success_msg += f"\n\n{len(missing)} glyphs not found in source:\n{', '.join(sorted(missing)[:10])}"
            if len(missing) > 10:
                success_msg += f"\n...and {len(missing) - 10} more"
        
        Message("Success", success_msg)
        print(f"\n✓ Successfully updated {len(widths_to_copy)} glyphs")
        if missing:
            print(f"\nNot found in source ({len(missing)}):")
            for name in sorted(missing)[:10]:
                print(f"  {name}")
            if len(missing) > 10:
                print(f"  ...and {len(missing) - 10} more")
        
    except Exception as e:
        error_msg = str(e)
        Message("Error", f"Failed to copy widths:\n\n{error_msg}")
        print(f"\nERROR: {error_msg}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()


# Run the script
if __name__ == "__main__":
    main()
else:
    main()