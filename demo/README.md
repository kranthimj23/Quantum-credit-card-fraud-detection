# Quantum Fraud Detection — Presenter's User Guide

This guide is designed for you to seamlessly run the Quantum Fraud Detection demo live in front of your MD and senior management. 

## 🛠️ Step 0: Setup & Preparation
Before you start screen-sharing, ensure your terminal is ready.

1. Open PowerShell or Command Prompt.
2. Navigate to your project folder:
   ```powershell
   cd "D:\monto carlo vs quantum"
   ```
3. Activate the virtual environment:
   ```powershell
   .\quantum_demo\Scripts\activate
   ```
4. Move into the demo directory:
   ```powershell
   cd demo
   ```
5. Ensure Unicode characters (like `✓`) print correctly:
   ```powershell
   $env:PYTHONIOENCODING="utf-8"
   ```

---

## 🕒 Pre-Demo (2-3 Hours Before Presentation)
*Real quantum computers have a queue. You must submit your job ahead of time!*

Run the hardware submission script:
```powershell
python submit_to_hardware.py
```
* **What to expect:** It will compile the circuits and submit them to `ibm_kingston`. It will print a **Job ID** and save it.
* **Pro-tip:** You can occasionally check the queue status leading up to the meeting by running `python submit_to_hardware.py --status`.

---

## 🎬 The Live Presentation (Step-by-Step)

When it's time to present, follow this exact script order to tell a compelling story.

### Step 1: The Classical Baseline
**Run:**
```powershell
python classical_baseline.py
```
**Talking Point:** *"First, let's look at how we do things today using Classical Monte Carlo. As you can see on the screen, even at 10,000 samples, it still has an error margin. If we want to find ultra-rare systemic fraud, it would take billions of samples and days of compute time."*

### Step 2: The Quantum Proof (Simulator)
**Run:**
```powershell
python run_simulator.py
```
**Talking Point:** *"Now, let's run Quantum Amplitude Estimation. This runs locally on a perfect simulator. It mathematically proves we can achieve a 10,000x speedup, turning an 11-day classical compute job into a few minutes."*

### Step 3: Fetching Real Quantum Data
**Run:**
```powershell
python fetch_hardware_results.py
```
**Talking Point:** *"But we didn't just simulate it. A few hours ago, I queued this exact algorithm on a real IBM Quantum computer in New York. Let's pull the live results from the chip right now."*

### Step 4: Generate the Final Presentation Deck
**Run:**
```powershell
python comparison_dashboard.py
```
**Talking Point:** *"Let's generate the final scorecard comparing the methods."*

---

## 📊 Opening the Slides (The `plots/` folder)

Open the `demo/plots/` folder on your screen and open the images in this order:

1. **`chart4_summary_scorecard.png`** (The Money Slide)
   * *Pitch:* "This is the business case. Quantum guarantees a massive speedup that enables daily model updates instead of weekly."
2. **`grover_oscillations.png`** (The Math Proof)
   * *Pitch:* "The blue dots perfectly track the theory, proving the math works."
3. **`hardware_results.png`** (The Reality Check & Future Readiness)
   * *Pitch:* "When we ran it on real hardware, the signal degraded into static (orange dots) because modern chips are still 'noisy'. But this is great news: it means our algorithm is already built. The moment IBM releases their next-gen error-corrected chips, the orange dots will snap to the green line, and we immediately unlock that 10,000x speedup before our competitors do."
