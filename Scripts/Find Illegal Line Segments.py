# MenuTitle: Find Illegal Line Segments
# -*- coding: utf-8 -*-
__doc__ = """
Scans all glyphs/layers/paths for the "Illegal line segment point count: 3"
error reported by fontmake/ufo2ft. This happens when a path segment
between two on-curve points contains exactly one off-curve point but is
not marked as a proper curve (qcurve/curve) — i.e. a "line" segment that
ends up with 3 points instead of 2.

Reports glyph name, layer (master), node index, and node coordinates for
any offending segment so you can fix them in Glyphs.
"""

from GlyphsApp import Glyphs, OFFCURVE, LINE, CURVE, QCURVE

font = Glyphs.font

if font is None:
	print("No font open.")
else:
	report = []

	for glyph in font.glyphs:
		for layer in glyph.layers:
			# Only check master layers (skip background, etc. if desired)
			if layer.isMasterLayer == False and layer.associatedMasterId is None:
				continue

			for path in layer.paths:
				nodes = path.nodes
				n = len(nodes)
				if n == 0:
					continue

				# Walk the path and group nodes into segments
				# A segment ends at each on-curve node, and consists of
				# that on-curve node plus the preceding off-curve nodes.
				segment = []
				for i in range(n):
					node = nodes[i]
					segment.append(node)
					if node.type != OFFCURVE:
						# End of segment - validate count
						seg_len = len(segment)
						on_curve_type = node.type

						# Valid counts:
						#  LINE / on-curve straight: segment should be length 1
						#  CURVE (cubic): segment should be length <=4 (1-3 off-curves + 1 on-curve)
						#  QCURVE: variable length allowed (TrueType quadratics)
						problem = False
						reason = ""

						if seg_len == 1:
							pass  # plain line/move/on-curve point, fine
						elif on_curve_type == LINE:
							# A LINE-type endpoint should never have off-curve
							# points before it
							problem = True
							reason = "On-curve node is type LINE but has {} preceding off-curve point(s)".format(seg_len - 1)
						elif on_curve_type == CURVE:
							if seg_len > 4:
								problem = True
								reason = "Cubic curve segment has {} points (too many off-curves)".format(seg_len)
							# seg_len in (2,3,4) is fine for cubic curves
						elif on_curve_type == QCURVE:
							pass  # TT quadratics: any number of off-curves OK
						else:
							pass

						if problem:
							coords = ", ".join(
								"(%.1f, %.1f)%s" % (
									pt.position.x, pt.position.y,
									" [%s]" % pt.type if pt.type == OFFCURVE else " [%s]" % pt.type
								)
								for pt in segment
							)
							report.append(
								"Glyph: %-12s Master: %-15s NodeIdx: %3d  Type: %-6s -> %s\n    Segment points: %s"
								% (glyph.name, layer.name, i, str(on_curve_type), reason, coords)
							)

						segment = []

				# Handle case where path doesn't end on an on-curve node
				# (shouldn't normally happen for closed paths, but check open paths)
				if segment and path.closed == False:
					if len(segment) > 0 and all(p.type == OFFCURVE for p in segment):
						report.append(
							"Glyph: %-12s Master: %-15s  Open path ends with %d trailing off-curve point(s) - check path"
							% (glyph.name, layer.name, len(segment))
						)

	if report:
		print("Found %d potential issue(s):\n" % len(report))
		for line in report:
			print(line)
			print("")
	else:
		print("No illegal line-segment point counts found. The issue may be elsewhere "
			  "(e.g. a corner component, a component with broken path data, or an "
			  "instance/interpolation producing a bad segment that doesn't exist "
			  "in any single master). Try:\n"
			  "  - Checking corner/cap components\n"
			  "  - Generating each master individually to isolate the problem\n"
			  "  - Running 'Path > Tidy up Paths' on all glyphs")
