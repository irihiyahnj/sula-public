document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll("[data-copy-target]");
  for (const button of buttons) {
    button.addEventListener("click", async () => {
      const targetId = button.getAttribute("data-copy-target");
      if (!targetId) {
        return;
      }
      const target = document.getElementById(targetId);
      if (!target) {
        return;
      }
      const text = target.innerText.trim();
      try {
        await navigator.clipboard.writeText(text);
        const original = button.textContent;
        button.textContent = "Copied";
        window.setTimeout(() => {
          button.textContent = original;
        }, 1400);
      } catch (error) {
        console.error("Failed to copy prompt", error);
        button.textContent = "Copy failed";
        window.setTimeout(() => {
          button.textContent = "Copy";
        }, 1400);
      }
    });
  }
});
