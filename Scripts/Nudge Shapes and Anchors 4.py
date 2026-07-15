# MenuTitle: Nudge Shapes and Anchors Horizontally 4
# -*- coding: utf-8 -*-
__doc__ = """
Shifts the selected paths/components and anchors of the current glyph(s)
left or right by an amount you specify - either the same amount across
all masters, or a different amount per master.

Usage:
- Select one or more glyphs in Font View (or just edit one glyph in Edit View).
- Run the script.
- Enter shift values per master (positive = right, negative = left).
- Choose whether to move:
	- selected items only (Edit View, current layer)
	- ALL shapes+anchors on the layer(s)
"""

from GlyphsApp import Glyphs, Message
import vanilla


class NudgeShapesAnchors(object):

	def __init__(self):
		self.font = Glyphs.font
		if self.font is None:
			Message("No font open", "Please open a font first.", OKButton="OK")
			return

		self.masters = list(self.font.masters)

		# Window
		windowWidth = 420
		rowHeight = 24
		padding = 14
		# header + one row per master + gap + 3 checkboxes + gap + button
		windowHeight = (
			padding * 2
			+ rowHeight  # header text
			+ rowHeight * len(self.masters)  # master rows
			+ 10  # gap
			+ rowHeight * 3  # checkboxes
			+ 10  # gap
			+ 24  # button
		)

		self.w = vanilla.FloatingWindow(
			(windowWidth, windowHeight), "Nudge Shapes & Anchors"
		)

		y = padding
		self.w.text1 = vanilla.TextBox((padding, y, -padding, 17),
			"Horizontal shift per master (units). Positive = right, negative = left:")
		y += rowHeight + 4

		self.masterFields = {}
		for master in self.masters:
			setattr(self.w, "label_%s" % master.id, vanilla.TextBox(
				(padding, y + 2, 200, 17), master.name
			))
			field = vanilla.EditText(
				(220, y, -padding, 22), "0"
			)
			setattr(self.w, "field_%s" % master.id, field)
			self.masterFields[master.id] = field
			y += rowHeight

		y += 6
		self.w.applySameCheckbox = vanilla.CheckBox(
			(padding, y, -padding, 20),
			"Use first master's value for ALL masters",
			value=False,
			callback=self.toggleSame
		)
		y += rowHeight

		self.w.allItemsCheckbox = vanilla.CheckBox(
			(padding, y, -padding, 20),
			"Move ALL shapes + anchors (ignore selection)",
			value=True
		)
		y += rowHeight

		self.w.allLayersCheckbox = vanilla.CheckBox(
			(padding, y, -padding, 20),
			"Apply to all layers of selected glyph(s), not just current",
			value=True
		)
		y += rowHeight + 10

		self.w.runButton = vanilla.Button(
			(padding, y, -padding, 24), "Nudge", callback=self.run
		)

		self.w.open()

	def toggleSame(self, sender):
		if sender.get():
			firstMaster = self.masters[0]
			firstValue = self.masterFields[firstMaster.id].get()
			for master in self.masters[1:]:
				self.masterFields[master.id].set(firstValue)
				self.masterFields[master.id].enable(False)
		else:
			for master in self.masters:
				self.masterFields[master.id].enable(True)

	def getShiftForMaster(self, masterId):
		try:
			value = float(self.masterFields[masterId].get())
		except ValueError:
			value = 0.0
		return value

	def shiftLayer(self, layer, shift, allItems):
		if shift == 0:
			return

		# Remember the original width so we can restore it afterwards.
		# Moving nodes/components can trigger Glyphs' automatic alignment
		# and/or metrics keys, which may otherwise change the width.
		originalWidth = layer.width

		# Temporarily disable automatic alignment on components so their
		# positions aren't recalculated when we move things.
		disabledAlignment = []
		for comp in layer.components:
			if comp.automaticAlignment:
				comp.automaticAlignment = False
				disabledAlignment.append(comp)

		if allItems:
			# Move all paths
			for path in layer.paths:
				for node in path.nodes:
					node.position = (node.position.x + shift, node.position.y)
			# Move all components
			for comp in layer.components:
				comp.position = (comp.position.x + shift, comp.position.y)
			# Move all anchors
			for anchor in layer.anchors:
				anchor.position = (anchor.position.x + shift, anchor.position.y)
		else:
			# Move only selected nodes/components/anchors
			for path in layer.paths:
				for node in path.nodes:
					if node.selected:
						node.position = (node.position.x + shift, node.position.y)
			for comp in layer.components:
				if comp.selected:
					comp.position = (comp.position.x + shift, comp.position.y)
			for anchor in layer.anchors:
				if anchor.selected:
					anchor.position = (anchor.position.x + shift, anchor.position.y)

		# Restore automatic alignment flags
		for comp in disabledAlignment:
			comp.automaticAlignment = True

		# Restore the original advance width
		layer.width = originalWidth

	def run(self, sender):
		font = self.font
		allItems = self.w.allItemsCheckbox.get()
		allLayers = self.w.allLayersCheckbox.get()

		# Determine which glyphs to operate on
		glyphs = []
		if font.currentTab and not font.selectedLayers == []:
			# Edit View: use the glyphs of the selected layers
			for layer in font.selectedLayers:
				if layer.parent not in glyphs:
					glyphs.append(layer.parent)
		else:
			# Font View: use selected glyphs
			for glyph in font.selection:
				glyphs.append(glyph)

		if not glyphs:
			Message("Nothing selected", "Please select glyph(s) in Font View or Edit View.", OKButton="OK")
			return

		font.disableUpdateInterface()
		try:
			for glyph in glyphs:
				if allLayers:
					targetLayers = [layer for layer in glyph.layers if layer.master is not None]
				else:
					# Only the layer(s) currently being edited for this glyph
					if font.currentTab:
						targetLayers = [layer for layer in font.selectedLayers if layer.parent == glyph]
					else:
						# Font view, no specific layer -> apply to all master layers
						targetLayers = [layer for layer in glyph.layers if layer.master is not None]

				for layer in targetLayers:
					master = layer.associatedFontMaster()
					if master is None:
						continue
					shift = self.getShiftForMaster(master.id)
					self.shiftLayer(layer, shift, allItems)
		finally:
			font.enableUpdateInterface()


NudgeShapesAnchors()
