/* Top-level glue: progress bar, sidebar TOC active state, scroll restore. */
(function () {
  const sidebar = document.getElementById("sidebar");
  const tocLinks = sidebar ? Array.from(sidebar.querySelectorAll(".toc a")) : [];
  const sections = tocLinks
    .map((a) => document.querySelector(a.getAttribute("href")))
    .filter(Boolean);
  const progressInner = document.getElementById("progress-bar-inner");

  function updateProgress() {
    const docH = document.documentElement.scrollHeight - window.innerHeight;
    const pct = docH > 0 ? Math.min(100, (window.scrollY / docH) * 100) : 0;
    if (progressInner) progressInner.style.width = pct + "%";
  }

  function updateActive() {
    const y = window.scrollY + 100;
    let activeIdx = 0;
    for (let i = 0; i < sections.length; i++) {
      if (sections[i].offsetTop <= y) activeIdx = i;
    }
    tocLinks.forEach((a, i) => a.classList.toggle("active", i === activeIdx));
  }

  function persistScroll() {
    try { localStorage.setItem("qcfd-scroll", String(window.scrollY)); } catch (e) {}
  }
  function restoreScroll() {
    try {
      const y = parseInt(localStorage.getItem("qcfd-scroll") || "0");
      if (!isNaN(y) && y > 0) window.scrollTo(0, y);
    } catch (e) {}
  }

  let ticking = false;
  window.addEventListener("scroll", () => {
    if (!ticking) {
      requestAnimationFrame(() => {
        updateProgress();
        updateActive();
        persistScroll();
        ticking = false;
      });
      ticking = true;
    }
  });

  // Restore scroll only after a small delay so all widgets render first
  window.addEventListener("load", () => {
    setTimeout(restoreScroll, 200);
    updateProgress();
    updateActive();
  });
})();
