#MenuTitle: Selected Glyph Names change to all lowercase
# -*- coding: utf-8 -*-
__doc__ = """
Renames selected glyphs so their names are all lowercase.
E.g. 'A' becomes 'a', 'Agrave' becomes 'agrave'.
"""

font = Glyphs.font

if not font:
    Message("No font open.", "Error")
else:
    selected_glyphs = [layer.parent for layer in font.selectedLayers]

    if not selected_glyphs:
        Message("No glyphs selected.", "Error")
    else:
        renamed = []
        skipped = []

        font.disableUpdateInterface()
        try:
            for glyph in selected_glyphs:
                old_name = glyph.name
                new_name = old_name.lower()

                if old_name == new_name:
                    skipped.append(old_name)
                    continue

                # Check for name collision with an existing glyph
                if font.glyphs[new_name] and font.glyphs[new_name] != glyph:
                    skipped.append(f"{old_name} → {new_name} (name already exists)")
                    continue

                glyph.name = new_name
                renamed.append(f"{old_name} → {new_name}")
        finally:
            font.enableUpdateInterface()

        # Build report
        lines = []
        if renamed:
            lines.append(f"Renamed {len(renamed)} glyph(s):")
            lines.extend(f"  {r}" for r in renamed)
        if skipped:
            lines.append(f"\nSkipped {len(skipped)} glyph(s):")
            lines.extend(f"  {s}" for s in skipped)
        if not renamed and not skipped:
            lines.append("Nothing to rename.")

        Message("\n".join(lines), "Lowercase Glyph Names — Done")