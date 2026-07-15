#MenuTitle: Find Stray/Backup Layers
# -*- coding: utf-8 -*-
"""
Find Stray / Backup / Duplicate Layers
────────────────────────────────────────
Looks for layers that are neither:
  - true master layers (layer.layerId == master.id), nor
  - brace layers ({...}), nor
  - bracket layers ([...])

These are typically Glyphs "backup" layers, often auto-named with a
timestamp such as:
    7 May 26, 17:04

Such layers can confuse glyphsLib / fontmake if:
  • a glyph ends up with MORE THAN ONE layer associated with the same
    master id (duplicate-per-master), which can cause list-indexing
    mismatches between glyphs during the build, or
  • the backup layer is accidentally the one marked as the "master"
    layer (associatedMasterId points to a master, but layerId differs
    from that master's id — i.e. it's a copy, not the original).

This script is READ-ONLY by default: it reports findings and
highlights/selects affected glyphs (colour label only). It does NOT
delete anything. A separate optional cleanup pass is included but
commented out — read the notes near CLEANUP_MODE before enabling it.
"""

from GlyphsApp import Glyphs, Message
import re
import traceback

HIGHLIGHT_COLOR = 1  # red

# Set to True to actually DELETE detected stray/backup layers.
# !! BACK UP YOUR FILE FIRST !!
# When False, the script only reports and highlights — nothing is changed.
CLEANUP_MODE = False


# Matches Glyphs' default backup-layer naming, e.g. "7 May 26, 17:04"
# or "12 Dec 2025, 9:41" — date + comma + time.
BACKUP_NAME_RE = re.compile(
    r"^\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4},?\s*\d{1,2}:\d{2}"
)


def is_brace_or_bracket(name):
    if not name:
        return False
    name = name.strip()
    return name.startswith("{") or name.startswith("[")


def looks_like_backup_name(name):
    if not name:
        return False
    return bool(BACKUP_NAME_RE.match(name.strip()))


def scan_font(font):
    """
    Returns a list of issue dicts:
        {
            "glyph_name": str,
            "glyph": GSGlyph,
            "stray_layers": [ {"name": str, "layer": GSLayer,
                                "associated_master": str or None,
                                "reason": str} ],
            "duplicate_master_layers": { master_name: [layer_names] }
        }
    """
    issues = []
    master_ids   = {m.id for m in font.masters}
    master_names = {m.id: m.name for m in font.masters}

    for glyph in font.glyphs:
        stray_layers = []
        layers_per_master = {}  # master_id -> [layer, ...]

        for layer in glyph.layers:
            name = layer.name or ""
            lid  = layer.layerId
            amid = layer.associatedMasterId

            # Track everything that claims to belong to a master
            if amid in master_ids:
                layers_per_master.setdefault(amid, []).append(layer)

            # Skip true master layers (the canonical one: layerId == master id)
            if lid in master_ids and lid == amid:
                continue

            # Skip brace/bracket layers
            if is_brace_or_bracket(name):
                continue

            # Anything else is "stray" — flag with a reason
            if looks_like_backup_name(name):
                reason = "looks like an auto-named backup layer (date/time)"
            elif amid in master_ids:
                reason = (
                    "associated with master '%s' but is NOT that master's "
                    "primary layer (possible duplicate)" % master_names.get(amid, amid)
                )
            else:
                reason = "not a master, brace, or bracket layer (orphaned layer)"

            stray_layers.append({
                "name": name or "(unnamed layer)",
                "layer": layer,
                "associated_master": master_names.get(amid) if amid in master_ids else None,
                "reason": reason,
            })

        # Detect duplicates: more than one layer claiming the same master
        duplicate_master_layers = {}
        for mid, layer_list in layers_per_master.items():
            if len(layer_list) > 1:
                duplicate_master_layers[master_names.get(mid, mid)] = [
                    (l.name or "(unnamed)") for l in layer_list
                ]

        if stray_layers or duplicate_master_layers:
            issues.append({
                "glyph_name": glyph.name,
                "glyph": glyph,
                "stray_layers": stray_layers,
                "duplicate_master_layers": duplicate_master_layers,
            })

    issues.sort(key=lambda r: r["glyph_name"])
    return issues


def build_report(font, issues):
    lines = []
    lines.append("=" * 70)
    lines.append("STRAY / BACKUP / DUPLICATE LAYER SCAN")
    lines.append("Font : %s" % (font.familyName or "(untitled)"))
    lines.append("=" * 70)

    if not issues:
        lines.append("")
        lines.append("No stray, backup-dated, or duplicate-per-master layers found.")
        lines.append("=" * 70)
        return "\n".join(lines)

    n_stray = sum(len(r["stray_layers"]) for r in issues)
    n_dupes = sum(1 for r in issues if r["duplicate_master_layers"])

    lines.append("")
    lines.append("Found %d glyph(s) with extra layers:" % len(issues))
    lines.append("   • %d stray/backup layer(s) total" % n_stray)
    lines.append("   • %d glyph(s) with duplicate per-master layers" % n_dupes)
    lines.append("")
    lines.append("-" * 70)

    for r in issues:
        lines.append("")
        lines.append("▸  %s" % r["glyph_name"])

        for sl in r["stray_layers"]:
            assoc = (" (associated master: %s)" % sl["associated_master"]) if sl["associated_master"] else ""
            lines.append("    ⚠  layer '%s'%s" % (sl["name"], assoc))
            lines.append("         reason: %s" % sl["reason"])

        if r["duplicate_master_layers"]:
            lines.append("    ⚠  DUPLICATE LAYERS PER MASTER:")
            for master_name, names in r["duplicate_master_layers"].items():
                lines.append("         master '%s' has %d layers: %s" %
                              (master_name, len(names), ", ".join(repr(n) for n in names)))

    lines.append("")
    lines.append("-" * 70)
    lines.append("WHAT THIS MEANS")
    lines.append("Layers named like '7 May 26, 17:04' are Glyphs auto-backup")
    lines.append("layers, usually created during editing (e.g. via Edit >")
    lines.append("Undo history, or certain destructive operations). They are")
    lines.append("normally harmless and hidden from export — BUT if one ends")
    lines.append("up registered as a duplicate for a master, glyphsLib can")
    lines.append("build mismatched per-master layer lists across glyphs,")
    lines.append("which surfaces as 'list index out of range' in fontmake.")
    lines.append("")
    lines.append("NEXT STEPS")
    lines.append("  1. Open each flagged glyph (Glyphs highlighted/selected).")
    lines.append("  2. Open the Layers panel (Window > Palette, or the layer")
    lines.append("     list in the bottom-left of the glyph view).")
    lines.append("  3. For each stray/backup layer listed above:")
    lines.append("       - If it's an old backup you don't need, select it")
    lines.append("         and delete it (right-click > Delete Layer, or the")
    lines.append("         '-' button in the layers palette).")
    lines.append("       - If 'DUPLICATE LAYERS PER MASTER' is shown, check")
    lines.append("         which of the two layers is the CORRECT current")
    lines.append("         design, keep that one, delete the other.")
    lines.append("  4. Re-run this script afterward to confirm a clean result,")
    lines.append("     then re-run fontmake.")
    lines.append("=" * 70)

    return "\n".join(lines)


def build_summary(issues):
    if not issues:
        return "No stray, backup, or duplicate-per-master layers found."

    n_stray = sum(len(r["stray_layers"]) for r in issues)
    n_dupes = sum(1 for r in issues if r["duplicate_master_layers"])

    return (
        "%d glyph(s) flagged.\n"
        "  • %d stray/backup layer(s)\n"
        "  • %d glyph(s) with duplicate per-master layers\n\n"
        "Flagged glyphs are highlighted and selected.\n"
        "See the Macro Panel for details and how to clean up."
        % (len(issues), n_stray, n_dupes)
    )


def highlight_and_select(font, issues):
    flagged_names = {r["glyph_name"] for r in issues}
    for glyph in font.glyphs:
        if glyph.name in flagged_names:
            glyph.color = HIGHLIGHT_COLOR

    try:
        font.selection = [r["glyph"] for r in issues]
    except Exception:
        pass


def cleanup_stray_layers(font, issues):
    """
    OPTIONAL destructive cleanup. Only runs if CLEANUP_MODE = True.

    Strategy (conservative):
      - For layers flagged as "looks like an auto-named backup layer",
        delete them outright.
      - For "duplicate per-master" cases, this function does NOT choose
        automatically which to keep — it only deletes layers that ALSO
        match the backup-name pattern, leaving true ambiguous duplicates
        for manual review.
    """
    deleted = 0
    for r in issues:
        glyph = r["glyph"]
        for sl in r["stray_layers"]:
            if "auto-named backup layer" in sl["reason"]:
                layer = sl["layer"]
                try:
                    glyph.layers.remove(layer)
                    deleted += 1
                except Exception:
                    pass
    return deleted


def main():
    font = Glyphs.font
    if not font:
        Message("No font open", "Please open a font first.")
        return

    try:
        issues  = scan_font(font)
        report  = build_report(font, issues)
        summary = build_summary(issues)

        print(report)

        if issues:
            highlight_and_select(font, issues)

        if CLEANUP_MODE and issues:
            deleted = cleanup_stray_layers(font, issues)
            print("\nCLEANUP: deleted %d auto-named backup layer(s)." % deleted)
            summary += "\n\nCLEANUP MODE: deleted %d backup layer(s)." % deleted

        Message("Find Stray/Backup Layers — done", summary)

    except Exception:
        tb = traceback.format_exc()
        print(tb)
        Message("Script error", tb)


main()
