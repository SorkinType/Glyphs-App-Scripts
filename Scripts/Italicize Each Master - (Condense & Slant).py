#MenuTitle: Transform Glyphs (Condense & Slant)
# -*- coding: utf-8 -*-
"""
Apply condensing and slanting transformations to selected glyphs.

Save this file in your Glyphs Scripts folder:
~/Library/Application Support/Glyphs 3/Scripts/

Usage:
1. Select glyphs in the font window or edit view
2. Run this script from Scripts menu
3. Choose to apply same values to all masters or set per-master values
4. Enter condensing percentage and slant angle
5. Click "Transform"
"""

from vanilla import Window, TextBox, EditText, Button, CheckBox, RadioGroup
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
        
        # Calculate window height based on number of masters
        num_masters = len(self.font.masters)
        base_height = 280
        per_master_height = 60
        window_height = base_height + (per_master_height * num_masters)
        
        self.w = Window((500, window_height), "Transform Glyphs")
        
        y = 10
        
        # Info about selection
        glyph_names = ", ".join([g.name for g in self.selected_glyphs[:5]])
        if len(self.selected_glyphs) > 5:
            glyph_names += f"... (+{len(self.selected_glyphs) - 5} more)"
        
        self.w.glyphsLabel = TextBox((10, y, -10, 40), 
            f"Selected glyphs ({len(self.selected_glyphs)}): {glyph_names}", 
            sizeStyle="small")
        y += 50
        
        # Mode selection
        self.w.modeGroup = RadioGroup((10, y, -10, 40),
            ["Same values for all masters", "Different values per master"],
            callback=self.modeChanged)
        self.w.modeGroup.set(0)
        y += 50
        
        # Global settings (shown when "same values" is selected)
        self.w.globalBox = vanilla.Box((10, y, -10, 120))
        box_y = 10
        
        self.w.globalBox.condenseLabel = TextBox((10, box_y, 150, 20), "Condense to percentage:")
        self.w.globalBox.condenseField = EditText((170, box_y, 80, 22), "90")
        self.w.globalBox.condenseInfo = TextBox((260, box_y, -10, 40), 
            "Any value > 0\n(e.g., 75, 50, 125)", 
            sizeStyle="small")
        box_y += 40
        
        self.w.globalBox.slantLabel = TextBox((10, box_y, 150, 20), "Slant angle (degrees):")
        self.w.globalBox.slantField = EditText((170, box_y, 80, 22), "0")
        self.w.globalBox.slantInfo = TextBox((260, box_y, -10, 40), 
            "Any angle\n(e.g., 0, 15, -12)", 
            sizeStyle="small")
        box_y += 40
        
        self.w.globalBox.sidebearingLabel = TextBox((10, box_y, 180, 20), "Scale sidebearings (%):")
        self.w.globalBox.sidebearingField = EditText((190, box_y, 60, 22), "100")
        
        y += 130
        
        # Per-master settings (shown when "different values" is selected)
        self.w.masterBox = vanilla.Box((10, y, -10, per_master_height * num_masters + 20))
        self.w.masterBox.show(False)
        
        self.master_fields = []
        box_y = 10
        
        for i, master in enumerate(self.font.masters):
            master_name = master.name if master.name else f"Master {i+1}"
            
            label = TextBox((10, box_y, 120, 20), master_name + ":", sizeStyle="small")
            condense_field = EditText((130, box_y, 60, 22), "90", sizeStyle="small")
            slant_field = EditText((200, box_y, 60, 22), "0", sizeStyle="small")
            sidebearing_field = EditText((270, box_y, 60, 22), "100", sizeStyle="small")
            
            setattr(self.w.masterBox, f"label{i}", label)
            setattr(self.w.masterBox, f"condense{i}", condense_field)
            setattr(self.w.masterBox, f"slant{i}", slant_field)
            setattr(self.w.masterBox, f"sidebearing{i}", sidebearing_field)
            
            self.master_fields.append({
                'master': master,
                'condense': condense_field,
                'slant': slant_field,
                'sidebearing': sidebearing_field
            })
            
            box_y += 30
        
        # Column headers for per-master mode
        self.w.masterBox.headerCondense = TextBox((130, -25, 60, 20), "Condense", sizeStyle="small")
        self.w.masterBox.headerSlant = TextBox((200, -25, 60, 20), "Slant", sizeStyle="small")
        self.w.masterBox.headerSidebearing = TextBox((270, -25, 60, 20), "Sidebear", sizeStyle="small")
        
        y += per_master_height * num_masters + 30
        
        # Info text
        self.w.info = TextBox((10, y, -10, 20), "", sizeStyle="small")
        y += 25
        
        # Buttons
        self.w.cancelButton = Button((10, -30, 120, 20), "Cancel", callback=self.cancel)
        self.w.transformButton = Button((-130, -30, 120, 20), "Transform", callback=self.transform)
        
        self.w.setDefaultButton(self.w.transformButton)
        self.w.open()
    
    def modeChanged(self, sender):
        mode = sender.get()
        if mode == 0:  # Same values for all
            self.w.globalBox.show(True)
            self.w.masterBox.show(False)
        else:  # Different values per master
            self.w.globalBox.show(False)
            self.w.masterBox.show(True)
    
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
            # Store original sidebearings
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
                path.applyTransform(transform_struct)
            
            # Apply transformation to all components
            for component in layer.components:
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
        
        mode = self.w.modeGroup.get()
        
        # Prepare settings based on mode
        master_settings = {}
        
        try:
            if mode == 0:  # Same values for all
                condense_percent = float(self.w.globalBox.condenseField.get())
                slant_degrees = float(self.w.globalBox.slantField.get())
                sidebearing_percent = float(self.w.globalBox.sidebearingField.get())
                
                # Validation
                if condense_percent <= 0:
                    raise ValueError("Condense percentage must be greater than 0")
                if sidebearing_percent < 0:
                    raise ValueError("Sidebearing percentage cannot be negative")
                
                # Apply same settings to all masters
                for master in self.font.masters:
                    master_settings[master.id] = {
                        'condense': condense_percent,
                        'slant': slant_degrees,
                        'sidebearing': sidebearing_percent
                    }
                
                print(f"\nMode: Same values for all masters")
                print(f"Condense to: {condense_percent}%")
                print(f"Slant angle: {slant_degrees}°")
                print(f"Sidebearing scale: {sidebearing_percent}%")
                
            else:  # Different values per master
                print(f"\nMode: Different values per master")
                
                for field_set in self.master_fields:
                    master = field_set['master']
                    condense_percent = float(field_set['condense'].get())
                    slant_degrees = float(field_set['slant'].get())
                    sidebearing_percent = float(field_set['sidebearing'].get())
                    
                    # Validation
                    if condense_percent <= 0:
                        raise ValueError(f"{master.name}: Condense percentage must be greater than 0")
                    if sidebearing_percent < 0:
                        raise ValueError(f"{master.name}: Sidebearing percentage cannot be negative")
                    
                    master_settings[master.id] = {
                        'condense': condense_percent,
                        'slant': slant_degrees,
                        'sidebearing': sidebearing_percent
                    }
                    
                    print(f"\n{master.name}:")
                    print(f"  Condense: {condense_percent}%")
                    print(f"  Slant: {slant_degrees}°")
                    print(f"  Sidebearing: {sidebearing_percent}%")
        
        except ValueError as e:
            self.w.info.set(f"Error: {e}")
            return
        
        print(f"\nGlyphs to process: {len(self.selected_glyphs)}")
        
        # Process glyphs
        total_layers = 0
        errors = 0
        
        for glyph in self.selected_glyphs:
            print(f"\n{glyph.name}:")
            
            for master in self.font.masters:
                layer = glyph.layers[master.id]
                if layer:
                    settings = master_settings[master.id]
                    success = self.transform_layer(
                        layer, 
                        settings['condense'], 
                        settings['slant'],
                        settings['sidebearing']
                    )
                    if success:
                        total_layers += 1
                        print(f"  ✓ Transformed in {master.name}")
                    else:
                        errors += 1
                        print(f"  ✗ Failed in {master.name}")
        
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