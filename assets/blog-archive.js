function initBlogArchive() {
  const layouts = document.querySelectorAll(".blog-layout");
  if (!layouts.length) return;

  layouts.forEach((layout, index) => {
    const sidebar = layout.querySelector("[data-blog-archive]");
    const toggle = layout.querySelector("[data-blog-archive-toggle]");
    if (!sidebar || !toggle) return;

    const storageKey = `blog-archive-collapsed-${index}`;
    const expandActiveBranch = () => {
      const activeLink = layout.querySelector(".blog-archive__post-link.is-active");
      if (!activeLink) return;

      const monthDetails = activeLink.closest("details.blog-archive__month");
      const yearDetails = activeLink.closest("details.blog-archive__year");
      if (monthDetails) monthDetails.open = true;
      if (yearDetails) yearDetails.open = true;
    };

    const setCollapsed = (collapsed) => {
      layout.classList.toggle("is-archive-collapsed", collapsed);
      toggle.setAttribute("aria-expanded", String(!collapsed));
      toggle.setAttribute("aria-label", collapsed ? "Expand blog archive" : "Collapse blog archive");
      toggle.setAttribute("title", collapsed ? "Expand blog archive" : "Collapse blog archive");

      const icon = toggle.querySelector("i");
      if (icon) {
        icon.className = collapsed ? "fa-solid fa-chevron-right" : "fa-solid fa-chevron-left";
      }

      if (!collapsed) {
        expandActiveBranch();
      }
    };

    const saved = window.localStorage.getItem(storageKey);
    setCollapsed(saved === "true");

    toggle.addEventListener("click", () => {
      const collapsed = !layout.classList.contains("is-archive-collapsed");
      setCollapsed(collapsed);
      window.localStorage.setItem(storageKey, String(collapsed));
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initBlogArchive);
} else {
  initBlogArchive();
}
