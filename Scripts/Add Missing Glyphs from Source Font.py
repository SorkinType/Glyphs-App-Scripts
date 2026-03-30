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
 
A glyph is considered "already present" if the current font contains either:
  - a glyph with the same name (case-insensitive), OR
  - a glyph that already carries the same Unicode value.
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
 
 
# ---------------------------------------------------------------------------
# Source font readers
# ---------------------------------------------------------------------------
 
def get_glyph_list_from_glyphs_file(source_path):
    source_font = GSFont(source_path)
    return [glyph.name for glyph in source_font.glyphs]
 
 
def get_glyph_list_from_ufo(source_path):
    if not DEFCON_AVAILABLE:
        raise ImportError("defcon is required for UFO files. Install with: pip3 install defcon")
    font = defcon.Font(source_path)
    return [glyph.name for glyph in font]
 
 
def get_glyph_list_from_binary(source_path):
    if not FONTTOOLS_AVAILABLE:
        raise ImportError("fontTools is required for TTF/OTF files. Install with: pip3 install fonttools")
    font = TTFont(source_path)
    return font.getGlyphOrder()
 
 
def get_glyph_data_from_glyphs_file(source_path, glyph_names):
    source_font = GSFont(source_path)
    glyph_data = {}
    for glyph_name in glyph_names:
        source_glyph = source_font.glyphs[glyph_name]
        if source_glyph:
            glyph_data[glyph_name] = {
                'unicode':     source_glyph.unicode,
                'category':    source_glyph.category,
                'subCategory': source_glyph.subCategory,
                'script':      source_glyph.script,
            }
    return glyph_data
 
 
def get_glyph_data_from_ufo(source_path, glyph_names):
    if not DEFCON_AVAILABLE:
        raise ImportError("defcon is required for UFO files")
    font = defcon.Font(source_path)
    glyph_data = {}
    for glyph_name in glyph_names:
        if glyph_name in font:
            source_glyph = font[glyph_name]
            unicode_val = None
            if source_glyph.unicodes:
                unicode_val = format(source_glyph.unicodes[0], '04X')
            glyph_data[glyph_name] = {
                'unicode':     unicode_val,
                'category':    None,
                'subCategory': None,
                'script':      None,
            }
    return glyph_data
 
 
def get_glyph_data_from_binary(source_path, glyph_names):
    if not FONTTOOLS_AVAILABLE:
        raise ImportError("fontTools is required for TTF/OTF files")
    font = TTFont(source_path)
    glyph_data = {}
    unicode_map = {}
    if 'cmap' in font:
        for table in font['cmap'].tables:
            if table.isUnicode():
                unicode_map.update(table.cmap)
    glyph_to_unicode = {}
    for unicode_val, glyph_name in unicode_map.items():
        if glyph_name not in glyph_to_unicode:
            glyph_to_unicode[glyph_name] = format(unicode_val, '04X')
    for glyph_name in glyph_names:
        glyph_data[glyph_name] = {
            'unicode':     glyph_to_unicode.get(glyph_name),
            'category':    None,
            'subCategory': None,
            'script':      None,
        }
    return glyph_data
 
 
def get_glyphs_and_data(source_path):
    ext = os.path.splitext(source_path)[1].lower()
    if ext in ['.glyphs', '.glyphx']:
        glyph_names = get_glyph_list_from_glyphs_file(source_path)
        glyph_data  = get_glyph_data_from_glyphs_file(source_path, glyph_names)
    elif ext == '.ufo' or os.path.isdir(source_path):
        glyph_names = get_glyph_list_from_ufo(source_path)
        glyph_data  = get_glyph_data_from_ufo(source_path, glyph_names)
    elif ext in ['.ttf', '.otf']:
        glyph_names = get_glyph_list_from_binary(source_path)
        glyph_data  = get_glyph_data_from_binary(source_path, glyph_names)
    else:
        raise ValueError(f"Unsupported format: {ext}")
    return glyph_names, glyph_data
 
 
# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------
 
def choose_source_file():
    panel = NSOpenPanel.openPanel()
    panel.setCanChooseFiles_(True)
    panel.setCanChooseDirectories_(True)
    panel.setAllowedFileTypes_(["glyphs", "glyphx", "ufo", "ttf", "otf"])
    panel.setTitle_("Choose Source Font")
    panel.setPrompt_("Select")
    if panel.runModal() == NSFileHandlingPanelOKButton:
        return panel.URL().path()
    return None
 
 
# ---------------------------------------------------------------------------
# Glyph addition
# ---------------------------------------------------------------------------
 
def add_glyph_to_font(font, glyph_name, glyph_info):
    new_glyph = GSGlyph(glyph_name)
    if glyph_info.get('unicode'):
        new_glyph.unicode = glyph_info['unicode']
    if glyph_info.get('category'):
        new_glyph.category = glyph_info['category']
    if glyph_info.get('subCategory'):
        new_glyph.subCategory = glyph_info['subCategory']
    if glyph_info.get('script'):
        new_glyph.script = glyph_info['script']
    font.glyphs.append(new_glyph)
    return new_glyph
 
 
# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
 
def main():
    font = Glyphs.font
    if not font:
        Message("No Font Open", "Please open a font first.")
        return
 
    Glyphs.showMacroWindow()
    print(f"\n=== Add Missing Glyphs from Source Font ===")
 
    # ------------------------------------------------------------------
    # Build lookup structures for the CURRENT font
    # ------------------------------------------------------------------
 
    # 1. Name-based lookup (case-insensitive)
    current_names_lower = {g.name.lower(): g.name for g in font.glyphs}
 
    # 2. Unicode-based lookup: map each normalised hex string -> glyph name
    #    glyph.unicodes may be None in Glyphs 3, so guard accordingly.
    current_unicodes = {}   # "00E9" -> "eacute"  (first glyph that owns it)
    for g in font.glyphs:
        unicodes = g.unicodes or []
        for uval in unicodes:
            key = uval.upper()
            if key not in current_unicodes:
                current_unicodes[key] = g.name
 
    print(f"Current font: {len(font.glyphs)} glyphs, "
          f"{len(current_unicodes)} unique Unicode values")
 
    # ------------------------------------------------------------------
    # Choose and read source font
    # ------------------------------------------------------------------
 
    source_path = choose_source_file()
    if not source_path:
        print("Cancelled by user")
        return
 
    print(f"\nReading glyph list from: {os.path.basename(source_path)}")
 
    try:
        source_glyphs, glyph_data = get_glyphs_and_data(source_path)
        print(f"Source font: {len(source_glyphs)} glyphs")
 
        # ------------------------------------------------------------------
        # Classify each source glyph
        # ------------------------------------------------------------------
 
        missing_glyphs          = []   # truly absent → will be added
        skipped_name_conflicts  = []   # same name (different case)
        skipped_unicode_matches = []   # different name, same Unicode
 
        for glyph_name in source_glyphs:
            info       = glyph_data.get(glyph_name, {})
            src_unicode = (info.get('unicode') or '').upper() or None
 
            # --- Check 1: name match (case-insensitive) ---
            existing_name = current_names_lower.get(glyph_name.lower())
            if existing_name is not None:
                if existing_name != glyph_name:
                    skipped_name_conflicts.append(
                        f"{glyph_name} (exists as '{existing_name}')"
                    )
                # exact name match: silently skip (font already has it)
                continue
 
            # --- Check 2: Unicode match ---
            if src_unicode and src_unicode in current_unicodes:
                existing_name = current_unicodes[src_unicode]
                skipped_unicode_matches.append(
                    f"{glyph_name} U+{src_unicode} "
                    f"(already covered by '{existing_name}')"
                )
                continue
 
            # --- Not present by name or Unicode → needs to be added ---
            missing_glyphs.append(glyph_name)
 
        # ------------------------------------------------------------------
        # Report skips
        # ------------------------------------------------------------------
 
        if skipped_name_conflicts:
            print(f"\nSkipped — name conflict, case mismatch "
                  f"({len(skipped_name_conflicts)}):")
            for line in skipped_name_conflicts[:10]:
                print(f"  {line}")
            if len(skipped_name_conflicts) > 10:
                print(f"  ...and {len(skipped_name_conflicts) - 10} more")
 
        if skipped_unicode_matches:
            print(f"\nSkipped — Unicode already present under different name "
                  f"({len(skipped_unicode_matches)}):")
            for line in skipped_unicode_matches[:10]:
                print(f"  {line}")
            if len(skipped_unicode_matches) > 10:
                print(f"  ...and {len(skipped_unicode_matches) - 10} more")
 
        if not missing_glyphs:
            Message("No Missing Glyphs",
                    "Your font already contains all glyphs from the source font\n"
                    "(matched by name or Unicode value).")
            print("\n✓ No missing glyphs — your font is complete!")
            return
 
        print(f"\nFound {len(missing_glyphs)} missing glyphs")
 
        # ------------------------------------------------------------------
        # Confirmation dialog
        # ------------------------------------------------------------------
 
        missing_glyphs_sorted = sorted(missing_glyphs)
        preview_list = missing_glyphs_sorted[:20]
        remaining    = len(missing_glyphs_sorted) - len(preview_list)
        preview_text = ", ".join(preview_list)
        if remaining > 0:
            preview_text += f"\n...and {remaining} more"
 
        message = f"Add {len(missing_glyphs)} missing glyphs?\n\n{preview_text}"
        result = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(
            "Add Missing Glyphs",
            "Add Glyphs",
            "Cancel",
            None,
            message
        ).runModal()
 
        if result != 1:
            print("Cancelled by user")
            return
 
        # ------------------------------------------------------------------
        # Add glyphs
        # ------------------------------------------------------------------
 
        added_count  = 0
        failed_glyphs = []
 
        for glyph_name in missing_glyphs_sorted:
            try:
                if font.glyphs[glyph_name] is not None:
                    print(f"  Skipping {glyph_name} — appeared after scan")
                    continue
 
                info = glyph_data.get(glyph_name, {})
                add_glyph_to_font(font, glyph_name, info)
                added_count += 1
 
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
 
        success_msg = f"✓ Successfully added {added_count} glyphs to your font"
        Message("Success", success_msg)
        print(f"\n{success_msg}")
        print(f"New total: {len(font.glyphs)} glyphs")
 
    except Exception as e:
        Message("Error", f"Failed to add glyphs:\n{e}")
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
 
 
main()