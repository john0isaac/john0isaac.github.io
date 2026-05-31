(() => {
  const storageKey = "theme";
  const root = document.documentElement;
  const toggle = document.querySelector("[data-theme-toggle]");
  const icon = document.querySelector("[data-theme-icon]");

  if (!toggle) {
    return;
  }

  const setTheme = (theme) => {
    const nextTheme = theme === "dark" ? "dark" : "light";
    const oppositeTheme = nextTheme === "dark" ? "light" : "dark";

    root.dataset.theme = nextTheme;
    root.style.colorScheme = nextTheme;
    localStorage.setItem(storageKey, nextTheme);

    if (icon) {
      icon.className =
        nextTheme === "dark" ? "fa-regular fa-lightbulb" : "fa-solid fa-lightbulb";
    }

    toggle.setAttribute("aria-label", `Switch to ${oppositeTheme} mode`);
    toggle.setAttribute("title", `Switch to ${oppositeTheme} mode`);
  };

  setTheme(root.dataset.theme || "light");

  toggle.addEventListener("click", () => {
    setTheme(root.dataset.theme === "dark" ? "light" : "dark");
  });
})();
