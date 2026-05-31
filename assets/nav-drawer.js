(() => {
  const drawer = document.getElementById("nav-drawer");
  const overlay = document.querySelector("[data-nav-overlay]");
  const openBtn = document.querySelector("[data-nav-open]");
  const closeBtn = document.querySelector("[data-nav-close]");

  if (!drawer) return;

  function openDrawer() {
    drawer.classList.add("is-open");
    overlay.classList.add("is-visible");
    document.body.classList.add("nav-drawer-open");
    drawer.setAttribute("aria-hidden", "false");
    openBtn?.setAttribute("aria-expanded", "true");
    closeBtn?.focus();
  }

  function closeDrawer() {
    drawer.classList.remove("is-open");
    overlay.classList.remove("is-visible");
    document.body.classList.remove("nav-drawer-open");
    drawer.setAttribute("aria-hidden", "true");
    openBtn?.setAttribute("aria-expanded", "false");
    openBtn?.focus();
  }

  openBtn?.addEventListener("click", openDrawer);
  closeBtn?.addEventListener("click", closeDrawer);
  overlay?.addEventListener("click", closeDrawer);

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && drawer.classList.contains("is-open")) {
      closeDrawer();
    }
  });
})();
