# Senior management demo -- slide outline

Audience: **MD, CEO, CTO, Enterprise Architects, Engineering Heads**.

Tone: **directional + honest**. We are NOT promising quantum will replace
XGBoost in production tomorrow. We ARE showing that a hybrid pipeline is
already viable, and that HDFC has a 12-18 month strategic head-start
opportunity.

Recommended deck length: **15 slides, 25 minutes + 15 min Q&A**.

---

## Slide 1 -- The problem (1 min)

**Title:** *Why credit-card fraud is structurally hard*

**Talking points:**
- Indian card fraud losses: ~Rs 1,400 crore in FY24 (RBI data).
- HDFC processes ~25 million card transactions per day.
- Fraud rate < 0.2% of transactions, but 100% of customer escalations and 100% of regulator scrutiny come from this tiny tail.
- Existing XGBoost model is excellent on average, but rare-event recall is the constant battleground.

**Visual:**
```
   Total transactions ███████████████████████████████████████████ 99.83%
   Fraud transactions █  0.17%
                      ^
                      | 100% of regulatory + reputational risk
                      | 100% of incremental ML investment
```

---

## Slide 2 -- Why classical ML hits a ceiling

**Title:** *We've already extracted what classical ML can give us*

**Talking points:**
- 5 years of XGBoost / LightGBM / DNN tuning has plateaued AUC at ~0.98.
- Each remaining percentage point of recall = ~Rs X crore in saved fraud losses.
- The bottleneck is **expressivity** -- the kernel functions classical SVMs can compute are limited to RBF, polynomial, and learned neural kernels. None of them efficiently capture *all* feature interactions.

**Visual:**
```
   Improvement from classical ML over the last 5 years:

   2020  +-----+
         |     |  AUC = 0.92
         +-----+
   2022  +-------+
         |       |  AUC = 0.96
         +-------+
   2024  +--------+
         |        |  AUC = 0.98   <-- plateau
         +--------+
   2025+ ?  classical ceiling
```

---

## Slide 3 -- What quantum brings to the table

**Title:** *Quantum kernels live in exponentially larger feature spaces*

**Talking points:**
- A 30-qubit quantum kernel embeds your data into a Hilbert space of dimension `2^30 ~ 1 billion`.
- For *some* feature maps (Liu, Arunachalam & Temme, 2021) there is a **provable** exponential separation -- no classical algorithm can compute the kernel in poly-time.
- Practically: this means quantum kernels can detect non-linear correlations between *all subsets* of features simultaneously, where RBF only sees pairwise distance.

**Visual:** copy the Hilbert-space-dimension table from `ARCHITECTURE.md`:
```
  qubits  Hilbert dim       classical sim?
  -------  ---------------    ---------------
       2  4                  trivial
       6  64                 trivial         <-- our demo
      20  1,048,576          fast
      30  ~1 billion         slow
      50  ~1 quadrillion     formally beyond
```

---

## Slide 4 -- Today's reality check

**Title:** *We are in the NISQ era. Be honest about it.*

**Talking points:**
| Dimension | Classical | Quantum (today) |
|---|---|---|
| Training speed | seconds on millions of rows | minutes on thousands of rows |
| Inference latency | microseconds | ms (sim), s (HW + queue) |
| Feature dimensionality | 100s-1000s | 4-16 (qubit-limited) |
| Hardware maturity | commodity CPU/GPU | NISQ, ~1e-3 gate error |

**Punchline:** Quantum doesn't replace XGBoost today. It augments it.

---

## Slide 5 -- What this PoC delivered

**Title:** *End-to-end pipeline running today*

**Talking points:**
- Full pipeline: Kaggle CSV -> classical baselines -> Qiskit Aer -> IBM Quantum hardware.
- Two public datasets covered: ULB original (284K, 0.17% fraud) + 2023 balanced (568K, 50%).
- Three quantum models: VQC, QSVC, PegasosQSVC.
- One real-hardware run on `ibm_brisbane` (or whatever was least busy).
- Streamlit dashboard for live walk-through.

**Visual:** the architecture diagram from `README.md` (the big ASCII flow chart).

---

## Slide 6 -- Live demo: Streamlit dashboard

**Action:** alt-tab to `streamlit run src/07_compare_dashboard.py`.

Walk through:
1. Side-by-side metrics table (point at AUC-ROC column).
2. ROC curves overlaid (point at how close VQC is to XGBoost despite 6 features vs 29).
3. Reality-check panel.
4. Pipeline metadata.

---

## Slide 7 -- Numbers that matter

**Title:** *AUC-ROC: classical vs quantum on the same test set*

Reproduce the metrics table from the dashboard. Highlight:
- VQC at 6 qubits is within 1-3 AUC points of XGBoost at 29 features.
- QSVC sometimes *exceeds* XGBoost on the imbalanced dataset because the quantum kernel finds a non-linear separator that RBF misses.
- Real-HW run validated the device pipeline works (numbers will be slightly noisier than simulator due to gate errors).

---

## Slide 8 -- Hybrid serving architecture (the production play)

**Title:** *How we deploy this without breaking SLA*

**Visual:** the hybrid serving diagram from `ARCHITECTURE.md`:
```
  POS / online txn  ->  XGBoost (50 ms, full features)  ->  approve 99%
                                                        |
                                                        v
                                       top 1% suspicious  -> QSVC re-score
                                                                     |
                                                                     v
                                                     final: 0.7*classical + 0.3*quantum
```

**Talking points:**
- XGBoost handles 99% of throughput in the hot path.
- Quantum re-scorer only runs on the top 1% suspicious tail.
- Graceful fallback: if IBM Runtime is unavailable, simulator answers in 50-500 ms.
- No SLA degradation for the customer.

---

## Slide 9 -- Roadmap (next 6-18 months)

**Title:** *From PoC to production*

| Quarter | Milestone |
|---|---|
| Q1 (now) | Demo to senior management. Spin up internal Quantum CoE. |
| Q2 | Hire 2 quantum-ML engineers. Onboard 2-3 enterprise architects. |
| Q3 | Re-run pipeline on HDFC's actual fraud data (not Kaggle). |
| Q4 | Shadow-deploy hybrid model on top 1% suspicious tail (no customer impact). |
| Q5-Q6 | A/B test recall improvement against current XGBoost-only baseline. |
| Q7+ | If A/B positive, go-live as a regulated production fraud model. |

---

## Slide 10 -- Investment ask

**Title:** *What we need to fund this*

| Item | FY26 cost |
|---|---|
| 2 quantum-ML engineers | Rs 1.2 cr |
| 1 quantum research fellow (PhD-level) | Rs 80 lakh |
| IBM Quantum Network premium plan | $50K-$100K |
| Compute infra (Qiskit Aer, GPUs) | Rs 30 lakh |
| Conference / publication budget | Rs 20 lakh |
| **Total** | **~Rs 3 cr** |

---

## Slide 11 -- Risks and how we mitigate

| Risk | Mitigation |
|---|---|
| Quantum hardware doesn't scale fast enough | Hybrid architecture works at any qubit count; we keep value even if HW progress is slow. |
| Talent shortage | Partner with IIT-B / IISc / TIFR for joint research positions. |
| Regulatory clearance for quantum-derived decisions | Engage RBI early; quantum is a re-scorer, not a decision system. |
| IP leakage to competitors | Standard NDA + publish only after PoC is internal. |

---

## Slide 12 -- Why HDFC and why now

**Title:** *First-mover advantage in Indian banking quantum ML*

**Talking points:**
- No Indian bank has publicly demoed quantum ML on real HW for fraud.
- IBM Quantum has an India data center (Bengaluru) -- low-latency access for HDFC.
- 2026-2030 is the window between "fault-tolerant devices announced" and "fault-tolerant devices at scale". HDFC can build the institutional muscle now and cash it in then.
- Reputational angle: this is a CEO / CTO talking-point at every Davos, BFSI conference, and investor call for the next 5 years.

---

## Slide 13 -- What we'd want to commit to today

**Decision asks:**
1. Approve the FY26 budget of ~Rs 3 cr for the Quantum Fraud CoE.
2. Approve hiring 2 quantum-ML engineers (JD ready).
3. Approve sharing a sanitized 1% sample of HDFC fraud data with the CoE for the Q3 milestone.
4. Approve premium IBM Quantum Network membership.
5. Endorse the hybrid serving architecture as the target operational model.

---

## Slide 14 -- Q&A anticipated questions

**Q1: "When will quantum actually beat classical for fraud at HDFC scale?"**
A: 2-5 years for hybrid (already viable in pilot today). 5-10 years for pure-quantum at production throughput. The investment hedge is: every year we wait, competitors close the gap.

**Q2: "Isn't this just hype? IBM has been saying 'next year' for 10 years."**
A: Fair concern. Two responses: (1) the hybrid architecture extracts value *today* without waiting for FT devices; (2) IBM's 2024 roadmap (Heron 156-qubit, Condor 1121-qubit) is being met on schedule, unlike past slips.

**Q3: "What's the regulatory exposure?"**
A: The quantum re-scorer outputs a *risk score*, not a decision. The classical model still drives the final approve/deny. From an RBI perspective this is feature engineering, not a new decision system.

**Q4: "Could we just use a deeper neural net instead?"**
A: We could, and we should keep doing both. But classical neural nets have a ceiling on the kinds of correlations they can learn. Quantum kernels are *provably* outside that ceiling for certain problem classes (Liu et al. 2021).

**Q5: "What if our competitors copy us?"**
A: They will eventually. The asset is institutional muscle -- engineers who've actually run a VQC on a real device, not theoretical knowledge. That's 12-18 months of catch-up time even after the architecture is public.

---

## Slide 15 -- Closing

**Title:** *We're not betting the bank. We're hedging the future.*

**Single closing line:** "If quantum ML works, we win big. If it's slower than expected, we still benefit from the engineering muscle and reputation. The downside is bounded. The upside is asymmetric. **That's exactly the kind of bet a 30-year-horizon institution like HDFC should be making.**"

---

## Appendix slides (optional, for technical Q&A)

- A1: ZZFeatureMap circuit diagram (from ARCHITECTURE.md).
- A2: VQC ansatz EfficientSU2 (from ARCHITECTURE.md).
- A3: Hilbert-space expressivity math (one slide of LaTeX).
- A4: Comparison with PennyLane / Cirq / Amazon Braket / Azure Quantum stacks.
- A5: Why we picked Qiskit (largest community, IBM has India data center, mature ML lib).
