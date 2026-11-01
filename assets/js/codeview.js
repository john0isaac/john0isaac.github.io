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

// CodeMirror's default light palette has a few colours (e.g. #e40, #f00) below the
// WCAG AA 4.5:1 ratio on our card background, so darken just those.
const LIGHT_CODE_BG = [0xff, 0xfd, 0xf9];

function luminance([r, g, b]) {
  const lin = (c) => {
    const v = c / 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}

function parseHex(hex) {
  const h = hex.length === 4 ? [...hex.slice(1)].map((c) => c + c).join("") : hex.slice(1);
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
}

function accessibleColor(color) {
  if (!/^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(color)) return color;
  let rgb = parseHex(color);
  const bg = luminance(LIGHT_CODE_BG) + 0.05;
  while (bg / (luminance(rgb) + 0.05) < 4.6) {
    rgb = rgb.map((c) => Math.floor(c * 0.9));
  }
  return "#" + rgb.map((c) => c.toString(16).padStart(2, "0")).join("");
}

const lightHighlightStyle = defaultHighlightStyle.constructor.define(
  defaultHighlightStyle.specs.map((spec) =>
    spec.color ? { ...spec, color: accessibleColor(spec.color) } : spec
  )
);

function themeExtension() {
  return isDark() ? oneDark : syntaxHighlighting(lightHighlightStyle);
}

function editorLabel(code) {
  const title = code.getAttribute("title");
  if (title) return `Code: ${title}`;
  const langClass = [...code.classList].find((c) => c.startsWith("language-"));
  return langClass ? `${langClass.slice("language-".length)} code` : "Code";
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
        EditorView.contentAttributes.of({ "aria-label": editorLabel(code), tabindex: "0" }),
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
