(() => {
  const filter = document.querySelector("[data-project-filter]");
  if (!filter) return;

  const pills = [...filter.querySelectorAll("[data-tech]")];
  const cards = [...document.querySelectorAll(".project-card[data-technologies]")];
  const sections = [...document.querySelectorAll(".projects-section")];
  const status = document.querySelector("[data-project-filter-status]");

  const applyFilter = (tech, { updateUrl = true } = {}) => {
    if (tech && !pills.some((pill) => pill.dataset.tech === tech)) tech = "";

    pills.forEach((pill) => {
      const active = pill.dataset.tech === tech;
      pill.classList.toggle("is-active", active);
      pill.setAttribute("aria-pressed", String(active));
      if (active && tech) pill.scrollIntoView({ block: "nearest", inline: "center" });
    });

    let visible = 0;
    cards.forEach((card) => {
      const match = !tech || card.dataset.technologies.split("|").includes(tech);
      card.hidden = !match;
      if (match) visible += 1;
    });
    sections.forEach((section) => {
      section.hidden = !section.querySelector(".project-card:not([hidden])");
    });

    if (status) {
      status.textContent = tech
        ? `Showing ${visible} ${visible === 1 ? "project" : "projects"} using ${tech}`
        : `Showing all ${visible} projects`;
    }

    if (updateUrl) {
      const url = new URL(window.location.href);
      if (tech) url.searchParams.set("tech", tech);
      else url.searchParams.delete("tech");
      history.replaceState(null, "", url);
    }
  };

  filter.addEventListener("click", (event) => {
    const pill = event.target.closest("[data-tech]");
    if (!pill) return;
    // Clicking the active technology again resets to "All".
    const tech = pill.classList.contains("is-active") ? "" : pill.dataset.tech;
    applyFilter(tech);
  });

  filter.hidden = false;
  applyFilter(new URLSearchParams(window.location.search).get("tech") || "", { updateUrl: false });
})();
