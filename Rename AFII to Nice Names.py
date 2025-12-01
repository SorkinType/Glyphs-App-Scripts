#MenuTitle: Rename AFII to Nice Names
# -*- coding: utf-8 -*-
"""
Rename selected glyphs from AFII names to nice names (or uni names as fallback).
Save this file in your Glyphs Scripts folder:
~/Library/Application Support/Glyphs 3/Scripts/

Usage:
1. Select glyphs with AFII names
2. Run this script from Scripts menu
3. Glyphs will be renamed to nice names or Unicode names
"""

# AFII to Unicode mapping
# Based on Adobe Glyph List and common AFII assignments
AFII_TO_UNICODE = {
    # Cyrillic
    'afii10017': '0410',  # A
    'afii10018': '0411',  # BE
    'afii10019': '0412',  # VE
    'afii10020': '0413',  # GHE
    'afii10021': '0414',  # DE
    'afii10022': '0415',  # IE
    'afii10023': '0401',  # IO
    'afii10024': '0416',  # ZHE
    'afii10025': '0417',  # ZE
    'afii10026': '0418',  # I
    'afii10027': '0419',  # SHORT I
    'afii10028': '041A',  # KA
    'afii10029': '041B',  # EL
    'afii10030': '041C',  # EM
    'afii10031': '041D',  # EN
    'afii10032': '041E',  # O
    'afii10033': '041F',  # PE
    'afii10034': '0420',  # ER
    'afii10035': '0421',  # ES
    'afii10036': '0422',  # TE
    'afii10037': '0423',  # U
    'afii10038': '0424',  # EF
    'afii10039': '0425',  # HA
    'afii10040': '0426',  # TSE
    'afii10041': '0427',  # CHE
    'afii10042': '0428',  # SHA
    'afii10043': '0429',  # SHCHA
    'afii10044': '042A',  # HARD SIGN
    'afii10045': '042B',  # YERU
    'afii10046': '042C',  # SOFT SIGN
    'afii10047': '042D',  # E
    'afii10048': '042E',  # YU
    'afii10049': '042F',  # YA
    'afii10065': '0430',  # a
    'afii10066': '0431',  # be
    'afii10067': '0432',  # ve
    'afii10068': '0433',  # ghe
    'afii10069': '0434',  # de
    'afii10070': '0435',  # ie
    'afii10071': '0451',  # io
    'afii10072': '0436',  # zhe
    'afii10073': '0437',  # ze
    'afii10074': '0438',  # i
    'afii10075': '0439',  # short i
    'afii10076': '043A',  # ka
    'afii10077': '043B',  # el
    'afii10078': '043C',  # em
    'afii10079': '043D',  # en
    'afii10080': '043E',  # o
    'afii10081': '043F',  # pe
    'afii10082': '0440',  # er
    'afii10083': '0441',  # es
    'afii10084': '0442',  # te
    'afii10085': '0443',  # u
    'afii10086': '0444',  # ef
    'afii10087': '0445',  # ha
    'afii10088': '0446',  # tse
    'afii10089': '0447',  # che
    'afii10090': '0448',  # sha
    'afii10091': '0449',  # shcha
    'afii10092': '044A',  # hard sign
    'afii10093': '044B',  # yeru
    'afii10094': '044C',  # soft sign
    'afii10095': '044D',  # e
    'afii10096': '044E',  # yu
    'afii10097': '044F',  # ya
    'afii10050': '0490',  # GHE WITH UPTURN
    'afii10098': '0491',  # ghe with upturn
    'afii10051': '0402',  # DJE
    'afii10052': '0403',  # GJE
    'afii10053': '0404',  # UKRAINIAN IE
    'afii10054': '0405',  # DZE
    'afii10055': '0406',  # BYELORUSSIAN-UKRAINIAN I
    'afii10056': '0407',  # YI
    'afii10057': '0408',  # JE
    'afii10058': '0409',  # LJE
    'afii10059': '040A',  # NJE
    'afii10060': '040B',  # TSHE
    'afii10061': '040C',  # KJE
    'afii10062': '040E',  # SHORT U
    'afii10145': '040F',  # DZHE
    'afii10099': '0452',  # dje
    'afii10100': '0453',  # gje
    'afii10101': '0454',  # ukrainian ie
    'afii10102': '0455',  # dze
    'afii10103': '0456',  # byelorussian-ukrainian i
    'afii10104': '0457',  # yi
    'afii10105': '0458',  # je
    'afii10106': '0459',  # lje
    'afii10107': '045A',  # nje
    'afii10108': '045B',  # tshe
    'afii10109': '045C',  # kje
    'afii10110': '045E',  # short u
    'afii10193': '045F',  # dzhe
    'afii10146': '0462',  # YAT
    'afii10194': '0463',  # yat
    'afii10147': '0472',  # FITA
    'afii10195': '0473',  # fita
    'afii10148': '0474',  # IZHITSA
    'afii10196': '0475',  # izhitsa
    
    # Hebrew
    'afii57664': '05D0',  # ALEF
    'afii57665': '05D1',  # BET
    'afii57666': '05D2',  # GIMEL
    'afii57667': '05D3',  # DALET
    'afii57668': '05D4',  # HE
    'afii57669': '05D5',  # VAV
    'afii57670': '05D6',  # ZAYIN
    'afii57671': '05D7',  # HET
    'afii57672': '05D8',  # TET
    'afii57673': '05D9',  # YOD
    'afii57674': '05DA',  # FINAL KAF
    'afii57675': '05DB',  # KAF
    'afii57676': '05DC',  # LAMED
    'afii57677': '05DD',  # FINAL MEM
    'afii57678': '05DE',  # MEM
    'afii57679': '05DF',  # FINAL NUN
    'afii57680': '05E0',  # NUN
    'afii57681': '05E1',  # SAMEKH
    'afii57682': '05E2',  # AYIN
    'afii57683': '05E3',  # FINAL PE
    'afii57684': '05E4',  # PE
    'afii57685': '05E5',  # FINAL TSADI
    'afii57686': '05E6',  # TSADI
    'afii57687': '05E7',  # QOF
    'afii57688': '05E8',  # RESH
    'afii57689': '05E9',  # SHIN
    'afii57690': '05EA',  # TAV
    
    # Greek
    'afii57595': '0391',  # ALPHA
    'afii57596': '0392',  # BETA
    'afii57597': '0393',  # GAMMA
    'afii57598': '0394',  # DELTA
    'afii57599': '0395',  # EPSILON
    'afii57600': '0396',  # ZETA
    'afii57601': '0397',  # ETA
    'afii57602': '0398',  # THETA
    'afii57603': '0399',  # IOTA
    'afii57604': '039A',  # KAPPA
    'afii57605': '039B',  # LAMDA
    'afii57606': '039C',  # MU
    'afii57607': '039D',  # NU
    'afii57608': '039E',  # XI
    'afii57609': '039F',  # OMICRON
    'afii57610': '03A0',  # PI
    'afii57611': '03A1',  # RHO
    'afii57612': '03A3',  # SIGMA
    'afii57613': '03A4',  # TAU
    'afii57614': '03A5',  # UPSILON
    'afii57615': '03A6',  # PHI
    'afii57616': '03A7',  # CHI
    'afii57617': '03A8',  # PSI
    'afii57618': '03A9',  # OMEGA
    'afii57619': '03B1',  # alpha
    'afii57620': '03B2',  # beta
    'afii57621': '03B3',  # gamma
    'afii57622': '03B4',  # delta
    'afii57623': '03B5',  # epsilon
    'afii57624': '03B6',  # zeta
    'afii57625': '03B7',  # eta
    'afii57626': '03B8',  # theta
    'afii57627': '03B9',  # iota
    'afii57628': '03BA',  # kappa
    'afii57629': '03BB',  # lamda
    'afii57630': '03BC',  # mu
    'afii57631': '03BD',  # nu
    'afii57632': '03BE',  # xi
    'afii57633': '03BF',  # omicron
    'afii57634': '03C0',  # pi
    'afii57635': '03C1',  # rho
    'afii57636': '03C2',  # final sigma
    'afii57637': '03C3',  # sigma
    'afii57638': '03C4',  # tau
    'afii57639': '03C5',  # upsilon
    'afii57640': '03C6',  # phi
    'afii57641': '03C7',  # chi
    'afii57642': '03C8',  # psi
    'afii57643': '03C9',  # omega
    
    # Additional common AFII codes
    'afii61664': '060C',  # ARABIC COMMA
    'afii61573': '061B',  # ARABIC SEMICOLON
    'afii61574': '061F',  # ARABIC QUESTION MARK
    'afii08941': '20A4',  # LIRA SIGN
}


def get_nice_name_from_unicode(unicode_value):
    """
    Get nice name from Unicode value using Glyphs' built-in glyph info.
    Returns None if no nice name is available.
    """
    try:
        # Try to get the production name (nice name) from Glyphs
        glyph_info = Glyphs.glyphInfoForUnicode(unicode_value)
        if glyph_info and glyph_info.name:
            # Check if it's actually a nice name (not a uni name)
            if not glyph_info.name.startswith('uni') and not glyph_info.name.startswith('u'):
                return glyph_info.name
    except:
        pass
    return None


def get_new_name_for_afii(afii_name):
    """
    Get the new name for an AFII glyph.
    Returns (new_name, name_type) where name_type is 'nice', 'uni', or None
    """
    # Check if it's an AFII name
    if not afii_name.startswith('afii'):
        return None, None
    
    # Look up the Unicode value
    unicode_value = AFII_TO_UNICODE.get(afii_name)
    if not unicode_value:
        return None, None
    
    # Try to get a nice name first
    nice_name = get_nice_name_from_unicode(unicode_value)
    if nice_name:
        return nice_name, 'nice'
    
    # Fall back to uni name
    uni_name = f"uni{unicode_value}"
    return uni_name, 'uni'


def rename_glyph(font, old_name, new_name):
    """
    Rename a glyph in the font.
    Returns True if successful, False otherwise.
    """
    glyph = font.glyphs[old_name]
    if not glyph:
        return False
    
    # Check if new name already exists
    if font.glyphs[new_name]:
        print(f"  ⚠️  Cannot rename {old_name} to {new_name}: name already exists")
        return False
    
    try:
        glyph.name = new_name
        return True
    except Exception as e:
        print(f"  ⚠️  Failed to rename {old_name} to {new_name}: {e}")
        return False


# Main execution
def main():
    # Check if a font is open
    font = Glyphs.font
    if not font:
        Message("No Font Open", "Please open a font first.")
        return
    
    # Check if glyphs are selected
    selected_layers = font.selectedLayers
    if not selected_layers:
        Message("No Selection", "Please select glyphs first.")
        return
    
    # Get unique glyph names from selection
    selected_glyph_names = list(set([layer.parent.name for layer in selected_layers if layer.parent]))
    
    if not selected_glyph_names:
        Message("No Valid Selection", "Please select valid glyphs.")
        return
    
    print(f"\n=== Rename AFII Glyphs to Nice Names ===")
    print(f"Selected {len(selected_glyph_names)} glyphs")
    
    # Find AFII glyphs and determine new names
    afii_glyphs = []
    for glyph_name in selected_glyph_names:
        if glyph_name.startswith('afii'):
            new_name, name_type = get_new_name_for_afii(glyph_name)
            if new_name:
                afii_glyphs.append((glyph_name, new_name, name_type))
    
    if not afii_glyphs:
        Message("No AFII Glyphs", "No AFII-named glyphs found in selection.")
        print("No AFII glyphs found in selection")
        return
    
    # Show preview
    print(f"\nFound {len(afii_glyphs)} AFII glyphs to rename:")
    nice_count = sum(1 for _, _, t in afii_glyphs if t == 'nice')
    uni_count = sum(1 for _, _, t in afii_glyphs if t == 'uni')
    print(f"  {nice_count} will get nice names")
    print(f"  {uni_count} will get uni names")
    
    preview_list = []
    for old, new, name_type in afii_glyphs[:10]:
        marker = "✨" if name_type == 'nice' else "→"
        preview_list.append(f"{old} {marker} {new}")
    
    preview_text = "\n".join(preview_list)
    if len(afii_glyphs) > 10:
        preview_text += f"\n...and {len(afii_glyphs) - 10} more"
    
    # Ask for confirmation
    message = f"Rename {len(afii_glyphs)} AFII glyphs?\n({nice_count} nice names, {uni_count} uni names)\n\n{preview_text}"
    result = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(
        "Rename AFII Glyphs",
        "Rename",
        "Cancel",
        None,
        message
    ).runModal()
    
    if result != 1:  # 1 = default button (Rename)
        print("Cancelled by user")
        return
    
    # Perform renaming
    renamed_count = 0
    failed_count = 0
    
    print("\nRenaming glyphs:")
    for old_name, new_name, name_type in afii_glyphs:
        marker = "✨" if name_type == 'nice' else "→"
        if rename_glyph(font, old_name, new_name):
            print(f"  {marker} {old_name} → {new_name}")
            renamed_count += 1
        else:
            failed_count += 1
    
    # Show results
    result_msg = f"✓ Renamed {renamed_count} glyphs"
    if failed_count > 0:
        result_msg += f"\n⚠️  {failed_count} failed"
    
    Message("Complete", result_msg)
    print(f"\n{result_msg}")


# Import NSAlert
from AppKit import NSAlert

# Run the script
main()