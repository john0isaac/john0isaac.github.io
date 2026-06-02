function initBlogArchive() {
  const layouts = document.querySelectorAll(".blog-layout");
  if (!layouts.length) return;

  layouts.forEach((layout, index) => {
    const sidebar = layout.querySelector("[data-blog-archive]");
    const toggle = layout.querySelector("[data-blog-archive-toggle]");
    if (!sidebar || !toggle) return;

    const storageKey = `blog-archive-open-${index}`;

    // Create floating open button (tab on left edge)
    const openBtn = document.createElement("button");
    openBtn.className = "blog-archive__open-btn";
    openBtn.type = "button";
    openBtn.setAttribute("aria-label", "Open blog archive");
    openBtn.setAttribute("title", "Open blog archive");
    openBtn.innerHTML = '<i class="fa-solid fa-chevron-right" aria-hidden="true"></i>';
    document.body.appendChild(openBtn);

    const expandActiveBranch = () => {
      const activeLink = layout.querySelector(".blog-archive__post-link.is-active");
      if (!activeLink) return;
      const monthDetails = activeLink.closest("details.blog-archive__month");
      const yearDetails = activeLink.closest("details.blog-archive__year");
      if (monthDetails) monthDetails.open = true;
      if (yearDetails) yearDetails.open = true;
    };

    const setOpen = (open) => {
      layout.classList.toggle("is-archive-open", open);
      openBtn.classList.toggle("is-open", open);
      const openBtnIcon = openBtn.querySelector("i");
      if (openBtnIcon) {
        openBtnIcon.className = open ? "fa-solid fa-chevron-left" : "fa-solid fa-chevron-right";
      }
      openBtn.setAttribute("aria-label", open ? "Close blog archive" : "Open blog archive");
      openBtn.setAttribute("title", open ? "Close blog archive" : "Open blog archive");
      toggle.setAttribute("aria-expanded", String(open));
      if (open) expandActiveBranch();
    };

    // Default: open on desktop, closed on mobile
    const saved = window.localStorage.getItem(storageKey);
    const defaultOpen = saved !== null
      ? saved === "true"
      : window.matchMedia("(min-width: 992px)").matches;

    setOpen(defaultOpen);

    toggle.addEventListener("click", () => {
      const open = !layout.classList.contains("is-archive-open");
      setOpen(open);
      window.localStorage.setItem(storageKey, String(open));
    });

    openBtn.addEventListener("click", () => {
      const open = !layout.classList.contains("is-archive-open");
      setOpen(open);
      window.localStorage.setItem(storageKey, String(open));
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && layout.classList.contains("is-archive-open")) {
        setOpen(false);
        window.localStorage.setItem(storageKey, "false");
      }
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initBlogArchive);
} else {
  initBlogArchive();
}
