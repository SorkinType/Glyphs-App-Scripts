#MenuTitle: Adjust Glyphs - All Masters
# -*- coding: utf-8 -*-
"""
Adjust side bearings, condensation, and slant for selected glyphs.
Each master can be adjusted independently with different values.

Save this file in your Glyphs Scripts folder:
~/Library/Application Support/Glyphs 3/Scripts/

Usage:
1. Select glyphs in Font View or Edit View
2. Run this script from Scripts menu
3. Configure adjustments for each master independently
4. Click Apply
"""

from vanilla import Window, EditText, Button, TextBox, RadioGroup, CheckBox, Box
from AppKit import NSColor, NSAffineTransform
import math

class GlyphAdjuster:
    def __init__(self):
        self.font = Glyphs.font
        
        if not self.font:
            Message("No Font Open", "Please open a font first.")
            return
        
        # Get selected glyphs
        self.selected_glyphs = self.get_selected_glyphs()
        
        if not self.selected_glyphs:
            Message("No Glyphs Selected", "Please select at least one glyph.")
            return
        
        # Get all masters
        self.masters = self.font.masters
        
        if not self.masters:
            Message("No Masters", "Font has no masters.")
            return
        
        # Calculate window height based on number of masters
        master_section_height = len(self.masters) * 135  # Each master needs ~135px
        window_height = 150 + master_section_height
        
        # Create window
        self.w = Window((750, window_height), "Adjust Glyphs - All Masters")
        
        y = 20
        
        # Info text
        self.w.info = TextBox((20, y, -20, 20), 
            f"Adjusting {len(self.selected_glyphs)} selected glyph(s)")
        y += 30
        
        self.w.instructionText = TextBox((20, y, -20, 30),
            "Configure adjustments for each master independently:")
        y += 40
        
        # Create master sections
        self.master_controls = []
        
        for i, master in enumerate(self.masters):
            master_group = self.create_master_section(master, i, y)
            self.master_controls.append(master_group)
            y += 135
        
        y += 10
        
        # Buttons
        self.w.applyButton = Button((20, y, -20, 30), "Apply", callback=self.apply)
        
        self.w.open()
    
    def create_master_section(self, master, index, y_pos):
        """Create controls for one master."""
        controls = {}
        
        section_height = 135
        
        # Add background box for even-numbered masters
        if index % 2 == 1:
            bg_box = Box((0, y_pos, -0, section_height))
            bg_box.getNSBox().setFillColor_(NSColor.colorWithCalibratedWhite_alpha_(0.95, 1.0))
            setattr(self.w, f"master{index}_bg", bg_box)
        
        # Master checkbox and name
        controls['checkbox'] = CheckBox((20, y_pos + 10, -20, 20), 
            f"{master.name}", 
            value=False,
            callback=lambda sender: self.master_checkbox_changed(index))
        
        y = y_pos + 35
        
        # Left bearing controls
        controls['left_mode'] = RadioGroup((40, y, 210, 20),
            ["Units", "%", "As is"],
            isVertical=False,
            sizeStyle="small",
            callback=lambda sender: self.mode_changed(index, 'left'))
        controls['left_mode'].set(2)  # Default to "As is"
        controls['left_value'] = EditText((260, y, 80, 22), "0", sizeStyle="small")
        controls['left_value'].enable(False)
        controls['left_label'] = TextBox((350, y + 2, 100, 20), "Left", sizeStyle="small")
        
        y += 30
        
        # Right bearing controls
        controls['right_mode'] = RadioGroup((40, y, 210, 20),
            ["Units", "%", "As is"],
            isVertical=False,
            sizeStyle="small",
            callback=lambda sender: self.mode_changed(index, 'right'))
        controls['right_mode'].set(2)  # Default to "As is"
        controls['right_value'] = EditText((260, y, 80, 22), "0", sizeStyle="small")
        controls['right_value'].enable(False)
        controls['right_label'] = TextBox((350, y + 2, 100, 20), "Right", sizeStyle="small")
        
        y += 30
        
        # Condensation controls
        controls['condense_label'] = TextBox((40, y + 2, 100, 20), "Condense to %:", sizeStyle="small")
        controls['condense_value'] = EditText((150, y, 80, 22), "100", sizeStyle="small")
        controls['condense_value'].enable(False)
        controls['condense_info'] = TextBox((240, y + 2, -20, 20), "(100 = no change)", sizeStyle="small")
        
        y += 30
        
        # Slant controls
        controls['slant_label'] = TextBox((40, y + 2, 100, 20), "Slant angle °:", sizeStyle="small")
        controls['slant_value'] = EditText((150, y, 80, 22), "0", sizeStyle="small")
        controls['slant_value'].enable(False)
        controls['slant_info'] = TextBox((240, y + 2, -20, 20), "(0 = no slant)", sizeStyle="small")
        
        # Store in window
        for key, control in controls.items():
            setattr(self.w, f"master{index}_{key}", control)
        
        return controls
    
    def mode_changed(self, index, side):
        """Enable/disable value input when mode changes."""
        checkbox = getattr(self.w, f"master{index}_checkbox")
        if not checkbox.get():
            return
        
        mode_control = getattr(self.w, f"master{index}_{side}_mode")
        value_control = getattr(self.w, f"master{index}_{side}_value")
        
        # Enable value field if not "As is" (index 2)
        value_control.enable(mode_control.get() != 2)
    
    def master_checkbox_changed(self, index):
        """Enable/disable controls when master checkbox changes."""
        checkbox = getattr(self.w, f"master{index}_checkbox")
        is_enabled = checkbox.get()
        
        # Enable/disable all controls for this master
        for control_type in ['left_label', 'left_mode', 'right_label', 'right_mode',
                            'condense_label', 'condense_value', 'condense_info',
                            'slant_label', 'slant_value', 'slant_info']:
            control = getattr(self.w, f"master{index}_{control_type}")
            control.enable(is_enabled)
        
        # Handle value fields based on mode
        if is_enabled:
            left_mode = getattr(self.w, f"master{index}_left_mode").get()
            right_mode = getattr(self.w, f"master{index}_right_mode").get()
            getattr(self.w, f"master{index}_left_value").enable(left_mode != 2)
            getattr(self.w, f"master{index}_right_value").enable(right_mode != 2)
        else:
            getattr(self.w, f"master{index}_left_value").enable(False)
            getattr(self.w, f"master{index}_right_value").enable(False)
    
    def get_selected_glyphs(self):
        """Get currently selected glyphs."""
        selected = []
        
        # Check if in Edit View
        if self.font.currentTab:
            for layer in self.font.currentTab.layers:
                if layer.parent:
                    selected.append(layer.parent)
        
        # Check if in Font View
        if not selected and self.font.selectedLayers:
            for layer in self.font.selectedLayers:
                if layer.parent:
                    selected.append(layer.parent)
        
        # Remove duplicates
        return list(set(selected))
    
    def parse_value(self, value_str, mode):
        """
        Parse the input value.
        Returns: (value, is_percentage, skip)
        """
        value_str = value_str.strip()
        
        if mode == 2:  # As is
            return (0, False, True)
        
        # Check if percentage mode
        if mode == 1:  # Percentage mode
            try:
                value = float(value_str)
                return (value, True, False)
            except:
                return (0, False, False)
        else:  # Fixed units mode
            try:
                value = float(value_str)
                return (value, False, False)
            except:
                return (0, False, False)
    
    def apply_bearing_adjustment(self, original_value, adjustment_value, is_percent):
        """
        Apply bearing adjustment with special handling for negative values.
        
        For negative original values:
        - Positive percentage: moves toward zero (e.g., -100 + 20% = -80)
        - Negative percentage: moves away from zero (e.g., -100 - 20% = -120)
        
        For positive original values:
        - Works normally (e.g., 100 + 20% = 120)
        """
        if not is_percent:
            # Fixed units - simple addition
            return original_value + adjustment_value
        
        # Percentage adjustment
        if original_value < 0:
            # For negative values, flip the logic
            # Positive % reduces the negative (moves toward zero)
            # Negative % increases the negative (moves away from zero)
            adjustment = abs(original_value) * (adjustment_value / 100.0)
            return original_value + adjustment  # Adding because we want -100 + (+20 of 100) = -80
        else:
            # For positive values, normal behavior
            adjustment = original_value * (adjustment_value / 100.0)
            return original_value + adjustment
        """Apply condensation and slant transformation to a layer."""
        
        if condense_percent == 100 and slant_degrees == 0:
            return  # No transformation needed
        
        # Create transformation matrix
        transform = NSAffineTransform.alloc().init()
        
        # Apply horizontal scaling (condensing)
        if condense_percent != 100:
            scale_factor = condense_percent / 100.0
            transform.scaleXBy_yBy_(scale_factor, 1.0)
        
        # Apply slanting (shearing)
        if slant_degrees != 0:
            slant_radians = math.radians(slant_degrees)
            skew = math.tan(slant_radians)
            
            skew_transform = NSAffineTransform.alloc().init()
            matrix = skew_transform.transformStruct()
            matrix.m11 = 1.0
            matrix.m12 = 0.0
            matrix.m21 = skew
            matrix.m22 = 1.0
            matrix.tX = 0.0
            matrix.tY = 0.0
            skew_transform.setTransformStruct_(matrix)
            
            transform.appendTransform_(skew_transform)
        
        # Apply transformation to all paths
        for path in layer.paths:
            path.applyTransform(transform.transformStruct())
        
        # Apply transformation to all components
        for component in layer.components:
            component.applyTransform(transform.transformStruct())
    
    def apply(self, sender):
        """Apply the adjustments to selected glyphs."""
        
        print("\n" + "="*60)
        print("ADJUSTING GLYPHS - ALL MASTERS")
        print("="*60)
        print(f"Glyphs to adjust: {len(self.selected_glyphs)}\n")
        
        # Collect settings for each master
        master_settings = []
        for i, master in enumerate(self.masters):
            checkbox = getattr(self.w, f"master{i}_checkbox")
            if not checkbox.get():
                print(f"Master '{master.name}': SKIPPED")
                master_settings.append(None)
                continue
            
            left_mode = getattr(self.w, f"master{i}_left_mode").get()
            left_value_str = getattr(self.w, f"master{i}_left_value").get()
            right_mode = getattr(self.w, f"master{i}_right_mode").get()
            right_value_str = getattr(self.w, f"master{i}_right_value").get()
            
            try:
                condense_str = getattr(self.w, f"master{i}_condense_value").get()
                slant_str = getattr(self.w, f"master{i}_slant_value").get()
                condense_percent = float(condense_str)
                slant_degrees = float(slant_str)
            except:
                condense_percent = 100
                slant_degrees = 0
            
            left_value, left_is_percent, left_skip = self.parse_value(left_value_str, left_mode)
            right_value, right_is_percent, right_skip = self.parse_value(right_value_str, right_mode)
            
            settings = {
                'master': master,
                'left_value': left_value,
                'left_is_percent': left_is_percent,
                'left_skip': left_skip,
                'right_value': right_value,
                'right_is_percent': right_is_percent,
                'right_skip': right_skip,
                'condense_percent': condense_percent,
                'slant_degrees': slant_degrees
            }
            master_settings.append(settings)
            
            # Print settings
            print(f"Master '{master.name}':")
            if not left_skip:
                if left_is_percent:
                    print(f"  Left: {left_value:+.1f}%")
                else:
                    print(f"  Left: {left_value:+.0f} units")
            else:
                print(f"  Left: as is")
            
            if not right_skip:
                if right_is_percent:
                    print(f"  Right: {right_value:+.1f}%")
                else:
                    print(f"  Right: {right_value:+.0f} units")
            else:
                print(f"  Right: as is")
            
            print(f"  Condense: {condense_percent}%")
            print(f"  Slant: {slant_degrees}°")
        
        print("\n" + "="*60 + "\n")
        
        # Apply adjustments
        for glyph in self.selected_glyphs:
            print(f"{glyph.name}:")
            
            for i, settings in enumerate(master_settings):
                if settings is None:
                    continue
                
                master = settings['master']
                layer = glyph.layers[master.id]
                
                if not layer:
                    print(f"  {master.name}: No layer found")
                    continue
                
                # Store original values
                old_lsb = layer.LSB
                old_rsb = layer.RSB
                
                # Apply transformation (condense/slant)
                self.transform_layer(layer, settings['condense_percent'], settings['slant_degrees'])
                
                # Adjust left bearing
                if not settings['left_skip']:
                    layer.LSB = self.apply_bearing_adjustment(
                        old_lsb, 
                        settings['left_value'], 
                        settings['left_is_percent']
                    )
                
                # Adjust right bearing
                if not settings['right_skip']:
                    layer.RSB = self.apply_bearing_adjustment(
                        old_rsb, 
                        settings['right_value'], 
                        settings['right_is_percent']
                    )
                
                new_lsb = layer.LSB
                new_rsb = layer.RSB
                
                print(f"  {master.name}: LSB {old_lsb:.0f}→{new_lsb:.0f}, RSB {old_rsb:.0f}→{new_rsb:.0f}")
        
        print("\n" + "="*60)
        print(f"Adjusted {len(self.selected_glyphs)} glyph(s)")
        print("="*60 + "\n")
        
        self.w.close()
        
        Message("Success", 
            f"Glyphs adjusted for {len(self.selected_glyphs)} glyph(s) across selected masters.")

# Run the script
GlyphAdjuster()