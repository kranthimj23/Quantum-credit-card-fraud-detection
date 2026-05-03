/* Self-check quiz with instant feedback. State persisted in localStorage. */
(function () {
  const form = document.getElementById("quiz-form");
  if (!form) return;
  const scoreBtn = document.getElementById("quiz-score");
  const resetBtn = document.getElementById("quiz-reset");
  const result = document.getElementById("quiz-result");

  const QUESTIONS = [
    {
      q: "What does a single qubit's state |&psi;&rang; = &alpha;|0&rang; + &beta;|1&rang; represent?",
      a: [
        "The qubit is simultaneously a 0 and a 1 in the classical sense.",
        "Probability amplitudes for measuring 0 or 1; |&alpha;|<sup>2</sup> + |&beta;|<sup>2</sup> = 1.",
        "An average of past measurement results.",
        "A noisy classical bit.",
      ],
      correct: 1,
      why: "The amplitudes are complex numbers; their squared magnitudes give the measurement probabilities and must sum to 1.",
    },
    {
      q: "Why do we apply PCA before the quantum encoder?",
      a: [
        "Because PCA always improves accuracy.",
        "To bring the feature count down to a number of qubits we can run reliably (typically 4&ndash;8 today).",
        "To make the data classical.",
        "Because Qiskit requires it.",
      ],
      correct: 1,
      why: "Today's quantum hardware can only entangle a small number of qubits cleanly. PCA picks the top-k informative axes so we keep the most signal in <em>k</em> qubits.",
    },
    {
      q: "What is the role of the ZZFeatureMap?",
      a: [
        "To train the model.",
        "To deterministically encode classical data into a quantum state |&phi;(x)&rang;.",
        "To measure the qubits.",
        "To denoise the hardware.",
      ],
      correct: 1,
      why: "ZZFeatureMap U_&phi;(x) is the data encoder. It has no trainable parameters; it just maps numbers to a quantum state.",
    },
    {
      q: "What is the difference between EfficientSU2 and ZZFeatureMap?",
      a: [
        "Both are training algorithms.",
        "EfficientSU2 is the trainable ansatz with parameters &theta;; ZZFeatureMap is a fixed data encoder.",
        "EfficientSU2 runs only on real hardware.",
        "There is no difference.",
      ],
      correct: 1,
      why: "Both are circuits. The ZZFeatureMap consumes the data x; the EfficientSU2 ansatz has trainable parameters &theta; that the optimiser updates.",
    },
    {
      q: "Why do we use SPSA instead of standard gradient descent on real hardware?",
      a: [
        "SPSA is exact while gradient descent is approximate.",
        "SPSA estimates the full gradient with only 2 circuit evaluations regardless of the number of parameters.",
        "SPSA does not need a loss function.",
        "SPSA produces deterministic results.",
      ],
      correct: 1,
      why: "On hardware, every circuit run costs queue time and money. SPSA's two-call cost vs. the parameter-shift rule's 2&middot;n_params makes it the practical choice.",
    },
    {
      q: "What does the quantum kernel K(x_i, x_j) compute?",
      a: [
        "The squared overlap |&lang;&phi;(x_i)|&phi;(x_j)&rang;|<sup>2</sup>.",
        "The Euclidean distance between x_i and x_j.",
        "The accuracy of the model.",
        "A random number.",
      ],
      correct: 0,
      why: "The fidelity quantum kernel is the squared inner product of the encoded states.",
    },
    {
      q: "Why might QSVC be 'expressively richer' than a classical RBF kernel?",
      a: [
        "It uses more memory.",
        "Its feature space has dimension 2<sup>n_qubits</sup>, which grows exponentially and includes high-order feature correlations.",
        "It uses GPUs.",
        "It is faster.",
      ],
      correct: 1,
      why: "RBF lives in an effectively high-dimensional space too, but the structure is fixed. The quantum feature map's space is exponential in qubits and shaped by the entangling pattern, capturing correlations a classical kernel cannot reproduce efficiently for some problem families.",
    },
    {
      q: "What does PegasosQSVC offer over plain QSVC?",
      a: [
        "Higher final accuracy guaranteed.",
        "It evaluates the kernel between the current point and only the support vectors; cost scales as O(T) rather than O(N<sup>2</sup>).",
        "It avoids using a quantum kernel.",
        "It does not need labels.",
      ],
      correct: 1,
      why: "Pegasos is an SGD-style SVM. For large N, full kernel evaluation is prohibitive; Pegasos avoids it.",
    },
    {
      q: "What is 'ISA-aware transpilation'?",
      a: [
        "Translating Python to C++.",
        "Mapping the logical circuit to a specific device's coupling map and native gate set, inserting SWAPs and choosing best physical qubits.",
        "An optimisation that runs on the laptop only.",
        "Removing entanglement from the circuit.",
      ],
      correct: 1,
      why: "Each IBM device has its own connectivity (heavy-hex on Eagle/Heron) and native gate set. The transpiler at level 3 produces a hardware-runnable circuit.",
    },
    {
      q: "In the recommended hybrid serving architecture, what runs on 99% of transactions?",
      a: [
        "The QSVC.",
        "The classical XGBoost model (Tier 1).",
        "Both quantum and classical in parallel.",
        "Nothing &mdash; transactions go straight through.",
      ],
      correct: 1,
      why: "Quantum touches only the suspicious top-1% tail (Tier 2). Classical Tier 1 is the latency-critical hot path.",
    },
  ];

  // Restore from localStorage
  let savedAnswers = {};
  try {
    savedAnswers = JSON.parse(localStorage.getItem("qcfd-quiz") || "{}");
  } catch (e) {
    savedAnswers = {};
  }

  function render() {
    form.innerHTML = "";
    QUESTIONS.forEach((q, qi) => {
      const wrap = document.createElement("div");
      wrap.className = "quiz-q";
      wrap.id = "quiz-q-" + qi;
      const heading = document.createElement("p");
      heading.innerHTML = `<span class="qnum">Q${qi + 1}.</span>${q.q}`;
      wrap.appendChild(heading);
      const list = document.createElement("ul");
      q.a.forEach((a, ai) => {
        const li = document.createElement("li");
        const id = `q${qi}-a${ai}`;
        const checked = savedAnswers[qi] === ai ? "checked" : "";
        li.innerHTML =
          `<label><input type="radio" name="q${qi}" value="${ai}" id="${id}" ${checked}/> <span>${a}</span></label>`;
        list.appendChild(li);
      });
      wrap.appendChild(list);
      const fb = document.createElement("div");
      fb.className = "quiz-feedback";
      wrap.appendChild(fb);
      form.appendChild(wrap);
    });
  }

  function saveAnswers() {
    const answers = {};
    QUESTIONS.forEach((_, qi) => {
      const sel = form.querySelector(`input[name="q${qi}"]:checked`);
      if (sel) answers[qi] = parseInt(sel.value);
    });
    try { localStorage.setItem("qcfd-quiz", JSON.stringify(answers)); } catch (e) {}
    return answers;
  }

  scoreBtn.addEventListener("click", () => {
    const answers = saveAnswers();
    let correct = 0;
    QUESTIONS.forEach((q, qi) => {
      const wrap = document.getElementById("quiz-q-" + qi);
      wrap.classList.remove("correct", "wrong");
      const fb = wrap.querySelector(".quiz-feedback");
      if (answers[qi] == null) {
        fb.innerHTML = `<em>No answer.</em> Correct answer: <strong>${q.a[q.correct]}</strong>. ${q.why}`;
        wrap.classList.add("wrong");
        return;
      }
      if (answers[qi] === q.correct) {
        correct++;
        wrap.classList.add("correct");
        fb.innerHTML = `<strong>Correct.</strong> ${q.why}`;
      } else {
        wrap.classList.add("wrong");
        fb.innerHTML = `<strong>Not quite.</strong> Correct: <strong>${q.a[q.correct]}</strong>. ${q.why}`;
      }
    });
    result.textContent = `Score: ${correct} / ${QUESTIONS.length}`;
  });

  form.addEventListener("change", saveAnswers);

  resetBtn.addEventListener("click", () => {
    try { localStorage.removeItem("qcfd-quiz"); } catch (e) {}
    savedAnswers = {};
    result.textContent = "";
    render();
  });

  render();
})();
