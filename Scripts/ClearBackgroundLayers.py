#MenuTitle: Clear Background Layers in Open Fonts...
# -*- coding: utf-8 -*-
__doc__ = """
Removes paths, components, and/or anchors from the background layer
of every glyph in one or more open fonts.
"""

import vanilla
from GlyphsApp import Glyphs, GSPath, GSComponent


class ClearBackgroundLayersInOpenFonts(object):
    def __init__(self):
        sp = 10
        txY = 17
        chY = 22
        btnX = 160
        btnY = 22

        fonts = Glyphs.fonts
        if not fonts:
            print("No fonts open.")
            return

        self.fonts = fonts
        num_fonts = len(fonts)

        # Dynamic height: font checkboxes + section labels + what-checkboxes + button
        winH = (sp * (7 + num_fonts) +
                txY * 2 +
                chY * (num_fonts + 3) +
                btnY)

        self.w = vanilla.FloatingWindow(
            (320, winH),
            "Clear Background Layers in Open Fonts...",
            autosaveName="com.script.ClearBackgroundLayersInOpenFonts.mainwindow"
        )

        y = sp

        # --- Which fonts ---
        self.w.text_fonts = vanilla.TextBox(
            (sp, y, -sp, txY),
            "Which open font(s)?",
            sizeStyle="regular"
        )
        y += txY + sp

        # One checkbox per open font
        self.font_checks = []
        for i, f in enumerate(fonts):
            name = f.familyName or "(unnamed)"
            if f.filepath:
                label = u"{} — {}".format(name, f.filepath.lastPathComponent())
            else:
                label = u"{} — unsaved".format(name)
            cb = vanilla.CheckBox(
                (sp * 2, y, -sp, chY),
                label,
                value=True,
                sizeStyle="small"
            )
            attr_name = "fontCheck_{}".format(i)
            setattr(self.w, attr_name, cb)
            self.font_checks.append(attr_name)
            y += chY + sp

        # --- What to delete ---
        y += sp  # extra gap before section
        self.w.text_what = vanilla.TextBox(
            (sp, y, -sp, txY),
            "What to delete from backgrounds?",
            sizeStyle="regular"
        )
        y += txY + sp

        self.w.pathCheck = vanilla.CheckBox(
            (sp * 2, y, -sp, chY),
            "Paths (incl. corner & cap components)",
            value=True
        )
        y += chY + sp

        self.w.compoCheck = vanilla.CheckBox(
            (sp * 2, y, -sp, chY),
            "Components",
            value=True
        )
        y += chY + sp

        self.w.anchorCheck = vanilla.CheckBox(
            (sp * 2, y, -sp, chY),
            "Anchors",
            value=True
        )
        y += chY + sp

        # --- Run button ---
        self.w.runButton = vanilla.Button(
            (-sp - btnX, -sp - btnY, -sp, btnY),
            "Clear Backgrounds",
            sizeStyle="regular",
            callback=self.run
        )
        self.w.setDefaultButton(self.w.runButton)

        self.w.open()
        self.w.makeKey()

    # ------------------------------------------------------------------

    def _clear_background(self, layer):
        bg = layer.background
        if bg is None:
            return 0

        cleared = 0

        if self.w.pathCheck.get():
            try:
                paths = [s for s in bg.shapes if isinstance(s, GSPath)]
                if paths:
                    bg.removeShapes_(paths)
                    cleared += len(paths)
            except Exception as e:
                print("  Path removal error:", e)

        if self.w.compoCheck.get():
            try:
                compos = [s for s in bg.shapes if isinstance(s, GSComponent)]
                if compos:
                    bg.removeShapes_(compos)
                    cleared += len(compos)
            except Exception as e:
                print("  Component removal error:", e)

        if self.w.anchorCheck.get():
            try:
                count = len(bg.anchors)
                if count:
                    bg.anchors = []
                    cleared += count
            except Exception as e:
                print("  Anchor removal error:", e)

        return cleared

    # ------------------------------------------------------------------

    def run(self, sender):
        try:
            # Collect selected fonts via individual checkboxes
            target_fonts = [
                self.fonts[i]
                for i, attr in enumerate(self.font_checks)
                if getattr(self.w, attr).get()
            ]

            if not target_fonts:
                print("No fonts selected — nothing to do.")
                return

            if not (self.w.pathCheck.get() or
                    self.w.compoCheck.get() or
                    self.w.anchorCheck.get()):
                print("Nothing selected for deletion — nothing to do.")
                return

            Glyphs.showMacroWindow()
            print("=" * 50)
            print("Clear Background Layers in Open Fonts")
            print("=" * 50)

            grand_total = 0

            for font in target_fonts:
                label = font.familyName or str(font.filepath) or "(unnamed)"
                print(u"\nFont: {}".format(label))

                font.disableUpdateInterface()
                font.undoManager().beginUndoGrouping()

                font_total = 0
                try:
                    for glyph in font.glyphs:
                        for layer in glyph.layers:
                            font_total += self._clear_background(layer)
                finally:
                    font.undoManager().endUndoGrouping()
                    font.enableUpdateInterface()

                grand_total += font_total
                print(u"  \u2192 {} background item(s) removed.".format(font_total))

            print("\n" + "=" * 50)
            print(u"Done. {} item(s) removed across {} font(s).".format(
                grand_total, len(target_fonts)
            ))
            print("=" * 50)

            self.w.close()

        except Exception as e:
            print("Unexpected error:", e)
            import traceback
            traceback.print_exc()


ClearBackgroundLayersInOpenFonts()
