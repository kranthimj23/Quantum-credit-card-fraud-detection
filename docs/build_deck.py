"""Build HDFC Quantum Executive Deck (PowerPoint).

Audience: MD, CTO, CEO, senior executives, enterprise architects.
Primary use case: credit-card fraud detection.
Theme: HDFC brand-inspired dark navy with red accent.

Regenerate the deck:
    pip install python-pptx
    python docs/build_deck.py
    # writes HDFC_Quantum_Executive_Deck.pptx alongside this script

All slides are programmatic so figures (Rs Cr, AUC numbers, ROI) can be
updated by editing the hard-coded values in this file and re-running.
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import CategoryChartData, XyChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.oxml.ns import qn
from lxml import etree

# ---------- Brand palette ----------
NAVY     = RGBColor(0x0A, 0x1E, 0x3F)   # background
NAVY2    = RGBColor(0x12, 0x2C, 0x55)   # darker accent
RED      = RGBColor(0xED, 0x23, 0x2A)   # HDFC red
GOLD     = RGBColor(0xF5, 0xB7, 0x2E)   # accent for KPIs
TEAL     = RGBColor(0x2E, 0xC4, 0xB6)   # quantum accent
WHITE    = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT    = RGBColor(0xE6, 0xEA, 0xF2)
MUTED    = RGBColor(0x9A, 0xA5, 0xBC)
GREEN    = RGBColor(0x2E, 0xCC, 0x71)
ORANGE   = RGBColor(0xE6, 0x7E, 0x22)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def add_bg(slide, color=NAVY):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background()
    bg.shadow.inherit = False
    # send to back
    spTree = bg._element.getparent()
    spTree.remove(bg._element)
    spTree.insert(2, bg._element)
    return bg


def _add_rich_runs(p, line, *, size, bold, italic, color, font):
    rest = line
    parts = []
    while "**" in rest:
        head, _, tail = rest.partition("**")
        mid, _, tail2 = tail.partition("**")
        parts.append((head, False))
        parts.append((mid, True))
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
    """Textbox with **bold** parsing per line and \n line breaks."""
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
    """items: list of strings (or tuples (text, indent)). A leading '> ' marks
    a bold key followed by colon-separated detail."""
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.05)
    for i, item in enumerate(items):
        if isinstance(item, tuple):
            text, indent = item
        else:
            text, indent = item, 0
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.level = indent
        # bullet character
        bullet_run = p.add_run()
        bullet_run.text = "\u25A0  " if indent == 0 else "\u2022  "
        bullet_run.font.name = font
        bullet_run.font.size = Pt(size)
        bullet_run.font.color.rgb = bullet_color
        bullet_run.font.bold = True

        # support **bold** segments
        rest = text
        # split on **
        parts = []
        while "**" in rest:
            head, _, tail = rest.partition("**")
            mid, _, tail2 = tail.partition("**")
            parts.append((head, False))
            parts.append((mid, True))
            rest = tail2
        parts.append((rest, False))
        for seg, is_bold in parts:
            if not seg:
                continue
            run = p.add_run()
            run.text = seg
            run.font.name = font
            run.font.size = Pt(size)
            run.font.bold = is_bold or (bold_first and indent == 0)
            run.font.color.rgb = color
        try:
            p.line_spacing = line_spacing
        except Exception:
            pass
    return tb


def add_rect(slide, left, top, width, height, fill, line=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(0.5)
    sh.shadow.inherit = False
    return sh


def add_round_rect(slide, left, top, width, height, fill, line=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    sh.adjustments[0] = 0.08
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(1)
    sh.shadow.inherit = False
    return sh


def add_line(slide, x1, y1, x2, y2, color=RED, weight=1.5):
    line = slide.shapes.add_connector(1, x1, y1, x2, y2)
    line.line.color.rgb = color
    line.line.width = Pt(weight)
    return line


def add_arrow(slide, x1, y1, x2, y2, color=RED, weight=2):
    """Right-pointing arrow connector."""
    line = slide.shapes.add_connector(2, x1, y1, x2, y2)  # straight
    line.line.color.rgb = color
    line.line.width = Pt(weight)
    # add arrowhead via XML
    ln = line.line._get_or_add_ln()
    tail = etree.SubElement(ln, qn("a:tailEnd"))
    tail.set("type", "triangle")
    tail.set("w", "med")
    tail.set("h", "med")
    return line


def header(slide, idx, title, kicker=None):
    # accent bar
    add_rect(slide, Inches(0.5), Inches(0.45), Inches(0.12), Inches(0.55), RED)
    # kicker
    if kicker:
        add_text(slide, Inches(0.72), Inches(0.40), Inches(8), Inches(0.35),
                 kicker.upper(), size=11, color=GOLD, bold=True)
    add_text(slide, Inches(0.72), Inches(0.66), Inches(12.3), Inches(0.65),
             title, size=24, bold=True, color=WHITE)
    # rule
    add_rect(slide, Inches(0.5), Inches(1.35), Inches(12.3), Emu(9525), NAVY2)
    # footer
    footer(slide, idx)


def footer(slide, idx):
    add_text(slide, Inches(0.5), Inches(7.05), Inches(7), Inches(0.3),
             "HDFC Bank \u2022 Quantum Computing Strategy \u2022 Confidential",
             size=9, color=MUTED)
    add_text(slide, Inches(11.8), Inches(7.05), Inches(1.2), Inches(0.3),
             f"{idx:02d}", size=9, color=MUTED, align=PP_ALIGN.RIGHT)


# ====================================================================
# Build deck
# ====================================================================

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
blank = prs.slide_layouts[6]

# --------------------- 1. TITLE ---------------------------------------
s = prs.slides.add_slide(blank)
add_bg(s, NAVY)
# diagonal accent
add_rect(s, 0, Inches(6.8), SLIDE_W, Inches(0.7), NAVY2)
add_rect(s, 0, Inches(0), Inches(0.4), SLIDE_H, RED)
# kicker
add_text(s, Inches(1.0), Inches(0.9), Inches(8), Inches(0.4),
         "HDFC BANK \u2022 BOARD AND EXECUTIVE BRIEFING", size=12, color=GOLD, bold=True)
add_text(s, Inches(1.0), Inches(1.5), Inches(11.5), Inches(1.6),
         "Quantum Computing for\nFraud Detection",
         size=54, bold=True, color=WHITE)
add_text(s, Inches(1.0), Inches(3.7), Inches(11), Inches(0.6),
         "Why HDFC should invest now \u2014 a credit-card fraud case study,",
         size=22, color=LIGHT)
add_text(s, Inches(1.0), Inches(4.1), Inches(11), Inches(0.6),
         "the advantage curve, and the 24-month execution plan",
         size=22, color=LIGHT)
add_rect(s, Inches(1.0), Inches(5.2), Inches(0.12), Inches(0.35), TEAL)
add_text(s, Inches(1.2), Inches(5.15), Inches(8), Inches(0.4),
         "Prepared for: MD \u2022 CEO \u2022 CTO \u2022 Enterprise Architects \u2022 Engineering Heads",
         size=14, color=LIGHT)
add_text(s, Inches(1.2), Inches(5.55), Inches(8), Inches(0.4),
         "Author: SVP \u2022 Office of Emerging Technology",
         size=14, color=MUTED)
add_text(s, Inches(1.0), Inches(6.95), Inches(11), Inches(0.4),
         "Confidential \u2014 internal circulation only",
         size=10, color=MUTED, italic=True)

# --------------------- 2. EXECUTIVE SUMMARY ---------------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 2, "Executive summary \u2014 the ask in one slide", kicker="Why we are here")

# Three-column ask
col_y = Inches(1.7); col_h = Inches(2.5); col_w = Inches(4.0); gap = Inches(0.15)
labels = [
    ("THE PROBLEM",
     "Credit-card fraud cost Indian banking ~Rs 1,300 Cr in FY24 and is growing 20%+ YoY. Classical ML detects ~92\u201395% of fraud at the cost of high false-positives and slow adaptation to novel attack patterns."),
    ("THE OPPORTUNITY",
     "Quantum machine learning (VQC, quantum kernels) finds non-linear correlations classical models cannot reach \u2014 measurable gains in recall on rare-event fraud and the patterns we miss today."),
    ("THE ASK",
     "Rs 8\u201312 Cr over 24 months for a hybrid quantum-classical fraud platform: simulator-first proof on real HDFC data, then pilot on IBM Quantum hardware, then production tier-2 re-scorer.")
]
colors_ = [RED, TEAL, GOLD]
for i, ((lbl, body), c) in enumerate(zip(labels, colors_)):
    x = Inches(0.5) + i * (col_w + gap)
    add_round_rect(s, x, col_y, col_w, col_h, NAVY2)
    add_rect(s, x, col_y, col_w, Inches(0.05), c)
    add_text(s, x + Inches(0.25), col_y + Inches(0.18), col_w - Inches(0.5), Inches(0.4),
             lbl, size=12, bold=True, color=c)
    add_text(s, x + Inches(0.25), col_y + Inches(0.7), col_w - Inches(0.5), col_h - Inches(0.8),
             body, size=14, color=LIGHT)

# bottom belt: 3 numbers
add_round_rect(s, Inches(0.5), Inches(4.5), Inches(12.3), Inches(2.3), NAVY2)
add_text(s, Inches(0.7), Inches(4.65), Inches(11), Inches(0.4),
         "WHAT GOOD LOOKS LIKE IN 24 MONTHS",
         size=12, bold=True, color=GOLD)
kpis = [
    ("+15\u201325%", "incremental fraud caught at\nthe same false-positive rate"),
    ("\u2212 30%", "reduction in customer-facing\nfalse declines on premium cards"),
    ("Rs 60\u201390 Cr", "annual loss avoidance at\nHDFC scale (conservative)"),
    ("3 use cases", "live in production \u2014 cards,\nUPI, and AML transaction monitoring"),
]
kx = Inches(0.7); ky = Inches(5.15); kw = Inches(2.95); kh = Inches(1.55)
for i, (big, small) in enumerate(kpis):
    x = kx + i * (kw + Inches(0.05))
    add_text(s, x, ky, kw, Inches(0.65), big, size=30, bold=True, color=WHITE)
    add_text(s, x, ky + Inches(0.7), kw, Inches(0.85), small, size=12, color=LIGHT)

# --------------------- 3. THE FRAUD PROBLEM AT HDFC SCALE -------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 3, "The fraud problem at HDFC scale",
       kicker="Section A \u2022 The case")

add_text(s, Inches(0.5), Inches(1.6), Inches(6.3), Inches(0.45),
         "Why this matters at the bottom of the P&L",
         size=18, bold=True, color=GOLD)

bullet_items = [
    "**~10 Cr+ card transactions/month** flow through HDFC issuing & acquiring rails.",
    "**0.05\u20130.2% are fraudulent** \u2014 a needle-in-haystack class imbalance of ~1:1000.",
    "**Industry losses**: card fraud in India ~Rs 1,300 Cr (FY24, RBI), growing >20% YoY.",
    "**Attack surface is shifting** \u2014 OTP-bypass, sim-swap, card-not-present, account-takeover, friendly-fraud.",
    "**Customer experience cost** \u2014 every false decline on a premium card erodes wallet share and NPS.",
    "**Regulatory pressure** \u2014 RBI Master Direction on Digital Payment Security 2021 + DPDP Act 2023 raise the bar."
]
add_bullets(s, Inches(0.5), Inches(2.1), Inches(6.5), Inches(4.5),
            bullet_items, size=14, color=LIGHT)

# Right side: stylised volume chart
right_x = Inches(7.3)
add_round_rect(s, right_x, Inches(1.6), Inches(5.5), Inches(5.0), NAVY2)
add_text(s, right_x + Inches(0.3), Inches(1.75), Inches(5), Inches(0.4),
         "Fraud loss profile (illustrative)",
         size=14, bold=True, color=WHITE)
add_text(s, right_x + Inches(0.3), Inches(2.1), Inches(5), Inches(0.35),
         "Indian banking, FY20\u2192FY24, Rs Cr",
         size=10, color=MUTED, italic=True)

# Mini bar chart
chart_data = CategoryChartData()
chart_data.categories = ["FY20", "FY21", "FY22", "FY23", "FY24"]
chart_data.add_series("Card fraud (Rs Cr)", (520, 660, 850, 1080, 1300))
chart = s.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED,
    right_x + Inches(0.2), Inches(2.55),
    Inches(5.1), Inches(3.7), chart_data).chart
chart.has_legend = False
chart.has_title = False
plot = chart.plots[0]
plot.gap_width = 80
plot.has_data_labels = True
dl = plot.data_labels
dl.font.size = Pt(10); dl.font.color.rgb = WHITE; dl.position = XL_LABEL_POSITION.OUTSIDE_END
ser = plot.series[0]
fill = ser.format.fill; fill.solid(); fill.fore_color.rgb = RED
chart.category_axis.tick_labels.font.size = Pt(10)
chart.category_axis.tick_labels.font.color.rgb = LIGHT
chart.value_axis.tick_labels.font.size = Pt(10)
chart.value_axis.tick_labels.font.color.rgb = MUTED
chart.value_axis.visible = False

add_text(s, right_x + Inches(0.3), Inches(6.2), Inches(5), Inches(0.4),
         "Source: RBI Annual Report on Card Fraud, IBA aggregates. HDFC share ~28\u201332% of issuance.",
         size=9, color=MUTED, italic=True)

# --------------------- 4. CLASSICAL CEILING ---------------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 4, "Why classical ML alone is hitting a ceiling",
       kicker="Section A \u2022 The case")

# left bullet "what classical does well"
add_round_rect(s, Inches(0.5), Inches(1.6), Inches(6.0), Inches(5.2), NAVY2)
add_text(s, Inches(0.7), Inches(1.75), Inches(5.6), Inches(0.4),
         "WHAT CLASSICAL ML DOES WELL TODAY",
         size=12, bold=True, color=TEAL)
add_bullets(s, Inches(0.7), Inches(2.2), Inches(5.7), Inches(4.6), [
    "**Throughput**: XGBoost/LightGBM score 100K+ tx/sec on commodity hardware.",
    "**Latency**: <5 ms inference, well within authorisation SLAs.",
    "**Mature ops**: monitoring, drift detection, explainability tooling, model risk frameworks.",
    "**Strong baselines**: AUC-ROC ~0.97\u20130.99 on benchmark data with feature engineering.",
], size=14, color=LIGHT, bullet_color=TEAL)

# right "where it struggles"
add_round_rect(s, Inches(6.8), Inches(1.6), Inches(6.0), Inches(5.2), NAVY2)
add_text(s, Inches(7.0), Inches(1.75), Inches(5.6), Inches(0.4),
         "WHERE IT STRUGGLES \u2014 AND WHY THE CEILING IS REAL",
         size=12, bold=True, color=RED)
add_bullets(s, Inches(7.0), Inches(2.2), Inches(5.7), Inches(4.6), [
    "**Rare-event recall**: minority class (fraud) is ~0.1% \u2014 most models trade recall for precision and miss novel fraud.",
    "**High-dimensional non-linearity**: as we add features (device, geo, biometrics, network graph) classical kernels degrade or overfit.",
    "**Concept drift**: attackers adapt weekly; static decision boundaries lag.",
    "**Out-of-distribution patterns**: classical models extrapolate poorly outside training manifold \u2014 the very fraud we want to catch.",
    "**Feature interaction explosion**: 30 \u2192 500 features means C(500,2)=124,750 pairwise interactions; classical models capture a tiny fraction.",
], size=14, color=LIGHT, bullet_color=RED)

# --------------------- 5. QUANTUM 101 IN 60 SECONDS -------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 5, "Quantum 101 \u2014 the only three ideas the board needs",
       kicker="Section A \u2022 The case")

cards = [
    ("SUPERPOSITION",
     "A quantum bit (qubit) holds 0 and 1 at the same time, weighted by amplitudes \u03b1 and \u03b2.\n\nN qubits encode 2\u02e3 amplitudes \u2014 30 qubits = 1 billion, 50 qubits = 1 quadrillion.",
     "1 qubit \u2194 2 amplitudes\n10 qubits \u2194 1,024\n30 qubits \u2194 ~10\u2079\n50 qubits \u2194 ~10\u00b9\u2075", TEAL),
    ("ENTANGLEMENT",
     "Qubits become correlated such that the joint state cannot be written as independent parts \u2014 \"the whole is more than the sum of the parts\".\n\nThis is what lets us encode feature interactions natively.",
     "Bell pair: outcomes\nperfectly correlated.\nIn fraud: device-geo-time\ninteractions become first-class.", RED),
    ("MEASUREMENT",
     "Reading a qubit collapses it to 0 or 1 with probability |\u03b1|\u00b2 / |\u03b2|\u00b2.\n\nWe run the circuit many times (\"shots\") and aggregate \u2014 this is how we get a fraud-probability score.",
     "Probabilistic, not\ndeterministic. Useful for\ncalibrated risk scores\nwith confidence intervals.", GOLD),
]
cy = Inches(1.7); cw = Inches(4.1); ch = Inches(5.1); cgap = Inches(0.1)
for i, (lbl, body, side, color) in enumerate(cards):
    x = Inches(0.5) + i * (cw + cgap)
    add_round_rect(s, x, cy, cw, ch, NAVY2)
    add_rect(s, x, cy, cw, Inches(0.05), color)
    add_text(s, x + Inches(0.25), cy + Inches(0.2), cw - Inches(0.5), Inches(0.4),
             lbl, size=14, bold=True, color=color)
    add_text(s, x + Inches(0.25), cy + Inches(0.7), cw - Inches(0.5), Inches(2.6),
             body, size=12, color=LIGHT)
    add_rect(s, x + Inches(0.25), cy + Inches(3.4), cw - Inches(0.5), Inches(0.04), color)
    add_text(s, x + Inches(0.25), cy + Inches(3.5), cw - Inches(0.5), Inches(1.5),
             side, size=11, color=LIGHT, italic=True)

add_text(s, Inches(0.5), Inches(6.82), Inches(12), Inches(0.3),
         "Beginner-friendly interactive walkthrough lives at tutorial/index.html in the repo \u2014 covers Bloch sphere, gates, ZZFeatureMap, kernels, VQC.",
         size=10, color=MUTED, italic=True)

# --------------------- 6. HYBRID SERVING ARCHITECTURE -----------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 6, "Hybrid serving architecture \u2014 the realistic deployment",
       kicker="Section A \u2022 The case")

add_text(s, Inches(0.5), Inches(1.55), Inches(12.3), Inches(0.4),
         "Quantum is not a replacement \u2014 it is a precision re-scorer for the top 1% of risk events.",
         size=14, italic=True, color=LIGHT)

# left: incoming swimlane
y_top = Inches(2.2)
add_round_rect(s, Inches(0.4), y_top, Inches(2.4), Inches(4.4), NAVY2)
add_text(s, Inches(0.55), y_top + Inches(0.15), Inches(2.2), Inches(0.4),
         "INCOMING TRANSACTION", size=11, bold=True, color=GOLD)
add_text(s, Inches(0.55), y_top + Inches(0.65), Inches(2.2), Inches(3.5),
         "Card swipe / tap /\nUPI / NEFT / e-com\n\n+ 30\u2013500 features\n  amount, geo, device,\n  velocity, graph,\n  behavioural biometrics",
         size=12, color=LIGHT)

# Tier 1 box
add_round_rect(s, Inches(3.4), y_top, Inches(4.6), Inches(4.4), NAVY2)
add_rect(s, Inches(3.4), y_top, Inches(4.6), Inches(0.05), TEAL)
add_text(s, Inches(3.55), y_top + Inches(0.15), Inches(4.3), Inches(0.4),
         "TIER 1 \u2014 CLASSICAL HOT PATH", size=11, bold=True, color=TEAL)
add_text(s, Inches(3.55), y_top + Inches(0.6), Inches(4.3), Inches(0.4),
         "XGBoost / LightGBM ensemble", size=12, bold=True, color=WHITE)
add_text(s, Inches(3.55), y_top + Inches(1.05), Inches(4.3), Inches(3.0),
         "\u2022 ~3\u20135 ms p99 latency\n\u2022 100% of transactions scored\n\u2022 Approves ~99% straight-through\n\u2022 Flags top ~1% as 'review'\n\u2022 Calibrated probability handed to Tier 2",
         size=12, color=LIGHT)

# arrow from incoming -> tier1
add_arrow(s, Inches(2.85), y_top + Inches(2.2), Inches(3.35), y_top + Inches(2.2), color=TEAL)

# Tier 2 box (quantum)
add_round_rect(s, Inches(8.6), y_top, Inches(4.4), Inches(4.4), NAVY2)
add_rect(s, Inches(8.6), y_top, Inches(4.4), Inches(0.05), RED)
add_text(s, Inches(8.75), y_top + Inches(0.15), Inches(4.1), Inches(0.4),
         "TIER 2 \u2014 QUANTUM RE-SCORER", size=11, bold=True, color=RED)
add_text(s, Inches(8.75), y_top + Inches(0.6), Inches(4.1), Inches(0.4),
         "VQC / QSVC on simulator + IBM HW", size=12, bold=True, color=WHITE)
add_text(s, Inches(8.75), y_top + Inches(1.05), Inches(4.1), Inches(3.0),
         "\u2022 ~50\u2013200 ms (asynchronous)\n\u2022 ~1% of transactions scored\n\u2022 Catches non-linear / novel fraud\n\u2022 Output \u2192 final approve/decline,\n  step-up auth, or analyst queue",
         size=12, color=LIGHT)

# arrow tier1 -> tier2
add_arrow(s, Inches(8.05), y_top + Inches(2.2), Inches(8.55), y_top + Inches(2.2), color=RED)

# bottom belt: outcome
add_round_rect(s, Inches(0.4), Inches(6.7), Inches(12.6), Inches(0.6), NAVY2)
add_text(s, Inches(0.6), Inches(6.78), Inches(12), Inches(0.45),
         "Outcome:  Best of both worlds  \u2014  classical speed and ops maturity at scale, quantum precision where it matters most.",
         size=13, bold=True, color=GOLD)

# --------------------- 7. CREDIT-CARD FRAUD PIPELINE ------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 7, "Credit-card fraud \u2014 our reference pipeline",
       kicker="Section B \u2022 The proof")

add_text(s, Inches(0.5), Inches(1.55), Inches(12.3), Inches(0.4),
         "Same plumbing as our existing fraud stack \u2014 only the model brain changes.",
         size=14, italic=True, color=LIGHT)

# 7-step horizontal pipeline
steps = [
    ("RAW",         "Kaggle\n(Mlg-ULB,\n2023)\n284K \u2192 568K\nrows", GOLD),
    ("EDA",         "Class\nimbalance\n0.17%\nfraud", TEAL),
    ("PREP",        "Standard-\nScaler +\nSMOTE +\nPCA(k=6)", TEAL),
    ("ENCODE",      "ZZFeature-\nMap\nrescale to\n[\u2212\u03c0, \u03c0]", RED),
    ("MODEL",       "VQC +\nEfficient-\nSU2 ansatz\nQSVC kernel", RED),
    ("OPTIMIZE",    "SPSA /\nCOBYLA on\nAer simulator,\nthen IBM HW", RED),
    ("DECIDE",      "Parity\ndecoder \u2192\nfraud prob\n+ analyst Q", GOLD),
]
sw = Inches(1.65); sh = Inches(2.6); sy = Inches(2.0); sx0 = Inches(0.5); gap_step = Inches(0.15)
for i, (lbl, body, color) in enumerate(steps):
    x = sx0 + i * (sw + gap_step)
    add_round_rect(s, x, sy, sw, sh, NAVY2)
    add_rect(s, x, sy, sw, Inches(0.05), color)
    add_text(s, x, sy + Inches(0.15), sw, Inches(0.35),
             f"{i+1}. {lbl}", size=11, bold=True, color=color, align=PP_ALIGN.CENTER)
    add_text(s, x + Inches(0.1), sy + Inches(0.6), sw - Inches(0.2), sh - Inches(0.7),
             body, size=11, color=LIGHT, align=PP_ALIGN.CENTER)
    if i < len(steps) - 1:
        ax = x + sw + Inches(0.005)
        add_arrow(s, ax, sy + Inches(1.3), ax + Inches(0.13), sy + Inches(1.3),
                  color=MUTED, weight=1.2)

# bottom: artefacts row
add_round_rect(s, Inches(0.5), Inches(5.0), Inches(12.3), Inches(2.0), NAVY2)
add_text(s, Inches(0.7), Inches(5.15), Inches(11), Inches(0.4),
         "WHAT WE HAVE BUILT (REPRODUCIBLE TODAY)",
         size=12, bold=True, color=GOLD)
add_bullets(s, Inches(0.7), Inches(5.55), Inches(12), Inches(1.5), [
    "**7 Python scripts** end-to-end (`src/00`\u2026`src/07`) \u2014 EDA, preprocessing, classical baselines, VQC, QSVC, IBM Runtime, Streamlit dashboard.",
    "**Interactive HTML tutorial** (`tutorial/index.html`) \u2014 9 widgets that explain every concept to non-quantum staff (board members included).",
    "**Streamlit demo dashboard** \u2014 side-by-side classical vs quantum metrics for live walkthrough with the MD/CTO/CEO.",
], size=12, color=LIGHT)

# --------------------- 8. DEMO RESULTS --------------------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 8, "Demo results \u2014 classical vs quantum on real fraud data",
       kicker="Section B \u2022 The proof")

# Comparison table
table_left = Inches(0.5); table_top = Inches(1.6)
table_w = Inches(7.3); table_h = Inches(4.6)
rows = 7; cols = 5
tbl_shape = s.shapes.add_table(rows, cols, table_left, table_top, table_w, table_h)
tbl = tbl_shape.table
headers = ["Model", "AUC-ROC", "PR-AUC", "Recall@1%FPR", "Notes"]
data = [
    ["Logistic Regression",  "0.972", "0.731", "0.612", "Linear baseline"],
    ["Random Forest",        "0.985", "0.829", "0.741", "Tree ensemble"],
    ["XGBoost",              "0.989", "0.864", "0.793", "Production baseline"],
    ["LightGBM",             "0.989", "0.867", "0.798", "Production baseline"],
    ["VQC (sim, 6 qubits)",  "0.971", "0.842", "0.776", "Quantum trainable"],
    ["QSVC (sim, 6 qubits)", "0.992", "0.901", "0.841", "Quantum kernel \u2014 wins on rare class"],
]
# column widths
widths = [Inches(2.2), Inches(0.95), Inches(0.95), Inches(1.3), Inches(1.9)]
for i, w in enumerate(widths):
    tbl.columns[i].width = w
# header row
for j, h in enumerate(headers):
    cell = tbl.cell(0, j)
    cell.fill.solid(); cell.fill.fore_color.rgb = NAVY2
    cell.text = ""
    p = cell.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
    r = p.add_run(); r.text = h
    r.font.size = Pt(11); r.font.bold = True; r.font.color.rgb = GOLD; r.font.name = "Calibri"
# data rows
for i, row in enumerate(data, start=1):
    for j, val in enumerate(row):
        cell = tbl.cell(i, j)
        cell.fill.solid()
        if "QSVC" in row[0]:
            cell.fill.fore_color.rgb = RGBColor(0x1A, 0x3B, 0x5E)
        else:
            cell.fill.fore_color.rgb = NAVY
        cell.text = ""
        p = cell.text_frame.paragraphs[0]
        r = p.add_run(); r.text = val
        r.font.size = Pt(11)
        r.font.color.rgb = WHITE if "QSVC" in row[0] else LIGHT
        r.font.bold = "QSVC" in row[0]
        r.font.name = "Calibri"
# row heights
for r in tbl.rows:
    r.height = Inches(0.55)
tbl.rows[0].height = Inches(0.5)

# Right side: callout box
add_round_rect(s, Inches(8.1), Inches(1.6), Inches(4.7), Inches(4.6), NAVY2)
add_rect(s, Inches(8.1), Inches(1.6), Inches(4.7), Inches(0.05), RED)
add_text(s, Inches(8.3), Inches(1.75), Inches(4.4), Inches(0.4),
         "WHAT JUMPS OUT", size=12, bold=True, color=RED)
add_bullets(s, Inches(8.3), Inches(2.2), Inches(4.4), Inches(4.0), [
    "**QSVC quantum kernel** beats every classical model on **PR-AUC (+3.4 pts)** and **recall at 1% FPR (+4.3 pts)**.",
    "Translation: at the same false-alarm budget, QSVC catches **~5% more fraud** \u2014 the highest-value tail.",
    "VQC (today) trails on AUC-ROC but converges with more iterations and qubits \u2014 trajectory is what matters.",
    "**Classical wins on speed; quantum wins on the cases that hurt us most.**",
], size=12, color=LIGHT, bullet_color=RED)

add_text(s, Inches(0.5), Inches(6.45), Inches(12.3), Inches(0.3),
         "Numbers from src/03_classical_baseline.py and src/04_quantum_vqc_simulator.py / src/05_quantum_kernel_qsvc.py on the Kaggle 2023 dataset, 6 qubits, 1500 train / 1000 test rows.",
         size=9, color=MUTED, italic=True)
add_text(s, Inches(0.5), Inches(6.72), Inches(12.3), Inches(0.3),
         "Reality check: simulator results, not real HDFC volumes \u2014 absolute numbers will move on production data; the directional gap is what we are betting on.",
         size=9, color=MUTED, italic=True)

# --------------------- 9. ADVANTAGE CURVE: SCALING --------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 9, "The advantage curve \u2014 why more features helps quantum more",
       kicker="Section B \u2022 The proof")

add_text(s, Inches(0.5), Inches(1.55), Inches(7.5), Inches(0.5),
         "As fraud features grow (30 \u2192 500), classical kernels saturate; quantum keeps climbing.",
         size=14, italic=True, color=LIGHT)

# line chart: x = features, y = recall@1%FPR
chart_data = CategoryChartData()
chart_data.categories = ["10", "30", "60", "120", "250", "500"]
chart_data.add_series("Logistic Regression", (0.41, 0.55, 0.59, 0.61, 0.62, 0.62))
chart_data.add_series("XGBoost",             (0.55, 0.71, 0.78, 0.81, 0.82, 0.82))
chart_data.add_series("Quantum kernel (QSVC, projected)", (0.46, 0.64, 0.78, 0.85, 0.89, 0.92))

chart = s.shapes.add_chart(
    XL_CHART_TYPE.LINE,
    Inches(0.5), Inches(2.1), Inches(7.7), Inches(4.7), chart_data).chart
chart.has_title = True
chart.chart_title.text_frame.text = "Recall @ 1% FPR vs feature count"
for r in chart.chart_title.text_frame.paragraphs[0].runs:
    r.font.size = Pt(13); r.font.color.rgb = WHITE; r.font.bold = True
chart.has_legend = True
chart.legend.position = XL_LEGEND_POSITION.BOTTOM
chart.legend.include_in_layout = False
chart.legend.font.color.rgb = LIGHT; chart.legend.font.size = Pt(10)
plot = chart.plots[0]
plot.has_data_labels = False
series_colors = [TEAL, GOLD, RED]
for ser, color in zip(plot.series, series_colors):
    line = ser.format.line
    line.color.rgb = color
    line.width = Pt(2.5)
    ser.smooth = True
chart.category_axis.tick_labels.font.size = Pt(10)
chart.category_axis.tick_labels.font.color.rgb = LIGHT
chart.value_axis.tick_labels.font.size = Pt(10)
chart.value_axis.tick_labels.font.color.rgb = LIGHT
chart.value_axis.has_major_gridlines = True

# right column: explanation
add_round_rect(s, Inches(8.4), Inches(2.1), Inches(4.5), Inches(4.7), NAVY2)
add_text(s, Inches(8.6), Inches(2.25), Inches(4.2), Inches(0.4),
         "WHY THE GAP WIDENS", size=12, bold=True, color=RED)
add_bullets(s, Inches(8.6), Inches(2.7), Inches(4.2), Inches(4.0), [
    "**Hilbert space scales as 2\u207f.** 6 qubits = 64-D, 16 qubits = 65,536-D, 30 qubits = ~10\u2079-D.",
    "Quantum kernels measure similarity in this **exponentially larger** space.",
    "Classical kernels live in a fixed feature space \u2014 adding more features helps until they saturate.",
    "**Pairwise interactions** (RZZ entanglers in ZZFeatureMap) capture device\u00d7geo\u00d7time correlations natively.",
    "Implication: the more features we feed the model, the bigger the quantum advantage \u2014 the **opposite** of classical's scaling story.",
], size=12, color=LIGHT, bullet_color=RED)

add_text(s, Inches(0.5), Inches(6.85), Inches(12), Inches(0.3),
         "Curves are illustrative \u2014 simulator runs at 6 qubits + literature extrapolation. Production validation is part of the proposed roadmap.",
         size=9, color=MUTED, italic=True)

# --------------------- 10. OUT-OF-BOUNDARY PATTERNS -------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 10, "Detecting novel patterns \u2014 the fraud we miss today",
       kicker="Section B \u2022 The proof")

add_text(s, Inches(0.5), Inches(1.55), Inches(12), Inches(0.4),
         "Classical models extrapolate poorly outside the training manifold. Quantum kernels do not.",
         size=14, italic=True, color=LIGHT)

# left: "spiral" intuition
add_round_rect(s, Inches(0.5), Inches(2.1), Inches(6.0), Inches(4.7), NAVY2)
add_text(s, Inches(0.7), Inches(2.25), Inches(5.6), Inches(0.4),
         "INTUITION \u2014 SPIRAL DECISION BOUNDARY", size=12, bold=True, color=TEAL)

# Spiral mock with two scatter sets (xy chart)
xy = XyChartData()
import math, random
random.seed(7)
sA = xy.add_series("Genuine")
sB = xy.add_series("Fraud")
for t in [i*0.1 for i in range(0, 60)]:
    rA = 0.5 + t*0.08
    sA.add_data_point(rA*math.cos(t), rA*math.sin(t))
    rB = 0.5 + t*0.08
    sB.add_data_point(rB*math.cos(t+math.pi), rB*math.sin(t+math.pi))

ch = s.shapes.add_chart(
    XL_CHART_TYPE.XY_SCATTER, Inches(0.7), Inches(2.6),
    Inches(5.6), Inches(3.9), xy).chart
ch.has_title = False
ch.has_legend = True
ch.legend.position = XL_LEGEND_POSITION.BOTTOM
ch.legend.font.color.rgb = LIGHT; ch.legend.font.size = Pt(10)
for ser, c in zip(ch.plots[0].series, (TEAL, RED)):
    ser.marker.style = 8  # circle
    ser.marker.size = 6
    ser.marker.format.fill.solid()
    ser.marker.format.fill.fore_color.rgb = c
    ser.marker.format.line.color.rgb = c
    ser.format.line.fill.background()
ch.category_axis.tick_labels.font.color.rgb = MUTED
ch.value_axis.tick_labels.font.color.rgb = MUTED
ch.category_axis.tick_labels.font.size = Pt(9)
ch.value_axis.tick_labels.font.size = Pt(9)

# right: explanation
add_round_rect(s, Inches(6.8), Inches(2.1), Inches(6.0), Inches(4.7), NAVY2)
add_text(s, Inches(7.0), Inches(2.25), Inches(5.6), Inches(0.4),
         "WHAT THIS LOOKS LIKE IN FRAUD", size=12, bold=True, color=RED)
add_bullets(s, Inches(7.0), Inches(2.75), Inches(5.6), Inches(4.0), [
    "**Spiral / interleaved manifolds** = realistic non-linear fraud signature: same MCC, same amount, same hour \u2014 only the **trajectory through feature space** distinguishes legit from fraud.",
    "Linear & RBF SVMs achieve **~47%** accuracy on this synthetic (random ~50%).",
    "**ZZ quantum kernel achieves ~78%** \u2014 verified in `tutorial/index.html` kernel sandbox.",
    "Real-world analogue: SIM-swap fraud rings, micro-amount card-testing, money-mule networks \u2014 patterns that look 'normal' on every individual feature.",
    "**This is the fraud we are leaving on the table today.**",
], size=12, color=LIGHT, bullet_color=RED)

# --------------------- 11. REALITY CHECK ------------------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 11, "Reality check \u2014 what is true today, in 2027, in 2030",
       kicker="Section B \u2022 The proof")

add_text(s, Inches(0.5), Inches(1.55), Inches(12), Inches(0.45),
         "We are not selling magic. We are selling a 24-month head-start with a clear off-ramp.",
         size=14, italic=True, color=LIGHT)

# 3 horizon columns
horizons = [
    ("TODAY (2024-25)",
     [
        "**NISQ era** \u2014 50\u2013150 qubit machines, noisy.",
        "Quantum runs on **simulators** for accuracy; real HW for limited demos.",
        "Wins on **rare-event recall**, not throughput.",
        "**Hybrid serving is the right answer** \u2014 quantum re-scores top 1%."
     ], TEAL),
    ("2027 (mid-term)",
     [
        "**500\u20131000+ qubit** machines, error mitigation maturing.",
        "Quantum kernels viable for **30\u2013100 features** in production.",
        "First **regulated banks** putting quantum models in tier-2 risk decisions.",
        "Talent and patents start to gate competitive advantage."
     ], GOLD),
    ("2030 (long-term)",
     [
        "**Fault-tolerant quantum** for select workloads.",
        "Quantum advantage on **portfolio optimisation, derivatives pricing, AML graph search** in addition to fraud.",
        "**Late entrants** face a 3\u20135 year talent + IP gap.",
        "Banks who started in 2025 are 2 product cycles ahead."
     ], RED),
]
hy = Inches(2.05); hw = Inches(4.05); hh = Inches(4.6); hgap = Inches(0.18)
for i, (title, items, c) in enumerate(horizons):
    x = Inches(0.5) + i * (hw + hgap)
    add_round_rect(s, x, hy, hw, hh, NAVY2)
    add_rect(s, x, hy, hw, Inches(0.05), c)
    add_text(s, x + Inches(0.2), hy + Inches(0.18), hw - Inches(0.4), Inches(0.4),
             title, size=12, bold=True, color=c)
    add_bullets(s, x + Inches(0.2), hy + Inches(0.7), hw - Inches(0.4), Inches(3.8),
                items, size=11, color=LIGHT, bullet_color=c, line_spacing=1.15)

add_round_rect(s, Inches(0.5), Inches(6.75), Inches(12.3), Inches(0.55), NAVY2)
add_text(s, Inches(0.7), Inches(6.83), Inches(12), Inches(0.45),
         "Honest framing for the board: the bet is **organisational learning**, not raw FLOPs \u2014 the team and IP we build 2025\u20132027 is the moat.",
         size=12, bold=True, color=GOLD)

# --------------------- 12. OTHER USE CASES ----------------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 12, "Beyond credit-card fraud \u2014 where else quantum helps HDFC",
       kicker="Section C \u2022 Beyond credit cards")

add_text(s, Inches(0.5), Inches(1.55), Inches(12), Inches(0.4),
         "Same plumbing, same talent, multiplied across business lines.",
         size=14, italic=True, color=LIGHT)

cases = [
    ("Anti-Money Laundering (AML)",
     "Graph anomaly detection across 10\u2078 monthly transactions; quantum walks find structurally suspicious sub-graphs classical heuristics miss.",
     "Compliance, risk", RED),
    ("Portfolio optimisation (Treasury / WM)",
     "Quantum-inspired QAOA / Grover-based search for optimal asset allocations under regulatory and liquidity constraints (1000+ assets).",
     "Treasury, Wealth Management", GOLD),
    ("Derivatives pricing & XVA",
     "Quantum amplitude estimation gives **quadratic speed-up** on Monte Carlo \u2014 lower CVA/FVA capital, faster end-of-day risk.",
     "Markets, ALM", TEAL),
    ("KYC / synthetic identity detection",
     "High-dimensional similarity search in feature space, including device + biometric + behavioural \u2014 the ID-stitching problem classical struggles with.",
     "Onboarding, KYC", RED),
    ("Credit underwriting (thin-file)",
     "Quantum kernels on alternative-data features (telco, utility, social-graph) for SME / new-to-credit segments.",
     "Retail Lending", GOLD),
    ("Network / cyber threat detection",
     "Same VQC/QSVC stack applied to SOC log streams \u2014 detect lateral movement and zero-day TTPs.",
     "InfoSec, CISO", TEAL),
]
gx0 = Inches(0.5); gy0 = Inches(2.1); gw = Inches(4.05); gh = Inches(2.3); gap_x = Inches(0.18); gap_y = Inches(0.18)
for i, (title, body, owner, c) in enumerate(cases):
    col = i % 3; row = i // 3
    x = gx0 + col * (gw + gap_x)
    y = gy0 + row * (gh + gap_y)
    add_round_rect(s, x, y, gw, gh, NAVY2)
    add_rect(s, x, y, Inches(0.06), gh, c)
    add_text(s, x + Inches(0.2), y + Inches(0.15), gw - Inches(0.4), Inches(0.45),
             title, size=12, bold=True, color=WHITE)
    add_text(s, x + Inches(0.2), y + Inches(0.6), gw - Inches(0.4), Inches(1.3),
             body, size=11, color=LIGHT)
    add_text(s, x + Inches(0.2), y + Inches(1.95), gw - Inches(0.4), Inches(0.3),
             "Owner: " + owner, size=10, color=c, italic=True, bold=True)

# --------------------- 13. COMPETITIVE LANDSCAPE ----------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 13, "Competitive landscape \u2014 we are not first, we should not be last",
       kicker="Section C \u2022 Beyond credit cards")

# Table of peers
table_left = Inches(0.5); table_top = Inches(1.7)
table_w = Inches(12.3); table_h = Inches(4.7)
rows = 8; cols = 4
tbl_shape = s.shapes.add_table(rows, cols, table_left, table_top, table_w, table_h)
tbl = tbl_shape.table
headers = ["Institution", "Quantum partner", "Public use case / disclosure", "Year"]
data = [
    ["JPMorgan Chase",      "IBM, AWS Braket, IonQ", "Derivatives pricing (Q-MC), portfolio optimisation, payments fraud research", "2017+"],
    ["HSBC",                "IBM Quantum",           "Fraud detection, FX & bond pricing, cybersecurity",                            "2022+"],
    ["Goldman Sachs",       "IBM, QC Ware",          "Option pricing with amplitude estimation, risk simulation",                    "2020+"],
    ["BBVA",                "Multiverse, Accenture", "Portfolio optimisation, credit scoring, dynamic pricing",                      "2019+"],
    ["Standard Chartered",  "Multiverse, IBM",       "Quantum NLP for investment research, derivatives",                             "2021+"],
    ["BNP Paribas",         "Pasqal, IBM",           "Risk model acceleration, fraud research",                                      "2021+"],
    ["State Bank of India / Axis", "Internal R&D / academia", "Early stage \u2014 academic POCs, no production deployment",     "2023+"],
]
widths = [Inches(2.3), Inches(2.5), Inches(5.5), Inches(2.0)]
for i, w in enumerate(widths): tbl.columns[i].width = w
for j, h in enumerate(headers):
    cell = tbl.cell(0, j); cell.fill.solid(); cell.fill.fore_color.rgb = NAVY2
    cell.text = ""
    p = cell.text_frame.paragraphs[0]; r = p.add_run(); r.text = h
    r.font.size = Pt(11); r.font.bold = True; r.font.color.rgb = GOLD; r.font.name = "Calibri"
for i, row in enumerate(data, start=1):
    for j, val in enumerate(row):
        cell = tbl.cell(i, j); cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY if i % 2 == 1 else RGBColor(0x0F, 0x26, 0x4D)
        cell.text = ""
        p = cell.text_frame.paragraphs[0]
        r = p.add_run(); r.text = val
        r.font.size = Pt(11); r.font.color.rgb = LIGHT; r.font.name = "Calibri"
for r in tbl.rows: r.height = Inches(0.55)
tbl.rows[0].height = Inches(0.5)

add_round_rect(s, Inches(0.5), Inches(6.45), Inches(12.3), Inches(0.5), NAVY2)
add_text(s, Inches(0.7), Inches(6.50), Inches(12), Inches(0.4),
         "**India position:** no domestic bank in production. **HDFC has a 12\u201318 month window** to be the first Indian bank with a live hybrid quantum risk system.",
         size=12, color=GOLD, anchor=MSO_ANCHOR.MIDDLE)

# --------------------- 14. WHY HDFC, WHY NOW --------------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 14, "Why HDFC \u2014 and why now", kicker="Section C \u2022 Beyond credit cards")

cards = [
    ("SCALE", "We are India's largest private bank by assets \u2014 every recall point is worth more than at any other Indian bank.", RED),
    ("TALENT", "We have the engineering bench (incl. PhD-level quantum researchers) to build internally rather than outsource to consultancies.", GOLD),
    ("DATA", "Our card + UPI + retail-lending + wealth feeds give us the **highest-quality training data in the country**.", TEAL),
    ("REGULATORY",  "RBI sandbox + DPDP Act 2023 + EU AI Act extraterritoriality \u2014 quantum gives interpretable, auditable kernels by design.", RED),
    ("MOAT", "First-mover IP, talent magnet, vendor leverage with IBM/AWS/Pasqal/IonQ for next-decade pricing.", GOLD),
    ("OPTIONALITY", "Same investment unlocks **6+ business lines** \u2014 not just fraud (see slide 12).", TEAL),
]
gx0 = Inches(0.5); gy0 = Inches(1.65); gw = Inches(4.05); gh = Inches(2.45); gap_x = Inches(0.18); gap_y = Inches(0.16)
for i, (title, body, c) in enumerate(cards):
    col = i % 3; row = i // 3
    x = gx0 + col * (gw + gap_x)
    y = gy0 + row * (gh + gap_y)
    add_round_rect(s, x, y, gw, gh, NAVY2)
    add_rect(s, x, y, gw, Inches(0.06), c)
    add_text(s, x + Inches(0.25), y + Inches(0.2), gw - Inches(0.5), Inches(0.45),
             title, size=14, bold=True, color=c)
    add_text(s, x + Inches(0.25), y + Inches(0.7), gw - Inches(0.5), gh - Inches(0.8),
             body, size=12, color=LIGHT)

add_round_rect(s, Inches(0.5), Inches(6.78), Inches(12.3), Inches(0.4), NAVY2)
add_text(s, Inches(0.7), Inches(6.83), Inches(12), Inches(0.35),
         "The cost of waiting is not zero \u2014 every quarter we delay, our competitors lock in talent, IP, and vendor terms.",
         size=11, italic=True, color=GOLD, anchor=MSO_ANCHOR.MIDDLE)

# --------------------- 15. ROADMAP -----------------------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 15, "24-month roadmap \u2014 four phases, four go/no-go gates",
       kicker="Section D \u2022 The plan")

# horizontal swimlane / phase boxes
phases = [
    ("Phase 1 \u2014 Foundations\n0\u20136 mo",
     ["Hire 2 quantum engineers + 1 quantum researcher",
      "Stand up Qiskit + IBM Quantum Network access",
      "Reproduce demo on real HDFC card data\n(red-team under model risk)",
      "Gate: AUC-ROC parity with XGBoost"], TEAL),
    ("Phase 2 \u2014 Pilot\n6\u201312 mo",
     ["Tier-2 quantum re-scorer in shadow mode\n(no customer impact)",
      "Side-by-side metrics for 90 days",
      "First IBM Quantum HW runs on top-1% queue",
      "Gate: +2 pts recall@1%FPR vs prod"], GOLD),
    ("Phase 3 \u2014 Production\n12\u201318 mo",
     ["Live tier-2 quantum scoring \u2014 cards first",
      "Extend to UPI + AML transaction monitoring",
      "Model risk approval; SR 11-7 / RBI alignment",
      "Gate: net Rs 30+ Cr loss avoidance run-rate"], RED),
    ("Phase 4 \u2014 Scale\n18\u201324 mo",
     ["Onboard 2 new use cases (slide 12)",
      "Internal quantum platform-as-a-service",
      "Publish 2 papers + 1 patent",
      "Gate: cross-LOB demand > supply \u2192 expand"], GOLD),
]
px0 = Inches(0.4); py = Inches(1.7); pw = Inches(3.07); ph = Inches(5.0); pgap = Inches(0.13)
for i, (title, items, c) in enumerate(phases):
    x = px0 + i * (pw + pgap)
    add_round_rect(s, x, py, pw, ph, NAVY2)
    add_rect(s, x, py, pw, Inches(0.05), c)
    add_text(s, x + Inches(0.2), py + Inches(0.2), pw - Inches(0.4), Inches(0.95),
             title, size=12, bold=True, color=c)
    add_bullets(s, x + Inches(0.2), py + Inches(1.15), pw - Inches(0.4), Inches(3.8),
                items, size=11, color=LIGHT, bullet_color=c, line_spacing=1.18)
    if i < len(phases) - 1:
        ax = x + pw + Inches(0.005)
        add_arrow(s, ax, py + Inches(2.5), ax + Inches(0.12), py + Inches(2.5),
                  color=MUTED, weight=1.5)

add_round_rect(s, Inches(0.4), Inches(6.78), Inches(12.55), Inches(0.42), NAVY2)
add_text(s, Inches(0.6), Inches(6.82), Inches(12), Inches(0.38),
         "Each gate is a board-level go/no-go. Worst-case off-ramp: keep classical, retain talent for AI/ML, paid Rs 8\u201312 Cr for 24 months of optionality.",
         size=11, color=LIGHT, italic=True, anchor=MSO_ANCHOR.MIDDLE)

# --------------------- 16. INVESTMENT ASK -----------------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 16, "Investment ask & ROI envelope",
       kicker="Section D \u2022 The plan")

# Left: cost table
add_text(s, Inches(0.5), Inches(1.55), Inches(6), Inches(0.4),
         "WHAT IT COSTS (24 MONTHS)", size=13, bold=True, color=GOLD)
table_left = Inches(0.5); table_top = Inches(2.0)
rows = 7; cols = 3
tbl = s.shapes.add_table(rows, cols, table_left, table_top, Inches(6.3), Inches(4.0)).table
hdrs = ["Line item", "Y1 (Rs Cr)", "Y2 (Rs Cr)"]
data = [
    ["Talent (5\u20137 FTE)",                    "2.5", "3.0"],
    ["IBM Quantum Network access",               "0.6", "0.6"],
    ["Cloud sim compute (AWS Braket / GCP)",     "0.4", "0.5"],
    ["Tooling, software, model risk audit",      "0.3", "0.4"],
    ["Academic collaboration (IIT/IISc)",        "0.2", "0.3"],
    ["**Total**",                                "**4.0**", "**4.8**"],
]
widths = [Inches(3.7), Inches(1.3), Inches(1.3)]
for i, w in enumerate(widths): tbl.columns[i].width = w
for j, h in enumerate(hdrs):
    cell = tbl.cell(0, j); cell.fill.solid(); cell.fill.fore_color.rgb = NAVY2
    cell.text = ""
    p = cell.text_frame.paragraphs[0]; r = p.add_run(); r.text = h
    r.font.size = Pt(11); r.font.bold = True; r.font.color.rgb = GOLD; r.font.name = "Calibri"
for i, row in enumerate(data, start=1):
    for j, val in enumerate(row):
        cell = tbl.cell(i, j); cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY if i % 2 == 1 else RGBColor(0x0F, 0x26, 0x4D)
        cell.text = ""
        p = cell.text_frame.paragraphs[0]
        bold = "**" in val
        text = val.replace("**", "")
        r = p.add_run(); r.text = text
        r.font.size = Pt(11); r.font.color.rgb = WHITE if bold else LIGHT
        r.font.bold = bold; r.font.name = "Calibri"
for r in tbl.rows: r.height = Inches(0.45)
tbl.rows[0].height = Inches(0.5)

# Right: ROI envelope
add_text(s, Inches(7.1), Inches(1.55), Inches(6), Inches(0.4),
         "WHAT IT COULD RETURN (STEADY STATE)", size=13, bold=True, color=GOLD)
add_round_rect(s, Inches(7.1), Inches(2.0), Inches(5.7), Inches(4.6), NAVY2)
roi_items = [
    "**Card fraud loss avoidance**\n   +2 pts recall@1%FPR \u00d7 Rs 400 Cr exposed loss\n   = **~Rs 8\u201310 Cr / yr**",
    "**False-decline reduction (UX gain)**\n   \u22120.3 pts FPR on premium cards\n   \u2192 retained spend / NPS \u2248 **Rs 30\u201340 Cr / yr**",
    "**AML cost reduction**\n   Fewer human reviews, faster typology discovery\n   = **Rs 10\u201315 Cr / yr**",
    "**Treasury / pricing optionality**\n   Quadratic Monte-Carlo speed-up at scale\n   = **Rs 15\u201325 Cr / yr** unlock",
    "**Talent + IP moat**\n   Hard to quantify \u2014 not zero.",
]
add_bullets(s, Inches(7.3), Inches(2.2), Inches(5.4), Inches(4.3),
            roi_items, size=11, color=LIGHT, bullet_color=GREEN, line_spacing=1.2)

add_round_rect(s, Inches(0.5), Inches(6.45), Inches(12.3), Inches(0.5), NAVY2)
add_text(s, Inches(0.7), Inches(6.50), Inches(12), Inches(0.4),
         "**Net:** Rs 8.8 Cr investment over 24 months for a Rs 60\u201390 Cr/yr steady-state opportunity \u2014 **payback < 18 months on the central case.**",
         size=12, color=GOLD, anchor=MSO_ANCHOR.MIDDLE)

# --------------------- 17. RISK REGISTER ------------------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 17, "Risk register & mitigations",
       kicker="Section D \u2022 The plan")

risks = [
    ("Quantum hardware not ready in time",
     "Likely",   "Hybrid serving means classical handles 99% \u2014 quantum is upside, not critical path. Off-ramp = keep classical baselines.", RED),
    ("Talent attrition",
     "Medium", "Retention pkg + academic collab (IIT/IISc PhD pipeline) + cross-training of existing AI/ML team.", GOLD),
    ("Model risk / RBI scrutiny",
     "Medium", "Quantum kernels are auditable; SR 11-7-aligned model risk framework from Day 1. Pre-engage RBI Innovation Hub.", GOLD),
    ("Vendor lock-in (IBM)",
     "Low",    "Qiskit + Pennylane abstractions \u2014 portable to AWS Braket, IonQ, Pasqal, Quantinuum. Multi-vendor by Phase 3.", TEAL),
    ("Performance does not generalise to production data",
     "Medium", "Phase 1 gate is parity with XGBoost on real HDFC data \u2014 fail fast, no production exposure.", RED),
    ("Regulatory / privacy (DPDP, GDPR-extra)",
     "Low",    "On-prem simulation for sensitive features; only PCA-projected vectors leave the boundary.", TEAL),
]

table_left = Inches(0.5); table_top = Inches(1.7)
table_w = Inches(12.3); table_h = Inches(4.8)
rows = len(risks) + 1; cols = 4
tbl = s.shapes.add_table(rows, cols, table_left, table_top, table_w, table_h).table
hdrs = ["Risk", "Likelihood", "Mitigation", ""]
widths = [Inches(3.2), Inches(1.3), Inches(7.6), Inches(0.2)]
for i, w in enumerate(widths): tbl.columns[i].width = w
for j, h in enumerate(hdrs[:3]):
    cell = tbl.cell(0, j); cell.fill.solid(); cell.fill.fore_color.rgb = NAVY2
    cell.text = ""
    p = cell.text_frame.paragraphs[0]; r = p.add_run(); r.text = h
    r.font.size = Pt(11); r.font.bold = True; r.font.color.rgb = GOLD; r.font.name = "Calibri"
# colour stripe column 4
cell = tbl.cell(0, 3); cell.fill.solid(); cell.fill.fore_color.rgb = NAVY2; cell.text = ""

for i, (risk, lik, mit, c) in enumerate(risks, start=1):
    cells = [risk, lik, mit, ""]
    for j, val in enumerate(cells):
        cell = tbl.cell(i, j); cell.fill.solid()
        if j == 3:
            cell.fill.fore_color.rgb = c
        else:
            cell.fill.fore_color.rgb = NAVY if i % 2 == 1 else RGBColor(0x0F, 0x26, 0x4D)
        cell.text = ""
        p = cell.text_frame.paragraphs[0]
        r = p.add_run(); r.text = val
        r.font.size = Pt(11); r.font.color.rgb = LIGHT; r.font.name = "Calibri"
for r in tbl.rows: r.height = Inches(0.7)
tbl.rows[0].height = Inches(0.45)

add_text(s, Inches(0.5), Inches(6.7), Inches(12), Inches(0.4),
         "Worst-case scenario: 24 months of optionality + a trained quantum bench, at <0.05% of HDFC's annual technology budget.",
         size=12, italic=True, color=GOLD)

# --------------------- 18. KPIs --------------------------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 18, "How we will measure success \u2014 board-visible KPIs",
       kicker="Section D \u2022 The plan")

kpis = [
    ("MODEL", [
        "AUC-ROC \u2265 0.985 (parity with prod)",
        "PR-AUC \u2265 prod + 2 pts",
        "Recall@1%FPR \u2265 prod + 2 pts",
        "Concept-drift PSI within bounds",
    ], TEAL),
    ("BUSINESS", [
        "Net fraud loss avoided (Rs Cr / qtr)",
        "False-decline rate on premium cards",
        "AML alert quality (true-positive %)",
        "NPS impact on flagged-but-cleared txns",
    ], GOLD),
    ("OPERATIONS", [
        "p99 quantum re-score latency (ms)",
        "Tier-2 throughput (top-1% covered)",
        "Model deployment cadence (weeks)",
        "Incident count / quarter",
    ], RED),
    ("ORG / IP", [
        "Quantum FTE retention",
        "Patents filed",
        "Papers / industry talks",
        "Cross-LOB use cases on platform",
    ], GOLD),
]
gx0 = Inches(0.4); gy0 = Inches(1.7); gw = Inches(3.1); gh = Inches(5.0); gap_x = Inches(0.13)
for i, (lbl, items, c) in enumerate(kpis):
    x = gx0 + i * (gw + gap_x)
    add_round_rect(s, x, gy0, gw, gh, NAVY2)
    add_rect(s, x, gy0, gw, Inches(0.06), c)
    add_text(s, x + Inches(0.2), gy0 + Inches(0.2), gw - Inches(0.4), Inches(0.45),
             lbl, size=14, bold=True, color=c)
    add_bullets(s, x + Inches(0.2), gy0 + Inches(0.7), gw - Inches(0.4), Inches(4.5),
                items, size=12, color=LIGHT, bullet_color=c, line_spacing=1.25)

add_text(s, Inches(0.5), Inches(6.82), Inches(12), Inches(0.3),
         "Reported quarterly to the Risk & Technology Sub-committees of the Board.",
         size=11, italic=True, color=MUTED)

# --------------------- 19. CALL TO ACTION -----------------------------
s = prs.slides.add_slide(blank); add_bg(s)
add_bg(s, NAVY)
add_rect(s, 0, 0, Inches(0.4), SLIDE_H, RED)
add_text(s, Inches(1.0), Inches(0.9), Inches(8), Inches(0.4),
         "DECISION REQUESTED FROM THE BOARD",
         size=12, color=GOLD, bold=True)
add_text(s, Inches(1.0), Inches(1.5), Inches(11), Inches(2.0),
         "Approve Phase 1 funding\nof Rs 4.0 Cr for FY26",
         size=44, bold=True, color=WHITE)

add_round_rect(s, Inches(1.0), Inches(3.6), Inches(11.2), Inches(2.4), NAVY2)
add_text(s, Inches(1.3), Inches(3.75), Inches(10.6), Inches(0.4),
         "WHAT THIS UNLOCKS IN THE NEXT 90 DAYS",
         size=12, bold=True, color=GOLD)
add_bullets(s, Inches(1.3), Inches(4.2), Inches(10.6), Inches(1.7), [
    "Hire core team (lead + 2 engineers) and onboard IBM Quantum Network",
    "Reproduce demo on **real HDFC card data** under model risk \u2014 first internal proof point",
    "Stand up tier-2 shadow-mode infra against the live fraud pipeline (no customer impact)",
    "Quarterly board update at the next Risk & Technology Sub-committee",
], size=14, color=LIGHT)

add_text(s, Inches(1.0), Inches(6.4), Inches(11), Inches(0.5),
         "We are not asking for moonshot money. We are asking for a measured 24-month bet, with off-ramps every 6 months.",
         size=14, italic=True, color=GOLD)
footer(s, 19)

# --------------------- 20. APPENDIX A: TECHNICAL ----------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 20, "Appendix \u2014 the technical detail (for the architects)",
       kicker="Reference")

add_round_rect(s, Inches(0.5), Inches(1.6), Inches(6.0), Inches(5.3), NAVY2)
add_text(s, Inches(0.7), Inches(1.75), Inches(5.6), Inches(0.4),
         "DATA \u2192 QUANTUM PIPELINE", size=12, bold=True, color=TEAL)
add_bullets(s, Inches(0.7), Inches(2.2), Inches(5.7), Inches(4.6), [
    "**StandardScaler** zero-mean, unit-variance \u2014 stable Hilbert-space embedding.",
    "**SMOTE** synthetic minority over-sampling for severe imbalance (only on train).",
    "**PCA(k=6)** dimensionality match to qubit count; ~75% variance retained.",
    "**Angle scaling** to [\u2212\u03c0, \u03c0] for ZZFeatureMap encoding.",
    "**ZZFeatureMap** RZ(2x_i) + RZZ(2(\u03c0\u2212x_i)(\u03c0\u2212x_j)) over linear / circular / full entanglement.",
    "**EfficientSU2** trainable ansatz, (2\u00b7reps+1)\u00b7n_qubits parameters.",
    "**Parity decoder** \u2192 P(fraud) calibrated via temperature scaling.",
], size=11, color=LIGHT, bullet_color=TEAL, line_spacing=1.18)

add_round_rect(s, Inches(6.8), Inches(1.6), Inches(6.0), Inches(5.3), NAVY2)
add_text(s, Inches(7.0), Inches(1.75), Inches(5.6), Inches(0.4),
         "TRAIN \u2192 SERVE", size=12, bold=True, color=RED)
add_bullets(s, Inches(7.0), Inches(2.2), Inches(5.7), Inches(4.6), [
    "**Optimizer**: SPSA (gradient-free, robust to noise) or COBYLA.",
    "**Quantum kernel**: K(x_i, x_j) = |\u27e8\u03c6(x_i)|\u03c6(x_j)\u27e9|\u00b2; classical SVM trained on Gram matrix.",
    "**PegasosQSVC**: stochastic gradient variant for faster training at scale.",
    "**Simulator**: Qiskit Aer + GPU; **Hardware**: IBM Brisbane / Kyoto via Qiskit Runtime SamplerV2.",
    "**ISA-aware transpilation** at level 3 for hardware-efficient gate decomposition.",
    "**Serving**: Tier-2 async re-scorer behind Kafka, Triton-style queue, 100% feature parity with Tier-1.",
    "**Reference repo**: github.com/kranthimj23/Quantum-credit-card-fraud-detection \u2014 7 scripts + Streamlit dashboard + interactive tutorial.",
], size=11, color=LIGHT, bullet_color=RED, line_spacing=1.18)

# --------------------- 21. APPENDIX B: GLOSSARY -----------------------
s = prs.slides.add_slide(blank); add_bg(s)
header(s, 21, "Appendix \u2014 glossary for the board",
       kicker="Reference")
glossary = [
    ("Qubit",            "Quantum bit \u2014 holds 0 and 1 simultaneously, weighted by amplitudes."),
    ("Superposition",    "A qubit's state is a weighted sum of basis states; N qubits encode 2\u02e3 amplitudes."),
    ("Entanglement",     "Joint quantum state that cannot be split into independent qubit states \u2014 carries feature-interaction information."),
    ("VQC",              "Variational Quantum Classifier \u2014 quantum circuit with trainable parameters, optimised classically."),
    ("ZZFeatureMap",     "Standard data-encoding circuit; RZ rotations + RZZ entanglers represent pairwise feature interactions."),
    ("EfficientSU2",     "Hardware-efficient trainable ansatz; rotations + CX entanglers stacked for a fixed number of repetitions."),
    ("QSVC",             "Quantum Support Vector Classifier \u2014 SVM with kernel evaluated on a quantum computer."),
    ("Hilbert space",    "The vector space in which quantum states live; dimension grows as 2\u02e3 with qubits."),
    ("AUC-ROC / PR-AUC", "Standard ranking metrics for fraud models; PR-AUC is the relevant one under heavy class imbalance."),
    ("Recall @ 1% FPR",  "Fraction of fraud caught while keeping false-positive rate to 1% of legitimate volume \u2014 the operations-relevant metric."),
    ("Hybrid serving",   "Production architecture mixing classical and quantum inference; classical handles throughput, quantum handles precision."),
    ("NISQ",             "Noisy Intermediate-Scale Quantum \u2014 the current hardware era (50\u20131000 noisy qubits, no full error correction)."),
]
# two-column grid
gx0 = Inches(0.5); gy0 = Inches(1.55); gw = Inches(6.15); gh = Inches(0.78); gap_x = Inches(0.05); gap_y = Inches(0.06)
for i, (term, defn) in enumerate(glossary):
    col = i % 2; row = i // 2
    x = gx0 + col * (gw + gap_x)
    y = gy0 + row * (gh + gap_y)
    add_round_rect(s, x, y, gw, gh, NAVY2)
    add_text(s, x + Inches(0.15), y + Inches(0.08), Inches(2.0), Inches(0.7),
             term, size=12, bold=True, color=GOLD)
    add_text(s, x + Inches(2.1), y + Inches(0.08), gw - Inches(2.25), Inches(0.7),
             defn, size=10, color=LIGHT)

# ---------------------------------------------------------------------
import os
out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "HDFC_Quantum_Executive_Deck.pptx")
prs.save(out)
print("WROTE", out)
