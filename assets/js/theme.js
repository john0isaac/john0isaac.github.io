(() => {
  const storageKey = "theme";
  const root = document.documentElement;
  const toggle = document.querySelector("[data-theme-toggle]");

  if (!toggle) {
    return;
  }

  const setTheme = (theme) => {
    const nextTheme = theme === "dark" ? "dark" : "light";
    const oppositeTheme = nextTheme === "dark" ? "light" : "dark";

    root.dataset.theme = nextTheme;
    root.style.colorScheme = nextTheme;
    localStorage.setItem(storageKey, nextTheme);

    toggle.setAttribute("aria-label", `Switch to ${oppositeTheme} mode`);
    toggle.setAttribute("title", `Switch to ${oppositeTheme} mode`);
  };

  setTheme(root.dataset.theme || "light");

  toggle.addEventListener("click", () => {
    setTheme(root.dataset.theme === "dark" ? "light" : "dark");
  });
})();
