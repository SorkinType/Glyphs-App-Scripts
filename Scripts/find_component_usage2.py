# MenuTitle: Find Component Use 2
# -*- coding: utf-8 -*-
"""
Find Component Use

Searches the CURRENT FONT (open in Glyphs 3) for every glyph that uses a
given glyph as a component. Prints a report to the Macro panel and selects
the matching glyphs in Font View so they're visually highlighted.

Install:
    Save this file as "Find Component Use.py" inside
    Glyphs > Script > Open Scripts Folder, then restart Glyphs (or
    Cmd+Opt+Shift+Y to reload scripts). It will appear under the
    Script menu.

Run:
    Script > Find Component Use
    Type a glyph name (e.g. "aring") when prompted.
"""

from GlyphsApp import Glyphs, Message
import vanilla


def find_usage(font, target_name):
	"""
	Returns a dict: {glyph_name: set(layer_names)} for every glyph whose
	layers contain a component referencing target_name.
	"""
	results = {}
	for glyph in font.glyphs:
		for layer in glyph.layers:
			for component in layer.components:
				if component.componentName == target_name:
					results.setdefault(glyph.name, set()).add(layer.name)
	return results


def report_and_highlight(font, target_name):
	if target_name not in [g.name for g in font.glyphs]:
		print(f"⚠️  '{target_name}' is not a glyph name in this font.")
		print("    (Searching anyway, in case it's referenced but missing.)\n")

	results = find_usage(font, target_name)

	print("-" * 60)
	print(f"Component usage report for: {target_name}")
	print(f"Font: {font.familyName}")
	print("-" * 60)

	if not results:
		print(f"No glyphs use '{target_name}' as a component.")
		Message(
			title="Find Component Use",
			message=f"No glyphs use '{target_name}' as a component.",
			OKButton="OK",
		)
		return

	for glyph_name in sorted(results):
		layers = ", ".join(sorted(results[glyph_name]))
		print(f"● {glyph_name}   (layers: {layers})")

	print(f"\nTotal glyphs using '{target_name}': {len(results)}")
	print("-" * 60)

	# Highlight: select the matching glyphs in Font View
	font.selection = [g for g in font.glyphs if g.name in results]

	# Bring Font View to front so the highlighted selection is visible
	font.parent.windowController().showFontView_(None) if hasattr(
		font.parent.windowController(), "showFontView_"
	) else None

	Message(
		title="Find Component Use",
		message=f"'{target_name}' is used as a component in {len(results)} glyph(s).\n"
		f"They are now selected in Font View. See Macro Panel for details.",
		OKButton="OK",
	)


class FindComponentUseUI:
	def __init__(self):
		self.w = vanilla.FloatingWindow((300, 100), "Find Component Use")
		self.w.text = vanilla.TextBox((15, 15, -15, 20), "Glyph name to search for:")
		self.w.glyphName = vanilla.EditText((15, 40, -15, 22), "")
		self.w.runButton = vanilla.Button((15, 70, -15, 22), "Find Usage", callback=self.run)
		self.w.setDefaultButton(self.w.runButton)
		self.w.glyphName.getNSTextField().becomeFirstResponder()
		self.w.open()

	def run(self, sender):
		font = Glyphs.font
		if font is None:
			Message(title="Find Component Use", message="No font is open.", OKButton="OK")
			return
		name = self.w.glyphName.get().strip()
		if not name:
			return
		Glyphs.clearLog()
		Glyphs.showMacroWindow()
		report_and_highlight(font, name)


FindComponentUseUI()