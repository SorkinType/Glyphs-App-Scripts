#MenuTitle: Copy Widths from Source Font
# -*- coding: utf-8 -*-
"""
Copy Widths from Source Font
────────────────────────────
Copies glyph widths from a source font into the selected glyphs of a target
font, with explicit master-to-master pairing so multi-master fonts are handled
correctly.

The dialog lets you:
  • Choose the source font (open in Glyphs or picked from disk)
  • Map each target master to the source master you want to read widths from
  • Review exactly what will happen before anything is written

Glyph matching is by name first, then by Unicode value.
Only glyphs selected in the target font are affected.
"""

import os
import traceback

from GlyphsApp import Glyphs, GSFont, Message
from vanilla import (
    Window, PopUpButton, TextBox, Button,
    HorizontalLine, RadioGroup, Group, SegmentedButton
)

# ── Optional libraries for non-Glyphs source formats ─────────────────────────
try:
    from fontTools.ttLib import TTFont
    FONTTOOLS_AVAILABLE = True
except ImportError:
    FONTTOOLS_AVAILABLE = False

try:
    import defcon
    DEFCON_AVAILABLE = True
except ImportError:
    DEFCON_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Width readers — return  {glyph_name: {master_index: width}}
# ─────────────────────────────────────────────────────────────────────────────

def read_widths_from_open_font(font):
    """
    Build a width table from an already-open GSFont.
    Returns:
        master_names : [str]  — ordered list of master names
        by_name      : {glyph_name: [width, ...]}  — one entry per master, in order
        by_unicode   : {unicode_hex: [width, ...]}
    """
    master_ids   = [m.id for m in font.masters]
    master_names = [m.name for m in font.masters]
    by_name    = {}
    by_unicode = {}

    for glyph in font.glyphs:
        widths = []
        for mid in master_ids:
            layer = glyph.layers[mid]
            widths.append(layer.width if layer else 0)
        by_name[glyph.name] = widths
        if glyph.unicode:
            by_unicode[glyph.unicode] = widths

    return master_names, by_name, by_unicode


def read_widths_from_glyphs_file(path):
    """Load a .glyphs file from disk and delegate to read_widths_from_open_font."""
    try:
        font = GSFont(path)
        return read_widths_from_open_font(font)
    except Exception as e:
        raise ValueError("Failed to read Glyphs file: %s" % e)


def read_widths_from_ufo(path):
    if not DEFCON_AVAILABLE:
        raise ImportError("defcon is required for UFO files.  pip3 install defcon")
    try:
        font = defcon.Font(path)
        master_names = ["Regular"]
        by_name    = {g.name: [g.width] for g in font}
        by_unicode = {}
        for g in font:
            if g.unicodes:
                by_unicode[format(g.unicodes[0], "04X")] = [g.width]
        return master_names, by_name, by_unicode
    except Exception as e:
        raise ValueError("Failed to read UFO: %s" % e)


def read_widths_from_binary(path):
    if not FONTTOOLS_AVAILABLE:
        raise ImportError("fontTools is required for TTF/OTF.  pip3 install fonttools")
    try:
        font = TTFont(path)
        if "hmtx" not in font:
            raise ValueError("Font has no hmtx table")
        hmtx = font["hmtx"]
        master_names = ["Regular"]
        by_name = {}
        for name in font.getGlyphOrder():
            try:
                width, _ = hmtx[name]
                by_name[name] = [width]
            except Exception:
                pass
        by_unicode = {}
        if "cmap" in font:
            for table in font["cmap"].tables:
                if table.isUnicode():
                    for cp, gname in table.cmap.items():
                        if gname in by_name:
                            by_unicode[format(cp, "04X")] = by_name[gname]
        return master_names, by_name, by_unicode
    except Exception as e:
        raise ValueError("Failed to read binary font: %s" % e)


def read_widths(path_or_font):
    """Dispatch to the right reader. Accepts a path string or an open GSFont."""
    if isinstance(path_or_font, str):
        path = path_or_font
        if not os.path.exists(path):
            raise ValueError("File not found: %s" % path)
        ext = os.path.splitext(path)[1].lower()
        if ext in (".glyphs", ".glyphx"):
            return read_widths_from_glyphs_file(path)
        elif ext == ".ufo" or os.path.isdir(path):
            return read_widths_from_ufo(path)
        elif ext in (".ttf", ".otf"):
            return read_widths_from_binary(path)
        else:
            raise ValueError("Unsupported format: %s" % ext)
    else:
        return read_widths_from_open_font(path_or_font)


# ─────────────────────────────────────────────────────────────────────────────
# File picker (for fonts not already open in Glyphs)
# ─────────────────────────────────────────────────────────────────────────────

def choose_source_file():
    from AppKit import NSOpenPanel, NSModalResponseOK
    panel = NSOpenPanel.openPanel()
    panel.setCanChooseFiles_(True)
    panel.setCanChooseDirectories_(True)
    panel.setAllowedFileTypes_(["glyphs", "glyphx", "ufo", "ttf", "otf"])
    panel.setTitle_("Choose Source Font")
    panel.setPrompt_("Select")
    if panel.runModal() == NSModalResponseOK:
        url = panel.URL()
        return url.path() if url else None
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Dialog
# ─────────────────────────────────────────────────────────────────────────────

def font_label(font):
    name = font.familyName or "(untitled)"
    if font.filepath:
        name += "  [%s]" % os.path.basename(font.filepath)
    return name


class CopyWidthsDialog:

    PADDING = 16
    ROW_H   = 22
    LABEL_W = 140
    POPUP_W = 250
    WIN_W   = 460

    def __init__(self):
        # ── Validate target font ──────────────────────────────────────────────
        self.target_font = Glyphs.font
        if not self.target_font:
            Message("No font open", "Please open a target font first.")
            return

        self.selected_glyph_names = self._get_selected_names()
        if not self.selected_glyph_names:
            Message("No glyphs selected", "Please select glyphs in the target font first.")
            return

        self.target_masters = list(self.target_font.masters)

        # Source state — populated after the user picks a source
        self._src_master_names = []
        self._src_by_name      = {}
        self._src_by_unicode   = {}
        self._src_label        = ""

        # Per-target-master source-master index (default 0)
        self._master_map = [0] * len(self.target_masters)

        # Dynamic popup references, built in _build_mapping_rows
        self._src_popups = []

        self._build_window()
        self.w.open()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_selected_names(self):
        names = []
        font = self.target_font
        # Font tab
        if font.selection:
            for g in font.selection:
                if hasattr(g, "name") and g.name not in names:
                    names.append(g.name)
        # Edit tab
        if not names and font.currentTab:
            for layer in font.currentTab.selectedLayers:
                if layer.parent and layer.parent.name not in names:
                    names.append(layer.parent.name)
        return names

    def _master_items(self):
        return self._src_master_names if self._src_master_names else ["— pick source first —"]

    # ── UI build ──────────────────────────────────────────────────────────────

    def _build_window(self):
        p  = self.PADDING
        rh = self.ROW_H
        lw = self.LABEL_W
        pw = self.POPUP_W
        w  = self.WIN_W

        n_masters = len(self.target_masters)
        # Sum every fixed row explicitly, then add per-master rows
        win_h = (
            p           # top padding
            + rh + 6    # target info label
            + 1 + 10    # divider0
            + rh + 6    # SOURCE FONT section label
            + rh + 8    # source popup + load button row
            + rh + 10   # source status label
            + 1 + 12    # divider1
            + rh + 8    # MASTER MAPPING label
            + n_masters * (rh + 8)  # one row per master
            + 1 + 12    # divider2
            + (rh + 4)  # buttons
            + p         # bottom padding
        )

        self.w = Window(
            (w, win_h),
            "Copy Widths from Source Font",
            autosaveName="com.copy_widths.dialog",
        )

        y = p

        # ── Target info ───────────────────────────────────────────────────────
        self.w.targetLabel = TextBox(
            (p, y, -p, rh),
            "TARGET: %s  (%d glyph(s) selected)" % (
                font_label(self.target_font), len(self.selected_glyph_names)
            ),
            sizeStyle="small",
        )
        y += rh + 6

        self.w.divider0 = HorizontalLine((p, y, -p, 1))
        y += 10

        # ── Source picker ─────────────────────────────────────────────────────
        self.w.sourceSectionLabel = TextBox(
            (p, y, -p, rh),
            "SOURCE FONT",
            sizeStyle="small",
        )
        y += rh + 6

        open_font_labels = [font_label(f) for f in Glyphs.fonts if f is not self.target_font]
        self._open_fonts = [f for f in Glyphs.fonts if f is not self.target_font]

        source_items = ["— choose from disk… —"] + open_font_labels
        self.w.sourceFontPopup = PopUpButton(
            (p, y, -p - 100, rh),
            source_items,
            callback=self._source_changed,
            sizeStyle="regular",
        )
        self.w.sourceLoadButton = Button(
            (-p - 90, y, 90, rh),
            "Load Source",
            callback=self._load_source,
        )
        y += rh + 8

        self.w.sourceStatusLabel = TextBox(
            (p, y, -p, rh),
            "No source loaded yet.",
            sizeStyle="small",
        )
        y += rh + 10

        self.w.divider1 = HorizontalLine((p, y, -p, 1))
        y += 12

        # ── Master mapping ────────────────────────────────────────────────────
        self.w.mappingLabel = TextBox(
            (p, y, -p, rh),
            "MASTER MAPPING  (target master  →  source master to read width from)",
            sizeStyle="small",
        )
        y += rh + 8

        self._src_popups = []
        for i, master in enumerate(self.target_masters):
            lbl = TextBox(
                (p, y, lw, rh),
                "%s :" % master.name,
                sizeStyle="regular",
            )
            setattr(self.w, "masterLabel_%d" % i, lbl)

            popup = PopUpButton(
                (p + lw, y, pw, rh),
                self._master_items(),
                sizeStyle="regular",
            )
            popup.enable(False)
            setattr(self.w, "masterPopup_%d" % i, popup)
            self._src_popups.append(popup)
            y += rh + 8

        self.w.divider2 = HorizontalLine((p, y, -p, 1))
        y += 12

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_w = 120
        self.w.cancelButton = Button(
            (p, y, btn_w, rh + 4),
            "Cancel",
            callback=self._cancel,
        )
        self.w.runButton = Button(
            (-p - btn_w, y, btn_w, rh + 4),
            "Copy Widths",
            callback=self._run,
        )
        self.w.runButton.enable(False)

    # ── Source loading ────────────────────────────────────────────────────────

    def _source_changed(self, sender):
        """User changed the source popup — reload if it's an open font."""
        idx = sender.get()
        if idx == 0:
            # "choose from disk" option — wait for Load button
            return
        font = self._open_fonts[idx - 1]
        self._load_from_font(font)

    def _load_source(self, sender):
        idx = self.w.sourceFontPopup.get()
        if idx == 0:
            # Load from disk
            path = choose_source_file()
            if not path:
                return
            try:
                names, by_name, by_unicode = read_widths(path)
                self._src_master_names = names
                self._src_by_name      = by_name
                self._src_by_unicode   = by_unicode
                self._src_label        = os.path.basename(path)
                self._refresh_mapping_ui()
            except Exception as e:
                Message("Could not load source", str(e))
        else:
            font = self._open_fonts[idx - 1]
            self._load_from_font(font)

    def _load_from_font(self, font):
        try:
            names, by_name, by_unicode = read_widths(font)
            self._src_master_names = names
            self._src_by_name      = by_name
            self._src_by_unicode   = by_unicode
            self._src_label        = font_label(font)
            self._refresh_mapping_ui()
        except Exception as e:
            Message("Could not read font", str(e))

    def _refresh_mapping_ui(self):
        items = self._src_master_names
        self.w.sourceStatusLabel.set(
            "✅  Loaded: %s  (%d master(s): %s)" % (
                self._src_label, len(items), ", ".join(items)
            )
        )
        for i, popup in enumerate(self._src_popups):
            popup.setItems(items)
            popup.enable(True)
            # Auto-match by name
            target_name = self.target_masters[i].name
            if target_name in items:
                popup.set(items.index(target_name))
            else:
                popup.set(min(i, len(items) - 1))
        self.w.runButton.enable(True)

    # ── Run ───────────────────────────────────────────────────────────────────

    def _cancel(self, sender):
        self.w.close()

    def _run(self, sender):
        self.w.close()

        # Build master map: target master index → source master index
        master_map = [p.get() for p in self._src_popups]

        font = self.target_font
        copied   = []
        no_match = []
        errors   = []

        for name in self.selected_glyph_names:
            glyph = font.glyphs[name]
            if glyph is None:
                no_match.append(name)
                continue

            # Find widths in source
            src_widths = self._src_by_name.get(name)
            if src_widths is None and glyph.unicode:
                src_widths = self._src_by_unicode.get(glyph.unicode)

            if src_widths is None:
                no_match.append(name)
                continue

            try:
                for tgt_idx, master in enumerate(self.target_masters):
                    src_idx = master_map[tgt_idx]
                    # Guard against source having fewer masters than expected
                    src_idx = min(src_idx, len(src_widths) - 1)
                    new_width = src_widths[src_idx]
                    layer = glyph.layers[master.id]
                    if layer:
                        layer.width = new_width
                copied.append(name)
            except Exception:
                errors.append((name, traceback.format_exc().strip().splitlines()[-1]))

        # ── Report ────────────────────────────────────────────────────────────
        lines = [
            "Target : %s" % font_label(font),
            "Source : %s" % self._src_label,
            "",
        ]
        for tgt_idx, master in enumerate(self.target_masters):
            src_idx  = master_map[tgt_idx]
            src_name = self._src_master_names[min(src_idx, len(self._src_master_names) - 1)]
            lines.append("  %s  ←  %s" % (master.name, src_name))

        lines += [
            "",
            "✅  Widths copied : %d glyph(s)" % len(copied),
        ]
        if no_match:
            lines += ["", "⚠️  Not found in source (%d):" % len(no_match)]
            lines += ["      " + n for n in sorted(no_match)]
        if errors:
            lines += ["", "❌  Errors (%d):" % len(errors)]
            lines += ["      %s: %s" % (n, msg) for n, msg in errors]

        report = "\n".join(lines)
        print(report)
        Message("Copy Widths — done", report)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

CopyWidthsDialog()