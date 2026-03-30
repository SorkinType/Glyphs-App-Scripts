#MenuTitle: Copy Sidebearings Between Masters
# -*- coding: utf-8 -*-
"""
Copy Sidebearings Between Masters
Copies left and/or sidebearings from a source master to a target master
for all glyphs in the current font.
"""

from GlyphsApp import *
from vanilla import Window, PopUpButton, CheckBox, Button, TextBox, dialogs
import objc

font = Glyphs.font

if font is None:
    Message("No font open.", "Please open a font file first.")
else:
    master_names = [m.name for m in font.masters]

    if len(master_names) < 2:
        Message("Not enough masters.", "The font needs at least two masters to copy sidebearings between.")
    else:

        class CopySidebearingsDialog:
            def __init__(self):
                self.result = None

                # Window dimensions
                w, h = 360, 200
                self.w = Window((w, h), "Copy Sidebearings Between Masters", autosaveName="CopySidebearingsWindow")

                # Source master
                self.w.sourceLabel = TextBox(
                    (20, 20, 130, 20),
                    "Copy FROM master:",
                    sizeStyle="small",
                )
                self.w.sourcePopup = PopUpButton(
                    (160, 16, -20, 22),
                    master_names,
                    sizeStyle="small",
                )

                # Target master
                self.w.targetLabel = TextBox(
                    (20, 54, 130, 20),
                    "Copy TO master:",
                    sizeStyle="small",
                )
                # Default target to second master so source != target initially
                self.w.targetPopup = PopUpButton(
                    (160, 50, -20, 22),
                    master_names,
                    sizeStyle="small",
                    callback=self.popupChanged_,
                )
                self.w.targetPopup.set(1)

                # Which sidebearings to copy
                self.w.optionsLabel = TextBox(
                    (20, 88, -20, 20),
                    "Sidebearings to copy:",
                    sizeStyle="small",
                )
                self.w.copyLSB = CheckBox(
                    (20, 110, 160, 20),
                    "Left sidebearing (LSB)",
                    sizeStyle="small",
                    value=True,
                )
                self.w.copyRSB = CheckBox(
                    (180, 110, 160, 20),
                    "Right sidebearing (RSB)",
                    sizeStyle="small",
                    value=True,
                )

                # Buttons
                self.w.cancelButton = Button(
                    (20, -44, 100, 22),
                    "Cancel",
                    sizeStyle="regular",
                    callback=self.cancel_,
                )
                self.w.copyButton = Button(
                    (-140, -44, 120, 22),
                    "Copy Sidebearings",
                    sizeStyle="regular",
                    callback=self.copy_,
                )

                self.w.setDefaultButton(self.w.copyButton)
                self.w.open()

            def popupChanged_(self, sender):
                pass  # Could add validation here if desired

            def cancel_(self, sender):
                self.result = None
                self.w.close()

            def copy_(self, sender):
                source_idx = self.w.sourcePopup.get()
                target_idx = self.w.targetPopup.get()

                if source_idx == target_idx:
                    Message(
                        "Same master selected.",
                        "Please choose different masters for source and target.",
                    )
                    return

                if not self.w.copyLSB.get() and not self.w.copyRSB.get():
                    Message(
                        "Nothing to copy.",
                        "Please select at least one sidebearing to copy (LSB and/or RSB).",
                    )
                    return

                self.result = {
                    "source_idx": source_idx,
                    "target_idx": target_idx,
                    "copy_lsb": bool(self.w.copyLSB.get()),
                    "copy_rsb": bool(self.w.copyRSB.get()),
                }
                self.w.close()

        # ---- Show dialog ----
        dialog = CopySidebearingsDialog()

        if dialog.result is not None:
            source_idx = dialog.result["source_idx"]
            target_idx = dialog.result["target_idx"]
            copy_lsb   = dialog.result["copy_lsb"]
            copy_rsb   = dialog.result["copy_rsb"]

            source_master = font.masters[source_idx]
            target_master = font.masters[target_idx]

            source_id = source_master.id
            target_id = target_master.id

            copied_count = 0
            skipped_count = 0

            font.disableUpdateInterface()
            try:
                for glyph in font.glyphs:
                    source_layer = glyph.layers[source_id]
                    target_layer = glyph.layers[target_id]

                    # Only copy for layers that actually exist and are not components-only
                    if source_layer is None or target_layer is None:
                        skipped_count += 1
                        continue

                    if copy_lsb:
                        target_layer.LSB = source_layer.LSB
                    if copy_rsb:
                        target_layer.RSB = source_layer.RSB

                    copied_count += 1

            finally:
                font.enableUpdateInterface()

            sides = []
            if copy_lsb:
                sides.append("LSB")
            if copy_rsb:
                sides.append("RSB")
            sides_str = " and ".join(sides)

            skipped_msg = " %d glyph(s) skipped (missing layers)." % skipped_count if skipped_count else ""
            Message(
                "Done!",
                "Copied %s from '%s' to '%s' for %d glyph(s).%s" % (
                    sides_str,
                    source_master.name,
                    target_master.name,
                    copied_count,
                    skipped_msg,
                ),
            )
