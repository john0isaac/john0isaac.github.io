// Adds a "Run" button to Python code blocks and executes them with Pyodide.
// Wrapped in an IIFE: other classic scripts on the page (e.g. search.js) also
// declare a global `renderResults`, which would otherwise clobber ours.
(function () {
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
    let toolbar = wrapper.querySelector(".code-toolbar");
    if (!toolbar) {
      toolbar = document.createElement("div");
      toolbar.className = "code-toolbar";
      wrapper.appendChild(toolbar);
    }
    return toolbar;
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
    const icon = button.querySelector("i");
    const label = button.querySelector("span");
    if (!icon || !label) return;

    if (state === "running") {
      button.disabled = true;
      icon.className = "fa-solid fa-spinner fa-spin";
      label.textContent = "Running";
      return;
    }

    button.disabled = false;
    icon.className = "fa-solid fa-play";
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
      button.innerHTML = '<i class="fa-solid fa-play" aria-hidden="true"></i><span>Run</span>';

      const clearButton = document.createElement("button");
      clearButton.type = "button";
      clearButton.className = "code-clear-btn";
      clearButton.hidden = true;
      clearButton.setAttribute("aria-label", "Clear output");
      clearButton.innerHTML = '<i class="fa-solid fa-xmark" aria-hidden="true"></i><span>Clear</span>';

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
