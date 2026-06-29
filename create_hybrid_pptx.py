from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

DARK_BLUE = RGBColor(0, 51, 102)
ACCENT_BLUE = RGBColor(0, 112, 192)
LIGHT_BLUE = RGBColor(217, 226, 243)
DARK_GRAY = RGBColor(64, 64, 64)
WHITE = RGBColor(255, 255, 255)
GREEN = RGBColor(0, 128, 0)
PURPLE = RGBColor(139, 92, 246)

def add_header(slide, title, color=DARK_BLUE):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.2))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()

    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.8))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = WHITE

def add_content_box(slide, x, y, w, h, title, content, header_color=ACCENT_BLUE):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(245, 247, 250)
    box.line.color.rgb = header_color

    hdr = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, Inches(0.35))
    hdr.fill.solid()
    hdr.fill.fore_color.rgb = header_color
    hdr.line.fill.background()

    txTitle = slide.shapes.add_textbox(x + Inches(0.1), y + Inches(0.05), w - Inches(0.2), Inches(0.3))
    tf = txTitle.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = WHITE

    txBox = slide.shapes.add_textbox(x + Inches(0.1), y + Inches(0.45), w - Inches(0.2), h - Inches(0.55))
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, line in enumerate(content):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = line
        p.font.size = Pt(11)
        p.font.color.rgb = DARK_GRAY
        p.space_after = Pt(3)

def add_diagram_box(slide, x, y, w, h, title, content_lines, border_color=ACCENT_BLUE):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(240, 244, 250)
    box.line.color.rgb = border_color

    txTitle = slide.shapes.add_textbox(x + Inches(0.15), y + Inches(0.1), w - Inches(0.3), Inches(0.3))
    tf = txTitle.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = border_color

    txBox = slide.shapes.add_textbox(x + Inches(0.15), y + Inches(0.4), w - Inches(0.3), h - Inches(0.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, line in enumerate(content_lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = line
        p.font.size = Pt(11)
        p.font.name = "Consolas"
        p.font.color.rgb = DARK_GRAY

# ============== SLIDE 1: Title ==============
slide1 = prs.slides.add_slide(prs.slide_layouts[6])

# Gradient-like header
shape = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(4))
shape.fill.solid()
shape.fill.fore_color.rgb = RGBColor(30, 27, 75)
shape.line.fill.background()

# Decorative accent
shape2 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(3.5), prs.slide_width, Inches(0.5))
shape2.fill.solid()
shape2.fill.fore_color.rgb = ACCENT_BLUE
shape2.line.fill.background()

txBox = slide1.shapes.add_textbox(Inches(0.5), Inches(1.2), Inches(12.3), Inches(1.5))
tf = txBox.text_frame
p = tf.paragraphs[0]
p.text = "Quantum-Classical Hybrid Approach"
p.font.size = Pt(48)
p.font.bold = True
p.font.color.rgb = WHITE

txBox2 = slide1.shapes.add_textbox(Inches(0.5), Inches(2.8), Inches(12.3), Inches(0.8))
tf2 = txBox2.text_frame
p2 = tf2.paragraphs[0]
p2.text = "Where Quantum Computing Actually Helps Fraud Detection"
p2.font.size = Pt(22)
p2.font.color.rgb = RGBColor(199, 210, 254)

txBox3 = slide1.shapes.add_textbox(Inches(0.5), Inches(5.5), Inches(12.3), Inches(1.5))
tf3 = txBox3.text_frame
p3 = tf3.paragraphs[0]
p3.text = "Key Topics:"
p3.font.size = Pt(16)
p3.font.bold = True
p3.font.color.rgb = DARK_GRAY

topics = ["Hybrid Architecture Design", "Weight Optimization (QAOA)", "Rare Event Simulation (QAE)", "Fraud Ring Detection"]
for topic in topics:
    p = tf3.add_paragraph()
    p.text = "  " + topic
    p.font.size = Pt(14)
    p.font.color.rgb = DARK_GRAY

# ============== SLIDE 2: Reality Check ==============
slide2 = prs.slides.add_slide(prs.slide_layouts[6])
add_header(slide2, "Reality Check: Why Hybrid?")

# Warning box
box = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(1.5), Inches(12.3), Inches(1.5))
box.fill.solid()
box.fill.fore_color.rgb = RGBColor(254, 242, 226)
box.line.color.rgb = RGBColor(245, 158, 11)

txBox = slide2.shapes.add_textbox(Inches(0.7), Inches(1.6), Inches(12), Inches(1.3))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Quantum computers today are NOT ready to replace classical systems."
p.font.size = Pt(18)
p.font.bold = True
p.font.color.rgb = RGBColor(180, 83, 9)

p = tf.add_paragraph()
p.text = "They're powerful for specific problems but too slow and error-prone for real-time transaction processing."
p.font.size = Pt(14)
p.font.color.rgb = DARK_GRAY

# Solution box
box2 = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(3.2), Inches(12.3), Inches(1.3))
box2.fill.solid()
box2.fill.fore_color.rgb = RGBColor(209, 250, 229)
box2.line.color.rgb = GREEN

txBox2 = slide2.shapes.add_textbox(Inches(0.7), Inches(3.3), Inches(12), Inches(1.1))
tf2 = txBox2.text_frame
p = tf2.paragraphs[0]
p.text = "Solution: Hybrid Approach"
p.font.size = Pt(20)
p.font.bold = True
p.font.color.rgb = RGBColor(5, 80, 36)

p = tf2.add_paragraph()
p.text = "Classical systems handle real-time processing. Quantum handles background optimization."
p.font.size = Pt(14)
p.font.color.rgb = DARK_GRAY

# Comparison boxes
add_content_box(slide2, Inches(0.5), Inches(4.7), Inches(5.8), Inches(2.4),
    "Classical Handles",
    ["  Simple pattern matching",
     "  Rule-based scoring",
     "  Small neural networks",
     "  Real-time decisions (< 100ms)",
     "  SQL queries",
     "  Basic ML models"],
    GREEN)

add_content_box(slide2, Inches(6.9), Inches(4.7), Inches(5.9), Inches(2.4),
    "Quantum Handles",
    ["  Complex optimization",
     "  High-dimensional sampling",
     "  Combinatorial problems",
     "  Rare event simulation",
     "  Graph analysis (fraud rings)",
     "  Weight optimization"],
    ACCENT_BLUE)

# ============== SLIDE 3: Architecture ==============
slide3 = prs.slides.add_slide(prs.slide_layouts[6])
add_header(slide3, "The Hybrid Architecture")

# Main explanation
txBox = slide3.shapes.add_textbox(Inches(0.5), Inches(1.4), Inches(12.3), Inches(0.6))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Quantum runs asynchronously in the background. Results are cached. Real-time transactions hit the cache with zero added latency!"
p.font.size = Pt(14)
p.font.color.rgb = DARK_GRAY

# Tier boxes
tier_data = [
    ("Tier 1: Real-Time Rules", "< 50ms", ["50 fast rules", "Blocklist check", "Amount threshold", "Instant decision"], GREEN),
    ("Tier 2: ML Scoring", "< 100ms", ["200 ML features", "XGBoost scoring", "Behavioral baseline", "Device check"], RGBColor(245, 158, 11)),
    ("Tier 3: Quantum (Async)", "100-500ms", ["Weight optimization", "Rare events", "Graph analysis", "Pre-computed"], ACCENT_BLUE),
    ("Final Decision", "Cached", ["Combined score", "More accurate", "Fewer misses", "Fewer false alarms"], PURPLE)
]

for i, (title, time, items, color) in enumerate(tier_data):
    x = Inches(0.5 + i * 3.2)
    y = Inches(2.2)
    w = Inches(2.9)
    h = Inches(2.8)

    # Main box
    box = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(245, 247, 250)
    box.line.color.rgb = color

    # Header
    hdr = slide3.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, Inches(0.45))
    hdr.fill.solid()
    hdr.fill.fore_color.rgb = color
    hdr.line.fill.background()

    txTitle = slide3.shapes.add_textbox(x + Inches(0.1), y + Inches(0.05), w - Inches(0.2), Inches(0.35))
    tf = txTitle.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = WHITE

    # Time badge
    txTime = slide3.shapes.add_textbox(x + Inches(0.1), y + Inches(0.55), w - Inches(0.2), Inches(0.3))
    tf = txTime.text_frame
    p = tf.paragraphs[0]
    p.text = time
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = color
    p.alignment = 1  # center

    # Items
    txItems = slide3.shapes.add_textbox(x + Inches(0.1), y + Inches(0.9), w - Inches(0.2), Inches(1.8))
    tf = txItems.text_frame
    tf.word_wrap = True
    for j, item in enumerate(items):
        if j == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = item
        p.font.size = Pt(10)
        p.font.color.rgb = DARK_GRAY

    # Arrow (except last)
    if i < 3:
        arr = slide3.shapes.add_textbox(x + Inches(2.85), y + Inches(1.2), Inches(0.4), Inches(0.5))
        tf = arr.text_frame
        p = tf.paragraphs[0]
        p.text = ">"
        p.font.size = Pt(24)
        p.font.bold = True
        p.font.color.rgb = ACCENT_BLUE

# Bottom note
box_note = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(5.2), Inches(12.3), Inches(0.8))
box_note.fill.solid()
box_note.fill.fore_color.rgb = LIGHT_BLUE
box_note.line.color.rgb = ACCENT_BLUE

txBox = slide3.shapes.add_textbox(Inches(0.7), Inches(5.35), Inches(12), Inches(0.5))
tf = txBox.text_frame
p = tf.paragraphs[0]
p.text = "Key Insight: Tier 3 (Quantum) runs in background. Production latency is NEVER affected by quantum computation."
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = DARK_BLUE

# ============== SLIDE 4: Weight Optimization ==============
slide4 = prs.slides.add_slide(prs.slide_layouts[6])
add_header(slide4, "Use Case 1: Weight Optimization")

# Explanation
txBox = slide4.shapes.add_textbox(Inches(0.5), Inches(1.4), Inches(12.3), Inches(0.5))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Finding optimal weights for 100+ parameters is a combinatorial nightmare. Quantum helps!"
p.font.size = Pt(14)
p.font.color.rgb = DARK_GRAY

# Classical box
add_diagram_box(slide4, Inches(0.5), Inches(2.0), Inches(5.8), Inches(2.6),
    "Classical Gradient Descent",
    ["Training Time:  4-8 hours",
     "Problem:        Can get stuck in local minima",
     "Convergence:    Slow",
     "Accuracy:       94.3%"],
    GREEN)

# Quantum box
add_diagram_box(slide4, Inches(6.9), Inches(2.0), Inches(5.9), Inches(2.6),
    "Hybrid QAOA Algorithm",
    ["Quantum Sampling:    3 minutes",
     "Advantage:          Explores multiple states",
     "Convergence:        Fast",
     "Accuracy:           95.1% (+0.8%)"],
    ACCENT_BLUE)

# Result box
box = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(4.8), Inches(12.3), Inches(1.2))
box.fill.solid()
box.fill.fore_color.rgb = RGBColor(209, 250, 229)
box.line.color.rgb = GREEN

txBox = slide4.shapes.add_textbox(Inches(0.7), Inches(4.95), Inches(12), Inches(1))
tf = txBox.text_frame
p = tf.paragraphs[0]
p.text = "Result: 17x faster, +0.8% accuracy improvement!"
p.font.size = Pt(22)
p.font.bold = True
p.font.color.rgb = RGBColor(5, 80, 36)

p = tf.add_paragraph()
p.text = "Quantum doesn't replace classical ML - it provides better initialization for classical optimization."
p.font.size = Pt(12)
p.font.color.rgb = DARK_GRAY

# ============== SLIDE 5: Rare Event Simulation ==============
slide5 = prs.slides.add_slide(prs.slide_layouts[6])
add_header(slide5, "Use Case 2: Rare Event Simulation")

# Problem statement
box = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(1.4), Inches(12.3), Inches(1.0))
box.fill.solid()
box.fill.fore_color.rgb = RGBColor(254, 242, 226)
box.line.color.rgb = RGBColor(245, 158, 11)

txBox = slide5.shapes.add_textbox(Inches(0.7), Inches(1.55), Inches(12), Inches(0.8))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Problem: Fraud events are rare (0.1% of transactions). Classical Monte Carlo needs billions of samples."
p.font.size = Pt(15)
p.font.color.rgb = RGBColor(180, 83, 9)

# Formula boxes
add_diagram_box(slide5, Inches(0.5), Inches(2.6), Inches(5.8), Inches(1.8),
    "Classical Monte Carlo",
    ["Samples needed:  O(1/epsilon)",
     "",
     "For epsilon = 1% error:",
     "  -> 10,000 samples needed"],
    GREEN)

add_diagram_box(slide5, Inches(6.9), Inches(2.6), Inches(5.9), Inches(1.8),
    "Quantum Amplitude Estimation",
    ["Operations needed:  O(1/epsilon)",
     "",
     "For epsilon = 1% error:",
     "  -> 100 quantum operations"],
    ACCENT_BLUE)

# Arrow and result
txArrow = slide5.shapes.add_textbox(Inches(6.0), Inches(3.15), Inches(1), Inches(0.5))
tf = txArrow.text_frame
p = tf.paragraphs[0]
p.text = "=>"
p.font.size = Pt(28)
p.font.bold = True
p.font.color.rgb = PURPLE

# Result
box2 = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(4.6), Inches(12.3), Inches(1.5))
box2.fill.solid()
box2.fill.fore_color.rgb = RGBColor(209, 250, 229)
box2.line.color.rgb = GREEN

txBox2 = slide5.shapes.add_textbox(Inches(0.7), Inches(4.8), Inches(12), Inches(1.2))
tf2 = txBox2.text_frame
p = tf2.paragraphs[0]
p.text = "Speedup: 100x"
p.font.size = Pt(28)
p.font.bold = True
p.font.color.rgb = RGBColor(5, 80, 36)

p = tf2.add_paragraph()
p.text = "Quantum Amplitude Estimation (QAE) provides quadratic speedup for rare event probability estimation."
p.font.size = Pt(12)
p.font.color.rgb = DARK_GRAY

p = tf2.add_paragraph()
p.text = "This is ideal for synthetic minority oversampling (SMOTE) and detecting subtle fraud patterns."
p.font.size = Pt(12)
p.font.color.rgb = DARK_GRAY

# ============== SLIDE 6: Fraud Ring Detection ==============
slide6 = prs.slides.add_slide(prs.slide_layouts[6])
add_header(slide6, "Use Case 3: Fraud Ring Detection")

# Problem
txBox = slide6.shapes.add_textbox(Inches(0.5), Inches(1.4), Inches(12.3), Inches(0.5))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Finding connected fraud rings is NP-hard. Classical graph traversal is slow. Quantum graph states explore multiple paths simultaneously!"
p.font.size = Pt(14)
p.font.color.rgb = DARK_GRAY

# Table data
table_data = [
    ["Method", "Time", "Rings Found", "Missed"],
    ["Classical (Apache Spark)", "47 hours", "12,847", "2,341"],
    ["Quantum-Assisted Hybrid", "3 hours", "15,189", "0"]
]

rows, cols = len(table_data), len(table_data[0])
table = slide6.shapes.add_table(rows, cols, Inches(0.5), Inches(2.1), Inches(12.3), Inches(1.5)).table

for i, row_data in enumerate(table_data):
    for j, cell_text in enumerate(row_data):
        cell = table.cell(i, j)
        cell.text = str(cell_text)
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(14)
        if i == 0:
            p.font.bold = True
            p.font.color.rgb = WHITE
            cell.fill.solid()
            cell.fill.fore_color.rgb = ACCENT_BLUE
        elif i == 2:
            p.font.color.rgb = RGBColor(5, 80, 36)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(209, 250, 229)
        else:
            p.font.color.rgb = DARK_GRAY

# Result
box = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(4.0), Inches(12.3), Inches(1.0))
box.fill.solid()
box.fill.fore_color.rgb = RGBColor(209, 250, 229)
box.line.color.rgb = GREEN

txBox = slide6.shapes.add_textbox(Inches(0.7), Inches(4.15), Inches(12), Inches(0.7))
tf = txBox.text_frame
p = tf.paragraphs[0]
p.text = "Result: 15x faster, 18% more fraud rings detected!"
p.font.size = Pt(22)
p.font.bold = True
p.font.color.rgb = RGBColor(5, 80, 36)

# Technical note
txBox2 = slide6.shapes.add_textbox(Inches(0.5), Inches(5.2), Inches(12.3), Inches(0.8))
tf2 = txBox2.text_frame
tf2.word_wrap = True
p = tf2.paragraphs[0]
p.text = "Technical Approach:"
p.font.size = Pt(14)
p.font.bold = True
p.font.color.rgb = DARK_GRAY

p = tf2.add_paragraph()
p.text = "  Max-Cut formulation for fraud ring partitioning using QAOA on quantum graph states"
p.font.size = Pt(12)
p.font.color.rgb = DARK_GRAY

p = tf2.add_paragraph()
p.text = "  Integration with NetworkX (classical) + Qiskit (quantum) for hybrid pipeline"
p.font.size = Pt(12)
p.font.color.rgb = DARK_GRAY

# ============== SLIDE 7: Key Takeaways ==============
slide7 = prs.slides.add_slide(prs.slide_layouts[6])
add_header(slide7, "Key Takeaways", GREEN)

takeaways = [
    ("Classical for Real-Time", "Rule-based scoring, simple patterns, ML inference in < 100ms"),
    ("Quantum for Background", "Weight optimization, rare events, graph analysis - runs async"),
    ("Zero Latency Impact", "Quantum results are cached. Production systems never wait for quantum."),
    ("QAOA for Optimization", "17x faster weight training, escapes local minima"),
    ("QAE for Rare Events", "100x speedup for rare fraud pattern detection"),
    ("Quantum Graph Analysis", "15x faster fraud ring detection, 18% more rings found")
]

for i, (title, desc) in enumerate(takeaways):
    y = Inches(1.5 + i * 0.9)

    # Number circle
    circle = slide7.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.5), y, Inches(0.4), Inches(0.4))
    circle.fill.solid()
    circle.fill.fore_color.rgb = ACCENT_BLUE
    circle.line.fill.background()

    txNum = slide7.shapes.add_textbox(Inches(0.5), y + Inches(0.05), Inches(0.4), Inches(0.35))
    tf = txNum.text_frame
    p = tf.paragraphs[0]
    p.text = str(i + 1)
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = 1

    # Title and description
    txBox = slide7.shapes.add_textbox(Inches(1.1), y, Inches(11.5), Inches(0.8))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = DARK_BLUE

    p = tf.add_paragraph()
    p.text = desc
    p.font.size = Pt(12)
    p.font.color.rgb = DARK_GRAY

# ============== SLIDE 8: Summary ==============
slide8 = prs.slides.add_slide(prs.slide_layouts[6])

# Header
shape = slide8.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(3))
shape.fill.solid()
shape.fill.fore_color.rgb = RGBColor(30, 27, 75)
shape.line.fill.background()

txBox = slide8.shapes.add_textbox(Inches(0.5), Inches(0.8), Inches(12.3), Inches(1))
tf = txBox.text_frame
p = tf.paragraphs[0]
p.text = "The Hybrid Future"
p.font.size = Pt(44)
p.font.bold = True
p.font.color.rgb = WHITE
p.alignment = 1

txBox2 = slide8.shapes.add_textbox(Inches(0.5), Inches(2.0), Inches(12.3), Inches(0.8))
tf2 = txBox2.text_frame
p2 = tf2.paragraphs[0]
p2.text = "Classical + Quantum = Better Together"
p2.font.size = Pt(24)
p2.font.color.rgb = RGBColor(199, 210, 254)
p2.alignment = 1

# Bottom summary boxes
box_data = [
    ("Architecture", "5-Tier Hybrid", ACCENT_BLUE),
    ("Speedup", "15-100x", GREEN),
    ("Accuracy Gain", "+0.8% to +5%", PURPLE)
]

for i, (label, value, color) in enumerate(box_data):
    x = Inches(1.5 + i * 3.5)
    y = Inches(4.0)

    box = slide8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(3), Inches(1.8))
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(245, 247, 250)
    box.line.color.rgb = color

    # Value
    txVal = slide8.shapes.add_textbox(x, y + Inches(0.3), Inches(3), Inches(0.8))
    tf = txVal.text_frame
    p = tf.paragraphs[0]
    p.text = value
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = color
    p.alignment = 1

    # Label
    txLab = slide8.shapes.add_textbox(x, y + Inches(1.1), Inches(3), Inches(0.5))
    tf = txLab.text_frame
    p = tf.paragraphs[0]
    p.text = label
    p.font.size = Pt(14)
    p.font.color.rgb = DARK_GRAY
    p.alignment = 1

# Final message
txBox3 = slide8.shapes.add_textbox(Inches(0.5), Inches(6.2), Inches(12.3), Inches(0.8))
tf3 = txBox3.text_frame
p3 = tf3.paragraphs[0]
p3.text = "Quantum doesn't replace classical computing. It enhances specific hard problems."
p3.font.size = Pt(16)
p3.font.italic = True
p3.font.color.rgb = DARK_GRAY
p3.alignment = 1

# Save
prs.save("d:\\monto carlo vs quantum\\Quantum_Classical_Hybrid_Approach.pptx")
print("Presentation created: Quantum_Classical_Hybrid_Approach.pptx")