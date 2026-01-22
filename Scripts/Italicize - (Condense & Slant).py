#MenuTitle: Italicize Glyphs (Condense & Slant)
# -*- coding: utf-8 -*-
"""
Apply condensing and slanting transformations to selected glyphs.

Save this file in your Glyphs Scripts folder:
~/Library/Application Support/Glyphs 3/Scripts/

Usage:
1. Select glyphs in the font window or edit view
2. Run this script from Scripts menu
3. Enter condensing percentage (100% = no change, 50% = half width)
4. Enter slant angle in degrees (0 = no slant, 15 = italic slant)
5. Choose whether to apply to all masters or only current layer
6. Click "Transform"
"""

from vanilla import Window, TextBox, EditText, Button, CheckBox
from AppKit import NSAffineTransform
import math


class TransformDialog:
    
    def __init__(self):
        self.font = Glyphs.font
        
        # Get current master
        self.current_master = None
        if self.font.currentTab:
            self.current_master = self.font.currentTab.graphicView().activeLayer().master
        elif self.font.selectedLayers:
            self.current_master = self.font.selectedLayers[0].master
        
        if not self.current_master:
            self.current_master = self.font.masters[0]
        
        # Get selected glyphs
        self.selected_glyphs = self.get_selected_glyphs()
        
        self.w = Window((400, 320), "Transform Glyphs")
        
        y = 10
        
        # Info about selection
        glyph_names = ", ".join([g.name for g in self.selected_glyphs[:5]])
        if len(self.selected_glyphs) > 5:
            glyph_names += f"... (+{len(self.selected_glyphs) - 5} more)"
        
        self.w.glyphsLabel = TextBox((10, y, -10, 40), 
            f"Selected glyphs ({len(self.selected_glyphs)}): {glyph_names}", 
            sizeStyle="small")
        y += 50
        
        # Condensing percentage
        self.w.condenseLabel = TextBox((10, y, 150, 20), "Condense to percentage:")
        self.w.condenseField = EditText((170, y, 80, 22), "75")
        self.w.condenseInfo = TextBox((260, y, -10, 40), 
            "Any value > 0\n(e.g., 75, 50, 125)", 
            sizeStyle="small")
        y += 50
        
        # Slant angle
        self.w.slantLabel = TextBox((10, y, 150, 20), "Slant angle (degrees):")
        self.w.slantField = EditText((170, y, 80, 22), "0")
        self.w.slantInfo = TextBox((260, y, -10, 40), 
            "Any angle\n(e.g., 0, 15, -12)", 
            sizeStyle="small")
        y += 50
        
        # Options
        self.w.allMasters = CheckBox((10, y, -10, 20), 
            "Apply to all masters", 
            value=True)
        y += 30
        
        # Sidebearing scaling option
        self.w.sidebearingLabel = TextBox((10, y, 200, 20), "Scale sidebearings to percentage:")
        self.w.sidebearingField = EditText((220, y, 80, 22), "100")
        self.w.sidebearingInfo = TextBox((310, y, -10, 40), 
            "100 = keep original\nMatch condense value\nor use custom value", 
            sizeStyle="small")
        y += 50
        
        # Info text
        self.w.info = TextBox((10, y, -10, 20), "", sizeStyle="small")
        y += 25
        
        # Buttons
        self.w.cancelButton = Button((10, -30, 120, 20), "Cancel", callback=self.cancel)
        self.w.transformButton = Button((-130, -30, 120, 20), "Transform", callback=self.transform)
        
        self.w.setDefaultButton(self.w.transformButton)
        self.w.open()
    
    def get_selected_glyphs(self):
        """Get list of unique selected glyphs."""
        glyphs = []
        
        if self.font.selectedLayers:
            glyphs = list(set([layer.parent for layer in self.font.selectedLayers if layer.parent]))
        
        return glyphs
    
    def cancel(self, sender):
        self.w.close()
    
    def transform_layer(self, layer, condense_percent, slant_degrees, sidebearing_percent):
        """Apply transformation to a single layer."""
        
        try:
            # Store original width and sidebearings
            original_lsb = layer.LSB
            original_rsb = layer.RSB
            
            # Create transformation matrix
            transform = NSAffineTransform.alloc().init()
            
            # Apply horizontal scaling (condensing)
            scale_factor = condense_percent / 100.0
            transform.scaleXBy_yBy_(scale_factor, 1.0)
            
            # Apply slanting (shearing)
            if slant_degrees != 0:
                # Convert degrees to radians and calculate skew
                slant_radians = math.radians(slant_degrees)
                skew = math.tan(slant_radians)
                
                # Create a new transform for skewing
                skew_transform = NSAffineTransform.alloc().init()
                
                # Set up the transformation matrix for skewing
                matrix = skew_transform.transformStruct()
                matrix.m11 = 1.0  # x scale
                matrix.m12 = 0.0  # y shear
                matrix.m21 = skew  # x shear (this creates the slant)
                matrix.m22 = 1.0  # y scale
                matrix.tX = 0.0
                matrix.tY = 0.0
                skew_transform.setTransformStruct_(matrix)
                
                # Combine transformations
                transform.appendTransform_(skew_transform)
            
            # Get the transform structure once
            transform_struct = transform.transformStruct()
            
            # Apply transformation to all paths
            for path in layer.paths:
                # FIXED: Use the correct method signature
                path.applyTransform(transform_struct)
            
            # Apply transformation to all components
            for component in layer.components:
                # FIXED: Use the correct method signature
                component.applyTransform(transform_struct)
            
            # Adjust sidebearings based on sidebearing_percent
            sidebearing_scale = sidebearing_percent / 100.0
            layer.LSB = original_lsb * sidebearing_scale
            layer.RSB = original_rsb * sidebearing_scale
            
            return True
            
        except Exception as e:
            print(f"    ERROR transforming layer: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def transform(self, sender):
        print("\n" + "="*60)
        print("TRANSFORM GLYPHS")
        print("="*60)
        
        if not self.font:
            self.w.info.set("Error: No font is open")
            return
        
        if not self.selected_glyphs:
            self.w.info.set("Error: No glyphs selected")
            return
        
        try:
            # Parse values
            condense_percent = float(self.w.condenseField.get())
            slant_degrees = float(self.w.slantField.get())
            sidebearing_percent = float(self.w.sidebearingField.get())
            
            # Basic validation - just check they're valid numbers
            if condense_percent <= 0:
                raise ValueError("Condense percentage must be greater than 0")
            
            if sidebearing_percent < 0:
                raise ValueError("Sidebearing percentage cannot be negative")
            
        except ValueError as e:
            self.w.info.set(f"Error: {e}")
            return
        
        apply_to_all = self.w.allMasters.get()
        
        print(f"\nCondense to: {condense_percent}%")
        print(f"Slant angle: {slant_degrees}°")
        print(f"Sidebearing scale: {sidebearing_percent}%")
        print(f"Apply to all masters: {apply_to_all}")
        print(f"Glyphs to process: {len(self.selected_glyphs)}")
        
        # Process glyphs
        total_layers = 0
        errors = 0
        
        for glyph in self.selected_glyphs:
            print(f"\n{glyph.name}:")
            
            if apply_to_all:
                # Apply to all masters
                for master in self.font.masters:
                    layer = glyph.layers[master.id]
                    if layer:
                        success = self.transform_layer(layer, condense_percent, slant_degrees, sidebearing_percent)
                        if success:
                            total_layers += 1
                            print(f"  ✓ Transformed in {master.name}")
                        else:
                            errors += 1
                            print(f"  ✗ Failed in {master.name}")
            else:
                # Apply only to current master
                layer = glyph.layers[self.current_master.id]
                if layer:
                    success = self.transform_layer(layer, condense_percent, slant_degrees, sidebearing_percent)
                    if success:
                        total_layers += 1
                        print(f"  ✓ Transformed in {self.current_master.name}")
                    else:
                        errors += 1
                        print(f"  ✗ Failed in {self.current_master.name}")
        
        # Show results
        print(f"\n{'='*60}")
        print(f"Total layers transformed: {total_layers}")
        if errors > 0:
            print(f"Errors encountered: {errors}")
        print(f"{'='*60}")
        
        if total_layers > 0:
            msg = f"✓ Transformed {total_layers} layers in {len(self.selected_glyphs)} glyphs"
            if errors > 0:
                msg += f"\n({errors} errors encountered)"
            Message("Success", msg)
            print(f"\n✓ SUCCESS: {msg}")
            self.w.close()
        else:
            msg = "No layers were transformed"
            self.w.info.set(msg)
            print(f"\n✗ {msg}")


# Main execution
def main():
    # Check if a font is open
    font = Glyphs.font
    if not font:
        Message("No Font Open", "Please open a font first.")
        return
    
    # Check if glyphs are selected
    if not font.selectedLayers:
        Message("No Selection", "Please select glyphs first.")
        return
    
    # Show dialog
    TransformDialog()


# Run the script
main()