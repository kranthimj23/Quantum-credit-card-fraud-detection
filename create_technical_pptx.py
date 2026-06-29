from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
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

def add_header(slide, title):
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

def add_content_box(slide, x, y, w, h, title, content, header_color=ACCENT_BLUE):
    # Box
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(245, 247, 250)
    box.line.color.rgb = ACCENT_BLUE

    # Header
    hdr = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, Inches(0.4))
    hdr.fill.solid()
    hdr.fill.fore_color.rgb = header_color
    hdr.line.fill.background()

    txTitle = slide.shapes.add_textbox(x + Inches(0.1), y + Inches(0.05), w - Inches(0.2), Inches(0.35))
    tf = txTitle.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = WHITE

    txBox = slide.shapes.add_textbox(x + Inches(0.15), y + Inches(0.5), w - Inches(0.3), h - Inches(0.6))
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, line in enumerate(content):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = line
        p.font.size = Pt(12)
        p.font.color.rgb = DARK_GRAY
        p.space_after = Pt(4)

# ============== SLIDE 1: Architecture Overview ==============
slide1 = prs.slides.add_slide(prs.slide_layouts[6])
add_header(slide1, "Hybrid Quantum-Classical Architecture")

# Three tier boxes
add_content_box(slide1, Inches(0.4), Inches(1.5), Inches(4), Inches(2.5),
    "TIER 1: Real-Time Rules Engine",
    ["• 50 deterministic rules for instant decisions",
     "• Latency: < 50ms",
     "• Pattern matching & blacklist checks",
     "• Auto-block high-confidence fraud",
     "• Rules stored in Redis for sub-ms access",
     "• Example: Velocity limits, geo-anomalies",
     "• Updates via API without system restart"])

add_content_box(slide1, Inches(4.6), Inches(1.5), Inches(4), Inches(2.5),
    "TIER 2: ML Scoring (XGBoost)",
    ["• 200 engineered features per transaction",
     "• Latency: < 100ms",
     "• Real-time feature computation pipeline",
     "• Features: RFM, device fingerprint,",
     "  network graph metrics, behavioral",
     "• Online learning with drift detection",
     "• Probability score: 0-1 threshold"])

add_content_box(slide1, Inches(8.8), Inches(1.5), Inches(4), Inches(2.5),
    "TIER 3-5: Quantum Enhancement",
    ["• Quantum Approximate Optimization (QAOA)",
     "• Variational Quantum Eigensolver (VQE)",
     "• Quantum Monte Carlo for rare events",
     "• Graph analysis via quantum circuits",
     "• Hybrid jobs via AWS Braket / IBM Q",
     "• Results cached for production use"])

# Bottom flow diagram
flow_box = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(4.3), Inches(12.5), Inches(2.5))
flow_box.fill.solid()
flow_box.fill.fore_color.rgb = LIGHT_BLUE
flow_box.line.fill.background()

txBox = slide1.shapes.add_textbox(Inches(0.6), Inches(4.5), Inches(12), Inches(2.2))
tf = txBox.text_frame
tf.word_wrap = True

lines = [
    "TRANSACTION FLOW:",
    "  Transaction → [TIER 1: Rules] ──ALLOW/BLOCK──→ Immediate Decision",
    "              └───ESCALATE──→ [TIER 2: XGBoost ML] ──Score < threshold──→ Manual Review",
    "                                          └───Score > threshold──→ [TIER 3-5: Quantum Batch] ──Optimized Weights→",
    "",
    "KEY: Quantum layer runs asynchronously in background. ML model weights are updated nightly via quantum optimization.",
    "     Production latency is NEVER affected by quantum computation."
]
for i, line in enumerate(lines):
    if i == 0:
        p = tf.paragraphs[0]
    else:
        p = tf.add_paragraph()
    p.text = line
    p.font.size = Pt(13)
    p.font.color.rgb = DARK_BLUE
    if i == 0:
        p.font.bold = True

# ============== SLIDE 2: Technical Deep Dive ==============
slide2 = prs.slides.add_slide(prs.slide_layouts[6])
add_header(slide2, "Technical Deep Dive")

# Left column
add_content_box(slide2, Inches(0.4), Inches(1.4), Inches(6.2), Inches(2.8),
    "Quantum Weight Optimization (QAOA)",
    ["• Problem: Optimizing 200+ feature weights for fraud detection",
     "• Classical: Gradient descent, 4+ hours per full training cycle",
     "• Quantum: QAOA on 127-qubit IBM Quantum processor",
     "• Hybrid classical-quantum variational ansatz",
     "• Result: Optimal weights in ~15 minutes",
     "• 20% improvement in fraud vs false-positive tradeoff",
     "• Batch job: Runs nightly during low-traffic window"])

add_content_box(slide2, Inches(0.4), Inches(4.4), Inches(6.2), Inches(2.8),
    "Quantum Monte Carlo (Rare Event Simulation)",
    ["• Problem: Detecting rare fraud patterns (< 0.1% of transactions)",
     "• Classical: Requires billions of samples (computationally expensive)",
     "• Quantum: Amplitude estimation for rare event probability",
     "• QAE (Quantum Amplitude Estimation) algorithm",
     "• Detects subtle fraud rings & coordinated attacks",
     "• 2% additional fraud detection accuracy",
     "• Ideal for synthetic minority oversampling"])

# Right column
add_content_box(slide2, Inches(6.8), Inches(1.4), Inches(6.2), Inches(2.8),
    "Quantum Graph Analysis (Fraud Rings)",
    ["• Problem: Detecting fraud rings (graph of connected accounts)",
     "• Classical: Graph traversal is exponential in worst case",
     "• Quantum: QAOA for minimum cut / community detection",
     "• Max-Cut formulation for fraud ring partitioning",
     "• 15x speedup on large graphs (10K+ nodes)",
     "• 5% additional accuracy on organized fraud",
     "• Integration: NetworkX + Qiskit optimization"])

add_content_box(slide2, Inches(6.8), Inches(4.4), Inches(6.2), Inches(2.8),
    "Feature Engineering Pipeline",
    ["• Real-time features (< 100ms):",
     "  - Transaction amount, frequency, time delta",
     "  - Device ID, IP geolocation, proxy detection",
     "  - Account age, transaction history stats",
     "• Batch features (nightly):",
     "  - 30/60/90-day rolling statistics",
     "  - Network graph centrality metrics",
     "  - Peer group behavioral profiles",
     "• Feature store: Redis + Apache Kafka"])

# ============== SLIDE 3: Integration Architecture ==============
slide3 = prs.slides.add_slide(prs.slide_layouts[6])
add_header(slide3, "System Integration & Technical Stack")

# System components
add_content_box(slide3, Inches(0.4), Inches(1.4), Inches(4), Inches(2.0),
    "Data Ingestion",
    ["• Apache Kafka: Real-time transaction stream",
     "• Debezium CDC for database changes",
     "• Apache Flink for stream processing",
     "• Rate: 10,000+ TPS"])

add_content_box(slide3, Inches(4.6), Inches(1.4), Inches(4), Inches(2.0),
    "ML Platform",
    ["• MLflow for experiment tracking",
     "• Seldon for model serving",
     "• XGBoost + LightGBM models",
     "• A/B testing framework"])

add_content_box(slide3, Inches(8.8), Inches(1.4), Inches(4), Inches(2.0),
    "Quantum Backend",
    ["• AWS Braket (Rigetti, IonQ)",
     "• IBM Quantum (127-qubit systems)",
     "• Azure Quantum (Quantinuum)",
     "• Qiskit + PennyLane SDKs"])

# Middle row
add_content_box(slide3, Inches(0.4), Inches(3.6), Inches(4), Inches(2.0),
    "Classical Compute",
    ["• Kubernetes on AWS EKS",
     "• Auto-scaling: 4-32 nodes",
     "• Redis cluster for caching",
     "• PostgreSQL + TimescaleDB"])

add_content_box(slide3, Inches(4.6), Inches(3.6), Inches(4), Inches(2.0),
    "API Gateway",
    ["• REST + gRPC endpoints",
     "• < 50ms p99 latency SLA",
     "• Circuit breakers (Hystrix)",
     "• Rate limiting & auth (OAuth2)"])

add_content_box(slide3, Inches(8.8), Inches(3.6), Inches(4), Inches(2.0),
    "Monitoring",
    ["• Prometheus + Grafana",
     "• Fraud model drift alerts",
     "• Quantum job success rates",
     "• Business KPIs dashboard"])

# Bottom: key differentiators
box = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(5.8), Inches(12.5), Inches(1.4))
box.fill.solid()
box.fill.fore_color.rgb = GREEN

txBox = slide3.shapes.add_textbox(Inches(0.6), Inches(5.9), Inches(12), Inches(1.2))
tf = txBox.text_frame
tf.word_wrap = True

diff_lines = [
    "KEY DIFFERENTIATORS:  Zero production latency impact (quantum runs async)  |  Hybrid classical-quantum (not all-or-nothing)  |  Multi-provider redundancy  |  Continuous model improvement via quantum optimization"
]
for i, line in enumerate(diff_lines):
    if i == 0:
        p = tf.paragraphs[0]
    else:
        p = tf.add_paragraph()
    p.text = line
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = WHITE

prs.save("d:\\monto carlo vs quantum\\Quantum_Fraud_Technical_Deep_Dive.pptx")
print("Technical presentation created: Quantum_Fraud_Technical_Deep_Dive.pptx")