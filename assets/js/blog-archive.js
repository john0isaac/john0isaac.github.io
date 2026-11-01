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

    // The archive floats over the page, so it always starts closed.
    window.localStorage.removeItem(storageKey);
    setOpen(false);

    // Skip the slide animation for the initial state so it doesn't visibly "glitch" in.
    layout.classList.add("is-initializing");
    openBtn.classList.add("is-initializing");
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        layout.classList.remove("is-initializing");
        openBtn.classList.remove("is-initializing");
      });
    });
    toggle.addEventListener("click", () => {
      const open = !layout.classList.contains("is-archive-open");
      setOpen(open);
    });

    openBtn.addEventListener("click", () => {
      const open = !layout.classList.contains("is-archive-open");
      setOpen(open);
    });

    // The archive floats over the page, so a click outside closes it.
    document.addEventListener("click", (e) => {
      if (!layout.classList.contains("is-archive-open")) return;
      if (sidebar.contains(e.target) || openBtn.contains(e.target)) return;
      setOpen(false);
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && layout.classList.contains("is-archive-open")) {
        setOpen(false);
        }
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initBlogArchive);
} else {
  initBlogArchive();
}
