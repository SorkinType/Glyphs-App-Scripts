#MenuTitle: Mark Non-Shared Glyphs in Red 8
__doc__ = """
Compares glyphs between two open fonts.
Glyphs not shared between them can be marked red. Shared glyphs are uncolored.
Matching priority: Unicode first, then glyph name as fallback.
Written for Glyphs 3.
"""

import vanilla
from GlyphsApp import *

# Glyphs 3 color index reference (glyph.color):
#   0  = red       1  = orange    2  = brown     3  = yellow
#   4  = light green  5 = dark green  6 = light blue  7 = dark blue
#   8  = purple    9  = magenta   10 = light gray  11 = charcoal
#   None = no color (uncolored / white)

RED   = 0     # red in Glyphs 3
CLEAR = None  # no color in Glyphs 3

class CompareFonts:
    def __init__(self):
        if not Glyphs.font:
            Message("No font open", "Please open at least two fonts.")
            return

        self.allFonts = list(Glyphs.fonts)

        if len(self.allFonts) < 2:
            Message("Not enough fonts", "Please open at least two fonts to compare.")
            return

        fontNames = [self.fontLabel(f) for f in self.allFonts]

        self.w = vanilla.FloatingWindow(
            (440, 250),
            "Mark Non-Shared Glyphs in Red 8"
        )

        self.w.labelA = vanilla.TextBox((15, 18, 80, 20), "Source A:", alignment="right")
        self.w.popupA = vanilla.PopUpButton((100, 15, -15, 22), fontNames, callback=self.validateSelections)

        self.w.labelB = vanilla.TextBox((15, 52, 80, 20), "Source B:", alignment="right")
        self.w.popupB = vanilla.PopUpButton((100, 49, -15, 22), fontNames, callback=self.validateSelections)

        if len(self.allFonts) > 1:
            self.w.popupB.set(1)

        self.w.divider = vanilla.HorizontalLine((15, 88, -15, 1))
        self.w.markLabel = vanilla.TextBox((15, 102, -15, 17), "Mark glyphs red in:", sizeStyle="small")

        self.w.markChoice = vanilla.RadioGroup(
            (15, 122, -15, 82),
            [
                "Source A only  (glyphs in A not found in B)",
                "Source B only  (glyphs in B not found in A)",
                "Both fonts  (mark unshared glyphs in each)",
            ],
            isVertical=True,
            sizeStyle="small"
        )
        self.w.markChoice.set(0)

        self.w.cancelButton = vanilla.Button((15, -42, 120, 22), "Cancel", callback=self.cancel)
        self.w.runButton = vanilla.Button((-135, -42, 120, 22), "Run", callback=self.compareFonts)
        self.w.statusLabel = vanilla.TextBox((15, -42, -145, 22), "", sizeStyle="small")

        self.w.open()

    def fontLabel(self, font):
        name = font.familyName or "Unnamed"
        path = font.filepath
        filename = path.split("/")[-1] if path else "(unsaved)"
        return f"{name}  —  {filename}"

    def validateSelections(self, sender):
        if self.w.popupA.get() == self.w.popupB.get():
            self.w.statusLabel.set("⚠ A and B are the same font.")
            self.w.runButton.enable(False)
        else:
            self.w.statusLabel.set("")
            self.w.runButton.enable(True)

    def cancel(self, sender):
        self.w.close()

    def getUnicode(self, glyph):
        """
        Return the glyph's unicode as a normalized uppercase hex string (e.g. '0041'),
        or None if unencoded. Uses glyph.unicode only — the reliable Glyphs 3 property.
        """
        uc = glyph.unicode
        if uc:
            return str(uc).strip().upper().zfill(4)
        return None

    def buildLookup(self, font):
        """
        Returns:
          unicode_set: hex strings for all encoded glyphs
          name_set:    glyph names for glyphs with no unicode (fallback matching only)
        """
        unicode_set = set()
        name_set = set()
        for glyph in font.glyphs:
            uc = self.getUnicode(glyph)
            if uc:
                unicode_set.add(uc)
            else:
                name_set.add(glyph.name)
        return unicode_set, name_set

    def setGlyphColor(self, glyph, colorValue):
        """
        Set color on the glyph only.
        Layer colors are only fixed if they differ from the new glyph color,
        to avoid the split-color display bug without iterating layers unnecessarily.
        """
        glyph.color = colorValue
        for layer in glyph.layers:
            if layer.color != colorValue:
                layer.color = colorValue

    def markFont(self, fontToMark, refUnicodes, refNames):
        marked  = 0
        unmarks = 0

        # Suppress all UI updates for the duration of the loop
        fontToMark.disableUpdateInterface()

        try:
            for glyph in fontToMark.glyphs:
                uc = self.getUnicode(glyph)
                if uc:
                    matched = uc in refUnicodes
                else:
                    matched = glyph.name in refNames

                newColor = CLEAR if matched else RED

                # Skip if already the right color — avoids triggering
                # any write or notification when nothing needs to change
                if glyph.color != newColor:
                    self.setGlyphColor(glyph, newColor)

                if matched:
                    unmarks += 1
                else:
                    marked += 1

        finally:
            # Always re-enable updates, even if something goes wrong
            fontToMark.enableUpdateInterface()

        return unmarks, marked

    def compareFonts(self, sender):
        idxA = self.w.popupA.get()
        idxB = self.w.popupB.get()

        if idxA == idxB:
            Message("Same font selected", "Please select two different fonts.")
            return

        fontA = self.allFonts[idxA]
        fontB = self.allFonts[idxB]
        direction = self.w.markChoice.get()  # 0=A only, 1=B only, 2=both

        unicodesA, namesA = self.buildLookup(fontA)
        unicodesB, namesB = self.buildLookup(fontB)

        lines = []

        if direction == 0 or direction == 2:
            unmarks, marked = self.markFont(fontA, unicodesB, namesB)
            lines.append(f"Source A — {self.fontLabel(fontA)}:\n  {marked} marked red,  {unmarks} matched (uncolored)")

        if direction == 1 or direction == 2:
            unmarks, marked = self.markFont(fontB, unicodesA, namesA)
            lines.append(f"Source B — {self.fontLabel(fontB)}:\n  {marked} marked red,  {unmarks} matched (uncolored)")

        self.w.close()
        Message("Compare complete", "\n\n".join(lines))

CompareFonts()
