function fallbackCopyText(text) {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "absolute";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
}

async function copyText(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  fallbackCopyText(text);
}

function setCopiedState(button, copied) {
  const icon = button.querySelector("i");
  const label = button.querySelector("span");
  if (!icon || !label) return;

  if (copied) {
    button.classList.add("is-copied");
    icon.className = "fa-solid fa-check";
    label.textContent = "Copied";
    return;
  }

  button.classList.remove("is-copied");
  icon.className = "fa-regular fa-copy";
  label.textContent = "Copy";
}

function ensureToolbar(wrapper) {
  let toolbar = wrapper.querySelector(".code-toolbar");
  if (!toolbar) {
    toolbar = document.createElement("div");
    toolbar.className = "code-toolbar";
    wrapper.appendChild(toolbar);
  }
  return toolbar;
}

// Pretty names for the languages used across the blog; anything else falls back
// to the capitalized fence token (e.g. "elixir" -> "Elixir").
const LANGUAGE_NAMES = {
  bash: "Shell",
  bicep: "Bicep",
  c: "C",
  console: "Terminal",
  cpp: "C++",
  cs: "C#",
  csharp: "C#",
  css: "CSS",
  diff: "Diff",
  dockerfile: "Dockerfile",
  go: "Go",
  html: "HTML",
  ini: "INI",
  java: "Java",
  js: "JavaScript",
  javascript: "JavaScript",
  json: "JSON",
  jsx: "JSX",
  kotlin: "Kotlin",
  md: "Markdown",
  markdown: "Markdown",
  php: "PHP",
  powershell: "PowerShell",
  ps1: "PowerShell",
  py: "Python",
  python: "Python",
  rb: "Ruby",
  ruby: "Ruby",
  rs: "Rust",
  rust: "Rust",
  scss: "SCSS",
  sh: "Shell",
  shell: "Shell",
  sql: "SQL",
  swift: "Swift",
  text: "Text",
  toml: "TOML",
  ts: "TypeScript",
  typescript: "TypeScript",
  tsx: "TSX",
  xml: "XML",
  yaml: "YAML",
  yml: "YAML",
  zsh: "Shell",
};

function codeTitle(code) {
  const explicit = code.getAttribute("title");
  if (explicit) {
    return explicit;
  }

  const langClass = [...code.classList].find((c) => c.startsWith("language-"));
  if (!langClass) {
    return "";
  }

  const lang = langClass.slice("language-".length).toLowerCase();
  return LANGUAGE_NAMES[lang] || lang.charAt(0).toUpperCase() + lang.slice(1);
}

function addTitle(wrapper, code) {
  if (wrapper.querySelector(".code-title")) {
    return;
  }

  const text = codeTitle(code);
  if (!text) {
    return;
  }

  const title = document.createElement("span");
  title.className = "code-title";
  title.textContent = text;
  title.title = text;
  wrapper.insertBefore(title, wrapper.firstChild);
}

function attachCopyButtons() {
  document.querySelectorAll(".prose pre > code").forEach((code) => {
    const pre = code.parentElement;
    if (!pre) {
      return;
    }

    let wrapper = pre.parentElement;
    if (!wrapper || !wrapper.classList.contains("code-block-wrap")) {
      wrapper = document.createElement("div");
      wrapper.className = "code-block-wrap";
      pre.insertAdjacentElement("beforebegin", wrapper);
      wrapper.appendChild(pre);
    }

    if (wrapper.querySelector(".code-copy-btn")) {
      return;
    }

    pre.classList.add("code-block");
    addTitle(wrapper, code);

    const button = document.createElement("button");
    button.type = "button";
    button.className = "code-copy-btn";
    button.setAttribute("aria-label", "Copy code to clipboard");
    button.innerHTML = '<i class="fa-regular fa-copy" aria-hidden="true"></i><span>Copy</span>';

    button.addEventListener("click", async () => {
      const text = code.textContent || "";
      try {
        await copyText(text);
        setCopiedState(button, true);
        window.setTimeout(() => setCopiedState(button, false), 1200);
      } catch (error) {
        console.error("Failed to copy code block", error);
      }
    });

    ensureToolbar(wrapper).appendChild(button);
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", attachCopyButtons);
} else {
  attachCopyButtons();
}
