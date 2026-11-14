// Octicons (MIT) - github.com/primer/octicons
const ARCHIVE_ICONS = {
  "chevron-left": '<svg class="icon icon--chevron-left" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M9.78 12.78a.75.75 0 0 1-1.06 0L4.47 8.53a.75.75 0 0 1 0-1.06l4.25-4.25a.751.751 0 0 1 1.042.018.751.751 0 0 1 .018 1.042L6.06 8l3.72 3.72a.75.75 0 0 1 0 1.06Z"/></svg>',
  "chevron-right": '<svg class="icon icon--chevron-right" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M6.22 3.22a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.751.751 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042L9.94 8 6.22 4.28a.75.75 0 0 1 0-1.06Z"/></svg>',
};

function initBlogArchive() {
  const layouts = document.querySelectorAll(".blog-layout");
  if (!layouts.length) return;

  layouts.forEach((layout, index) => {
    const sidebar = layout.querySelector("[data-blog-archive]");
    const toggle = layout.querySelector("[data-blog-archive-toggle]");
    if (!sidebar || !toggle) return;

    const storageKey = `blog-archive-open-${index}`;
    if (!sidebar.id) sidebar.id = `blog-archive-${index}`;

    // Create floating open button (tab on left edge). It goes right before the
    // archive so keyboard users reach it there, not at the end of the page.
    const openBtn = document.createElement("button");
    openBtn.className = "blog-archive__open-btn";
    openBtn.type = "button";
    openBtn.setAttribute("aria-label", "Open blog archive");
    openBtn.setAttribute("title", "Open blog archive");
    openBtn.setAttribute("aria-controls", sidebar.id);
    openBtn.innerHTML = ARCHIVE_ICONS["chevron-right"];
    sidebar.before(openBtn);

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
      openBtn.innerHTML = ARCHIVE_ICONS[open ? "chevron-left" : "chevron-right"];
      openBtn.setAttribute("aria-label", open ? "Close blog archive" : "Open blog archive");
      openBtn.setAttribute("title", open ? "Close blog archive" : "Open blog archive");
      toggle.setAttribute("aria-expanded", String(open));
      openBtn.setAttribute("aria-expanded", String(open));
      if (open) expandActiveBranch();
    };

    // The open button hides while the archive is open, so focus has to move with it.
    const openWithFocus = () => {
      setOpen(true);
      requestAnimationFrame(() => toggle.focus());
    };

    const closeWithFocus = () => {
      const hadFocus = sidebar.contains(document.activeElement);
      setOpen(false);
      if (hadFocus) openBtn.focus();
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
      if (layout.classList.contains("is-archive-open")) closeWithFocus();
      else openWithFocus();
    });

    openBtn.addEventListener("click", () => {
      if (layout.classList.contains("is-archive-open")) closeWithFocus();
      else openWithFocus();
    });

    // The archive floats over the page, so a click outside closes it.
    document.addEventListener("click", (e) => {
      if (!layout.classList.contains("is-archive-open")) return;
      if (sidebar.contains(e.target) || openBtn.contains(e.target)) return;
      setOpen(false);
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && layout.classList.contains("is-archive-open")) {
        closeWithFocus();
      }
    });

    // Tabbing out of the floating archive closes it, like clicking outside does.
    sidebar.addEventListener("focusout", (e) => {
      if (!layout.classList.contains("is-archive-open")) return;
      if (!e.relatedTarget || sidebar.contains(e.relatedTarget)) return;
      setOpen(false);
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initBlogArchive);
} else {
  initBlogArchive();
}
