#MenuTitle: Center Shapes in Advance Width 3
# -*- coding: utf-8 -*-

"""
Center Shapes in Advance Width
================================
Centers all shapes (paths and components) of selected glyphs within
their advance width. Works on either a specified master or all masters.
The advance width of each glyph is preserved.

Usage:
  - Select glyphs in the Font tab (or open them in Edit view)
  - Run the script
  - A dialog lets you choose a specific master or all masters
"""

from __future__ import division, print_function
from GlyphsApp import *
import vanilla
from AppKit import NSApp


# ── helpers ──────────────────────────────────────────────────────────────────

def bounds_of_layer(layer):
	"""Return (min_x, max_x) across all paths and components, or None."""
	xs_min = []
	xs_max = []

	for path in layer.paths:
		b = path.bounds
		if b is None:
			continue
		xs_min.append(b.origin.x)
		xs_max.append(b.origin.x + b.size.width)

	for comp in layer.components:
		b = comp.bounds
		if b is None:
			continue
		xs_min.append(b.origin.x)
		xs_max.append(b.origin.x + b.size.width)

	if not xs_min:
		return None
	return min(xs_min), max(xs_max)


def center_layer(layer):
	"""Shift all shapes so their bounding box is centered in the advance width.
	Returns True if anything was moved."""
	advance_width = layer.width
	result = bounds_of_layer(layer)
	if result is None:
		return False

	min_x, max_x = result
	shapes_center = (min_x + max_x) / 2.0
	target_center = advance_width / 2.0
	delta_x = target_center - shapes_center

	if abs(delta_x) < 0.01:
		return False

	t = (1, 0, 0, 1, delta_x, 0)  # affine: identity + x translation

	for path in layer.paths:
		path.applyTransform(t)
	for comp in layer.components:
		comp.applyTransform(t)

	return True


# ── vanilla dialog ────────────────────────────────────────────────────────────

class CenterShapesDialog(object):

	def __init__(self, font):
		self.font = font
		self.target = None  # result: None=cancel, 'all', or a GSFontMaster

		self.master_labels = ["All Masters"] + [m.name for m in font.masters]

		row_h  = 20
		pad    = 16
		btn_h  = 22
		list_h = max(60, min(len(self.master_labels), 8) * row_h)
		win_w  = 300
		win_h  = pad + 18 + 8 + list_h + pad + btn_h + pad

		self.w = vanilla.FloatingWindow(
			(win_w, win_h),
			"Center Shapes in Advance Width"
		)

		y = pad
		self.w.label = vanilla.TextBox(
			(pad, y, -pad, 18),
			"Process which master(s)?"
		)
		y += 18 + 8

		self.w.masterList = vanilla.List(
			(pad, y, -pad, list_h),
			self.master_labels,
			allowsMultipleSelection=False,
		)
		self.w.masterList.setSelection([0])
		y += list_h + pad

		self.w.cancelButton = vanilla.Button(
			(pad, y, 90, btn_h),
			"Cancel",
			callback=self.on_cancel
		)
		self.w.okButton = vanilla.Button(
			(-pad - 90, y, 90, btn_h),
			"OK",
			callback=self.on_ok
		)
		self.w.setDefaultButton(self.w.okButton)

		self.w.open()
		self.w.center()
		NSApp.runModalForWindow_(self.w._window)

	def _close(self):
		NSApp.stopModal()
		self.w.close()

	def on_cancel(self, sender):
		self.target = None
		self._close()

	def on_ok(self, sender):
		sel = self.w.masterList.getSelection()
		idx = sel[0] if sel else 0
		if idx == 0:
			self.target = "all"
		else:
			self.target = self.font.masters[idx - 1]
		self._close()


# ── main ─────────────────────────────────────────────────────────────────────

def main():
	font = Glyphs.font
	if font is None:
		Message("Please open a font first.", "Center Shapes")
		return

	# Collect selected glyphs, deduplicated
	seen = set()
	unique_glyphs = []
	for layer in font.selectedLayers:
		glyph = layer.parent
		if glyph and glyph.name not in seen:
			seen.add(glyph.name)
			unique_glyphs.append(glyph)

	if not unique_glyphs:
		Message("Please select at least one glyph.", "Center Shapes")
		return

	dialog = CenterShapesDialog(font)
	target = dialog.target
	if target is None:
		return  # cancelled

	font.disableUpdateInterface()
	try:
		glyph_count = 0

		for glyph in unique_glyphs:
			glyph_moved = False

			if target == "all":
				layers_to_process = list(glyph.layers)
			else:
				layers_to_process = [
					l for l in glyph.layers
					if l.associatedMasterId == target.id
				]

			for layer in layers_to_process:
				if not (layer.isMasterLayer or layer.isSpecialLayer):
					continue
				if center_layer(layer):
					glyph_moved = True

			if glyph_moved:
				glyph_count += 1

		master_label = "all masters" if target == "all" else "master '%s'" % target.name
		print("Center Shapes: %d glyph(s) centered across %s." % (glyph_count, master_label))

		if glyph_count == 0:
			Message(
				"All selected glyphs were already centered, or had no shapes.",
				"Center Shapes"
			)
		else:
			Message(
				"Centered %d glyph(s) across %s." % (glyph_count, master_label),
				"Center Shapes — Done"
			)
	finally:
		font.enableUpdateInterface()


main()
