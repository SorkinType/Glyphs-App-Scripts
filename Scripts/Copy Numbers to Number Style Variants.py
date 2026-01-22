# MenuTitle: Create Number Variants
# -*- coding: utf-8 -*-
__doc__ = """
Creates component copies of default numbers (0-9) with various suffixes.
"""

import vanilla
from GlyphsApp import Glyphs, GSGlyph, GSComponent

class NumberVariantGenerator:
    def __init__(self):
        self.font = Glyphs.font
        
        if not self.font:
            Message("No Font Open", "Please open a font first.")
            return
        
        # Window setup
        self.w = vanilla.FloatingWindow((300, 380), "Number Variant Generator")
        
        y = 10
        
        # Instructions
        self.w.info = vanilla.TextBox((10, y, -10, 30), 
            "Select variants to create from numbers 0-9:")
        y += 40
        
        # Checkboxes for standard variants
        self.w.lfCheck = vanilla.CheckBox((10, y, -10, 20), 
            "Lining Figures (.lf)", value=False)
        y += 25
        
        self.w.tfCheck = vanilla.CheckBox((10, y, -10, 20), 
            "Tabular Figures (.tf)", value=False)
        y += 25
        
        self.w.osfCheck = vanilla.CheckBox((10, y, -10, 20), 
            "Old Style Figures (.osf)", value=False)
        y += 25
        
        self.w.tosfCheck = vanilla.CheckBox((10, y, -10, 20), 
            "Tabular Old Style Figures (.tosf)", value=False)
        y += 25
        
        self.w.dnomCheck = vanilla.CheckBox((10, y, -10, 20), 
            "Denominators (.dnom)", value=False)
        y += 25
        
        self.w.numrCheck = vanilla.CheckBox((10, y, -10, 20), 
            "Numerators (.numr)", value=False)
        y += 35
        
        # Stylistic sets section
        self.w.ssTitle = vanilla.TextBox((10, y, -10, 20), 
            "Stylistic Sets (optional):")
        y += 25
        
        self.w.ss01Check = vanilla.CheckBox((10, y, 80, 20), 
            "Custom:", value=False, callback=self.toggleSS01)
        self.w.ss01Text = vanilla.EditText((90, y-2, -10, 22), 
            "ss01", sizeStyle="small")
        y += 30
        
        self.w.ss02Check = vanilla.CheckBox((10, y, 80, 20), 
            "Custom:", value=False, callback=self.toggleSS02)
        self.w.ss02Text = vanilla.EditText((90, y-2, -10, 22), 
            "ss02", sizeStyle="small")
        y += 40
        
        # Options
        self.w.overwriteCheck = vanilla.CheckBox((10, y, -10, 20), 
            "Overwrite existing glyphs", value=False)
        y += 35
        
        # Buttons
        self.w.cancelButton = vanilla.Button((10, y, 135, 25), 
            "Cancel", callback=self.cancelCallback)
        self.w.generateButton = vanilla.Button((155, y, 135, 25), 
            "Generate", callback=self.generateCallback)
        
        self.w.setDefaultButton(self.w.generateButton)
        self.w.open()
    
    def toggleSS01(self, sender):
        self.w.ss01Text.enable(sender.get())
    
    def toggleSS02(self, sender):
        self.w.ss02Text.enable(sender.get())
    
    def cancelCallback(self, sender):
        self.w.close()
    
    def generateCallback(self, sender):
        # Collect selected variants
        variants = []
        
        if self.w.lfCheck.get():
            variants.append("lf")
        if self.w.tfCheck.get():
            variants.append("tf")
        if self.w.osfCheck.get():
            variants.append("osf")
        if self.w.tosfCheck.get():
            variants.append("tosf")
        if self.w.dnomCheck.get():
            variants.append("dnom")
        if self.w.numrCheck.get():
            variants.append("numr")
        if self.w.ss01Check.get():
            suffix = self.w.ss01Text.get().strip()
            if suffix and not suffix.startswith('.'):
                suffix = '.' + suffix
            if suffix:
                variants.append(suffix.lstrip('.'))
        if self.w.ss02Check.get():
            suffix = self.w.ss02Text.get().strip()
            if suffix and not suffix.startswith('.'):
                suffix = '.' + suffix
            if suffix:
                variants.append(suffix.lstrip('.'))
        
        if not variants:
            Message("No Variants Selected", 
                "Please select at least one variant to generate.")
            return
        
        overwrite = self.w.overwriteCheck.get()
        
        # Generate glyphs
        self.createNumberVariants(variants, overwrite)
        
        self.w.close()
    
    def createNumberVariants(self, suffixes, overwrite):
        created_count = 0
        skipped_count = 0
        
        # Base number glyphs
        base_numbers = ['zero', 'one', 'two', 'three', 'four', 
                       'five', 'six', 'seven', 'eight', 'nine']
        
        for base_name in base_numbers:
            base_glyph = self.font.glyphs[base_name]
            
            if not base_glyph:
                print(f"Warning: Base glyph '{base_name}' not found. Skipping.")
                continue
            
            for suffix in suffixes:
                new_name = f"{base_name}.{suffix}"
                
                # Check if glyph already exists
                if self.font.glyphs[new_name]:
                    if overwrite:
                        del self.font.glyphs[new_name]
                    else:
                        print(f"Skipped: {new_name} (already exists)")
                        skipped_count += 1
                        continue
                
                # Create new glyph
                new_glyph = GSGlyph(new_name)
                self.font.glyphs.append(new_glyph)
                
                # Copy layers
                for master in self.font.masters:
                    base_layer = base_glyph.layers[master.id]
                    new_layer = new_glyph.layers[master.id]
                    
                    # Create component reference
                    component = GSComponent(base_name)
                    new_layer.components.append(component)
                    
                    # Copy width
                    new_layer.width = base_layer.width
                
                # Copy Unicode and category info if appropriate
                new_glyph.category = base_glyph.category
                new_glyph.subCategory = base_glyph.subCategory
                
                created_count += 1
                print(f"Created: {new_name}")
        
        # Show completion message
        message = f"Created {created_count} glyph(s)."
        if skipped_count > 0:
            message += f"\nSkipped {skipped_count} existing glyph(s)."
        
        Message("Generation Complete", message)

# Run the script
NumberVariantGenerator()