// Octicons (MIT) - github.com/primer/octicons
const CODE_ICONS = {
  "copy": '<svg class="icon icon--copy" viewBox="0 0 16 16" aria-hidden="true"><path d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 0 1 0 1.5h-1.5a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-1.5a.75.75 0 0 1 1.5 0v1.5A1.75 1.75 0 0 1 9.25 16h-7.5A1.75 1.75 0 0 1 0 14.25Z"/><path d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0 1 14.25 11h-7.5A1.75 1.75 0 0 1 5 9.25Zm1.75-.25a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-7.5a.25.25 0 0 0-.25-.25Z"/></svg>',
  "check": '<svg class="icon icon--check" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"/></svg>',
};

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
  const icon = button.querySelector(".icon");
  const label = button.querySelector("span");
  if (!icon || !label) return;

  if (copied) {
    button.classList.add("is-copied");
    icon.outerHTML = CODE_ICONS.check;
    label.textContent = "Copied";
    return;
  }

  button.classList.remove("is-copied");
  icon.outerHTML = CODE_ICONS.copy;
  label.textContent = "Copy";
}

function ensureToolbar(wrapper) {
  const header = ensureHeader(wrapper);
  let toolbar = wrapper.querySelector(".code-toolbar");
  if (!toolbar) {
    toolbar = document.createElement("div");
    toolbar.className = "code-toolbar";
    header.appendChild(toolbar);
  }
  return toolbar;
}

function ensureHeader(wrapper) {
  let header = wrapper.querySelector(".code-header");
  if (!header) {
    header = document.createElement("div");
    header.className = "code-header";
    wrapper.insertBefore(header, wrapper.firstChild);
  }
  return header;
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
  ensureHeader(wrapper).prepend(title);
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
    button.innerHTML = `${CODE_ICONS.copy}<span>Copy</span>`;

    button.addEventListener("click", async () => {
      const text = code.textContent || "";
      try {
        await copyText(text);
        setCopiedState(button, true);
        window.announce?.("Code copied to clipboard");
        window.setTimeout(() => setCopiedState(button, false), 1200);
      } catch (error) {
        console.error("Failed to copy code block", error);
        window.announce?.("Couldn't copy the code");
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
