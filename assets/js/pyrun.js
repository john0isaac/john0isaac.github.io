// Adds a "Run" button to Python code blocks and executes them with Pyodide.
// Wrapped in an IIFE: other classic scripts on the page (e.g. search.js) also
// declare a global `renderResults`, which would otherwise clobber ours.
(function () {
  // Octicons (MIT) - github.com/primer/octicons
  const ICONS = {
    "play": '<svg class="icon icon--play" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Zm4.879-2.773 4.264 2.559a.25.25 0 0 1 0 .428l-4.264 2.559A.25.25 0 0 1 6 10.559V5.442a.25.25 0 0 1 .379-.215Z"/></svg>',
    "sync": '<svg class="icon icon--sync is-spinning" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M1.705 8.005a.75.75 0 0 1 .834.656 5.5 5.5 0 0 0 9.592 2.97l-1.204-1.204a.25.25 0 0 1 .177-.427h3.646a.25.25 0 0 1 .25.25v3.646a.25.25 0 0 1-.427.177l-1.38-1.38A7.002 7.002 0 0 1 1.05 8.84a.75.75 0 0 1 .656-.834ZM8 2.5a5.487 5.487 0 0 0-4.131 1.869l1.204 1.204A.25.25 0 0 1 4.896 6H1.25A.25.25 0 0 1 1 5.75V2.104a.25.25 0 0 1 .427-.177l1.38 1.38A7.002 7.002 0 0 1 14.95 7.16a.75.75 0 0 1-1.49.178A5.5 5.5 0 0 0 8 2.5Z"/></svg>',
    "x": '<svg class="icon icon--x" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M3.72 3.72a.75.75 0 0 1 1.06 0L8 6.94l3.22-3.22a.749.749 0 0 1 1.275.326.749.749 0 0 1-.215.734L9.06 8l3.22 3.22a.749.749 0 0 1-.326 1.275.749.749 0 0 1-.734-.215L8 9.06l-3.22 3.22a.751.751 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042L6.94 8 3.72 4.78a.75.75 0 0 1 0-1.06Z"/></svg>',
  };

  let pyodidePromise = null;

  function getPyodide() {
    if (!pyodidePromise) {
      pyodidePromise = loadPyodide();
    }
    return pyodidePromise;
  }

  function buildSection(title, text, isError) {
    const section = document.createElement("div");
    section.className = "code-run-section" + (isError ? " is-error" : "");

    const heading = document.createElement("p");
    heading.className = "code-run-section__title";
    heading.textContent = title;

    const panel = document.createElement("pre");
    panel.className = "code-run-section__panel";
    const codeEl = document.createElement("code");
    codeEl.textContent = text;
    panel.appendChild(codeEl);

    section.appendChild(heading);
    section.appendChild(panel);
    return section;
  }

  function ensureResults(wrapper) {
    let results = wrapper.querySelector(".code-run-results");
    if (!results) {
      results = document.createElement("div");
      results.className = "code-run-results";
      wrapper.appendChild(results);
    }
    return results;
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

  function renderResults(results, { output, stdout, error }) {
    results.innerHTML = "";
    if (error) {
      results.appendChild(buildSection("Error", error, true));
    } else if (!output && !stdout) {
      results.appendChild(buildSection("Value of final expression", "No output from code execution.", false));
    }
    if (output) {
      results.appendChild(buildSection("Value of final expression", output, false));
    }
    if (stdout) {
      results.appendChild(buildSection("Standard output (i.e. from print statements)", stdout, false));
    }
    results.hidden = false;
  }

  function setRunState(button, state) {
    const icon = button.querySelector(".icon");
    const label = button.querySelector("span");
    if (!icon || !label) return;

    if (state === "running") {
      button.disabled = true;
      icon.outerHTML = ICONS.sync;
      label.textContent = "Running";
      return;
    }

    button.disabled = false;
    icon.outerHTML = ICONS.play;
    label.textContent = "Run";
  }

  async function runPythonBlock(code) {
    const pyodide = await getPyodide();
    const stdoutLines = [];
    pyodide.setStdout({ batched: (line) => stdoutLines.push(line) });
    pyodide.setStderr({ batched: (line) => stdoutLines.push(line) });

    try {
      const result = await pyodide.runPythonAsync(code.textContent || "");
      const output = result !== undefined ? String(result) : "";
      return { output, stdout: stdoutLines.join("\n"), error: "" };
    } catch (error) {
      return { output: "", stdout: stdoutLines.join("\n"), error: String(error.message || error) };
    } finally {
      pyodide.setStdout();
      pyodide.setStderr();
    }
  }

  function attachRunButtons() {
    const selector = ".prose pre > code.language-py, .prose pre > code.language-python";
    document.querySelectorAll(selector).forEach((code) => {
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

      if (wrapper.querySelector(".code-run-btn")) {
        return;
      }

      pre.classList.add("code-block");
      const toolbar = ensureToolbar(wrapper);

      const button = document.createElement("button");
      button.type = "button";
      button.className = "code-run-btn";
      button.setAttribute("aria-label", "Run Python code");
      button.innerHTML = `${ICONS.play}<span>Run</span>`;

      const clearButton = document.createElement("button");
      clearButton.type = "button";
      clearButton.className = "code-clear-btn";
      clearButton.hidden = true;
      clearButton.setAttribute("aria-label", "Clear output");
      clearButton.innerHTML = `${ICONS.x}<span>Clear</span>`;

      clearButton.addEventListener("click", () => {
        const results = wrapper.querySelector(".code-run-results");
        if (results) {
          results.innerHTML = "";
          results.hidden = true;
        }
        clearButton.hidden = true;
      });

      button.addEventListener("click", async () => {
        const results = ensureResults(wrapper);
        results.hidden = true;
        setRunState(button, "running");
        try {
          renderResults(results, await runPythonBlock(code));
        } catch (error) {
          renderResults(results, { output: "", stdout: "", error: "Failed to load Python runtime: " + String(error) });
        } finally {
          setRunState(button, "idle");
          clearButton.hidden = false;
        }
      });

      toolbar.appendChild(button);
      toolbar.appendChild(clearButton);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", attachRunButtons);
  } else {
    attachRunButtons();
  }
})();
