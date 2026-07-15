#MenuTitle: Find Glyph in OpenType Features
# -*- coding: utf-8 -*-
__doc__ = """
Searches all OpenType classes, feature prefixes, and features in the
current font for references to a specific glyph name (typed in, or
taken from your current selection), and reports matches in the
Macro window. Also reports indirect references: if the glyph is
inside a class, and that class is used in a feature, the feature is
flagged too.
"""

import re
import vanilla
from GlyphsApp import Glyphs, Message


def get_default_glyph_name():
	"""Grab a sensible default glyph name from the current selection, if any."""
	font = Glyphs.font
	if font is None:
		return ""
	try:
		if font.selectedLayers:
			layer = font.selectedLayers[0]
			if layer is not None and layer.parent is not None:
				return layer.parent.name
	except Exception:
		pass
	return ""


def make_pattern(glyphName):
	# Match the glyph name as a whole token. Glyph/class names can
	# contain letters, digits, underscores, periods and hyphens, and
	# classes are prefixed with @ -- none of those should count as a
	# "boundary", so we exclude them on both sides of the match.
	boundary = r'(?<![A-Za-z0-9_.\-@])'
	boundary_end = r'(?![A-Za-z0-9_.\-@])'
	return re.compile(boundary + re.escape(glyphName) + boundary_end)


def find_matches(code, pattern):
	if not code:
		return []
	matches = []
	for lineNumber, line in enumerate(code.splitlines(), start=1):
		codePart = line.split('#', 1)[0]  # ignore comments
		if pattern.search(codePart):
			matches.append((lineNumber, line.strip()))
	return matches


def run_search(font, glyphName):
	pattern = make_pattern(glyphName)
	Glyphs.clearLog()
	Glyphs.showMacroWindow()
	print("Searching for '%s' in the OpenType code of font '%s'\n" % (glyphName, font.familyName))

	foundAnything = False

	# 1) Classes whose glyph list contains the glyph
	classesContainingGlyph = []
	for glyphClass in font.classes:
		matches = find_matches(glyphClass.code, pattern)
		if matches:
			foundAnything = True
			classesContainingGlyph.append(glyphClass.name)
			print("Class @%s:" % glyphClass.name)
			for lineNumber, line in matches:
				print("    line %i: %s" % (lineNumber, line))
			print("")

	# 2) Feature prefixes
	for prefix in font.featurePrefixes:
		matches = find_matches(prefix.code, pattern)
		if matches:
			foundAnything = True
			print("Feature Prefix '%s':" % prefix.name)
			for lineNumber, line in matches:
				print("    line %i: %s" % (lineNumber, line))
			print("")

	# 3) Features: direct mentions, plus indirect mentions via classes
	classRefPatterns = {
		className: re.compile(r'@' + re.escape(className) + r'\b')
		for className in classesContainingGlyph
	}

	for feature in font.features:
		directMatches = find_matches(feature.code, pattern)
		indirectClassHits = set()
		for line in feature.code.splitlines():
			codePart = line.split('#', 1)[0]
			for className, classPattern in classRefPatterns.items():
				if classPattern.search(codePart):
					indirectClassHits.add(className)

		if directMatches or indirectClassHits:
			foundAnything = True
			status = []
			if feature.disabled:
				status.append("disabled")
			if feature.automatic:
				status.append("automatic")
			statusText = (" [%s]" % ", ".join(status)) if status else ""
			print("Feature '%s'%s:" % (feature.name, statusText))
			for lineNumber, line in directMatches:
				print("    line %i (direct): %s" % (lineNumber, line))
			for className in indirectClassHits:
				print("    references class @%s, which contains '%s'" % (className, glyphName))
			print("")

	if not foundAnything:
		print("No references to '%s' were found in classes, feature prefixes, or features." % glyphName)

	print("Done.")


class GlyphFeatureSearch:

	def __init__(self):
		defaultName = get_default_glyph_name()
		self.w = vanilla.FloatingWindow((320, 110), "Find Glyph in Features")
		self.w.text = vanilla.TextBox((15, 15, -15, 20), "Glyph name to search for:")
		self.w.glyphName = vanilla.EditText((15, 38, -15, 22), defaultName)
		self.w.searchButton = vanilla.Button((15, -32, -15, 22), "Search", callback=self.search)
		self.w.setDefaultButton(self.w.searchButton)
		self.w.open()
		self.w.glyphName.getNSTextField().becomeFirstResponder()

	def search(self, sender):
		glyphName = self.w.glyphName.get().strip()
		if not glyphName:
			Message("Please enter a glyph name.", title="Find Glyph in Features")
			return

		font = Glyphs.font
		if font is None:
			Message("No font open.", title="Find Glyph in Features")
			return

		self.w.close()
		run_search(font, glyphName)


GlyphFeatureSearch()
