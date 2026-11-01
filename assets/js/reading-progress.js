(() => {
  const bar = document.querySelector("[data-reading-progress]");
  const article = document.querySelector(".post-layout");
  if (!bar || !article) return;

  let queued = false;
  const update = () => {
    queued = false;
    const rect = article.getBoundingClientRect();
    const total = rect.height - window.innerHeight;
    const progress = total > 0 ? Math.min(1, Math.max(0, -rect.top / total)) : 1;
    bar.style.transform = `scaleX(${progress})`;
  };
  const schedule = () => {
    if (!queued) {
      queued = true;
      window.requestAnimationFrame(update);
    }
  };

  window.addEventListener("scroll", schedule, { passive: true });
  window.addEventListener("resize", schedule);
  update();
})();
