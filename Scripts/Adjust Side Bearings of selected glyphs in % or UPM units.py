#MenuTitle: Adjust Side Bearings
# -*- coding: utf-8 -*-
"""
Adjust left and right side bearings of selected glyphs by:
- Fixed UPM units (e.g., +10, -10)
- Percentage of existing value (e.g., +10%, -10%)
- Leave unchanged

Can adjust each master independently with different values.

Save this file in your Glyphs Scripts folder:
~/Library/Application Support/Glyphs 3/Scripts/

Usage:
1. Select glyphs in Font View or Edit View
2. Run this script from Scripts menu
3. Choose which masters to adjust and enter values for each
4. Click Apply
"""

from vanilla import Window, EditText, Button, TextBox, RadioGroup, CheckBox, Group, Box
from AppKit import NSColor
import re

class SideBearingAdjuster:
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
        master_section_height = len(self.masters) * 95  # Each master needs ~95px
        window_height = 150 + master_section_height
        
        # Create window
        self.w = Window((700, window_height), "Adjust Side Bearings - All Masters")
        
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
            y += 95
        
        y += 10
        
        # Buttons
        self.w.applyButton = Button((20, y, -20, 30), "Apply", callback=self.apply)
        
        self.w.open()
    
    def create_master_section(self, master, index, y_pos):
        """Create controls for one master."""
        from vanilla import Box
        controls = {}
        
        section_height = 95
        
        # Add background box for even-numbered masters (0, 2, 4, etc.)
        if index % 2 == 1:  # Odd index = second, fourth, etc. master
            bg_box = Box((0, y_pos, -0, section_height))
            bg_box.getNSBox().setFillColor_(NSColor.colorWithCalibratedWhite_alpha_(0.95, 1.0))
            setattr(self.w, f"master{index}_bg", bg_box)
        
        # Master checkbox and name
        controls['checkbox'] = CheckBox((20, y_pos + 10, -20, 20), 
            f"{master.name}", 
            value=True,
            callback=lambda sender: self.master_checkbox_changed(index))
        
        y = y_pos + 35
        
        # Left bearing controls
        controls['left_mode'] = RadioGroup((40, y, 210, 20),
            ["Units", "%", "As is"],
            isVertical=False,
            sizeStyle="small",
            callback=lambda sender: self.mode_changed(index, 'left'))
        controls['left_mode'].set(2)  # Default to unchanged
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
        controls['right_mode'].set(2)  # Default to unchanged
        controls['right_value'] = EditText((260, y, 80, 22), "0", sizeStyle="small")
        controls['right_value'].enable(False)
        controls['right_label'] = TextBox((350, y + 2, 100, 20), "Right", sizeStyle="small")
        
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
        for control_type in ['left_label', 'left_mode', 'right_label', 'right_mode']:
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
        
        if mode == 2:  # Unchanged
            return (0, False, True)
        
        # Check if percentage
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
    
    def apply(self, sender):
        """Apply the adjustments to selected glyphs."""
        
        print("\n" + "="*60)
        print("ADJUSTING SIDE BEARINGS - ALL MASTERS")
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
            
            left_value, left_is_percent, left_skip = self.parse_value(left_value_str, left_mode)
            right_value, right_is_percent, right_skip = self.parse_value(right_value_str, right_mode)
            
            settings = {
                'master': master,
                'left_value': left_value,
                'left_is_percent': left_is_percent,
                'left_skip': left_skip,
                'right_value': right_value,
                'right_is_percent': right_is_percent,
                'right_skip': right_skip
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
                print(f"  Left: unchanged")
            
            if not right_skip:
                if right_is_percent:
                    print(f"  Right: {right_value:+.1f}%")
                else:
                    print(f"  Right: {right_value:+.0f} units")
            else:
                print(f"  Right: unchanged")
        
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
                
                old_lsb = layer.LSB
                old_rsb = layer.RSB
                
                # Adjust left bearing
                if not settings['left_skip']:
                    if settings['left_is_percent']:
                        adjustment = old_lsb * (settings['left_value'] / 100.0)
                        layer.LSB = old_lsb + adjustment
                    else:
                        layer.LSB = old_lsb + settings['left_value']
                
                # Adjust right bearing
                if not settings['right_skip']:
                    if settings['right_is_percent']:
                        adjustment = old_rsb * (settings['right_value'] / 100.0)
                        layer.RSB = old_rsb + adjustment
                    else:
                        layer.RSB = old_rsb + settings['right_value']
                
                new_lsb = layer.LSB
                new_rsb = layer.RSB
                
                print(f"  {master.name}: LSB {old_lsb:.0f}→{new_lsb:.0f}, RSB {old_rsb:.0f}→{new_rsb:.0f}")
        
        print("\n" + "="*60)
        print(f"Adjusted {len(self.selected_glyphs)} glyph(s)")
        print("="*60 + "\n")
        
        self.w.close()
        
        Message("Success", 
            f"Side bearings adjusted for {len(self.selected_glyphs)} glyph(s) across selected masters.")

# Run the script
SideBearingAdjuster()