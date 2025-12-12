#MenuTitle: Recolor Glyph Parts
# -*- coding: utf-8 -*-
"""
Change color of paths/components in font from one color to another.
Uses a "pick from selection" approach to capture the exact target color.

Save this file in your Glyphs Scripts folder:
~/Library/Application Support/Glyphs 3/Scripts/

Usage:
1. Select a single shape (path or component) with the target color
2. Run this script from Scripts menu
3. The target color will be auto-detected
4. Enter the new RGB color to apply
5. All matching shapes in the font will be recolored
"""

from vanilla import Window, TextBox, EditText, Button, CheckBox
from AppKit import NSColor


def rgb_to_nscolor(r, g, b, a=1.0):
    """Convert RGB values (0-255) to NSColor."""
    return NSColor.colorWithCalibratedRed_green_blue_alpha_(
        r / 255.0,
        g / 255.0,
        b / 255.0,
        a
    )


def nscolor_to_rgb(nscolor):
    """Convert NSColor to RGB tuple (0-255) for display."""
    if nscolor is None:
        return None
    
    try:
        # The color is already in calibrated RGB space, just get components directly
        r = int(round(nscolor.redComponent() * 255))
        g = int(round(nscolor.greenComponent() * 255))
        b = int(round(nscolor.blueComponent() * 255))
        
        return (r, g, b)
    except Exception as e:
        print(f"  Error converting NSColor to RGB: {e}")
        return None


def get_fill_color(shape):
    """
    Extract fillColor from a shape (path or component).
    Returns NSColor object or None.
    """
    if not hasattr(shape, 'attributes') or not shape.attributes:
        return None
    
    fill_color = shape.attributes.get('fillColor')
    
    # fillColor might be stored as NSColor object or needs to be retrieved differently
    if fill_color and isinstance(fill_color, NSColor):
        return fill_color
    
    return fill_color


def colors_match_exact(color1_obj, color2_obj):
    """
    Compare two NSColor objects for exact match.
    """
    if color1_obj is None or color2_obj is None:
        return False
    
    try:
        # Get components directly - they're already in calibrated RGB
        tolerance = 0.002  # About 0.5 in 0-255 scale
        
        return (abs(color1_obj.redComponent() - color2_obj.redComponent()) < tolerance and
                abs(color1_obj.greenComponent() - color2_obj.greenComponent()) < tolerance and
                abs(color1_obj.blueComponent() - color2_obj.blueComponent()) < tolerance)
    except Exception as e:
        print(f"Error comparing colors: {e}")
        return False


def get_color_from_shape(layer):
    """
    Extract fillColor from the first colored path or component in a layer.
    Returns (NSColor object, description string) or (None, error message).
    """
    print(f"\n{'='*60}")
    print(f"Examining layer: {layer.name if hasattr(layer, 'name') else 'unnamed'}")
    print(f"Paths: {len(layer.paths)}, Components: {len(layer.components)}")
    
    # Check paths
    for i, path in enumerate(layer.paths):
        print(f"\n  Path {i}:")
        
        if hasattr(path, 'attributes') and path.attributes:
            fill_color = path.attributes.get('fillColor')
            print(f"    fillColor: {fill_color}")
            
            if fill_color:
                # fillColor is an NSColor object
                rgb = nscolor_to_rgb(fill_color)
                print(f"    RGB: {rgb}")
                
                if rgb:
                    return (fill_color, f"Path {i}: RGB({rgb[0]}, {rgb[1]}, {rgb[2]})")
        else:
            print(f"    No attributes")
    
    # Check components
    for i, component in enumerate(layer.components):
        print(f"\n  Component {i} ({component.componentName}):")
        
        if hasattr(component, 'attributes') and component.attributes:
            fill_color = component.attributes.get('fillColor')
            print(f"    fillColor: {fill_color}")
            
            if fill_color:
                rgb = nscolor_to_rgb(fill_color)
                print(f"    RGB: {rgb}")
                
                if rgb:
                    return (fill_color, f"Component {i} ({component.componentName}): RGB({rgb[0]}, {rgb[1]}, {rgb[2]})")
        else:
            print(f"    No attributes")
    
    print(f"\n{'='*60}\n")
    return (None, "No colored shapes found")


def recolor_shape(shape, target_color_obj, new_color_obj):
    """
    Check if a shape matches target fillColor and recolor if it does.
    Returns True if recolored, False otherwise.
    """
    if not hasattr(shape, 'attributes') or not shape.attributes:
        return False
    
    current_color = shape.attributes.get('fillColor')
    
    if not current_color:
        return False
    
    # Check if it matches target
    if colors_match_exact(current_color, target_color_obj):
        try:
            shape.attributes['fillColor'] = new_color_obj
            return True
        except Exception as e:
            print(f"    Error setting fillColor: {e}")
            return False
    
    return False


def recolor_layer(layer, target_color_obj, new_color_obj):
    """Recolor all shapes in a layer that match the target color."""
    changes = 0
    
    # Process paths
    for path in layer.paths:
        if recolor_shape(path, target_color_obj, new_color_obj):
            changes += 1
    
    # Process components
    for component in layer.components:
        if recolor_shape(component, target_color_obj, new_color_obj):
            changes += 1
    
    return changes


class RecolorDialog:
    
    def __init__(self, target_color_obj, target_description):
        self.font = Glyphs.font
        self.target_color_obj = target_color_obj
        self.target_rgb = nscolor_to_rgb(target_color_obj)
        
        self.w = Window((420, 220), "Recolor Glyph Parts")
        
        y = 10
        
        # Target color (detected)
        self.w.targetLabel = TextBox((10, y, -10, 20), "Target color (detected from selection):")
        y += 25
        self.w.targetInfo = TextBox((10, y, -10, 40), target_description, sizeStyle="small")
        
        y += 50
        
        # New color
        self.w.newLabel = TextBox((10, y, 150, 20), "New color (R, G, B):")
        y += 25
        self.w.newR = EditText((10, y, 60, 22), "0")
        self.w.newG = EditText((80, y, 60, 22), "0")
        self.w.newB = EditText((150, y, 60, 22), "255")
        self.w.newPreview = TextBox((220, y, -10, 22), f"← Enter RGB values (0-255)")
        
        y += 35
        
        # Options
        self.w.allGlyphs = CheckBox((10, y, -10, 20), "Apply to all glyphs in font", value=True)
        
        y += 30
        
        # Info
        self.w.info = TextBox((10, y, -10, 20), "", sizeStyle="small")
        
        y += 30
        
        # Buttons
        self.w.cancelButton = Button((10, -30, 120, 20), "Cancel", callback=self.cancel)
        self.w.recolorButton = Button((-130, -30, 120, 20), "Recolor", callback=self.recolor)
        
        self.w.setDefaultButton(self.w.recolorButton)
        self.w.open()
    
    def cancel(self, sender):
        self.w.close()
    
    def parse_rgb(self):
        """Parse RGB values from text fields."""
        try:
            r = int(self.w.newR.get())
            g = int(self.w.newG.get())
            b = int(self.w.newB.get())
            
            if not all(0 <= v <= 255 for v in [r, g, b]):
                raise ValueError("RGB values must be between 0-255")
            
            return (r, g, b)
        except ValueError as e:
            raise ValueError(f"Invalid RGB values: {e}")
    
    def recolor(self, sender):
        print("\n" + "="*60)
        print("RECOLOR GLYPH PARTS")
        print("="*60)
        
        if not self.font:
            self.w.info.set("Error: No font is open")
            return
        
        try:
            # Parse new color
            new_rgb = self.parse_rgb()
            new_color_obj = rgb_to_nscolor(new_rgb[0], new_rgb[1], new_rgb[2])
            
            print(f"\nTarget RGB: {self.target_rgb}")
            print(f"New RGB: {new_rgb}")
            
            # Determine which glyphs to process
            if self.w.allGlyphs.get():
                glyphs_to_process = list(self.font.glyphs)
                print(f"\nProcessing all {len(glyphs_to_process)} glyphs in font")
            else:
                selected_layers = self.font.selectedLayers
                glyphs_to_process = list(set([layer.parent for layer in selected_layers if layer.parent]))
                print(f"\nProcessing {len(glyphs_to_process)} selected glyphs")
            
            if not glyphs_to_process:
                self.w.info.set("Error: No glyphs to process")
                return
            
            # Process glyphs
            total_changes = 0
            glyphs_changed = 0
            
            for glyph in glyphs_to_process:
                glyph_changes = 0
                
                # Process all masters
                for master in self.font.masters:
                    layer = glyph.layers[master.id]
                    if layer:
                        changes = recolor_layer(layer, self.target_color_obj, new_color_obj)
                        glyph_changes += changes
                        total_changes += changes
                
                if glyph_changes > 0:
                    glyphs_changed += 1
                    print(f"  {glyph.name}: {glyph_changes} shapes recolored")
            
            # Show results
            print(f"\n{'='*60}")
            print(f"Total shapes recolored: {total_changes}")
            print(f"Glyphs affected: {glyphs_changed}")
            print(f"{'='*60}")
            
            if total_changes > 0:
                msg = f"✓ Recolored {total_changes} shapes in {glyphs_changed} glyphs"
                Message("Success", msg)
                self.w.close()
            else:
                msg = "No matching shapes found"
                self.w.info.set(msg)
                print(f"\n{msg}")
        
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.w.info.set(error_msg)
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()


# Main execution
def main():
    # Check if a font is open
    font = Glyphs.font
    if not font:
        Message("No Font Open", "Please open a font first.")
        return
    
    # Check if a layer is selected
    selected_layers = font.selectedLayers
    if not selected_layers:
        Message("No Selection", "Please select a shape with the target color.")
        return
    
    # Get target color from first selected layer
    target_color_obj = None
    target_description = None
    
    for layer in selected_layers:
        target_color_obj, target_description = get_color_from_shape(layer)
        if target_color_obj:
            break
    
    if not target_color_obj:
        Message("No Color Found", "The selected shape doesn't have a fillColor assigned.\n\nPlease select a colored path or component.")
        return
    
    # Show dialog
    RecolorDialog(target_color_obj, target_description)


# Run the script
main()