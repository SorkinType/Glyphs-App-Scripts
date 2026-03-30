# MenuTitle: Copy Glyphs Between Files
# -*- coding: utf-8 -*-
__doc__ = """
Copy glyphs from one open font file to another.
Glyphs that already exist in the target file will not be modified.
New glyphs added to the target file will be colored purple.
"""

import vanilla
from GlyphsApp import Glyphs, GSGlyph

class GlyphCopier:
    def __init__(self):
        # Get all open fonts
        self.fonts = Glyphs.fonts
        
        if len(self.fonts) < 2:
            Message("Not Enough Fonts Open", 
                "Please open at least 2 font files to copy glyphs between them.")
            return
        
        # Create font name list for dropdowns
        self.font_names = [self.get_font_display_name(font) for font in self.fonts]
        
        # Window setup - INCREASED HEIGHT
        self.w = vanilla.FloatingWindow((400, 320), "Copy Glyphs Between Files")
        
        y = 10
        
        # Instructions
        self.w.info = vanilla.TextBox((10, y, -10, 40), 
            "Copy glyphs from source to target file.\nExisting glyphs in target will not be modified.")
        y += 50
        
        # Source file selection
        self.w.sourceLabel = vanilla.TextBox((10, y, 80, 20), "Source file:")
        self.w.sourcePopup = vanilla.PopUpButton((100, y, -10, 20), 
            self.font_names, callback=self.sourceChanged)
        y += 30
        
        # Source info
        self.w.sourceInfo = vanilla.TextBox((100, y, -10, 20), 
            "", sizeStyle="small")
        y += 25
        
        # Target file selection
        self.w.targetLabel = vanilla.TextBox((10, y, 80, 20), "Target file:")
        self.w.targetPopup = vanilla.PopUpButton((100, y, -10, 20), 
            self.font_names, callback=self.targetChanged)
        
        # Set default target to second font if available
        if len(self.fonts) > 1:
            self.w.targetPopup.set(1)
        
        y += 30
        
        # Target info
        self.w.targetInfo = vanilla.TextBox((100, y, -10, 20), 
            "", sizeStyle="small")
        y += 30
        
        # Preview section
        self.w.previewLabel = vanilla.TextBox((10, y, -10, 20), 
            "Glyphs to copy:")
        y += 25
        
        self.w.previewInfo = vanilla.TextBox((10, y, -10, 40), 
            "", sizeStyle="small")
        y += 50
        
        # Options
        self.w.colorCheck = vanilla.CheckBox((10, y, -10, 20), 
            "Color new glyphs purple", value=True)
        y += 30
        
        # Buttons
        self.w.cancelButton = vanilla.Button((10, -30, 120, 20), 
            "Cancel", callback=self.cancelCallback)
        self.w.copyButton = vanilla.Button((-120, -30, 110, 20), 
            "Copy Glyphs", callback=self.copyCallback)
        
        self.w.setDefaultButton(self.w.copyButton)
        
        # Initial update
        self.updatePreview()
        
        self.w.open()
    
    def get_font_display_name(self, font):
        """Get a display name for the font."""
        if font.familyName:
            name = font.familyName
            if font.filepath:
                import os
                filename = os.path.basename(font.filepath)
                name += f" ({filename})"
            return name
        elif font.filepath:
            import os
            return os.path.basename(font.filepath)
        else:
            return "Untitled Font"
    
    def sourceChanged(self, sender):
        """Called when source font selection changes."""
        self.updatePreview()
    
    def targetChanged(self, sender):
        """Called when target font selection changes."""
        self.updatePreview()
    
    def updatePreview(self):
        """Update the preview of what will be copied."""
        source_idx = self.w.sourcePopup.get()
        target_idx = self.w.targetPopup.get()
        
        if source_idx == target_idx:
            self.w.previewInfo.set("⚠ Source and target are the same file!")
            self.w.copyButton.enable(False)
            return
        
        source_font = self.fonts[source_idx]
        target_font = self.fonts[target_idx]
        
        # Update font info
        self.w.sourceInfo.set(f"{len(source_font.glyphs)} glyphs")
        self.w.targetInfo.set(f"{len(target_font.glyphs)} glyphs")
        
        # Find glyphs to copy (in source but not in target)
        source_glyph_names = set(g.name for g in source_font.glyphs)
        target_glyph_names = set(g.name for g in target_font.glyphs)
        
        glyphs_to_copy = source_glyph_names - target_glyph_names
        glyphs_in_both = source_glyph_names & target_glyph_names
        
        # Update preview
        if glyphs_to_copy:
            preview_list = sorted(list(glyphs_to_copy))[:10]
            preview_text = ", ".join(preview_list)
            if len(glyphs_to_copy) > 10:
                preview_text += f"... (+{len(glyphs_to_copy) - 10} more)"
            
            info_text = f"{len(glyphs_to_copy)} glyphs will be copied:\n{preview_text}"
            if glyphs_in_both:
                info_text += f"\n\n{len(glyphs_in_both)} glyphs already exist in target (will be skipped)"
            
            self.w.previewInfo.set(info_text)
            self.w.copyButton.enable(True)
        else:
            self.w.previewInfo.set("No new glyphs to copy.\nAll glyphs from source already exist in target.")
            self.w.copyButton.enable(False)
    
    def cancelCallback(self, sender):
        self.w.close()
    
    def copyCallback(self, sender):
        source_idx = self.w.sourcePopup.get()
        target_idx = self.w.targetPopup.get()
        
        if source_idx == target_idx:
            Message("Error", "Source and target cannot be the same file.")
            return
        
        source_font = self.fonts[source_idx]
        target_font = self.fonts[target_idx]
        color_glyphs = self.w.colorCheck.get()
        
        # Copy glyphs
        copied_count = self.copyGlyphs(source_font, target_font, color_glyphs)
        
        if copied_count > 0:
            Message("Copy Complete", 
                f"Successfully copied {copied_count} glyph(s) to {self.get_font_display_name(target_font)}.")
            self.w.close()
        else:
            Message("Nothing Copied", 
                "No new glyphs were copied (all glyphs already exist in target).")
    
    def copyGlyphs(self, source_font, target_font, color_glyphs):
        """Copy glyphs from source to target font."""
        copied_count = 0
        
        print("\n" + "="*60)
        print("COPYING GLYPHS BETWEEN FILES")
        print("="*60)
        print(f"Source: {self.get_font_display_name(source_font)}")
        print(f"Target: {self.get_font_display_name(target_font)}")
        print(f"Color new glyphs: {color_glyphs}")
        print("")
        
        # Purple color (magenta)
        # Colors in Glyphs are stored as integers 0-11
        # Purple/Magenta is color index 8
        purple_color = 8
        
        for source_glyph in source_font.glyphs:
            glyph_name = source_glyph.name
            
            # FIXED: Check if glyph already exists in target using proper method
            existing_glyph = target_font.glyphs[glyph_name]
            if existing_glyph is not None:
                print(f"Skipped: {glyph_name} (already exists in target)")
                continue
            
            try:
                # Create new glyph in target
                new_glyph = GSGlyph(glyph_name)
                target_font.glyphs.append(new_glyph)
                
                # Copy basic properties
                new_glyph.unicode = source_glyph.unicode
                new_glyph.category = source_glyph.category
                new_glyph.subCategory = source_glyph.subCategory
                new_glyph.script = source_glyph.script
                new_glyph.productionName = source_glyph.productionName
                new_glyph.glyphInfo = source_glyph.glyphInfo
                
                # Set color if requested
                if color_glyphs:
                    new_glyph.color = purple_color
                
                # Copy layers for each master
                for source_master in source_font.masters:
                    source_layer = source_glyph.layers[source_master.id]
                    
                    # Find corresponding master in target font by name
                    target_master = None
                    for tm in target_font.masters:
                        if tm.name == source_master.name:
                            target_master = tm
                            break
                    
                    # If no matching master found, use first master
                    if not target_master:
                        if len(target_font.masters) > 0:
                            target_master = target_font.masters[0]
                        else:
                            print(f"  Warning: No masters in target font for {glyph_name}")
                            continue
                    
                    target_layer = new_glyph.layers[target_master.id]
                    
                    # Copy layer properties
                    target_layer.width = source_layer.width
                    
                    # Copy paths
                    for path in source_layer.paths:
                        target_layer.paths.append(path.copy())
                    
                    # Copy components
                    for component in source_layer.components:
                        target_layer.components.append(component.copy())
                    
                    # Copy anchors
                    for anchor in source_layer.anchors:
                        target_layer.anchors.append(anchor.copy())
                
                copied_count += 1
                print(f"Copied: {glyph_name}")
                
            except Exception as e:
                print(f"Error copying {glyph_name}: {e}")
                import traceback
                traceback.print_exc()
        
        print("")
        print("="*60)
        print(f"Total glyphs copied: {copied_count}")
        print("="*60)
        
        return copied_count


# Main execution
def main():
    # Check if any fonts are open
    if not Glyphs.fonts:
        Message("No Fonts Open", "Please open at least 2 font files first.")
        return
    
    if len(Glyphs.fonts) < 2:
        Message("Not Enough Fonts Open", 
            "Please open at least 2 font files to copy glyphs between them.")
        return
    
    # Show dialog
    GlyphCopier()


# Run the script
main()