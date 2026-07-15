#MenuTitle: Remove Non-Orthogonal Nodes (Refit Curve) 3
# encoding: utf-8
"""
Removes every non-orthogonal SMOOTH on-curve node from the selected glyph(s)
and refits the surrounding bezier curve as closely as possible — exactly as
Glyphs does when you manually delete a smooth node.

Works across ALL masters for each selected glyph.

What is skipped (never touched)
────────────────────────────────
• Sharp / corner nodes  (node.smooth == False)
• LINE nodes
• Any node where EITHER handle is within the orthogonality tolerance of
  horizontal or vertical — those are intentionally orthogonal nodes
• Nodes whose surrounding structure isn't two clean cubic segments

Orthogonality tolerance (user-adjustable in the UI)
────────────────────────────────────────────────────
A handle is considered "axis-aligned" (orthogonal) when its angle is within
this many degrees of 0°, 90°, 180°, or 270°.  Default is 5°, giving a
comfortable margin for nearly-vertical or nearly-horizontal handles that
should be preserved.

Refit algorithm
───────────────
For each pair of cubic segments  A→B→C  where B is the node to remove:

  Segment 1:  P0, H1, H2, P1   (P1 == B.position)
  Segment 2:  P1, H3, H4, P2

We want a single cubic  P0, Q1, Q2, P2  that best approximates the
combined curve.  The approach:
  1. Sample N points along both original segments (de Casteljau evaluation).
  2. Map each sample to t on [0,1] by chord-length parameterisation.
  3. Solve the 2×2 least-squares system for Q1 and Q2 with P0, P2 fixed.
"""

import math
import os
from Foundation import NSPoint
from GlyphsApp import *
from vanilla import Window, TextBox, PopUpButton, Button, EditText, HorizontalLine


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_TOLERANCE = 5.0   # degrees — handles within this of an axis are kept
SAMPLE_COUNT      = 24    # curve sample points for least-squares fit


# ─────────────────────────────────────────────────────────────────────────────
# Geometry helpers
# ─────────────────────────────────────────────────────────────────────────────

def is_axis_aligned(dx, dy, tol):
    """Return True if the vector (dx, dy) is within *tol* degrees of any
    of the four cardinal directions (0°, 90°, 180°, 270°).

    Uses the acute angle to the nearest axis, so the check is symmetric
    and works correctly for all quadrants without modulo trickery.
    """
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return True   # zero-length handle — treat as orthogonal / safe

    # Angle to nearest horizontal axis  (0° or 180°)
    # |cos θ| close to 1  →  nearly horizontal
    length    = math.hypot(dx, dy)
    cos_angle = abs(dx) / length          # |cos| of angle to horizontal
    sin_angle = abs(dy) / length          # |sin| of angle to horizontal
                                          # also == |cos| of angle to vertical

    tol_rad = math.radians(tol)
    # Close to horizontal: sin of the deviation is small
    near_horiz = sin_angle < math.sin(tol_rad)
    # Close to vertical: cos of the deviation from vertical is small
    near_vert  = cos_angle < math.sin(tol_rad)

    return near_horiz or near_vert


def eval_cubic(p0, p1, p2, p3, t):
    """Evaluate cubic bezier at parameter t. Points are (x, y) tuples."""
    u  = 1.0 - t
    u2 = u  * u;  u3 = u2 * u
    t2 = t  * t;  t3 = t2 * t
    x  = u3*p0[0] + 3*u2*t*p1[0] + 3*u*t2*p2[0] + t3*p3[0]
    y  = u3*p0[1] + 3*u2*t*p1[1] + 3*u*t2*p2[1] + t3*p3[1]
    return (x, y)


def sample_two_cubics(seg1, seg2, n=SAMPLE_COUNT):
    """Sample n points across two consecutive cubic bezier segments and return
    (pts, params) where params are chord-length-parameterised t values."""
    half = n // 2
    pts  = []
    for i in range(half + 1):
        pts.append(eval_cubic(*seg1, i / float(half)))
    for i in range(1, half + 1):
        pts.append(eval_cubic(*seg2, i / float(half)))

    dists = [0.0]
    for i in range(1, len(pts)):
        dx = pts[i][0] - pts[i-1][0]
        dy = pts[i][1] - pts[i-1][1]
        dists.append(dists[-1] + math.hypot(dx, dy))
    total = dists[-1]
    if total < 1e-9:
        params = [i / float(len(pts) - 1) for i in range(len(pts))]
    else:
        params = [d / total for d in dists]

    return pts, params


def fit_cubic(p0, p3, pts, params):
    """Least-squares cubic fit with fixed endpoints. Returns (Q1, Q2)."""
    b1 = [3*(1-t)**2*t    for t in params]
    b2 = [3*(1-t)*t**2    for t in params]
    b0 = [(1-t)**3        for t in params]
    b3 = [t**3            for t in params]

    rx = [pts[i][0] - b0[i]*p0[0] - b3[i]*p3[0] for i in range(len(pts))]
    ry = [pts[i][1] - b0[i]*p0[1] - b3[i]*p3[1] for i in range(len(pts))]

    A00 = sum(b1[i]*b1[i] for i in range(len(pts)))
    A01 = sum(b1[i]*b2[i] for i in range(len(pts)))
    A11 = sum(b2[i]*b2[i] for i in range(len(pts)))
    bx0 = sum(b1[i]*rx[i] for i in range(len(pts)))
    bx1 = sum(b2[i]*rx[i] for i in range(len(pts)))
    by0 = sum(b1[i]*ry[i] for i in range(len(pts)))
    by1 = sum(b2[i]*ry[i] for i in range(len(pts)))

    det = A00*A11 - A01*A01
    if abs(det) < 1e-12:
        # Degenerate — fall back to linear interpolation at 1/3 and 2/3
        def lerp(a, b, t): return (a[0]+t*(b[0]-a[0]), a[1]+t*(b[1]-a[1]))
        return lerp(p0, p3, 1/3.0), lerp(p0, p3, 2/3.0)

    inv = 1.0 / det
    q1x = inv * ( A11*bx0 - A01*bx1)
    q1y = inv * ( A11*by0 - A01*by1)
    q2x = inv * (-A01*bx0 + A00*bx1)
    q2y = inv * (-A01*by0 + A00*by1)
    return (q1x, q1y), (q2x, q2y)


# ─────────────────────────────────────────────────────────────────────────────
# Node classification
# ─────────────────────────────────────────────────────────────────────────────

def node_is_target(path, node_idx, tol):
    """Return True if the node should be removed:
      - Must be a CURVE node
      - Must be smooth  (node.smooth == True)
      - BOTH surrounding handles must be non-axis-aligned beyond *tol* degrees
        (if either handle is orthogonal the node is intentional — keep it)
    """
    nodes = path.nodes
    n     = len(nodes)
    node  = nodes[node_idx]

    # Only CURVE-type nodes
    if node.type != CURVE:
        return False

    # Skip sharp / corner nodes — only remove smooth ones
    if not node.smooth:
        return False

    # Surrounding nodes must be off-curves
    prev_off = nodes[(node_idx - 1) % n]
    next_off = nodes[(node_idx + 1) % n]
    if prev_off.type != OFFCURVE or next_off.type != OFFCURVE:
        return False

    # Handle vectors relative to the on-curve node
    dx_in  = prev_off.position.x - node.position.x
    dy_in  = prev_off.position.y - node.position.y
    dx_out = next_off.position.x - node.position.x
    dy_out = next_off.position.y - node.position.y

    # If EITHER handle is axis-aligned the node is intentionally orthogonal
    if is_axis_aligned(dx_in,  dy_in,  tol):
        return False
    if is_axis_aligned(dx_out, dy_out, tol):
        return False

    return True   # both handles are genuinely non-orthogonal → candidate


# ─────────────────────────────────────────────────────────────────────────────
# Node removal + refit
# ─────────────────────────────────────────────────────────────────────────────

def get_pos(node):
    return (node.position.x, node.position.y)


def remove_node_refit(path, node_idx):
    """Remove on-curve node B and refit the merged cubic. Returns True on
    success, False if the surrounding structure is unexpected."""
    nodes  = path.nodes
    n      = len(nodes)

    B_idx  = node_idx
    H2_idx = (B_idx - 1) % n   # incoming off-curve (close to B)
    H1_idx = (B_idx - 2) % n   # outgoing off-curve from A
    A_idx  = (B_idx - 3) % n   # previous on-curve
    H3_idx = (B_idx + 1) % n   # outgoing off-curve (close to B)
    H4_idx = (B_idx + 2) % n   # incoming off-curve to C
    C_idx  = (B_idx + 3) % n   # next on-curve

    # Verify cubic structure
    if (nodes[H2_idx].type != OFFCURVE or
            nodes[H1_idx].type != OFFCURVE or
            nodes[H3_idx].type != OFFCURVE or
            nodes[H4_idx].type != OFFCURVE):
        return False

    p0 = get_pos(nodes[A_idx])
    h1 = get_pos(nodes[H1_idx])
    h2 = get_pos(nodes[H2_idx])
    p1 = get_pos(nodes[B_idx])
    h3 = get_pos(nodes[H3_idx])
    h4 = get_pos(nodes[H4_idx])
    p2 = get_pos(nodes[C_idx])

    pts, params = sample_two_cubics((p0, h1, h2, p1), (p1, h3, h4, p2))
    q1, q2      = fit_cubic(p0, p2, pts, params)

    # Update the outer handles with the fitted positions
    nodes[H1_idx].position = NSPoint(round(q1[0]), round(q1[1]))
    nodes[H4_idx].position = NSPoint(round(q2[0]), round(q2[1]))

    # Delete B and its two adjacent inner off-curves
    for nd in [nodes[B_idx], nodes[H2_idx], nodes[H3_idx]]:
        path.removeNode_(nd)

    return True


def process_layer(layer, tol):
    """Remove all qualifying non-orthogonal smooth nodes from *layer*.
    Returns the count of nodes removed."""
    count = 0
    for path in layer.paths:
        changed = True
        while changed:
            changed = False
            for i in range(len(path.nodes)):
                if node_is_target(path, i, tol):
                    if remove_node_refit(path, i):
                        count  += 1
                        changed = True
                        break   # restart after any removal (indices shifted)
    return count


# ─────────────────────────────────────────────────────────────────────────────
# Vanilla UI
# ─────────────────────────────────────────────────────────────────────────────

class RemoveNonOrthogonalUI(object):

    W  = 560
    P  = 16
    LW = 200

    def __init__(self):
        font = Glyphs.font
        if not font:
            Message("Please open a font first.",
                    title="Remove Non-Orthogonal Nodes")
            return

        selected = [g for g in font.glyphs if g.selected]
        if not selected:
            Message("Please select one or more glyphs first.",
                    title="Remove Non-Orthogonal Nodes")
            return

        self.font     = font
        self.selected = selected
        self._build_window()

    def _build_window(self):
        W, P, LW = self.W, self.P, self.LW
        n_sel     = len(self.selected)
        n_masters = len(self.font.masters)

        font_name = self.font.familyName or "Untitled"
        try:
            if self.font.filepath:
                font_name += "  (%s)" % os.path.basename(str(self.font.filepath))
        except Exception:
            pass

        body_h = (
            P + 22 + 6          # heading
            + 14 + P            # sub note
            + 1  + P            # div
            + 18 + 8            # font info
            + 18 + 8            # glyphs info
            + 18 + P            # masters info
            + 1  + P            # div
            + 22 + 6            # tolerance row
            + 14 + 8            # tolerance note line 1
            + 14 + P            # tolerance note line 2
            + 1  + P            # div
            + 14 + P            # warning
            + 1  + P            # div
            + 28 + P            # buttons
        )

        self.w = Window(
            (W, body_h),
            "Remove Non-Orthogonal Nodes",
            minSize=(W, body_h),
            maxSize=(W + 200, body_h),
        )
        w = self.w
        y = P

        # ── Heading ───────────────────────────────────────────────────────
        w.heading = TextBox(
            (P, y, -P, 20),
            "Remove Non-Orthogonal Nodes & Refit Curve",
            sizeStyle="regular"
        )
        y += 22 + 6

        w.subNote = TextBox(
            (P, y, -P, 14),
            "Removes smooth curve nodes whose handles are not axis-aligned, "
            "refitting the surrounding bezier to match as closely as possible. "
            "Sharp (corner) nodes are never touched.",
            sizeStyle="mini"
        )
        y += 14 + P

        w.div1 = HorizontalLine((P, y, -P, 1))
        y += 1 + P

        # ── Font / selection info ─────────────────────────────────────────
        w.fontInfo = TextBox(
            (P, y, -P, 18),
            "Font     :  %s" % font_name,
            sizeStyle="small"
        )
        y += 18 + 8

        w.glyphInfo = TextBox(
            (P, y, -P, 18),
            "Glyphs   :  %d selected" % n_sel,
            sizeStyle="small"
        )
        y += 18 + 8

        w.masterInfo = TextBox(
            (P, y, -P, 18),
            "Masters  :  %d  (all will be processed)" % n_masters,
            sizeStyle="small"
        )
        y += 18 + P

        w.div2 = HorizontalLine((P, y, -P, 1))
        y += 1 + P

        # ── Tolerance ─────────────────────────────────────────────────────
        w.tolLabel = TextBox(
            (P, y + 4, LW, 18),
            "Orthogonality tolerance (°):",
            sizeStyle="small"
        )
        w.tolField = EditText(
            (P + LW, y, 60, 22),
            text=str(DEFAULT_TOLERANCE),
            sizeStyle="small"
        )
        y += 22 + 6

        w.tolNote1 = TextBox(
            (P, y, -P, 14),
            "Handles within this many degrees of horizontal or vertical are treated as "
            "intentionally orthogonal and the node is preserved.",
            sizeStyle="mini"
        )
        y += 14 + 8

        w.tolNote2 = TextBox(
            (P, y, -P, 14),
            "Recommended range: 2°–10°.  Lower = stricter (removes fewer nodes).  "
            "Higher = more permissive (removes more nodes).",
            sizeStyle="mini"
        )
        y += 14 + P

        w.div3 = HorizontalLine((P, y, -P, 1))
        y += 1 + P

        # ── Warning ───────────────────────────────────────────────────────
        w.warningNote = TextBox(
            (P, y, -P, 14),
            "⚠  Save or take a snapshot before applying — this cannot be auto-undone.",
            sizeStyle="mini"
        )
        y += 14 + P

        w.div4 = HorizontalLine((P, y, -P, 1))
        y += 1 + P

        # ── Buttons ───────────────────────────────────────────────────────
        btn_w = 120
        w.cancelBtn = Button(
            (P, y, btn_w, 26), "Cancel",
            callback=self._on_cancel
        )
        w.applyBtn = Button(
            (-P - btn_w, y, btn_w, 26), "Apply",
            callback=self._on_apply
        )
        w.applyBtn._nsObject.setKeyEquivalent_("\r")

        w.open()

    def _on_cancel(self, sender):
        self.w.close()

    def _on_apply(self, sender):
        # Read and validate tolerance
        try:
            tol = float(self.w.tolField.get())
            if tol < 0 or tol > 45:
                raise ValueError
        except ValueError:
            Message(
                "Please enter a tolerance between 0 and 45 degrees.",
                title="Remove Non-Orthogonal Nodes"
            )
            return

        self.w.close()
        self._run(tol)

    def _run(self, tol):
        font    = self.font
        masters = font.masters

        total_nodes  = 0
        total_glyphs = 0
        log_lines    = []

        font.disableUpdateInterface()
        try:
            for glyph in self.selected:
                glyph_count = 0
                for master in masters:
                    layer = glyph.layers[master.id]
                    if layer is None:
                        continue
                    count = process_layer(layer, tol)
                    if count:
                        glyph_count += count
                        log_lines.append(
                            "  %-30s  [%s]  %d node%s removed"
                            % (glyph.name, master.name, count,
                               "s" if count != 1 else "")
                        )
                if glyph_count:
                    total_nodes  += glyph_count
                    total_glyphs += 1
        finally:
            font.enableUpdateInterface()

        if len(log_lines) > 80:
            log_lines = log_lines[:80] + ["  … and more."]

        summary = (
            "Tolerance used  : %.1f°\n\n"
            "Nodes removed   : %d\n"
            "Glyphs affected : %d\n\n"
            "Log:\n%s"
        ) % (
            tol,
            total_nodes,
            total_glyphs,
            "\n".join(log_lines) if log_lines else "  No qualifying nodes found."
        )

        Message(summary, title="Remove Non-Orthogonal Nodes — Done")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    RemoveNonOrthogonalUI()
