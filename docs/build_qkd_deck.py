"""Build HDFC Quantum-Safe Communications Deck (PowerPoint).

Audience: MD, CTO, CEO, CISO, CRO, senior executives, enterprise architects.
Topic: post-quantum cryptography (PQC) + quantum key distribution (QKD)
       roadmap for HDFC's HQ (Mumbai) <-> Primary DC (Mumbai) <-> Far DR
       (Delhi) topology, including HSM key-hierarchy deep-dive, costs, and
       a 36-month adoption roadmap.

Theme: HDFC brand (navy + red + teal + gold), 16:9 widescreen, HDFC logo on
       every slide.

Regenerate the deck:
    pip install python-pptx
    python docs/build_qkd_deck.py
    # writes HDFC_Quantum_Safe_Comms_Deck.pptx alongside this script

The helpers / palette below are kept in sync with docs/build_deck.py so the
quantum-safe-comms deck visually matches the executive deck. If you tweak
the palette or logo placement, do it in both files.
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree
import os

# ---------- Brand palette (mirrors build_deck.py) -------------------
NAVY     = RGBColor(0x0A, 0x1E, 0x3F)
NAVY2    = RGBColor(0x12, 0x2C, 0x55)
RED      = RGBColor(0xED, 0x23, 0x2A)
GOLD     = RGBColor(0xF5, 0xB7, 0x2E)
TEAL     = RGBColor(0x2E, 0xC4, 0xB6)
WHITE    = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT    = RGBColor(0xE6, 0xEA, 0xF2)
MUTED    = RGBColor(0x9A, 0xA5, 0xBC)
GREEN    = RGBColor(0x2E, 0xCC, 0x71)
ORANGE   = RGBColor(0xE6, 0x7E, 0x22)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

_ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
HDFC_LOGO_PATH = os.path.join(_ASSET_DIR, "hdfc_bank_logo.png")

_SLIDE_IDX = [0]
def _idx():
    _SLIDE_IDX[0] += 1
    return _SLIDE_IDX[0]


def add_logo(slide, *, large=False):
    if not os.path.exists(HDFC_LOGO_PATH):
        return None
    if large:
        w = Inches(2.6); h = Inches(0.45)
        left = SLIDE_W - w - Inches(0.55); top = Inches(0.55)
    else:
        w = Inches(1.45); h = Inches(0.25)
        left = SLIDE_W - w - Inches(0.40); top = Inches(0.40)
    return slide.shapes.add_picture(HDFC_LOGO_PATH, left, top, width=w, height=h)


def add_bg(slide, color=NAVY):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    bg.fill.solid(); bg.fill.fore_color.rgb = color
    bg.line.fill.background(); bg.shadow.inherit = False
    spTree = bg._element.getparent()
    spTree.remove(bg._element); spTree.insert(2, bg._element)
    return bg


def _add_rich_runs(p, line, *, size, bold, italic, color, font):
    rest = line
    parts = []
    while "**" in rest:
        head, _, tail = rest.partition("**")
        mid, _, tail2 = tail.partition("**")
        parts.append((head, False)); parts.append((mid, True))
        rest = tail2
    parts.append((rest, False))
    if not any(seg for seg, _ in parts):
        run = p.add_run(); run.text = ""
        run.font.name = font; run.font.size = Pt(size)
        run.font.bold = bold; run.font.italic = italic
        run.font.color.rgb = color
        return
    for seg, is_bold in parts:
        if not seg:
            continue
        run = p.add_run(); run.text = seg
        run.font.name = font; run.font.size = Pt(size)
        run.font.bold = is_bold or bold
        run.font.italic = italic
        run.font.color.rgb = color


def add_text(slide, left, top, width, height, text, *,
             size=18, bold=False, color=WHITE, align=PP_ALIGN.LEFT,
             font="Calibri", anchor=MSO_ANCHOR.TOP, italic=False):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = anchor
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        _add_rich_runs(p, line, size=size, bold=bold, italic=italic,
                       color=color, font=font)
    return tb


def add_bullets(slide, left, top, width, height, items, *,
                size=16, color=WHITE, bullet_color=RED, font="Calibri",
                line_spacing=1.15, bold_first=False):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.05)
    for i, item in enumerate(items):
        if isinstance(item, tuple):
            text, indent = item
        else:
            text, indent = item, 0
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT; p.level = indent
        bullet_run = p.add_run()
        bullet_run.text = "\u25A0  " if indent == 0 else "\u2022  "
        bullet_run.font.name = font; bullet_run.font.size = Pt(size)
        bullet_run.font.color.rgb = bullet_color; bullet_run.font.bold = True
        rest = text
        parts = []
        while "**" in rest:
            head, _, tail = rest.partition("**")
            mid, _, tail2 = tail.partition("**")
            parts.append((head, False)); parts.append((mid, True))
            rest = tail2
        parts.append((rest, False))
        for seg, is_bold in parts:
            if not seg:
                continue
            run = p.add_run(); run.text = seg
            run.font.name = font; run.font.size = Pt(size)
            run.font.bold = is_bold or (bold_first and indent == 0)
            run.font.color.rgb = color
        try:
            p.line_spacing = line_spacing
        except Exception:
            pass
    return tb


def add_rect(slide, left, top, width, height, fill, line=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line; sh.line.width = Pt(0.5)
    sh.shadow.inherit = False
    return sh


def add_round_rect(slide, left, top, width, height, fill, line=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    sh.adjustments[0] = 0.08
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line; sh.line.width = Pt(1)
    sh.shadow.inherit = False
    return sh


def add_arrow(slide, x1, y1, x2, y2, color=RED, weight=2):
    line = slide.shapes.add_connector(1, x1, y1, x2, y2)
    line.line.color.rgb = color; line.line.width = Pt(weight)
    ln = line.line._get_or_add_ln()
    tail = etree.SubElement(ln, qn("a:tailEnd"))
    tail.set("type", "triangle"); tail.set("w", "med"); tail.set("h", "med")
    return line


def header(slide, idx, title, kicker=None):
    add_rect(slide, Inches(0.5), Inches(0.45), Inches(0.12), Inches(0.55), RED)
    if kicker:
        add_text(slide, Inches(0.72), Inches(0.40), Inches(8), Inches(0.35),
                 kicker.upper(), size=11, color=GOLD, bold=True)
    add_text(slide, Inches(0.72), Inches(0.66), Inches(10.5), Inches(0.65),
             title, size=24, bold=True, color=WHITE)
    add_rect(slide, Inches(0.5), Inches(1.35), Inches(12.3), Emu(9525), NAVY2)
    add_logo(slide)
    footer(slide, idx)


def footer(slide, idx):
    add_text(slide, Inches(0.5), Inches(7.05), Inches(7), Inches(0.3),
             "HDFC Bank \u2022 Quantum-Safe Communications \u2022 Confidential",
             size=9, color=MUTED)
    add_text(slide, Inches(11.8), Inches(7.05), Inches(1.2), Inches(0.3),
             f"{idx:02d}", size=9, color=MUTED, align=PP_ALIGN.RIGHT)


def style_table(tbl, *, header_fill=NAVY2, header_font=GOLD,
                body_fill=NAVY, body_font=LIGHT, font_size=11,
                header_size=12, header_bold=True):
    """Apply HDFC styling to a python-pptx table."""
    rows = len(tbl.rows)
    cols = len(tbl.columns)
    for r in range(rows):
        for c in range(cols):
            cell = tbl.cell(r, c)
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = header_fill
            else:
                cell.fill.fore_color.rgb = body_fill
            for p in cell.text_frame.paragraphs:
                for run in p.runs:
                    run.font.name = "Calibri"
                    if r == 0:
                        run.font.size = Pt(header_size)
                        run.font.bold = header_bold
                        run.font.color.rgb = header_font
                    else:
                        run.font.size = Pt(font_size)
                        run.font.color.rgb = body_font
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.04)
            cell.margin_bottom = Inches(0.04)


# ====================================================================
# Build deck
# ====================================================================

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
blank = prs.slide_layouts[6]


# --------------------- 1. TITLE -------------------------------------
_idx()
s = prs.slides.add_slide(blank); add_bg(s, NAVY)
add_rect(s, 0, Inches(6.8), SLIDE_W, Inches(0.7), NAVY2)
add_rect(s, 0, Inches(0), Inches(0.4), SLIDE_H, RED)
add_logo(s, large=True)
add_text(s, Inches(1.0), Inches(0.9), Inches(9), Inches(0.4),
         "HDFC BANK \u2022 BOARD AND EXECUTIVE BRIEFING",
         size=12, color=GOLD, bold=True)
add_text(s, Inches(1.0), Inches(1.5), Inches(11.5), Inches(2.0),
         "Quantum-Safe\nCommunications",
         size=54, bold=True, color=WHITE)
add_text(s, Inches(1.0), Inches(3.9), Inches(11), Inches(0.6),
         "PQC + QKD architecture for HDFC \u2014",
         size=22, color=LIGHT)
add_text(s, Inches(1.0), Inches(4.3), Inches(11), Inches(0.6),
         "HQ Mumbai \u2022 Primary DC Mumbai \u2022 Far DR Delhi",
         size=22, color=LIGHT)
add_rect(s, Inches(1.0), Inches(5.3), Inches(0.12), Inches(0.35), TEAL)
add_text(s, Inches(1.2), Inches(5.25), Inches(8), Inches(0.4),
         "Author: SVP \u2014 Kranthi Molleti",
         size=14, color=LIGHT, bold=True)
add_text(s, Inches(1.0), Inches(6.95), Inches(11), Inches(0.4),
         "Confidential \u2014 internal circulation only",
         size=10, color=MUTED, italic=True)


# --------------------- 2. EXECUTIVE SUMMARY -------------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, _idx(), "Quantum-safe communications \u2014 the ask in one slide",
       kicker="Why we are here")

col_y = Inches(1.55)
col_h = Inches(2.85)
col_w = Inches(4.05)
gap   = Inches(0.075)

labels = [
    ("THE THREAT",
     "Adversaries can record encrypted traffic today and decrypt it in 2030\u201335 once cryptographically-relevant quantum computers (CRQC) arrive \u2014 \u201Charvest now, decrypt later\u201D. Our HQ\u2013DC, DC\u2013DR and partner-bank links all use RSA/ECDH today."),
    ("THE ARCHITECTURE",
     "Two-layer defence \u2014 **PQC (Kyber + Dilithium)** as the workhorse on every link including branches and customer apps; **QKD as a selective overlay** on the Mumbai HQ\u2013DC metro fibre. AES-256 inside the HSM is already largely quantum-safe."),
    ("THE ASK",
     "Rs 50\u201370 Cr over FY26\u2013FY28: HSM refresh + PQC migration + QKD pilot on the HQ\u2013DC metro link + R&D bet on satellite-QKD with ISRO for the Delhi DR \u2014 puts HDFC ahead of RBI and on the National Quantum Mission map."),
]
colors_ = [RED, TEAL, GOLD]
for i, ((lbl, body), c) in enumerate(zip(labels, colors_)):
    x = Inches(0.5) + i * (col_w + gap)
    add_round_rect(s, x, col_y, col_w, col_h, NAVY2)
    add_rect(s, x, col_y, col_w, Inches(0.05), c)
    add_text(s, x + Inches(0.25), col_y + Inches(0.18), col_w - Inches(0.5), Inches(0.4),
             lbl, size=12, bold=True, color=c)
    add_text(s, x + Inches(0.25), col_y + Inches(0.7), col_w - Inches(0.5), col_h - Inches(0.8),
             body, size=12, color=LIGHT)

# bottom belt: 4 KPIs
add_round_rect(s, Inches(0.5), Inches(4.65), Inches(12.3), Inches(2.2), NAVY2)
add_text(s, Inches(0.7), Inches(4.78), Inches(11), Inches(0.4),
         "WHAT GOOD LOOKS LIKE BY FY28", size=12, bold=True, color=GOLD)
kpis = [
    ("100%",  "of internal mTLS,\nbranch IPsec, and customer-facing\nTLS migrated to **hybrid PQC**"),
    ("1 Gbps+", "**QKD-secured DWDM channel**\nbetween HQ Mumbai and\nPrimary DC Mumbai"),
    ("AES-256", "rotated **every ~1 sec** on the\nHQ\u2013DC link via QKD-derived\nsymmetric keys"),
    ("Rs 0",   "regulatory penalty exposure on\n**HNDL** \u2014 RBI / SEBI /\nFIU expectations met early"),
]
kx = Inches(0.7); ky = Inches(5.25); kw = Inches(2.95); kh = Inches(1.55)
for i, (big, small) in enumerate(kpis):
    x = kx + i * (kw + Inches(0.05))
    add_text(s, x, ky, kw, Inches(0.65), big,
             size=28, bold=True, color=WHITE)
    add_text(s, x, ky + Inches(0.65), kw, Inches(1.0), small,
             size=11, color=LIGHT)


# --------------------- 3. TOPOLOGY ----------------------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, _idx(), "HDFC topology \u2014 and the distance reality check",
       kicker="What we are protecting")

# left: topology diagram
diag_x = Inches(0.5); diag_y = Inches(1.6)
diag_w = Inches(7.6); diag_h = Inches(5.2)
add_round_rect(s, diag_x, diag_y, diag_w, diag_h, NAVY2)

add_text(s, diag_x + Inches(0.25), diag_y + Inches(0.15), diag_w - Inches(0.5), Inches(0.35),
         "FIBRE TOPOLOGY", size=11, bold=True, color=GOLD)

# HQ Mumbai (top-left)
hq_x = diag_x + Inches(0.6); hq_y = diag_y + Inches(0.7)
add_round_rect(s, hq_x, hq_y, Inches(2.6), Inches(0.95), NAVY)
add_rect(s, hq_x, hq_y, Inches(2.6), Inches(0.05), TEAL)
add_text(s, hq_x + Inches(0.15), hq_y + Inches(0.10), Inches(2.3), Inches(0.35),
         "HQ MUMBAI", size=10, bold=True, color=TEAL)
add_text(s, hq_x + Inches(0.15), hq_y + Inches(0.40), Inches(2.3), Inches(0.55),
         "Lower Parel / BKC\nTreasury, FX, MIS",
         size=10, color=LIGHT)

# Primary DC Mumbai (middle-left)
dc_x = diag_x + Inches(0.6); dc_y = diag_y + Inches(2.4)
add_round_rect(s, dc_x, dc_y, Inches(2.6), Inches(1.1), NAVY)
add_rect(s, dc_x, dc_y, Inches(2.6), Inches(0.05), RED)
add_text(s, dc_x + Inches(0.15), dc_y + Inches(0.10), Inches(2.3), Inches(0.35),
         "PRIMARY DC MUMBAI", size=10, bold=True, color=RED)
add_text(s, dc_x + Inches(0.15), dc_y + Inches(0.40), Inches(2.3), Inches(0.65),
         "Andheri / Navi Mumbai\nCore banking, card switch,\nUPI / NEFT / RTGS, fraud",
         size=10, color=LIGHT)

# DR Delhi (right side)
dr_x = diag_x + Inches(4.5); dr_y = diag_y + Inches(2.4)
add_round_rect(s, dr_x, dr_y, Inches(2.6), Inches(1.1), NAVY)
add_rect(s, dr_x, dr_y, Inches(2.6), Inches(0.05), GOLD)
add_text(s, dr_x + Inches(0.15), dr_y + Inches(0.10), Inches(2.3), Inches(0.35),
         "FAR DR DELHI", size=10, bold=True, color=GOLD)
add_text(s, dr_x + Inches(0.15), dr_y + Inches(0.40), Inches(2.3), Inches(0.65),
         "Different seismic zone\nAsync replica\nRPO few minutes",
         size=10, color=LIGHT)

# HQ -> DC arrow (vertical, short)
add_arrow(s,
          hq_x + Inches(1.3), hq_y + Inches(0.95),
          dc_x + Inches(1.3), dc_y, color=TEAL, weight=2)
add_text(s, hq_x + Inches(1.45), hq_y + Inches(1.05), Inches(2.5), Inches(0.4),
         "5\u201330 km\nintra-Mumbai dark fibre",
         size=10, color=TEAL, italic=True)

# DC -> DR arrow (horizontal, long, with break label)
add_arrow(s,
          dc_x + Inches(2.6), dc_y + Inches(0.55),
          dr_x, dr_y + Inches(0.55), color=GOLD, weight=2)
add_text(s, dc_x + Inches(2.75), dc_y + Inches(0.18), Inches(1.6), Inches(0.4),
         "~1,150 km",
         size=12, bold=True, color=GOLD)
add_text(s, dc_x + Inches(2.75), dc_y + Inches(0.55), Inches(1.65), Inches(0.55),
         "carrier DWDM /\nMPLS, multi-hop",
         size=9, color=LIGHT, italic=True)

# Branches cluster (bottom)
br_x = diag_x + Inches(0.6); br_y = diag_y + Inches(4.1)
add_round_rect(s, br_x, br_y, Inches(6.5), Inches(0.85), NAVY)
add_rect(s, br_x, br_y, Inches(6.5), Inches(0.05), MUTED)
add_text(s, br_x + Inches(0.15), br_y + Inches(0.10), Inches(6.3), Inches(0.35),
         "8,000+ BRANCHES \u2022 18,000+ ATMS",
         size=10, bold=True, color=MUTED)
add_text(s, br_x + Inches(0.15), br_y + Inches(0.40), Inches(6.3), Inches(0.45),
         "MPLS / SD-WAN / 4G-5G failover \u2014 multi-hop carrier IP, no dark fibre",
         size=10, color=LIGHT)

# DC -> Branches arrow (diagonal)
add_arrow(s,
          dc_x + Inches(1.3), dc_y + Inches(1.1),
          br_x + Inches(3.0), br_y, color=MUTED, weight=1.5)

# right: distance reality table
tbl_x = Inches(8.4); tbl_y = Inches(1.6)
tbl_w = Inches(4.6); tbl_h = Inches(5.2)
add_round_rect(s, tbl_x, tbl_y, tbl_w, tbl_h, NAVY2)
add_text(s, tbl_x + Inches(0.25), tbl_y + Inches(0.15), tbl_w - Inches(0.5), Inches(0.35),
         "DISTANCE REALITY CHECK", size=11, bold=True, color=GOLD)

zones = [
    ("HQ Mumbai \u2194 DC Mumbai", "5\u201330 km",
     "QKD: yes \u2014 sweet spot.",
     "Standard Toshiba MDI-QKD or ID Quantique Clavis comfortably handle this; coexistence with classical DWDM proven up to ~100 km (JPMC 2022).", TEAL),
    ("DC Mumbai \u2194 DR Delhi", "~1,150 km",
     "QKD: no commercial path.",
     "QKD is exponentially loss-limited (~0.2 dB/km). Practical reach ~120 km. Need trusted-node relays (China Beijing\u2013Shanghai) or satellite (Micius / EAGLE-1) \u2014 not available in India yet.", GOLD),
    ("Branches \u2194 DC", "10\u20132,000 km",
     "QKD: physically infeasible.",
     "Multi-hop carrier IP/MPLS, shared paths, no dark fibre. PQC over SD-WAN is the only viable path.", MUTED),
]
zy = tbl_y + Inches(0.55)
zh = Inches(1.45)
for i, (link, dist, verdict, body, c) in enumerate(zones):
    yy = zy + i * (zh + Inches(0.05))
    add_round_rect(s, tbl_x + Inches(0.18), yy, tbl_w - Inches(0.36), zh, NAVY)
    add_rect(s, tbl_x + Inches(0.18), yy, Inches(0.05), zh, c)
    add_text(s, tbl_x + Inches(0.32), yy + Inches(0.06), tbl_w - Inches(0.5), Inches(0.32),
             link, size=11, bold=True, color=c)
    add_text(s, tbl_x + Inches(0.32), yy + Inches(0.34), tbl_w - Inches(0.5), Inches(0.32),
             f"{dist}  \u2014  {verdict}",
             size=10, bold=True, color=LIGHT)
    add_text(s, tbl_x + Inches(0.32), yy + Inches(0.65), tbl_w - Inches(0.5), Inches(0.78),
             body, size=9, color=LIGHT)


# --------------------- 4. THE THREAT (HNDL) -------------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, _idx(), "Harvest now, decrypt later \u2014 the urgent threat",
       kicker="Why this is urgent, not theoretical")

# top: timeline arrow
tl_x = Inches(0.7); tl_y = Inches(1.8)
tl_w = Inches(11.9); tl_h = Inches(2.2)
add_round_rect(s, tl_x, tl_y, tl_w, tl_h, NAVY2)
add_text(s, tl_x + Inches(0.25), tl_y + Inches(0.15), Inches(11), Inches(0.35),
         "THE 10-YEAR THREAT TIMELINE", size=11, bold=True, color=GOLD)

# arrow line
add_rect(s, tl_x + Inches(0.4), tl_y + Inches(1.05), tl_w - Inches(0.8), Inches(0.04), MUTED)

milestones = [
    ("2024\u201326",  "Adversaries silently record encrypted traffic\nfrom carrier fibre, optical amplifier huts,\nor compromised leased lines.", RED),
    ("2027\u201329",  "NIST PQC standards (Kyber, Dilithium) become\nmandatory in regulated sectors. Banks that\nhave not migrated face audit findings.", GOLD),
    ("2030\u201332",  "First **CRQCs** with 1\u20133 M physical qubits.\nShor's algorithm runs against captured\nRSA-2048 / ECDH-256 handshakes.", ORANGE),
    ("2033\u201335",  "All **harvested 2024\u201332 traffic is decrypted**.\nKYC, loan files, treasury positions, source code,\nHSM key wraps \u2014 all readable.", RED),
]
mw = (tl_w - Inches(0.8)) / 4
mx0 = tl_x + Inches(0.4)
for i, (yr, body, c) in enumerate(milestones):
    cx = mx0 + i * mw + mw / 2
    # marker
    dot = add_round_rect(s, cx - Inches(0.075), tl_y + Inches(0.95), Inches(0.18), Inches(0.18), c)
    # label above
    add_text(s, cx - mw/2 + Inches(0.1), tl_y + Inches(0.45), mw - Inches(0.2), Inches(0.4),
             yr, size=12, bold=True, color=c, align=PP_ALIGN.CENTER)
    # body below
    add_text(s, cx - mw/2 + Inches(0.1), tl_y + Inches(1.25), mw - Inches(0.2), Inches(0.85),
             body, size=9, color=LIGHT, align=PP_ALIGN.CENTER)

# bottom: what's at risk for HDFC
bot_x = Inches(0.5); bot_y = Inches(4.25); bot_w = Inches(12.3); bot_h = Inches(2.55)
add_round_rect(s, bot_x, bot_y, bot_w, bot_h, NAVY2)
add_text(s, bot_x + Inches(0.25), bot_y + Inches(0.15), bot_w - Inches(0.5), Inches(0.35),
         "WHAT IS ON HDFC'S HQ\u2013DC AND DC\u2013DR FIBRE TODAY", size=11, bold=True, color=GOLD)

risks = [
    ("Core banking journal", "Every CASA, FD, loan tx \u2014 PII + balances. 10s of Gbps."),
    ("Card switch", "Every card auth \u2014 PAN, ARQC cryptograms. 100k+ tps peak."),
    ("UPI / NEFT / RTGS", "Every retail transfer \u2014 VPA, beneficiary, amount."),
    ("HSM cluster sync", "Master keys that derive every PIN, MAC, working key. Tiny but catastrophic."),
    ("Treasury / FX feeds", "Live rates, derivatives positions, trade tickets."),
    ("Backups + admin sessions", "Full DB images. SSH/RDP root creds."),
]
cx0 = bot_x + Inches(0.3); cy0 = bot_y + Inches(0.7)
cw = (bot_w - Inches(0.6)) / 3
ch = (bot_h - Inches(0.85)) / 2
for i, (k, v) in enumerate(risks):
    rr = i // 3; cc = i % 3
    rx = cx0 + cc * cw; ry = cy0 + rr * ch
    add_text(s, rx, ry, cw - Inches(0.1), Inches(0.32),
             k, size=11, bold=True, color=RED)
    add_text(s, rx, ry + Inches(0.32), cw - Inches(0.1), ch - Inches(0.4),
             v, size=10, color=LIGHT)


# --------------------- 5. TWO DEFENCES SIDE-BY-SIDE -----------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, _idx(), "Two defences \u2014 and why we need both",
       kicker="The architecture")

intro_y = Inches(1.55)
add_text(s, Inches(0.5), intro_y, Inches(12.3), Inches(0.4),
         "PQC handles **breadth** \u2014 every TLS, every IPsec, every branch. QKD handles **depth** \u2014 the 2\u20134 highest-value pipes inside a metro.",
         size=12, italic=True, color=LIGHT)

col_y = Inches(2.05); col_h = Inches(4.85); col_w = Inches(6.05); gap = Inches(0.2)

# Left column: PQC
pqc_x = Inches(0.5)
add_round_rect(s, pqc_x, col_y, col_w, col_h, NAVY2)
add_rect(s, pqc_x, col_y, col_w, Inches(0.08), TEAL)
add_text(s, pqc_x + Inches(0.3), col_y + Inches(0.18), col_w - Inches(0.6), Inches(0.4),
         "POST-QUANTUM CRYPTOGRAPHY (PQC)", size=12, bold=True, color=TEAL)
add_text(s, pqc_x + Inches(0.3), col_y + Inches(0.55), col_w - Inches(0.6), Inches(0.4),
         "Math-based defence \u2014 software upgrade",
         size=11, italic=True, color=LIGHT)
add_bullets(s, pqc_x + Inches(0.3), col_y + Inches(1.05), col_w - Inches(0.6), col_h - Inches(1.2), [
    "Hard-math problems believed secure against **classical + quantum**: lattice (ML-KEM Kyber), hash-based signatures (SLH-DSA SPHINCS+).",
    "**Drop-in replacement** for ECDH/RSA in TLS, IPsec, SSH, JWT, code signing.",
    "Run in **hybrid mode** \u2014 ECDH + Kyber together \u2014 so neither algorithm alone needs to be perfect.",
    "**NIST FIPS-203 / 204 / 205** standardised Aug 2024. Apple iOS 18, Chrome, Cloudflare ship Kyber today.",
    "Cost \u2014 **firmware + library upgrade**, no new hardware. Same fibre, same boxes.",
    "**Use everywhere:** branches, customer apps, partner APIs, internal services.",
], size=11, color=LIGHT, bullet_color=TEAL, line_spacing=1.18)

# Right column: QKD
qkd_x = pqc_x + col_w + gap
add_round_rect(s, qkd_x, col_y, col_w, col_h, NAVY2)
add_rect(s, qkd_x, col_y, col_w, Inches(0.08), RED)
add_text(s, qkd_x + Inches(0.3), col_y + Inches(0.18), col_w - Inches(0.6), Inches(0.4),
         "QUANTUM KEY DISTRIBUTION (QKD)", size=12, bold=True, color=RED)
add_text(s, qkd_x + Inches(0.3), col_y + Inches(0.55), col_w - Inches(0.6), Inches(0.4),
         "Physics-based defence \u2014 selective overlay",
         size=11, italic=True, color=LIGHT)
add_bullets(s, qkd_x + Inches(0.3), col_y + Inches(1.05), col_w - Inches(0.6), col_h - Inches(1.2), [
    "Sends single photons \u2014 **measuring disturbs them** (Heisenberg uncertainty), so any eavesdropper is detected.",
    "Generates a stream of **fresh AES-256 keys every ~1 sec** between two endpoints over fibre.",
    "Feeds those keys into existing **MACsec / IPsec / OTN encryptors** for AES-256 bulk encryption of 10\u2013400 Gbps.",
    "**Information-theoretically secure** for the key-exchange step \u2014 no math, no Shor, no Grover.",
    "Limits: **dedicated dark fibre or DWDM wavelength**, ~120 km without trusted-node relays, dedicated hardware (Toshiba / ID Quantique).",
    "**Use selectively:** HQ\u2013DC and inter-DC fibre inside a metro. **Not** for branches, customer apps, or DR > 200 km.",
], size=11, color=LIGHT, bullet_color=RED, line_spacing=1.18)


# --------------------- 6. ZONE-BY-ZONE OPTIONS ----------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, _idx(), "Recommended option per zone",
       kicker="What we do where")

# build a styled table
table_left = Inches(0.5); table_top = Inches(1.55)
table_w = Inches(12.3); table_h = Inches(5.3)
rows = 8; cols = 4
tbl_shape = s.shapes.add_table(rows, cols, table_left, table_top, table_w, table_h)
tbl = tbl_shape.table
# Column widths
tbl.columns[0].width = Inches(3.4)
tbl.columns[1].width = Inches(3.4)
tbl.columns[2].width = Inches(3.0)
tbl.columns[3].width = Inches(2.5)
headers_ = ["Zone", "Recommended option", "Why", "Maturity"]
for c, h in enumerate(headers_):
    tbl.cell(0, c).text = h
rows_data = [
    ("HQ Mumbai \u2194 Primary DC Mumbai",
     "Hybrid PQC + QKD at IPsec/MACsec layer; QKD AES-256 keys rotated every ~1 sec",
     "Highest-value pipe; in metro QKD range; carries core-bank sync, HSM cluster, treasury",
     "Production (HSBC, JPMC)"),
    ("Primary DC Mumbai \u2194 Far DR Delhi",
     "PQC-only (Kyber+ECDH hybrid) over MACsec/IPsec; AES-256 rotated every 60 sec",
     "1,150 km is beyond direct QKD; PQC + frequent rotation is correct answer for HNDL",
     "NIST FIPS-203 (Aug 2024)"),
    ("HQ \u2194 Treasury / FX (intra-building)",
     "MACsec + PQC firmware on switches; HSM-backed identity",
     "Inside trust boundary; main concern is cert lifecycle and crypto-agility",
     "Standard refresh"),
    ("DC \u2194 NPCI / RBI / SWIFT",
     "PQC over carrier links; HSM-backed mutual TLS",
     "Regulatory rails; can't self-deploy QKD; SWIFT CSP v2025/26 adds PQC",
     "Vendor-led"),
    ("Branches \u2194 Regional Hub \u2194 DC",
     "PQC over SD-WAN/MPLS; TLS handshake = ECDH + Kyber hybrid",
     "8,000+ sites; QKD physically infeasible; piggy-back on SD-WAN refresh",
     "FIPS-203 standard"),
    ("ATMs / POS",
     "PQC libraries on next ATM refresh; HSM-backed PIN encryption stays AES",
     "Slow refresh (~5\u20137 yrs); ride hardware refresh cycle",
     "Vendor roadmap"),
    ("Mobile / net banking",
     "Hybrid TLS \u2014 X25519 + ML-KEM-768; HSM-backed signing keys \u2192 ML-DSA",
     "Customer-facing; iOS 18, Chrome already negotiate Kyber",
     "Production at FAANG scale"),
]
for r, row in enumerate(rows_data, start=1):
    for c, val in enumerate(row):
        tbl.cell(r, c).text = val
style_table(tbl, font_size=10, header_size=11)


# --------------------- 7. HSM KEY HIERARCHY DEEP-DIVE ---------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, _idx(), "How keys are stored in an HSM \u2014 the hierarchy",
       kicker="HSM deep dive (1 of 2)")

# left: hierarchy diagram
hi_x = Inches(0.5); hi_y = Inches(1.55)
hi_w = Inches(7.5); hi_h = Inches(5.3)
add_round_rect(s, hi_x, hi_y, hi_w, hi_h, NAVY2)
add_text(s, hi_x + Inches(0.25), hi_y + Inches(0.15), hi_w - Inches(0.5), Inches(0.35),
         "KEY HIERARCHY \u2014 NEVER LEAVES THE HSM IN CLEAR",
         size=11, bold=True, color=GOLD)

# LMK box (top)
lmk_x = hi_x + Inches(2.0); lmk_y = hi_y + Inches(0.7)
lmk_w = Inches(3.5); lmk_h = Inches(0.85)
add_round_rect(s, lmk_x, lmk_y, lmk_w, lmk_h, NAVY)
add_rect(s, lmk_x, lmk_y, lmk_w, Inches(0.05), RED)
add_text(s, lmk_x + Inches(0.15), lmk_y + Inches(0.10), lmk_w - Inches(0.3), Inches(0.32),
         "LMK \u2014 Local Master Key (AES-256)", size=11, bold=True, color=RED)
add_text(s, lmk_x + Inches(0.15), lmk_y + Inches(0.40), lmk_w - Inches(0.3), Inches(0.42),
         "Generated in ceremony, split via Shamir,\nnever appears in clear outside HSM",
         size=9, color=LIGHT, italic=True)

# Three branches: ZMK, KEK, DEK roots
mid_y = lmk_y + lmk_h + Inches(0.4)
mid_h = Inches(0.85)
mid_w = Inches(2.15)
mid_gap = Inches(0.07)
mid_x0 = hi_x + Inches(0.25)

mid_blocks = [
    ("ZMK", "Zone Master Key (per partner:\nVisa, MC, NPCI, RBI)", TEAL),
    ("KEK", "Key Encryption Key\n(intra-bank, intra-DC)",   GOLD),
    ("DEK roots", "App-internal data\nencryption roots",      ORANGE),
]
mid_centers_x = []
for i, (lbl, body, c) in enumerate(mid_blocks):
    mx = mid_x0 + i * (mid_w + mid_gap)
    add_round_rect(s, mx, mid_y, mid_w, mid_h, NAVY)
    add_rect(s, mx, mid_y, mid_w, Inches(0.05), c)
    add_text(s, mx + Inches(0.15), mid_y + Inches(0.08), mid_w - Inches(0.3), Inches(0.32),
             lbl, size=10, bold=True, color=c)
    add_text(s, mx + Inches(0.15), mid_y + Inches(0.36), mid_w - Inches(0.3), mid_h - Inches(0.4),
             body, size=8.5, color=LIGHT)
    mid_centers_x.append(mx + mid_w / 2)
    # arrow from LMK (centre-bottom) to this block (centre-top)
    add_arrow(s, lmk_x + lmk_w / 2, lmk_y + lmk_h,
              mx + mid_w / 2, mid_y, color=MUTED, weight=1)

# Working keys (bottom row)
wk_y = mid_y + mid_h + Inches(0.4)
wk_h = Inches(1.1)
wk_blocks = [
    ("PIN keys, MAC keys,\nCard cryptograms (CVK,\nAC), DUKPT derivation",
     "These actually encrypt customer\nPINs, sign card cryptograms",
     TEAL),
    ("Working AES sessions for\nFinacle, fraud platform,\nmiddleware",
     "Short-lived; rotated daily;\nused by app calls into HSM",
     GOLD),
    ("Token / file encryption,\nLog integrity (HMAC),\nDB column encryption",
     "App-layer protection;\nGDPR/RBI data localisation",
     ORANGE),
]
for i, (k, v, c) in enumerate(wk_blocks):
    wx = mid_x0 + i * (mid_w + mid_gap)
    add_round_rect(s, wx, wk_y, mid_w, wk_h, NAVY)
    add_rect(s, wx, wk_y, mid_w, Inches(0.05), c)
    add_text(s, wx + Inches(0.13), wk_y + Inches(0.10), mid_w - Inches(0.26), Inches(0.55),
             k, size=8.5, bold=True, color=LIGHT)
    add_text(s, wx + Inches(0.13), wk_y + Inches(0.55), mid_w - Inches(0.26), wk_h - Inches(0.6),
             v, size=8, italic=True, color=MUTED)
    # arrow from corresponding mid block
    add_arrow(s, mid_centers_x[i], mid_y + mid_h,
              wx + mid_w / 2, wk_y, color=MUTED, weight=1)

# Caption strip at bottom
cap_y = hi_y + hi_h - Inches(0.55)
add_text(s, hi_x + Inches(0.25), cap_y, hi_w - Inches(0.5), Inches(0.4),
         "Apps see only **wrapped** key blobs from the database \u2014 the HSM unwraps inside its tamper-protected boundary, performs the op, discards plaintext.",
         size=9, color=LIGHT, italic=True)

# right: quantum impact column
ri_x = Inches(8.2); ri_y = Inches(1.55)
ri_w = Inches(4.7); ri_h = Inches(5.3)
add_round_rect(s, ri_x, ri_y, ri_w, ri_h, NAVY2)
add_text(s, ri_x + Inches(0.25), ri_y + Inches(0.15), ri_w - Inches(0.5), Inches(0.35),
         "WHERE QUANTUM HITS \u2014 AND WHAT IS ALREADY SAFE",
         size=11, bold=True, color=GOLD)

# table
qt_left = ri_x + Inches(0.25); qt_top = ri_y + Inches(0.55)
qt_w = ri_w - Inches(0.5); qt_h = Inches(3.85)
qrows = 6; qcols = 3
qtbl_shape = s.shapes.add_table(qrows, qcols, qt_left, qt_top, qt_w, qt_h)
qtbl = qtbl_shape.table
qtbl.columns[0].width = Inches(1.55)
qtbl.columns[1].width = Inches(1.55)
qtbl.columns[2].width = Inches(1.55)
hdr = ["Crypto inside HSM", "Quantum impact", "Fix"]
for c, h in enumerate(hdr):
    qtbl.cell(0, c).text = h
qrows_data = [
    ("AES-256 (LMK, KEK, working)", "Grover halves to ~128-bit. OK", "Stay on AES-256"),
    ("3DES (legacy DUKPT, old PIN)", "Broken classically already", "Migrate to AES DUKPT"),
    ("RSA-2048/3072 (TR-34, certs, code sign)", "Shor breaks", "ML-DSA / ML-KEM"),
    ("ECDSA / ECDH (mTLS, key agreement)", "Shor breaks", "ML-KEM, ML-DSA"),
    ("SHA-256 / SHA-3 (MAC, integrity)", "Grover halves preimage. OK", "Stay on SHA-256/384"),
]
for r, row in enumerate(qrows_data, start=1):
    for c, val in enumerate(row):
        qtbl.cell(r, c).text = val
style_table(qtbl, font_size=8.5, header_size=10)

# bottom strip on right
brt_y = ri_y + Inches(4.55)
add_text(s, ri_x + Inches(0.25), brt_y, ri_w - Inches(0.5), Inches(0.7),
         "Bottom line: payments are mostly AES-256 \u2014 already largely quantum-safe. Vulnerable parts are the **public-key wrappers** around the keys. Those need PQC.",
         size=9.5, italic=True, color=LIGHT)


# --------------------- 8. KEY CEREMONY + TR-31/TR-34 ----------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, _idx(), "Key ceremony and TR-31 / TR-34 transport",
       kicker="HSM deep dive (2 of 2)")

# left: key ceremony
kc_x = Inches(0.5); kc_y = Inches(1.55)
kc_w = Inches(6.05); kc_h = Inches(5.3)
add_round_rect(s, kc_x, kc_y, kc_w, kc_h, NAVY2)
add_rect(s, kc_x, kc_y, kc_w, Inches(0.06), TEAL)
add_text(s, kc_x + Inches(0.25), kc_y + Inches(0.18), kc_w - Inches(0.5), Inches(0.35),
         "LMK GENERATION \u2014 THE KEY CEREMONY", size=12, bold=True, color=TEAL)
add_bullets(s, kc_x + Inches(0.25), kc_y + Inches(0.7), kc_w - Inches(0.5), kc_h - Inches(0.85), [
    "**Multi-custodian**: 3\u20135 trusted officers (CISO, CRO, Head of Tech, Audit, RBI observer for top-tier).",
    "Officers gather in a secure room with **CCTV + signed witnesses**. HSM goes into ceremony mode via a physical key/smart card.",
    "HSM internally generates the LMK using its **TRNG** (avalanche-photodiode noise / quantum noise).",
    "LMK is **split via Shamir's Secret Sharing** \u2014 typically **3-of-5** or **2-of-3**: no single custodian can rebuild it; any quorum can.",
    "Each custodian receives their share on a **PIN-protected smart card** (Thales SafeNet / PSGcards) or in tamper-evident printed envelope.",
    "Ceremony log is signed and retained **10 years** (RBI / FIPS audit).",
    "To re-load the LMK (DR sync, firmware upgrade), the quorum reassembles, inserts cards, HSM reconstructs the LMK **internally**.",
    "**Why this matters**: protects the bank from any single insider walking out with all keys; this is also why LMK rotation is non-trivial \u2014 it triggers re-encryption of every wrapped key in the DB.",
], size=10, color=LIGHT, bullet_color=TEAL, line_spacing=1.18)

# right: TR-31/TR-34
tr_x = Inches(6.75); tr_y = Inches(1.55)
tr_w = Inches(6.05); tr_h = Inches(5.3)
add_round_rect(s, tr_x, tr_y, tr_w, tr_h, NAVY2)
add_rect(s, tr_x, tr_y, tr_w, Inches(0.06), GOLD)
add_text(s, tr_x + Inches(0.25), tr_y + Inches(0.18), tr_w - Inches(0.5), Inches(0.35),
         "INTER-HSM TRANSPORT \u2014 TR-34 / TR-31 / PQ TR-34", size=12, bold=True, color=GOLD)
add_bullets(s, tr_x + Inches(0.25), tr_y + Inches(0.7), tr_w - Inches(0.5), tr_h - Inches(0.85), [
    "Need to move a ZMK between HDFC and NPCI / Visa / partner bank \u2014 you can't use the LMK because each org has its own.",
    "**TR-34 (one-time exchange)** \u2014 RSA digital envelope wraps the new ZMK + identity certificate. **This is the part vulnerable to Shor**.",
    "**TR-31 (key block format)** \u2014 once a shared KEK is in place, all subsequent keys move as AES-wrapped key blocks with CBC-MAC integrity. **Already quantum-safe**.",
    "**TR-34 PQ migration** \u2014 ANSI X9 working group has 2024 draft language replacing RSA wrap with **ML-KEM-1024**.",
    "Vendor support: **Thales payShield 10K firmware 2.x** ships ML-KEM/ML-DSA in 2024\u201325; **IBM CryptoExpress 8S (4770)** has PQC on z16.",
    "**Action for HDFC**: schedule next TR-34 ceremony with NPCI for FY27 once their PQ profile is published; in the meantime, all new ZMKs use 4096-bit RSA + AES-256 wrap (defence in depth).",
    "Existing TR-31 traffic (working keys flowing intra-bank, intra-DC) is **AES-wrapped** \u2014 no migration needed.",
], size=10, color=LIGHT, bullet_color=GOLD, line_spacing=1.18)


# --------------------- 9. QKD <-> HSM INTEGRATION -------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, _idx(), "QKD keys flowing into HSM-anchored encryptors",
       kicker="The architecture")

# Two endpoints (HQ left, DC right)
ep_w = Inches(2.6)
left_ep_x  = Inches(0.7)
right_ep_x = Inches(10.05)

ep_y = Inches(1.55); ep_h = Inches(0.65)
for x, label, c in [(left_ep_x, "HQ MUMBAI", TEAL),
                    (right_ep_x, "PRIMARY DC MUMBAI", RED)]:
    add_round_rect(s, x, ep_y, ep_w, ep_h, NAVY2)
    add_rect(s, x, ep_y, ep_w, Inches(0.05), c)
    add_text(s, x + Inches(0.15), ep_y + Inches(0.07), ep_w - Inches(0.3), Inches(0.28),
             label, size=11, bold=True, color=c, align=PP_ALIGN.CENTER)
    add_text(s, x + Inches(0.15), ep_y + Inches(0.32), ep_w - Inches(0.3), Inches(0.30),
             "5\u201330 km dark fibre", size=9, color=LIGHT, italic=True,
             align=PP_ALIGN.CENTER)

# QKD photon channel strip (spans across)
qkd_y = Inches(2.30); qkd_h = Inches(0.42)
qkd_x = left_ep_x + Inches(0.2)
qkd_w = right_ep_x + ep_w - Inches(0.2) - qkd_x
add_round_rect(s, qkd_x, qkd_y, qkd_w, qkd_h, RGBColor(0x1A, 0x3A, 0x5C))
add_text(s, qkd_x + Inches(0.2), qkd_y + Inches(0.05), qkd_w - Inches(0.4), Inches(0.34),
         "QKD photon channel \u2014 dedicated O-band wavelength \u2014 outputs identical 256-bit AES key every ~1 sec at both ends",
         size=10, italic=True, color=TEAL, align=PP_ALIGN.CENTER)

# QKD boxes
qb_y = Inches(2.85); qb_h = Inches(0.85)
for x, lbl in [(left_ep_x, "Toshiba MDI-QKD\nor IDQ Clavis XGR"),
               (right_ep_x, "Toshiba MDI-QKD\nor IDQ Clavis XGR")]:
    add_round_rect(s, x, qb_y, ep_w, qb_h, NAVY2)
    add_rect(s, x, qb_y, ep_w, Inches(0.05), TEAL)
    add_text(s, x + Inches(0.15), qb_y + Inches(0.07), ep_w - Inches(0.3), Inches(0.28),
             "QKD BOX (KME)", size=10, bold=True, color=TEAL, align=PP_ALIGN.CENTER)
    add_text(s, x + Inches(0.15), qb_y + Inches(0.32), ep_w - Inches(0.3), Inches(0.50),
             lbl, size=9, color=LIGHT, align=PP_ALIGN.CENTER)

# ETSI caption (in middle column, between QKD boxes vertically aligned with them)
add_round_rect(s, Inches(3.65), qb_y + Inches(0.10), Inches(6.2), Inches(0.65),
               RGBColor(0x14, 0x33, 0x44))
add_text(s, Inches(3.7), qb_y + Inches(0.12), Inches(6.1), Inches(0.6),
         "ETSI GS QKD 014/004 REST API delivers fresh\nAES-256 keys into the encryptor every ~1 second.",
         size=10, italic=True, color=TEAL, align=PP_ALIGN.CENTER)

# Encryptors
enc_y = Inches(3.95); enc_h = Inches(0.85)
for x, lbl in [(left_ep_x, "Thales CN9100 / Senetas\nCN6140 / Ciena WL5e"),
               (right_ep_x, "Thales CN9100 / Senetas\nCN6140 / Ciena WL5e")]:
    add_round_rect(s, x, enc_y, ep_w, enc_h, NAVY2)
    add_rect(s, x, enc_y, ep_w, Inches(0.05), GOLD)
    add_text(s, x + Inches(0.15), enc_y + Inches(0.07), ep_w - Inches(0.3), Inches(0.28),
             "ENCRYPTOR", size=10, bold=True, color=GOLD, align=PP_ALIGN.CENTER)
    add_text(s, x + Inches(0.15), enc_y + Inches(0.32), ep_w - Inches(0.3), Inches(0.50),
             lbl, size=9, color=LIGHT, align=PP_ALIGN.CENTER)

# Bulk encrypted DWDM channel between encryptors
bk_y = Inches(4.95); bk_h = Inches(0.42)
bk_x = qkd_x; bk_w = qkd_w
add_round_rect(s, bk_x, bk_y, bk_w, bk_h, RGBColor(0x33, 0x1B, 0x1B))
add_text(s, bk_x + Inches(0.2), bk_y + Inches(0.05), bk_w - Inches(0.4), Inches(0.34),
         "AES-256 encrypted bulk traffic \u2014 10\u2013400 Gbps DWDM channels (core banking, card switch, treasury, HSM sync)",
         size=10, italic=True, color=GOLD, align=PP_ALIGN.CENTER)

# Identity caption (middle column, between encryptors and HSMs)
id_cap_y = Inches(5.55)
add_round_rect(s, Inches(3.65), id_cap_y, Inches(6.2), Inches(0.55),
               RGBColor(0x33, 0x1B, 0x22))
add_text(s, Inches(3.7), id_cap_y + Inches(0.06), Inches(6.1), Inches(0.5),
         "Encryptor authenticates to the HSM at boot (ML-DSA / ECDSA),\nreceives its long-lived identity certificate.",
         size=10, italic=True, color=RED, align=PP_ALIGN.CENTER)

# HSMs (bottom)
hs_y = Inches(6.20); hs_h = Inches(0.70)
for x, lbl in [(left_ep_x, "Thales payShield 10K HSM cluster"),
               (right_ep_x, "Thales payShield 10K HSM cluster")]:
    add_round_rect(s, x, hs_y, ep_w, hs_h, NAVY2)
    add_rect(s, x, hs_y, ep_w, Inches(0.05), RED)
    add_text(s, x + Inches(0.15), hs_y + Inches(0.07), ep_w - Inches(0.3), Inches(0.28),
             "HSM", size=10, bold=True, color=RED, align=PP_ALIGN.CENTER)
    add_text(s, x + Inches(0.15), hs_y + Inches(0.34), ep_w - Inches(0.3), Inches(0.32),
             lbl, size=9, color=LIGHT, align=PP_ALIGN.CENTER)

# arrows: QKD-box -> Encryptor (key feed) and HSM -> Encryptor (identity attest)
for x_center in [left_ep_x + ep_w / 2, right_ep_x + ep_w / 2]:
    # QKD-box bottom -> Encryptor top
    add_arrow(s, x_center, qb_y + qb_h, x_center, enc_y, color=TEAL, weight=1.5)
    # HSM top -> Encryptor bottom (upward identity attestation)
    add_arrow(s, x_center, hs_y, x_center, enc_y + enc_h, color=RED, weight=1.5)


# --------------------- 10. COSTS ------------------------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, _idx(), "Cost \u2014 Indian context, FY26 INR",
       kicker="Capex + opex envelope")

# left: capex table
cx = Inches(0.5); cy = Inches(1.55)
cw = Inches(7.6); ch = Inches(5.3)
add_round_rect(s, cx, cy, cw, ch, NAVY2)
add_rect(s, cx, cy, cw, Inches(0.06), RED)
add_text(s, cx + Inches(0.25), cy + Inches(0.15), cw - Inches(0.5), Inches(0.35),
         "PROGRAMME CAPEX OVER 24\u201336 MONTHS", size=12, bold=True, color=RED)

cap_left = cx + Inches(0.3); cap_top = cy + Inches(0.6)
cap_w = cw - Inches(0.6); cap_h = ch - Inches(0.85)
caprows = 11; capcols = 3
captbl_shape = s.shapes.add_table(caprows, capcols, cap_left, cap_top, cap_w, cap_h)
captbl = captbl_shape.table
captbl.columns[0].width = Inches(3.6)
captbl.columns[1].width = Inches(2.0)
captbl.columns[2].width = Inches(1.4)
chdr = ["Item", "Detail", "Rs Cr"]
for c, h in enumerate(chdr):
    captbl.cell(0, c).text = h
caprows_data = [
    ("HSM refresh (Thales payShield 10K)", "16 prod (DC) + 6 (DR) + 4 (HQ)", "9\u201313"),
    ("PQC integration services",            "Libraries + cert PKI + apps",   "6\u201310"),
    ("QKD pair, HQ \u2194 DC Mumbai",        "Toshiba MDI-QKD or IDQ Clavis", "8\u201315"),
    ("Quantum-safe encryptors",              "Thales CN9100 / Senetas CN6140", "2.5\u20134"),
    ("Dark fibre / DWDM wavelength capex",   "If not already owned (~30 km)", "1\u20133"),
    ("Branch-side PQC",                      "TLS lib upgrade + cert refresh", "4\u20136"),
    ("PKI overhaul",                         "Internal CA, OCSP, ML-DSA",     "3\u20135"),
    ("CryptoBOM tooling",                    "IBM Crypto Discovery / SandboxAQ", "2\u20134"),
    ("DR satellite-QKD R&D pilot",           "ISRO / TIFR partnership",       "5\u20138 (R&D)"),
    ("Training, consulting, RBI engagement", "Programme",                     "3\u20135"),
]
for r, row in enumerate(caprows_data, start=1):
    for c, val in enumerate(row):
        captbl.cell(r, c).text = val
style_table(captbl, font_size=9, header_size=10)

# right: opex + total
ox = Inches(8.3); oy = Inches(1.55)
ow = Inches(4.55); oh = Inches(5.3)
add_round_rect(s, ox, oy, ow, oh, NAVY2)
add_rect(s, ox, oy, ow, Inches(0.06), GOLD)
add_text(s, ox + Inches(0.25), oy + Inches(0.15), ow - Inches(0.5), Inches(0.35),
         "ANNUAL OPEX (POST-ROLLOUT)", size=12, bold=True, color=GOLD)

op_left = ox + Inches(0.3); op_top = oy + Inches(0.6)
op_w = ow - Inches(0.6); op_h = Inches(2.55)
oprows = 7; opcols = 2
optbl_shape = s.shapes.add_table(oprows, opcols, op_left, op_top, op_w, op_h)
optbl = optbl_shape.table
optbl.columns[0].width = Inches(2.7)
optbl.columns[1].width = Inches(1.25)
ohdr = ["Item", "Rs Cr / yr"]
for c, h in enumerate(ohdr):
    optbl.cell(0, c).text = h
oprows_data = [
    ("HSM maintenance + FIPS recerts", "1.5\u20132.5"),
    ("QKD link maintenance",             "1.5\u20133"),
    ("Dark fibre lease",                 "1\u20132"),
    ("PQC library subs (PQShield, etc.)","0.5\u20131"),
    ("Annual key ceremonies + audits",   "0.5\u20131"),
    ("Skilled crypto / quantum team (8\u201312 FTE)", "4\u20136"),
]
for r, row in enumerate(oprows_data, start=1):
    for c, val in enumerate(row):
        optbl.cell(r, c).text = val
style_table(optbl, font_size=9, header_size=10)

# Bottom number to take to MD
ts_y = oy + Inches(3.4)
add_round_rect(s, ox + Inches(0.25), ts_y, ow - Inches(0.5), Inches(1.65), NAVY)
add_rect(s, ox + Inches(0.25), ts_y, ow - Inches(0.5), Inches(0.06), GREEN)
add_text(s, ox + Inches(0.4), ts_y + Inches(0.15), ow - Inches(0.8), Inches(0.4),
         "THE NUMBER FOR THE MD", size=10, bold=True, color=GREEN)
add_text(s, ox + Inches(0.4), ts_y + Inches(0.5), ow - Inches(0.8), Inches(0.5),
         "Rs 50\u201370 Cr",
         size=22, bold=True, color=WHITE)
add_text(s, ox + Inches(0.4), ts_y + Inches(1.0), ow - Inches(0.8), Inches(0.55),
         "programme over FY26\u2013FY28\nplus Rs 10\u201315 Cr/yr opex",
         size=10, color=LIGHT)


# --------------------- 11. ADOPTION ROADMAP -------------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, _idx(), "Adoption roadmap \u2014 36 months, 5 phases",
       kicker="How we get there")

# horizontal phase columns
ph_y = Inches(1.55); ph_h = Inches(5.3); ph_gap = Inches(0.075)
n_phases = 5
ph_w = (Inches(12.3) - ph_gap * (n_phases - 1)) / n_phases
ph_x0 = Inches(0.5)

phases = [
    ("Phase 0", "Months 0\u20133",
     "**CryptoBOM**", [
        "Inventory **every** classical asymmetric crypto use (TLS, IPsec, code sign, certs, JWT, S/MIME, archived data).",
        "Tag by algorithm, key length, sensitivity, retention, replacement difficulty.",
        "Tools: IBM Crypto Discovery, SandboxAQ AQtive Guard, open-source crypto-cbom.",
        "Output: heat-map of where to migrate first.",
        "Cost: ~Rs 2\u20133 Cr.",
     ], TEAL),
    ("Phase 1", "Months 3\u20139",
     "**HSM + PKI foundation**", [
        "Refresh HSM fleet to current gen (Thales payShield 10K firmware \u2265 2.x, IBM CryptoExpress 8S).",
        "Both vendors ship **ML-KEM and ML-DSA** in 2024\u201325 firmware.",
        "Stand up post-quantum-ready internal CA (EJBCA 8.x with Dilithium, Entrust nShield CA).",
        "Add **crypto-agility wrapper** to internal libs so apps swap algos without code change.",
     ], GOLD),
    ("Phase 2", "Months 6\u201315",
     "**PQC pilot**", [
        "Pick one **non-customer-facing TLS endpoint** (admin portal, MIS dashboard).",
        "Deploy in **hybrid mode**: handshake = X25519 + ML-KEM-768.",
        "If ML-KEM is broken, X25519 still protects you; if X25519 is broken by quantum, ML-KEM does.",
        "Measure latency, cert size, library compat. Train SOC.",
     ], ORANGE),
    ("Phase 3", "Months 12\u201324",
     "**PQC fleet rollout**", [
        "Roll PQC out to **all internal mTLS** between microservices.",
        "Migrate **branch \u2194 regional hub IPsec** during SD-WAN refresh cycle.",
        "Migrate **mobile / net banking TLS** to hybrid (iOS 18, Chrome already negotiate Kyber).",
        "Upgrade **TR-34** ceremonies with NPCI / Visa / MC as their PQ profiles ratify.",
     ], RED),
    ("Phase 4 + 5", "Months 18\u201336+",
     "**QKD metro + DR R&D**", [
        "Procure **Toshiba MDI-QKD or IDQ Clavis XGR pair** for HQ \u2194 Primary DC.",
        "Deploy Thales/Senetas/Ciena PQC encryptors on either side (ETSI GS QKD 014).",
        "Carry HSM cluster sync, treasury, Finacle replication. Shadow mode 6 mo, then prod.",
        "**DR R&D**: free-space / satellite QKD with TIFR / IISc / ISRO. NQM-funded.",
     ], TEAL),
]
for i, (ph, when, sub, items, c) in enumerate(phases):
    x = ph_x0 + i * (ph_w + ph_gap)
    add_round_rect(s, x, ph_y, ph_w, ph_h, NAVY2)
    add_rect(s, x, ph_y, ph_w, Inches(0.07), c)
    add_text(s, x + Inches(0.15), ph_y + Inches(0.18), ph_w - Inches(0.3), Inches(0.32),
             ph, size=12, bold=True, color=c)
    add_text(s, x + Inches(0.15), ph_y + Inches(0.5), ph_w - Inches(0.3), Inches(0.32),
             when, size=10, color=LIGHT, italic=True)
    add_text(s, x + Inches(0.15), ph_y + Inches(0.85), ph_w - Inches(0.3), Inches(0.4),
             sub, size=11, bold=True, color=WHITE)
    add_bullets(s, x + Inches(0.15), ph_y + Inches(1.3), ph_w - Inches(0.3), ph_h - Inches(1.45),
                items, size=8.5, color=LIGHT, bullet_color=c, line_spacing=1.15)


# --------------------- 12. CALL TO ACTION ---------------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, _idx(), "Call to action",
       kicker="Decision required")

# Big ask box (top)
ask_x = Inches(0.5); ask_y = Inches(1.55)
ask_w = Inches(12.3); ask_h = Inches(2.0)
add_round_rect(s, ask_x, ask_y, ask_w, ask_h, NAVY2)
add_rect(s, ask_x, ask_y, ask_w, Inches(0.08), RED)
add_text(s, ask_x + Inches(0.3), ask_y + Inches(0.18), ask_w - Inches(0.6), Inches(0.42),
         "RECOMMENDATION", size=12, bold=True, color=RED)
add_text(s, ask_x + Inches(0.3), ask_y + Inches(0.6), ask_w - Inches(0.6), Inches(1.3),
         "Approve **Phase 0 + Phase 1 funding of Rs 12\u201318 Cr for FY26**\n\u2014 CryptoBOM inventory, HSM refresh to PQC-capable firmware, internal PKI overhaul.\nGo / no-go gate at month 9 for **PQC pilot (Phase 2)**.\nFull programme envelope **Rs 50\u201370 Cr** over FY26\u2013FY28.",
         size=16, color=LIGHT)

# Three reason cards
why_y = Inches(3.85); why_h = Inches(2.25); why_w = Inches(4.05); why_gap = Inches(0.075)
reasons = [
    ("REGULATORY", "RBI Master Direction on IT Governance (Nov 2023) and SEBI CSCRF (2024) flag PQC migration as a forward-looking control.\nNIST FIPS-203 / 204 / 205 finalised Aug 2024 \u2014 audit baseline now established.", TEAL),
    ("THREAT REALITY", "**Harvest now, decrypt later** is happening today on carrier fibre. KYC, loan files, treasury positions captured in 2024 will be readable in 2030\u201335. The clock is already running.", RED),
    ("STRATEGIC", "JPMC and HSBC have shipped QKD pilots; SBI, ICICI and Axis are early in PQC. **18-month head-start** maps directly to talent acquisition, IP, and India's National Quantum Mission positioning.", GOLD),
]
for i, (lbl, body, c) in enumerate(reasons):
    x = Inches(0.5) + i * (why_w + why_gap)
    add_round_rect(s, x, why_y, why_w, why_h, NAVY2)
    add_rect(s, x, why_y, why_w, Inches(0.05), c)
    add_text(s, x + Inches(0.25), why_y + Inches(0.18), why_w - Inches(0.5), Inches(0.4),
             lbl, size=12, bold=True, color=c)
    add_text(s, x + Inches(0.25), why_y + Inches(0.65), why_w - Inches(0.5), why_h - Inches(0.8),
             body, size=11, color=LIGHT)

# Bottom strip
fb_y = Inches(6.3); fb_h = Inches(0.65)
add_rect(s, Inches(0.5), fb_y, Inches(12.3), fb_h, NAVY2)
add_text(s, Inches(0.7), fb_y + Inches(0.15), Inches(12), Inches(0.4),
         "Author: SVP \u2014 Kranthi Molleti  \u2022  HDFC Bank Quantum Computing Strategy",
         size=11, bold=True, color=GOLD)


# --------------------- WRITE FILE -----------------------------------
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "HDFC_Quantum_Safe_Comms_Deck.pptx")
prs.save(out_path)
print(f"WROTE {out_path}")
