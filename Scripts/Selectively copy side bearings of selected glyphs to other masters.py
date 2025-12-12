#MenuTitle: Selectively copy side bearings of selected glyphs to other masters
# -*- coding: utf-8 -*-
"""
Copy sidebearings from selected glyphs in the current master to other masters.

Save this file in your Glyphs Scripts folder:
~/Library/Application Support/Glyphs 3/Scripts/

Usage:
1. Select glyphs in the font window or edit view
2. Run this script from Scripts menu
3. Choose which masters to copy the sidebearings to
4. Click "Copy Sidebearings"
"""

from vanilla import Window, TextBox, Button, CheckBox, VerticalStackGroup


class CopySidebearingsDialog:
    
    def __init__(self):
        self.font = Glyphs.font
        
        # Get current master (from active edit view or first selected layer)
        self.source_master = None
        if self.font.currentTab:
            self.source_master = self.font.currentTab.graphicView().activeLayer().master
        elif self.font.selectedLayers:
            self.source_master = self.font.selectedLayers[0].master
        
        if not self.source_master:
            self.source_master = self.font.masters[0]
        
        # Get selected glyphs
        self.selected_glyphs = self.get_selected_glyphs()
        
        # Calculate window height based on number of masters
        num_masters = len(self.font.masters)
        window_height = 180 + (num_masters * 25)
        
        self.w = Window((400, window_height), "Copy Sidebearings to Masters")
        
        y = 10
        
        # Info about source
        self.w.sourceLabel = TextBox((10, y, -10, 20), f"Source master: {self.source_master.name}")
        y += 25
        
        glyph_names = ", ".join([g.name for g in self.selected_glyphs[:5]])
        if len(self.selected_glyphs) > 5:
            glyph_names += f"... (+{len(self.selected_glyphs) - 5} more)"
        
        self.w.glyphsLabel = TextBox((10, y, -10, 40), 
            f"Selected glyphs ({len(self.selected_glyphs)}): {glyph_names}", 
            sizeStyle="small")
        y += 50
        
        # Target masters selection
        self.w.targetLabel = TextBox((10, y, -10, 20), "Copy sidebearings to:")
        y += 25
        
        # Create checkboxes for each master (except source)
        self.master_checkboxes = {}
        
        for master in self.font.masters:
            if master.id != self.source_master.id:
                cb = CheckBox((20, y, -10, 20), master.name, value=True)
                self.master_checkboxes[master.id] = cb
                setattr(self.w, f"master_{master.id}", cb)
                y += 25
        
        if not self.master_checkboxes:
            self.w.noMastersLabel = TextBox((20, y, -10, 20), 
                "No other masters available", 
                sizeStyle="small")
            y += 25
        
        y += 10
        
        # Options
        self.w.leftCheckbox = CheckBox((10, y, 100, 20), "Left (LSB)", value=True)
        self.w.rightCheckbox = CheckBox((120, y, 100, 20), "Right (RSB)", value=True)
        self.w.widthCheckbox = CheckBox((230, y, 150, 20), "Width", value=False)
        y += 30
        
        # Info text
        self.w.info = TextBox((10, y, -10, 20), "", sizeStyle="small")
        y += 25
        
        # Buttons
        self.w.cancelButton = Button((10, -30, 120, 20), "Cancel", callback=self.cancel)
        self.w.copyButton = Button((-130, -30, 120, 20), "Copy Sidebearings", callback=self.copy_sidebearings)
        
        self.w.setDefaultButton(self.w.copyButton)
        self.w.open()
    
    def get_selected_glyphs(self):
        """Get list of unique selected glyphs."""
        glyphs = []
        
        # Try to get from selected layers
        if self.font.selectedLayers:
            glyphs = list(set([layer.parent for layer in self.font.selectedLayers if layer.parent]))
        
        return glyphs
    
    def cancel(self, sender):
        self.w.close()
    
    def copy_sidebearings(self, sender):
        print("\n" + "="*60)
        print("COPY SIDEBEARINGS TO MASTERS")
        print("="*60)
        
        if not self.font:
            self.w.info.set("Error: No font is open")
            return
        
        if not self.selected_glyphs:
            self.w.info.set("Error: No glyphs selected")
            return
        
        # Get target masters
        target_masters = []
        for master_id, checkbox in self.master_checkboxes.items():
            if checkbox.get():
                master = self.font.masters[master_id]
                target_masters.append(master)
        
        if not target_masters:
            self.w.info.set("Error: Please select at least one target master")
            return
        
        # Get options
        copy_left = self.w.leftCheckbox.get()
        copy_right = self.w.rightCheckbox.get()
        copy_width = self.w.widthCheckbox.get()
        
        if not copy_left and not copy_right and not copy_width:
            self.w.info.set("Error: Please select at least one option (LSB/RSB/Width)")
            return
        
        print(f"\nSource master: {self.source_master.name}")
        print(f"Target masters: {', '.join([m.name for m in target_masters])}")
        print(f"Copy LSB: {copy_left}, RSB: {copy_right}, Width: {copy_width}")
        print(f"Glyphs to process: {len(self.selected_glyphs)}")
        
        # Process glyphs
        total_changes = 0
        
        for glyph in self.selected_glyphs:
            print(f"\n{glyph.name}:")
            
            # Get source layer
            source_layer = glyph.layers[self.source_master.id]
            
            if not source_layer:
                print(f"  ⚠ No layer found in source master")
                continue
            
            source_lsb = source_layer.LSB
            source_rsb = source_layer.RSB
            source_width = source_layer.width
            
            print(f"  Source: LSB={source_lsb}, RSB={source_rsb}, Width={source_width}")
            
            # Apply to target masters
            for target_master in target_masters:
                target_layer = glyph.layers[target_master.id]
                
                if not target_layer:
                    print(f"  ⚠ No layer found in {target_master.name}")
                    continue
                
                changes_made = False
                
                if copy_width:
                    # Copy width directly
                    old_width = target_layer.width
                    target_layer.width = source_width
                    print(f"  {target_master.name}: Width {old_width} → {source_width}")
                    changes_made = True
                else:
                    # Copy sidebearings
                    if copy_left:
                        old_lsb = target_layer.LSB
                        target_layer.LSB = source_lsb
                        print(f"  {target_master.name}: LSB {old_lsb} → {source_lsb}")
                        changes_made = True
                    
                    if copy_right:
                        old_rsb = target_layer.RSB
                        target_layer.RSB = source_rsb
                        print(f"  {target_master.name}: RSB {old_rsb} → {source_rsb}")
                        changes_made = True
                
                if changes_made:
                    total_changes += 1
        
        # Show results
        print(f"\n{'='*60}")
        print(f"Total layer changes: {total_changes}")
        print(f"{'='*60}")
        
        if total_changes > 0:
            msg = f"✓ Copied sidebearings to {total_changes} layers"
            Message("Success", msg)
            print(f"\n✓ SUCCESS: {msg}")
            self.w.close()
        else:
            msg = "No changes were made"
            self.w.info.set(msg)
            print(f"\n✗ {msg}")


# Main execution
def main():
    # Check if a font is open
    font = Glyphs.font
    if not font:
        Message("No Font Open", "Please open a font first.")
        return
    
    # Check if there are multiple masters
    if len(font.masters) < 2:
        Message("Only One Master", "This font only has one master. You need at least two masters to copy sidebearings between them.")
        return
    
    # Check if glyphs are selected
    if not font.selectedLayers:
        Message("No Selection", "Please select glyphs first.")
        return
    
    # Show dialog
    CopySidebearingsDialog()


# Run the script
main()