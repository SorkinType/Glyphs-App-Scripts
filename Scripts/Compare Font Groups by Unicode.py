#MenuTitle: Compare Font Groups by Unicode
# -*- coding: utf-8 -*-
"""
Compare two groups of Glyphs font files by Unicode values and mark glyphs based on presence:
- Light Blue: Glyph's unicode exists in both groups
- Red: Glyph's unicode exists only in Group A
- Yellow: Glyph's unicode exists only in Group B
- Uncolored: Glyphs without unicode values

Save this file in your Glyphs Scripts folder:
~/Library/Application Support/Glyphs 3/Scripts/

Usage:
1. Open all the font files you want to compare
2. Run this script from Scripts menu
3. Select which fonts belong to Group A and Group B
4. All glyphs in all fonts will be colored based on unicode comparison
"""

from vanilla import Window, Button, TextBox, CheckBox, HorizontalLine

class FontGroupComparator:
    def __init__(self):
        self.fonts = Glyphs.fonts
        
        if len(self.fonts) < 2:
            Message("Not Enough Fonts", "Please open at least 2 font files before running this script.")
            return
        
        # Calculate window height based on number of fonts
        checkbox_height = 22
        base_height = 230  # Increased base for header, instructions, buttons, and padding
        fonts_section_height = len(self.fonts) * checkbox_height * 2  # Both groups
        window_height = base_height + fonts_section_height
        
        # Ensure minimum and maximum reasonable heights
        window_height = max(400, min(window_height, 900))
        
        # Create window
        self.w = Window((500, window_height), "Compare Font Groups by Unicode")
        
        y = 20
        
        # Instructions
        self.w.instructions = TextBox((20, y, -20, 40), 
            "Select which fonts belong to each group, then click Compare.\nComparison is based on Unicode values.")
        y += 50
        
        # Group A header
        self.w.groupALabel = TextBox((20, y, 200, 20), "Group A:", sizeStyle="small")
        self.w.groupASelectAll = Button((230, y-2, 100, 20), "Select All", 
            callback=self.selectAllGroupA, sizeStyle="small")
        self.w.groupADeselectAll = Button((335, y-2, 100, 20), "Deselect All", 
            callback=self.deselectAllGroupA, sizeStyle="small")
        y += 25
        
        # Group A checkboxes
        self.groupA_checkboxes = []
        for i, font in enumerate(self.fonts):
            font_name = f"{font.familyName} ({len(font.glyphs)} glyphs)"
            cb = CheckBox((40, y, -20, 20), font_name, value=False, sizeStyle="small")
            setattr(self.w, f"groupA_{i}", cb)
            self.groupA_checkboxes.append(cb)
            y += checkbox_height
        
        y += 10
        self.w.line1 = HorizontalLine((20, y, -20, 1))
        y += 15
        
        # Group B header
        self.w.groupBLabel = TextBox((20, y, 200, 20), "Group B:", sizeStyle="small")
        self.w.groupBSelectAll = Button((230, y-2, 100, 20), "Select All", 
            callback=self.selectAllGroupB, sizeStyle="small")
        self.w.groupBDeselectAll = Button((335, y-2, 100, 20), "Deselect All", 
            callback=self.deselectAllGroupB, sizeStyle="small")
        y += 25
        
        # Group B checkboxes
        self.groupB_checkboxes = []
        for i, font in enumerate(self.fonts):
            font_name = f"{font.familyName} ({len(font.glyphs)} glyphs)"
            cb = CheckBox((40, y, -20, 20), font_name, value=False, sizeStyle="small")
            setattr(self.w, f"groupB_{i}", cb)
            self.groupB_checkboxes.append(cb)
            y += checkbox_height
        
        y += 20
        self.w.line2 = HorizontalLine((20, y, -20, 1))
        y += 20
        
        # Compare button
        self.w.compareButton = Button((20, y, -20, 30), "Compare Groups", 
            callback=self.compare)
        
        self.w.open()
    
    def selectAllGroupA(self, sender):
        for cb in self.groupA_checkboxes:
            cb.set(True)
    
    def deselectAllGroupA(self, sender):
        for cb in self.groupA_checkboxes:
            cb.set(False)
    
    def selectAllGroupB(self, sender):
        for cb in self.groupB_checkboxes:
            cb.set(True)
    
    def deselectAllGroupB(self, sender):
        for cb in self.groupB_checkboxes:
            cb.set(False)
    
    def compare(self, sender):
        # Get selected fonts for each group
        groupA_fonts = []
        groupB_fonts = []
        
        for i, font in enumerate(self.fonts):
            if self.groupA_checkboxes[i].get():
                groupA_fonts.append(font)
            if self.groupB_checkboxes[i].get():
                groupB_fonts.append(font)
        
        # Validate selection
        if len(groupA_fonts) == 0 or len(groupB_fonts) == 0:
            Message("Invalid Selection", 
                "Please select at least one font for both Group A and Group B.")
            return
        
        # Run comparison
        self.w.close()
        self.compare_groups(groupA_fonts, groupB_fonts)
    
    def get_unicode_value(self, glyph):
        """Get the unicode value from a glyph. Returns None if no unicode."""
        if glyph.unicode:
            return glyph.unicode
        return None
    
    def compare_groups(self, groupA_fonts, groupB_fonts):
        """Compare two groups of fonts by unicode and color all glyphs accordingly."""
        
        print("\n" + "="*60)
        print("COMPARING FONT GROUPS BY UNICODE")
        print("="*60)
        print(f"\nGroup A ({len(groupA_fonts)} fonts):")
        for font in groupA_fonts:
            print(f"  - {font.familyName} ({len(font.glyphs)} glyphs)")
        
        print(f"\nGroup B ({len(groupB_fonts)} fonts):")
        for font in groupB_fonts:
            print(f"  - {font.familyName} ({len(font.glyphs)} glyphs)")
        print("="*60 + "\n")
        
        # Define color indices
        LIGHT_BLUE = 6    # Glyphs with unicode in both groups
        RED = 0           # Glyphs with unicode only in Group A
        YELLOW = 3        # Glyphs with unicode only in Group B
        
        # Collect all unicode values from each group
        groupA_unicodes = set()
        groupA_glyphs_without_unicode = 0
        for font in groupA_fonts:
            for glyph in font.glyphs:
                unicode_val = self.get_unicode_value(glyph)
                if unicode_val:
                    groupA_unicodes.add(unicode_val)
                else:
                    groupA_glyphs_without_unicode += 1
        
        groupB_unicodes = set()
        groupB_glyphs_without_unicode = 0
        for font in groupB_fonts:
            for glyph in font.glyphs:
                unicode_val = self.get_unicode_value(glyph)
                if unicode_val:
                    groupB_unicodes.add(unicode_val)
                else:
                    groupB_glyphs_without_unicode += 1
        
        # Find shared and unique unicode values
        shared_unicodes = groupA_unicodes & groupB_unicodes
        only_in_A = groupA_unicodes - groupB_unicodes
        only_in_B = groupB_unicodes - groupA_unicodes
        
        print(f"Unique unicodes in Group A: {len(groupA_unicodes)} ({groupA_glyphs_without_unicode} glyphs without unicode)")
        print(f"Unique unicodes in Group B: {len(groupB_unicodes)} ({groupB_glyphs_without_unicode} glyphs without unicode)")
        print(f"Shared unicodes: {len(shared_unicodes)}")
        print(f"Only in Group A: {len(only_in_A)}")
        print(f"Only in Group B: {len(only_in_B)}")
        print()
        
        # Color all glyphs in all fonts based on which group they belong to
        print("\n" + "="*60)
        print("COLORING GLYPHS")
        print("="*60)
        
        total_colored = 0
        total_uncolored = 0
        
        # Color Group A fonts
        for font in groupA_fonts:
            print(f"\nColoring glyphs in Group A: {font.familyName}")
            blue_count = 0
            red_count = 0
            no_unicode_count = 0
            
            for glyph in font.glyphs:
                unicode_val = self.get_unicode_value(glyph)
                
                if unicode_val is None:
                    # No unicode - leave uncolored
                    glyph.color = None
                    no_unicode_count += 1
                elif unicode_val in shared_unicodes:
                    # Unicode exists in both groups
                    glyph.color = LIGHT_BLUE
                    blue_count += 1
                else:
                    # Unicode exists only in Group A
                    glyph.color = RED
                    red_count += 1
            
            print(f"  Light Blue (shared unicode): {blue_count}")
            print(f"  Red (only in Group A): {red_count}")
            print(f"  Uncolored (no unicode): {no_unicode_count}")
            total_colored += blue_count + red_count
            total_uncolored += no_unicode_count
        
        # Color Group B fonts
        for font in groupB_fonts:
            # Skip if already processed in Group A
            if font in groupA_fonts:
                continue
                
            print(f"\nColoring glyphs in Group B: {font.familyName}")
            blue_count = 0
            yellow_count = 0
            no_unicode_count = 0
            
            for glyph in font.glyphs:
                unicode_val = self.get_unicode_value(glyph)
                
                if unicode_val is None:
                    # No unicode - leave uncolored
                    glyph.color = None
                    no_unicode_count += 1
                elif unicode_val in shared_unicodes:
                    # Unicode exists in both groups
                    glyph.color = LIGHT_BLUE
                    blue_count += 1
                else:
                    # Unicode exists only in Group B
                    glyph.color = YELLOW
                    yellow_count += 1
            
            print(f"  Light Blue (shared unicode): {blue_count}")
            print(f"  Yellow (only in Group B): {yellow_count}")
            print(f"  Uncolored (no unicode): {no_unicode_count}")
            total_colored += blue_count + yellow_count
            total_uncolored += no_unicode_count
        
        # Show summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Total unique unicodes in Group A:  {len(groupA_unicodes)}")
        print(f"Total unique unicodes in Group B:  {len(groupB_unicodes)}")
        print(f"Shared unicode values:             {len(shared_unicodes)}")
        print(f"Only in Group A:                   {len(only_in_A)}")
        print(f"Only in Group B:                   {len(only_in_B)}")
        print(f"{'='*60}")
        print(f"Total glyphs colored:              {total_colored}")
        print(f"Total glyphs uncolored (no uni):   {total_uncolored}")
        print(f"{'='*60}\n")
        
        if only_in_A:
            print("\nUnicode values only in Group A:")
            for uni in sorted(only_in_A)[:20]:  # Show first 20
                try:
                    char = chr(int(uni, 16))
                    print(f"  - U+{uni}: {char}")
                except:
                    print(f"  - U+{uni}")
            if len(only_in_A) > 20:
                print(f"  ... and {len(only_in_A) - 20} more")
            print()
        
        if only_in_B:
            print("\nUnicode values only in Group B:")
            for uni in sorted(only_in_B)[:20]:  # Show first 20
                try:
                    char = chr(int(uni, 16))
                    print(f"  - U+{uni}: {char}")
                except:
                    print(f"  - U+{uni}")
            if len(only_in_B) > 20:
                print(f"  ... and {len(only_in_B) - 20} more")
            print()
        
        # Show success message
        Message("Comparison Complete", 
                f"Group A: {len(groupA_fonts)} fonts ({len(groupA_unicodes)} unicodes)\n"
                f"Group B: {len(groupB_fonts)} fonts ({len(groupB_unicodes)} unicodes)\n\n"
                f"● {len(shared_unicodes)} unicodes in BOTH groups (light blue)\n"
                f"● {len(only_in_A)} unicodes ONLY in Group A (red)\n"
                f"● {len(only_in_B)} unicodes ONLY in Group B (yellow)\n"
                f"● {total_uncolored} glyphs without unicode (uncolored)")

# Run the script
FontGroupComparator()