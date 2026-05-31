async function loadSearchIndex() {
  const response = await fetch("/search.json", { cache: "no-store" });
  return response.json();
}

function normalize(value) {
  return (value || "").toLowerCase();
}

function scoreRecord(record, query) {
  const needle = normalize(query);
  if (!needle) return 0;

  const title = normalize(record.title);
  const description = normalize(record.description);
  const text = normalize(record.text);
  const tags = normalize((record.tags || []).join(" "));
  const categories = normalize((record.categories || []).join(" "));

  if (title.includes(needle)) return 100;
  if (description.includes(needle)) return 80;
  if (tags.includes(needle)) return 60;
  if (categories.includes(needle)) return 50;
  if (text.includes(needle)) return 30;
  return 0;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function highlightText(value, query) {
  const text = String(value || "");
  const needle = normalize(query);
  if (!needle) {
    return escapeHtml(text);
  }

  const lower = text.toLowerCase();
  const index = lower.indexOf(needle);
  if (index < 0) {
    return escapeHtml(text);
  }

  const before = escapeHtml(text.slice(0, index));
  const match = escapeHtml(text.slice(index, index + needle.length));
  const after = escapeHtml(text.slice(index + needle.length));
  return `${before}<mark>${match}</mark>${after}`;
}

function buildTagStats(records, query) {
  const needle = normalize(query);
  const tagCounts = new Map();

  records
    .filter((record) => record.kind === "post")
    .filter((record) => !needle || scoreRecord(record, needle) > 0)
    .forEach((record) => {
      (record.tags || []).forEach((tag) => {
        const name = String(tag || "").trim();
        if (!name) return;
        tagCounts.set(name, (tagCounts.get(name) || 0) + 1);
      });
    });

  return [...tagCounts.entries()]
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
    .slice(0, 12)
    .map(([tag, count]) => ({ tag, count }));
}

function matchesSelectedTags(record, selectedTags) {
  if (!selectedTags.size) return true;
  if (record.kind !== "post") return false;

  const recordTags = new Set((record.tags || []).map((tag) => normalize(tag)));
  return [...selectedTags].every((tag) => recordTags.has(tag));
}

function renderFilterList(container, tags, selectedTags) {
  if (!container) return;

  container.innerHTML = tags
    .map(({ tag, count }) => {
      const normalizedTag = normalize(tag);
      const isActive = selectedTags.has(normalizedTag);
      return `
        <button
          class="search-modal__filter${isActive ? " is-active" : ""}"
          type="button"
          data-search-filter="${escapeHtml(tag)}"
          aria-pressed="${isActive ? "true" : "false"}"
        >
          <span class="search-modal__filter-name">${escapeHtml(tag)}</span>
          <span class="search-modal__filter-count">${count}</span>
        </button>
      `;
    })
    .join("");
}

function renderResults(container, results, query, activeIndex) {
  if (!query && !results.length) {
    container.innerHTML = "";
    return;
  }

  if (!results.length) {
    container.innerHTML = '<p class="navbar-search__empty">No matches found.</p>';
    return;
  }

  container.innerHTML = results
    .map((record) => {
      const categoryText = [record.kind, ...(record.categories || [])]
        .filter(Boolean)
        .join(" · ");
      const description = record.description
        ? `<span class="navbar-search__item-desc">${highlightText(record.description, query)}</span>`
        : "";

      return `
        <a
          class="navbar-search__item${activeIndex === record.__index ? " is-active" : ""}"
          href="${escapeHtml(record.url)}"
          data-result-index="${record.__index}"
          role="option"
          aria-selected="${activeIndex === record.__index ? "true" : "false"}"
        >
          <span class="navbar-search__item-top">
            <span class="navbar-search__item-title">${highlightText(record.title, query)}</span>
            <span class="navbar-search__item-meta-wrap">
              <span class="navbar-search__item-meta">${escapeHtml(categoryText)}</span>
              ${activeIndex === record.__index ? '<span class="navbar-search__item-action" aria-hidden="true">↵</span>' : ""}
            </span>
          </span>
          ${description}
        </a>
      `;
    })
    .join("");
}

function initSearchWidget(widget, index) {
  const input = document.querySelector("[data-search-input]");
  const modal = document.querySelector("[data-search-modal]");
  const resultsContainer = document.querySelector("[data-search-results]");
  const countNode = document.querySelector("[data-search-count]");
  const filtersNode = document.querySelector("[data-search-filters]");
  const filterList = document.querySelector("[data-search-filter-list]");
  const filtersToggle = document.querySelector("[data-search-filters-toggle]");
  const filtersBadge = document.querySelector("[data-search-filters-badge]");
  const openButtons = widget.querySelectorAll("[data-search-open]");
  const closeButtons = document.querySelectorAll("[data-search-close]");
  const shortcutLabels = document.querySelectorAll("[data-search-shortcut]");

  if (!input || !modal || !resultsContainer) return;

  let currentResults = [];
  let activeIndex = -1;
  let lastActiveElement = null;
  let filtersCollapsed = false;
  const selectedTags = new Set();

  const setFiltersCollapsed = (collapsed) => {
    filtersCollapsed = collapsed;
    modal.classList.toggle("is-filters-collapsed", collapsed);
    if (filtersNode) {
      filtersNode.setAttribute("aria-hidden", String(collapsed));
    }
    syncFiltersToggle();
  };

  const syncFiltersToggle = () => {
    if (filtersToggle) {
      filtersToggle.setAttribute("aria-expanded", String(!filtersCollapsed));
    }
    if (filtersBadge) {
      filtersBadge.hidden = selectedTags.size === 0;
      filtersBadge.textContent = String(selectedTags.size);
    }
  };

  const isMac = navigator.platform.includes("Mac");
  const shortcutLabel = isMac ? "⌘ K" : "Ctrl K";
  shortcutLabels.forEach((node) => {
    node.textContent = shortcutLabel;
  });

  const update = () => {
    const query = input.value.trim();
    const tagStats = buildTagStats(index, query);
    renderFilterList(filterList, tagStats, selectedTags);
    syncFiltersToggle();

    currentResults = index
      .map((record) => ({ record, score: scoreRecord(record, query) }))
      .filter((entry) => matchesSelectedTags(entry.record, selectedTags))
      .filter((entry) => query || selectedTags.size > 0)
      .filter((entry) => (query ? entry.score > 0 : true))
      .sort((left, right) => right.score - left.score)
      .map((entry, resultIndex) => ({ ...entry.record, __index: resultIndex }))
      .slice(0, 6);

    if (!query && selectedTags.size === 0) {
      if (countNode) {
        countNode.hidden = true;
        countNode.textContent = "";
      }
      resultsContainer.innerHTML = "";
      activeIndex = -1;
      return;
    }

    if (activeIndex >= currentResults.length) {
      activeIndex = currentResults.length - 1;
    }
    if (activeIndex < 0 && currentResults.length) {
      activeIndex = 0;
    }

    if (countNode) {
      countNode.hidden = false;
      if (query) {
        countNode.textContent = `${currentResults.length} result${currentResults.length === 1 ? "" : "s"}`;
      } else {
        countNode.textContent = `${currentResults.length} result${currentResults.length === 1 ? "" : "s"} for selected tag${selectedTags.size === 1 ? "" : "s"}`;
      }
    }

    renderResults(resultsContainer, currentResults, query, activeIndex);
  };

  const showModal = () => {
    if (!modal.hidden) {
      input.focus();
      return;
    }

    lastActiveElement = document.activeElement;
    modal.hidden = false;
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("search-open");
    syncFiltersToggle();
    window.requestAnimationFrame(() => {
      input.focus();
      input.select();
      update();
    });
  };

  const hideModal = () => {
    modal.hidden = true;
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("search-open");
    input.value = "";
    activeIndex = -1;
    currentResults = [];
    selectedTags.clear();
    syncFiltersToggle();
    if (countNode) {
      countNode.hidden = true;
      countNode.textContent = "";
    }
    resultsContainer.innerHTML = "";
    if (lastActiveElement && typeof lastActiveElement.focus === "function") {
      lastActiveElement.focus();
    }
  };

  input.addEventListener("input", update);
  input.addEventListener("focus", update);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      hideModal();
      return;
    }

    if (!currentResults.length) {
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      activeIndex = (activeIndex + 1) % currentResults.length;
      renderResults(resultsContainer, currentResults, input.value.trim(), activeIndex);
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      activeIndex = activeIndex <= 0 ? currentResults.length - 1 : activeIndex - 1;
      renderResults(resultsContainer, currentResults, input.value.trim(), activeIndex);
      return;
    }

    if (event.key === "Enter" && activeIndex >= 0) {
      const selected = currentResults[activeIndex];
      if (selected) {
        window.location.assign(selected.url);
      }
    }
  });

  openButtons.forEach((button) => {
    button.addEventListener("click", showModal);
  });

  closeButtons.forEach((button) => {
    button.addEventListener("click", hideModal);
  });

  if (filterList) {
    filterList.addEventListener("click", (event) => {
      const button = event.target.closest("[data-search-filter]");
      if (!button) return;

      const rawTag = button.getAttribute("data-search-filter") || "";
      const normalizedTag = normalize(rawTag);

      if (selectedTags.has(normalizedTag)) {
        selectedTags.delete(normalizedTag);
      } else if (normalizedTag) {
        selectedTags.add(normalizedTag);
      }

      update();
      input.focus();
    });
  }

  if (filtersToggle && filtersNode) {
    filtersToggle.addEventListener("click", () => {
      setFiltersCollapsed(!filtersCollapsed);
    });
  }

  resultsContainer.addEventListener("mousemove", (event) => {
    const item = event.target.closest("[data-result-index]");
    if (!item) return;
    activeIndex = Number(item.getAttribute("data-result-index"));
    renderResults(resultsContainer, currentResults, input.value.trim(), activeIndex);
  });

  document.addEventListener("keydown", (event) => {
    const isShortcut = (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k";
    const isSlash = event.key === "/" && !event.metaKey && !event.ctrlKey && !event.altKey;
    const target = event.target;
    const typingTarget =
      target instanceof HTMLElement &&
      (target.matches("input, textarea, select") || target.isContentEditable);

    if ((isShortcut || isSlash) && !typingTarget) {
      event.preventDefault();
      showModal();
    }
  });

  setFiltersCollapsed(false);
  hideModal();
}

async function initSearch() {
  const widgets = document.querySelectorAll("[data-search-widget]");
  if (!widgets.length) return;

  const index = await loadSearchIndex();
  widgets.forEach((widget) => initSearchWidget(widget, index));
}

initSearch().catch((error) => {
  console.error("Search failed to initialize", error);
});
