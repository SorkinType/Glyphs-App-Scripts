#MenuTitle: Randomize Kerning Values
# -*- coding: utf-8 -*-
"""
Make pseudo-random changes to kerning values in all masters.
Values can increase or decrease by a small amount.
Approximately 1 in 7 values will remain unchanged.

Save this file in your Glyphs Scripts folder:
~/Library/Application Support/Glyphs 3/Scripts/
"""

import vanilla
import random

class KerningRandomizer:
    
    def __init__(self):
        self.font = Glyphs.font
        
        if not self.font:
            Message("No Font Open", "Please open a font first.")
            return
        
        # Count existing kerning pairs
        self.total_pairs = self.count_kerning_pairs()
        
        # Window setup
        self.w = vanilla.FloatingWindow((400, 280), "Randomize Kerning Values")
        
        y = 10
        
        # Info about font
        self.w.fontInfo = vanilla.TextBox((10, y, -10, 40), 
            f"Font: {self.font.familyName}\n"
            f"Masters: {len(self.font.masters)} | "
            f"Total kerning pairs: {self.total_pairs}")
        y += 50
        
        # Maximum change amount
        self.w.maxChangeLabel = vanilla.TextBox((10, y, 180, 20), 
            "Maximum change amount:")
        self.w.maxChangeField = vanilla.EditText((200, y, 60, 22), "2")
        self.w.maxChangeInfo = vanilla.TextBox((270, y, -10, 40), 
            "Values will change by\n±1 to ±this amount", 
            sizeStyle="small")
        y += 50
        
        # Unchanged probability
        self.w.unchangedLabel = vanilla.TextBox((10, y, 180, 20), 
            "Keep unchanged (1 in X):")
        self.w.unchangedField = vanilla.EditText((200, y, 60, 22), "7")
        self.w.unchangedInfo = vanilla.TextBox((270, y, -10, 40), 
            "1 in 7 means ~14%\nwill stay the same", 
            sizeStyle="small")
        y += 50
        
        # Random seed
        self.w.seedCheck = vanilla.CheckBox((10, y, 120, 20), 
            "Use random seed:", value=False, callback=self.toggleSeed)
        self.w.seedField = vanilla.EditText((130, y, 80, 22), "12345")
        self.w.seedField.enable(False)
        self.w.seedInfo = vanilla.TextBox((220, y, -10, 40), 
            "For repeatable results", 
            sizeStyle="small")
        y += 40
        
        # Preview
        self.w.previewLabel = vanilla.TextBox((10, y, -10, 20), 
            "", sizeStyle="small")
        y += 25
        
        # Buttons
        self.w.cancelButton = vanilla.Button((10, -30, 120, 20), 
            "Cancel", callback=self.cancel)
        self.w.randomizeButton = vanilla.Button((-130, -30, 120, 20), 
            "Randomize", callback=self.randomize)
        
        self.w.setDefaultButton(self.w.randomizeButton)
        self.updatePreview()
        self.w.open()
    
    def toggleSeed(self, sender):
        """Enable/disable seed field."""
        self.w.seedField.enable(sender.get())
    
    def count_kerning_pairs(self):
        """Count total kerning pairs across all masters."""
        total = 0
        for master in self.font.masters:
            if master.id in self.font.kerning:
                total += len(self.font.kerning[master.id])
        return total
    
    def updatePreview(self):
        """Update the preview text."""
        try:
            max_change = int(self.w.maxChangeField.get())
            unchanged_prob = int(self.w.unchangedField.get())
            
            keep_pct = int(100.0 / unchanged_prob)
            change_pct = 100 - keep_pct
            
            self.w.previewLabel.set(
                f"Will modify ~{change_pct}% of {self.total_pairs} kerning pairs "
                f"(~{int(self.total_pairs * change_pct / 100)} pairs)"
            )
        except:
            self.w.previewLabel.set("")
    
    def cancel(self, sender):
        self.w.close()
    
    def randomize_value(self, original_value, max_change, unchanged_prob):
        """
        Randomize a single kerning value.
        
        Args:
            original_value: The original kerning value
            max_change: Maximum amount to change (positive integer)
            unchanged_prob: 1 in X chance to leave unchanged
        
        Returns:
            The new kerning value
        """
        # 1 in X chance to leave unchanged
        if random.randint(1, unchanged_prob) == 1:
            return original_value
        
        # Generate random change from -max_change to +max_change (excluding 0)
        change = random.randint(-max_change, max_change)
        if change == 0:
            # If we got 0, pick either -1 or +1
            change = random.choice([-1, 1])
        
        new_value = original_value + change
        
        return new_value
    
    def randomize(self, sender):
        print("\n" + "="*60)
        print("RANDOMIZING KERNING VALUES")
        print("="*60)
        
        if not self.font:
            self.w.previewLabel.set("Error: No font is open")
            return
        
        try:
            max_change = int(self.w.maxChangeField.get())
            unchanged_prob = int(self.w.unchangedField.get())
            
            if max_change < 1:
                raise ValueError("Maximum change must be at least 1")
            if unchanged_prob < 1:
                raise ValueError("Unchanged probability must be at least 1")
            
        except ValueError as e:
            self.w.previewLabel.set(f"Error: {e}")
            return
        
        # Set random seed if requested
        if self.w.seedCheck.get():
            try:
                seed = int(self.w.seedField.get())
                random.seed(seed)
                print(f"Using random seed: {seed}")
            except ValueError:
                self.w.previewLabel.set("Error: Seed must be a number")
                return
        
        print(f"Maximum change: ±{max_change}")
        print(f"Unchanged probability: 1 in {unchanged_prob}")
        print(f"Masters: {len(self.font.masters)}")
        print("")
        
        total_pairs = 0
        changed_pairs = 0
        unchanged_pairs = 0
        
        # Process each master
        for master in self.font.masters:
            master_name = master.name if master.name else master.id
            print(f"\nMaster: {master_name}")
            
            if master.id not in self.font.kerning:
                print(f"  No kerning data")
                continue
            
            kerning_dict = self.font.kerning[master.id]
            master_changed = 0
            master_unchanged = 0
            
            # Process each kerning pair
            # We need to iterate over a copy of keys because we're modifying the dict
            kerning_pairs = list(kerning_dict.keys())
            
            for left_glyph in kerning_pairs:
                if left_glyph not in kerning_dict:
                    continue
                    
                right_dict = kerning_dict[left_glyph]
                right_glyphs = list(right_dict.keys())
                
                for right_glyph in right_glyphs:
                    if right_glyph not in right_dict:
                        continue
                    
                    original_value = right_dict[right_glyph]
                    new_value = self.randomize_value(original_value, max_change, unchanged_prob)
                    
                    # Update the kerning value
                    kerning_dict[left_glyph][right_glyph] = new_value
                    
                    total_pairs += 1
                    
                    if new_value != original_value:
                        changed_pairs += 1
                        master_changed += 1
                    else:
                        unchanged_pairs += 1
                        master_unchanged += 1
            
            print(f"  Pairs: {master_changed + master_unchanged}")
            print(f"  Changed: {master_changed}")
            print(f"  Unchanged: {master_unchanged}")
        
        # Show results
        print(f"\n{'='*60}")
        print(f"Total pairs processed: {total_pairs}")
        print(f"Changed: {changed_pairs} ({100.0 * changed_pairs / total_pairs:.1f}%)")
        print(f"Unchanged: {unchanged_pairs} ({100.0 * unchanged_pairs / total_pairs:.1f}%)")
        print(f"{'='*60}")
        
        Message("Randomization Complete", 
            f"Processed {total_pairs} kerning pairs.\n"
            f"Changed: {changed_pairs} ({100.0 * changed_pairs / total_pairs:.1f}%)\n"
            f"Unchanged: {unchanged_pairs} ({100.0 * unchanged_pairs / total_pairs:.1f}%)")
        
        self.w.close()


# Main execution
def main():
    # Check if a font is open
    font = Glyphs.font
    if not font:
        Message("No Font Open", "Please open a font first.")
        return
    
    # Check if font has kerning
    has_kerning = False
    for master in font.masters:
        if master.id in font.kerning and len(font.kerning[master.id]) > 0:
            has_kerning = True
            break
    
    if not has_kerning:
        Message("No Kerning Data", 
            "This font has no kerning data to randomize.")
        return
    
    # Show dialog
    KerningRandomizer()


# Run the script
main()