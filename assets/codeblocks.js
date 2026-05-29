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

    wrapper.appendChild(button);
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", attachCopyButtons);
} else {
  attachCopyButtons();
}
