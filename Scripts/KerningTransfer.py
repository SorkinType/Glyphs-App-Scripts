# MenuTitle: Kerning Transfer Between Fonts
# -*- coding: utf-8 -*-
__doc__ = """
Transfer kerning from one open font to another.
Correctly translates glyph UUIDs, kerning group names, and plain glyph
names so pairs are never written as raw UUID strings in the target font.
"""

import traceback
from GlyphsApp import Glyphs, Message
import vanilla

# ── key-translation helpers ───────────────────────────────────────────────────

def build_lookup(font):
    """
    Return two dicts for *font*:

    id_to_name  – {glyph_id (UUID string): glyph_name}
    name_to_id  – {glyph_name: glyph_id}

    Glyphs 3 kerning dicts use one of three key formats per entry:
      • "@MMK_L_groupname" / "@MMK_R_groupname"  – kerning group reference
      • "glyphname"                               – single-glyph exception
      • "UUID-string"                             – internal glyph ID
                                                   (older .glyphs files)
    We normalise everything to the group-name / glyph-name form that
    Glyphs 3 writes natively.
    """
    id_to_name = {}
    name_to_id = {}
    for g in font.glyphs:
        id_to_name[g.id] = g.name
        name_to_id[g.name] = g.id
    return id_to_name, name_to_id


def resolve_key(raw_key, id_to_name):
    """
    Convert a raw kerning key to its canonical string form:
      • Already a group ref (@MMK_…) → return as-is
      • Known glyph name              → return as-is
      • UUID present in id_to_name    → return the glyph name
      • Otherwise                     → return None  (drop the pair)
    """
    if raw_key.startswith("@"):          # kerning group ref — keep
        return raw_key
    if raw_key in id_to_name.values():   # already a plain glyph name
        return raw_key
    if raw_key in id_to_name:            # UUID → translate to glyph name
        return id_to_name[raw_key]
    return None                          # unresolvable — skip


def target_key_for(resolved_key, tgt_font, side):
    """
    Given a resolved key (group ref or glyph name) from the source font,
    return the best key to use in the *target* font.

    side = "left" or "right"
    prefix = "@MMK_L_" for left, "@MMK_R_" for right

    If the key is already a group ref we use it directly — the group may or
    may not exist in the target, but Glyphs will simply ignore unknown groups.
    If it's a plain glyph name we return it as-is (single-glyph exception).
    """
    return resolved_key   # pass through; Glyphs handles unknown groups fine


# ── font / master label helpers ───────────────────────────────────────────────

def font_label(font):
    name = font.familyName or "Untitled"
    path = font.filepath
    filename = path.split("/")[-1] if path else "<unsaved>"
    return "%s  (%s)" % (name, filename)

def master_label(master):
    return master.name or ("Master " + str(master.id))


# ── core transfer ─────────────────────────────────────────────────────────────

def transfer_kerning(source_font, target_font, master_map,
                     replace=True, copy_groups=True):
    """
    master_map  -- {source_master_id: target_master_id}
    replace     -- if True, wipe the target master kerning completely first so
                   no old pairs survive (clean replace, not a merge).
                   if False, merge source pairs in, leaving untouched pairs.
    Returns (pairs_written, pairs_skipped, groups_updated).
    """
    pairs_written  = 0
    pairs_skipped  = 0
    groups_updated = 0

    src_id_to_name, _ = build_lookup(source_font)

    # ── 1. Sync kerning groups (left/right class membership) ─────────────────
    if copy_groups:
        tgt_glyph_names = set(g.name for g in target_font.glyphs)
        for sg in source_font.glyphs:
            if sg.name not in tgt_glyph_names:
                continue
            tg = target_font.glyphs[sg.name]
            changed = False
            if sg.leftKerningGroup and tg.leftKerningGroup != sg.leftKerningGroup:
                tg.leftKerningGroup = sg.leftKerningGroup
                changed = True
            if sg.rightKerningGroup and tg.rightKerningGroup != sg.rightKerningGroup:
                tg.rightKerningGroup = sg.rightKerningGroup
                changed = True
            if changed:
                groups_updated += 1

    # ── 2. Copy kerning pairs, translating keys ───────────────────────────────
    for src_mid, tgt_mid in master_map.items():
        src_kerning = source_font.kerning.get(src_mid, {})

        # Wipe the target master kerning entirely before writing
        if replace and tgt_mid in target_font.kerning:
            del target_font.kerning[tgt_mid]

        if not src_kerning:
            continue

        # Start from a clean dict
        target_font.kerning[tgt_mid] = {}
        tgt_kerning = target_font.kerning[tgt_mid]

        for raw_left, right_dict in src_kerning.items():

            left_key = resolve_key(raw_left, src_id_to_name)
            if left_key is None:
                pairs_skipped += len(right_dict)
                continue

            left_key = target_key_for(left_key, target_font, "left")

            if left_key not in tgt_kerning:
                tgt_kerning[left_key] = {}

            for raw_right, value in right_dict.items():

                right_key = resolve_key(raw_right, src_id_to_name)
                if right_key is None:
                    pairs_skipped += 1
                    continue

                right_key = target_key_for(right_key, target_font, "right")

                if replace or right_key not in tgt_kerning[left_key]:
                    tgt_kerning[left_key][right_key] = value
                    pairs_written += 1

    return pairs_written, pairs_skipped, groups_updated


# ── UI ────────────────────────────────────────────────────────────────────────

class KerningTransferDialog(object):

    MARGIN = 14
    ROW_H  = 22
    LBL_W  = 170
    POP_W  = 220
    WIN_W  = 460

    def __init__(self):
        fonts = Glyphs.fonts
        if len(fonts) < 2:
            Message("Not enough fonts open",
                    "Please open at least two font files in Glyphs "
                    "before running this script.")
            return

        self.fonts  = list(fonts)
        self.labels = [font_label(f) for f in self.fonts]
        self._master_popups = []   # [(src_master, tgt_masters_list, popup)]
        self._build()

    # ── window ────────────────────────────────────────────────────────────────

    def _build(self):
        m  = self.MARGIN
        rh = self.ROW_H
        W  = self.WIN_W

        n_masters = len(self.fonts[0].masters)
        total_h = (m
                   + rh + 4
                   + rh + 8
                   + 1  + 8
                   + rh + 6
                   + n_masters * (rh + 4)
                   + 8
                   + 1  + 6
                   + rh + 4
                   + rh + 10
                   + 24 + m)

        self.w = vanilla.FloatingWindow((W, total_h),
                                        "Transfer Kerning Between Fonts")
        f = self.w
        y = m

        # Source
        f.srcLabel = vanilla.TextBox(
            (m, y+3, self.LBL_W, rh), "Source font:", sizeStyle="small")
        f.srcPopup = vanilla.PopUpButton(
            (m+self.LBL_W, y, self.POP_W, rh), self.labels,
            sizeStyle="small", callback=self._on_font_change)
        y += rh + 4

        # Target
        f.tgtLabel = vanilla.TextBox(
            (m, y+3, self.LBL_W, rh), "Target font:", sizeStyle="small")
        f.tgtPopup = vanilla.PopUpButton(
            (m+self.LBL_W, y, self.POP_W, rh), self.labels,
            sizeStyle="small", callback=self._on_font_change)
        f.tgtPopup.set(1)
        y += rh + 8

        f.sep1 = vanilla.HorizontalLine((m, y, -m, 1))
        y += 1 + 8

        f.mapHeader = vanilla.TextBox(
            (m, y, -m, rh),
            "Master mapping  (source  \u2192  target)",
            sizeStyle="small")
        y += rh + 6

        self._master_row_y = y
        self._build_master_rows()
        y = self._after_master_rows_y

        f.sep2 = vanilla.HorizontalLine((m, y, -m, 1))
        y += 1 + 6

        f.overwriteCheck = vanilla.CheckBox(
            (m, y, -m, rh),
            "Replace target kerning completely (delete old pairs first)",
            value=True, sizeStyle="small")
        y += rh + 4

        f.groupsCheck = vanilla.CheckBox(
            (m, y, -m, rh),
            "Copy kerning groups to matching glyphs",
            value=True, sizeStyle="small")
        y += rh + 10

        f.cancelBtn = vanilla.Button(
            (m, y, 90, 22), "Cancel", callback=self._on_cancel)
        f.transferBtn = vanilla.Button(
            (-(m+150), y, 150, 22), "Transfer Kerning",
            callback=self._on_transfer)

        self.w.open()

    # ── master rows ───────────────────────────────────────────────────────────

    def _build_master_rows(self):
        m  = self.MARGIN
        rh = self.ROW_H
        f  = self.w

        src_font   = self.fonts[f.srcPopup.get()]
        tgt_font   = self.fonts[f.tgtPopup.get()]
        tgt_labels = ["(skip)"] + [master_label(m_) for m_ in tgt_font.masters]

        if hasattr(f, "masterGroup"):
            del f.masterGroup

        self._master_popups = []
        n       = len(src_font.masters)
        group_h = n * (rh + 4)

        f.masterGroup = vanilla.Group(
            (0, self._master_row_y, self.WIN_W, group_h))
        g  = f.masterGroup
        gy = 0

        for idx, src_master in enumerate(src_font.masters):
            setattr(g, "lbl%d" % idx, vanilla.TextBox(
                (m, gy+3, self.LBL_W, rh),
                "  " + master_label(src_master),
                sizeStyle="small"))
            pop = vanilla.PopUpButton(
                (m+self.LBL_W, gy, self.POP_W, rh),
                tgt_labels, sizeStyle="small")
            pop.set(min(idx+1, len(tgt_labels)-1))
            setattr(g, "pop%d" % idx, pop)

            self._master_popups.append((src_master, tgt_font.masters, pop))
            gy += rh + 4

        self._after_master_rows_y = self._master_row_y + group_h + 8

    # ── callbacks ─────────────────────────────────────────────────────────────

    def _on_font_change(self, sender):
        f = self.w
        si, ti = f.srcPopup.get(), f.tgtPopup.get()
        if si == ti:
            f.tgtPopup.set((ti + 1) % len(self.fonts))
        self._build_master_rows()

    def _on_cancel(self, sender):
        self.w.close()

    def _on_transfer(self, sender):
        f = self.w
        si, ti = f.srcPopup.get(), f.tgtPopup.get()

        if si == ti:
            Message("Same font selected",
                    "Source and target fonts must be different.")
            return

        src_font = self.fonts[si]
        tgt_font = self.fonts[ti]

        master_map = {}
        for src_master, tgt_masters, pop in self._master_popups:
            choice = pop.get()
            if choice == 0:
                continue
            master_map[src_master.id] = tgt_masters[choice-1].id

        if not master_map:
            Message("No masters mapped",
                    "Please map at least one source master to a target master.")
            return

        replace     = bool(f.overwriteCheck.get())
        copy_groups = bool(f.groupsCheck.get())

        try:
            pairs, skipped, groups = transfer_kerning(
                src_font, tgt_font, master_map, replace, copy_groups)
        except Exception:
            Message("Transfer failed", traceback.format_exc())
            return

        lines = []
        for src_master, tgt_masters, pop in self._master_popups:
            choice = pop.get()
            if choice == 0:
                continue
            lines.append("  %s  \u2192  %s" % (
                master_label(src_master),
                master_label(tgt_masters[choice-1])))

        skip_note = ("\nPairs skipped (unresolvable keys) : %d" % skipped
                     if skipped else "")

        Message("Transfer complete",
                "Kerning transferred successfully!\n\n"
                "From : %s\nTo   : %s\n\n"
                "Master mapping:\n%s\n\n"
                "Pairs written : %d%s\n"
                "Groups synced : %d"
                % (src_font.familyName or "Source",
                   tgt_font.familyName or "Target",
                   "\n".join(lines), pairs, skip_note, groups))
        self.w.close()


# Keep the dialog object alive at module scope (prevents garbage collection)
_dlg = KerningTransferDialog()