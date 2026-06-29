from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import re

# Create presentation
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Color scheme
DARK_BLUE = RGBColor(0, 51, 102)
ACCENT_BLUE = RGBColor(0, 112, 192)
LIGHT_BLUE = RGBColor(217, 226, 243)
DARK_GRAY = RGBColor(64, 64, 64)
WHITE = RGBColor(255, 255, 255)
GREEN = RGBColor(0, 128, 0)
ORANGE = RGBColor(255, 102, 0)

def add_title_slide(prs, title, subtitle=""):
    slide_layout = prs.slide_layouts[6]  # Blank
    slide = prs.slides.add_slide(slide_layout)

    # Blue header bar
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(3.2))
    shape.fill.solid()
    shape.fill.fore_color.rgb = DARK_BLUE
    shape.line.fill.background()

    # Title
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(1.0), Inches(12.3), Inches(1.5))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = WHITE

    # Subtitle
    if subtitle:
        txBox2 = slide.shapes.add_textbox(Inches(0.5), Inches(2.5), Inches(12.3), Inches(0.8))
        tf2 = txBox2.text_frame
        p2 = tf2.paragraphs[0]
        p2.text = subtitle
        p2.font.size = Pt(24)
        p2.font.color.rgb = WHITE

    return slide

def add_content_slide(prs, title, bullets=None, tables=None, highlights=None):
    slide_layout = prs.slide_layouts[6]  # Blank
    slide = prs.slides.add_slide(slide_layout)

    # Header bar
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.2))
    shape.fill.solid()
    shape.fill.fore_color.rgb = DARK_BLUE
    shape.line.fill.background()

    # Title
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.8))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = WHITE

    y_pos = Inches(1.5)

    # Highlights (big numbers)
    if highlights:
        for i, h in enumerate(highlights):
            txBox = slide.shapes.add_textbox(Inches(0.5 + (i % 3) * 4), y_pos if i < 3 else y_pos + Inches(0.8), Inches(3.8), Inches(0.7))
            tf = txBox.text_frame
            p = tf.paragraphs[0]
            p.text = h
            p.font.size = Pt(20)
            p.font.bold = True
            p.font.color.rgb = ACCENT_BLUE
            p.alignment = PP_ALIGN.CENTER

    # Bullet points
    if bullets:
        txBox = slide.shapes.add_textbox(Inches(0.5), y_pos, Inches(12.3), Inches(5.5))
        tf = txBox.text_frame
        tf.word_wrap = True

        for i, bullet in enumerate(bullets):
            if i == 0:
                p = tf.paragraphs[0]
            else:
                p = tf.add_paragraph()
            p.text = bullet
            p.font.size = Pt(20)
            p.font.color.rgb = DARK_GRAY
            p.level = 0

    # Tables
    if tables:
        for table_data in tables:
            rows, cols = len(table_data), len(table_data[0])
            table = slide.shapes.add_table(rows, cols, Inches(0.5), y_pos, Inches(12.3), Inches(0.5 * rows)).table

            for i, row_data in enumerate(table_data):
                for j, cell_text in enumerate(row_data):
                    cell = table.cell(i, j)
                    cell.text = str(cell_text)
                    cell.text_frame.paragraphs[0].font.size = Pt(14)
                    cell.text_frame.paragraphs[0].font.color.rgb = DARK_GRAY
                    if i == 0:
                        cell.text_frame.paragraphs[0].font.bold = True
                        cell.text_frame.paragraphs[0].font.color.rgb = WHITE
                        cell.fill.solid()
                        cell.fill.fore_color.rgb = ACCENT_BLUE

    return slide

def add_table_slide(prs, title, table_data, col_widths=None):
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)

    # Header
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.2))
    shape.fill.solid()
    shape.fill.fore_color.rgb = DARK_BLUE
    shape.line.fill.background()

    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.8))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = WHITE

    rows, cols = len(table_data), len(table_data[0])
    table_width = Inches(12.3)
    table = slide.shapes.add_table(rows, cols, Inches(0.5), Inches(1.5), table_width, Inches(0.5 * rows)).table

    for i, row_data in enumerate(table_data):
        for j, cell_text in enumerate(row_data):
            cell = table.cell(i, j)
            cell.text = str(cell_text)
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(16)
            p.font.color.rgb = DARK_GRAY
            if i == 0:
                p.font.bold = True
                p.font.color.rgb = WHITE
                cell.fill.solid()
                cell.fill.fore_color.rgb = ACCENT_BLUE

    return slide

def add_diagram_slide(prs, title, content_lines):
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)

    # Header
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.2))
    shape.fill.solid()
    shape.fill.fore_color.rgb = DARK_BLUE
    shape.line.fill.background()

    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.8))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = WHITE

    # Diagram content
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(12.3), Inches(5.5))
    tf = txBox.text_frame
    tf.word_wrap = True

    for i, line in enumerate(content_lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = line
        p.font.size = Pt(18)
        p.font.name = "Courier New"
        p.font.color.rgb = DARK_GRAY

    return slide

def add_ask_slide(prs, title, main_point, bullets):
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)

    # Header
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.2))
    shape.fill.solid()
    shape.fill.fore_color.rgb = GREEN
    shape.line.fill.background()

    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.8))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = WHITE

    # Main point box
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1), Inches(1.8), Inches(11.3), Inches(1.2))
    box.fill.solid()
    box.fill.fore_color.rgb = LIGHT_BLUE
    box.line.color.rgb = ACCENT_BLUE

    txBox = slide.shapes.add_textbox(Inches(1.2), Inches(2.0), Inches(11), Inches(0.8))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = main_point
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = DARK_BLUE
    p.alignment = PP_ALIGN.CENTER

    # Summary bullets
    txBox = slide.shapes.add_textbox(Inches(1), Inches(3.5), Inches(11.3), Inches(3.5))
    tf = txBox.text_frame
    tf.word_wrap = True

    for i, bullet in enumerate(bullets):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = "✓ " + bullet
        p.font.size = Pt(22)
        p.font.color.rgb = DARK_GRAY
        p.space_before = Pt(10)

    return slide

# ============================================================
# CREATE SLIDES
# ============================================================

# Slide 1: Title
add_title_slide(prs, "Quantum-Enhanced Fraud Detection", "Investment Proposal | May 2026")

# Slide 2: The Opportunity
add_content_slide(prs, "The Opportunity", highlights=[
    "Fraud Detection +20%",
    "False Positives -40%",
    "ROI +271%"
])

# Slide 3: Investment Overview
add_table_slide(prs, "Investment Overview", [
    ["Metric", "Value"],
    ["Investment (Year 1)", "₹3.5 Crore"],
    ["Expected Annual Benefit", "₹13 Crore"],
    ["Net ROI", "+271%"],
    ["Payback Period", "4 months"],
    ["3-Year NPV", "₹28+ Crore"]
])

# Slide 4: What We Build
add_table_slide(prs, "5-Tier Fraud Detection Architecture", [
    ["Tier", "Component", "Latency", "Accuracy Gain"],
    ["1", "50 real-time rules", "< 50ms", "Baseline"],
    ["2", "200 ML features (XGBoost)", "< 100ms", "+8%"],
    ["3", "Quantum weight optimization", "Batch", "+5%"],
    ["4", "Quantum Monte Carlo", "Batch", "+2%"],
    ["5", "Quantum graph analysis", "Batch", "+5%"]
])

# Slide 5: How It Works
add_diagram_slide(prs, "How It Works", [
    "    TRANSACTION",
    "        │",
    "        ▼",
    "┌─────────────────────────────────────┐",
    "│  CLASSICAL LAYER (Real-time)       │",
    "│  • 50 rules (< 50ms)               │",
    "│  • ML scoring (< 100ms)            │",
    "└─────────────┬───────────────────────┘",
    "              │  Uncertain cases",
    "              ▼",
    "┌─────────────────────────────────────┐",
    "│  QUANTUM LAYER (Background)         │",
    "│  • Weight optimization              │",
    "│  • Rare event simulation            │",
    "│  • Fraud ring detection            │",
    "│  (Zero latency impact)             │",
    "└─────────────────────────────────────┘"
])

# Slide 6: Cost Breakdown
add_table_slide(prs, "Cost Breakdown", [
    ["Category", "Item", "Cost"],
    ["CapEx", "Data engineering & pipeline", "₹20L"],
    ["CapEx", "ML models & integration", "₹35L"],
    ["CapEx", "Quantum bridge development", "₹25L"],
    ["CapEx", "Hybrid pipeline", "₹40L"],
    ["CapEx", "Training & certifications", "₹15L"],
    ["CapEx", "Contingency (15%)", "₹22L"],
    ["", "Total CapEx", "₹1.57 Cr"],
    ["OpEx (Monthly)", "Cloud compute", "₹8L"],
    ["OpEx (Monthly)", "Quantum API access", "₹15L"],
    ["OpEx (Monthly)", "Quantum specialist", "₹5L"],
    ["", "Total OpEx (Year 1)", "₹3.06 Cr"],
    ["", "TOTAL YEAR 1", "₹3.5 Crore"]
])

# Slide 7: ROI Breakdown
add_table_slide(prs, "ROI Breakdown", [
    ["Benefit Category", "Calculation", "Value"],
    ["Fraud detected (+15%)", "15% × ₹40Cr existing prevention", "+₹6Cr"],
    ["False positive reduction (-40%)", "Fewer wrongly blocked customers", "+₹5Cr"],
    ["Operational savings", "20% less manual review", "+₹1.5Cr"],
    ["Regulatory compliance", "Reduced chargebacks", "+₹0.5Cr"],
    ["", "TOTAL ANNUAL BENEFIT", "₹13 Crore"]
])

# Slide 8: Implementation Timeline
add_diagram_slide(prs, "Implementation Timeline", [
    "Month:       1      2      3      4      5      6",
    "             │      │      │      │      │      │",
    "Phase 1      ████████████████████████",
    "             Rules    ML      Complete",
    "             Setup    Model",
    "",
    "Phase 2                       ████████████████████",
    "                              Quantum   Bridge    Production",
    "                              Setup     Dev       Rollout",
    "",
    "Milestones:    Month 3: Foundation Ready",
    "               Month 4: Quantum Ready",
    "               Month 6: Full Hybrid Live"
])

# Slide 9: Risk Mitigation
add_table_slide(prs, "Risk Mitigation", [
    ["Risk", "Likelihood", "Mitigation"],
    ["Quantum HW unavailable", "Low", "Falls back to classical-only mode"],
    ["Integration complexity", "Medium", "Phased rollout with rollback"],
    ["Team upskilling", "Medium", "External consultants + certifications"],
    ["Provider downtime", "Low", "Multi-provider redundancy"]
])

# Slide 10: Why Quantum Now
add_table_slide(prs, "Why Quantum Now?", [
    ["Capability", "Classical Only", "Hybrid Approach"],
    ["Fraud detection accuracy", "Baseline", "+20% improvement"],
    ["False positive rate", "Baseline", "-40% reduction"],
    ["Model update frequency", "Weekly", "Daily"],
    ["Rare event detection", "Poor", "Excellent"],
    ["Competitive edge", "None", "First-mover in sector"]
])

# Slide 11: Recommended Approach
add_content_slide(prs, "Recommended Approach", bullets=[
    "Phase 1: Approve ₹1.5 Crore (Now)",
    "    • Build classical foundation (Tier 1-2)",
    "    • Select quantum provider (IBM/AWS/Azure)",
    "    • Design hybrid architecture",
    "    • Validated baseline at Month 3",
    "",
    "Phase 2: Month 4 Decision (₹2 Crore)",
    "    • Full quantum integration",
    "    • Production rollout",
    "    • Conditional on Phase 1 validation"
])

# Slide 12: Next Steps
add_content_slide(prs, "Next Steps", bullets=[
    "Week 1-2:   Sign quantum provider contracts",
    "Week 2-4:   Assign quantum-specialized data scientist",
    "Week 4-8:   Build classical foundation (Tier 1-2)",
    "Week 8-12:  Develop quantum integration",
    "Month 4:    Phase 1 validation & Phase 2 approval",
    "Month 6:    Full hybrid system live in production"
])

# Slide 13: The Ask
add_ask_slide(prs, "Our Ask",
    "Approve Phase 1: ₹1.5 Crore",
    [
        "₹3.5 Crore total investment | ₹13 Crore annual benefit",
        "+271% ROI with 4-month payback period",
        "Low risk with phased approach — quantum runs in background",
        "First-mover competitive advantage in our sector"
    ]
)

# Slide 14: Contact
add_title_slide(prs, "Questions?", "Contact your Data Science Team | May 2026")

# Save
prs.save("d:\\monto carlo vs quantum\\Quantum_Fraud_Detection_Proposal.pptx")
print("PowerPoint created: Quantum_Fraud_Detection_Proposal.pptx")
