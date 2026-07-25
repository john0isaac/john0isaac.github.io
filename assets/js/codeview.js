// Enhances static code blocks with an editable CodeMirror view:
// line numbers, code folding, syntax highlighting (all languages,
// lazy-loaded), and light/dark theme that follows the site theme.
import {
  EditorView,
  EditorState,
  Compartment,
  lineNumbers,
  foldGutter,
  syntaxHighlighting,
  defaultHighlightStyle,
  LanguageDescription,
  languages,
  oneDark,
} from "/vendor/codemirror/codemirror.min.js";

const themeCompartment = new Compartment();
const views = [];

function isDark() {
  return document.documentElement.dataset.theme === "dark";
}

function themeExtension() {
  return isDark() ? oneDark : syntaxHighlighting(defaultHighlightStyle);
}

async function languageExtension(code) {
  const langClass = [...code.classList].find((c) => c.startsWith("language-"));
  if (!langClass) {
    return [];
  }
  const token = langClass.slice("language-".length);
  // Fence tokens are sometimes a name/alias ("python", "bash") and sometimes a
  // file extension ("py", "rs"), so try both lookups.
  const desc =
    LanguageDescription.matchLanguageName(languages, token, true) ||
    LanguageDescription.matchFilename(languages, "file." + token);
  if (!desc) {
    return [];
  }
  try {
    return [await desc.load()];
  } catch (error) {
    console.warn("Failed to load CodeMirror language:", error);
    return [];
  }
}

async function enhanceCodeBlock(code) {
  const pre = code.parentElement;
  const wrapper = pre?.parentElement;
  if (!pre || !wrapper) {
    return;
  }

  const doc = (code.textContent || "").replace(/\n$/, "");
  const view = new EditorView({
    state: EditorState.create({
      doc,
      extensions: [
        lineNumbers(),
        foldGutter(),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
            code.textContent = update.state.doc.toString();
          }
        }),
        themeCompartment.of(themeExtension()),
        ...(await languageExtension(code)),
      ],
    }),
  });

  view.dom.classList.add("code-view");
  wrapper.insertBefore(view.dom, pre);
  pre.hidden = true;
  views.push(view);
}

function switchThemes() {
  for (const view of views) {
    view.dispatch({ effects: themeCompartment.reconfigure(themeExtension()) });
  }
}

function init() {
  document.querySelectorAll(".prose pre > code").forEach((code) => {
    const pre = code.parentElement;
    let wrapper = pre.parentElement;
    if (!wrapper.classList.contains("code-block-wrap")) {
      wrapper = document.createElement("div");
      wrapper.className = "code-block-wrap";
      pre.insertAdjacentElement("beforebegin", wrapper);
      wrapper.appendChild(pre);
    }
    enhanceCodeBlock(code);
  });

  new MutationObserver(switchThemes).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-theme"],
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
