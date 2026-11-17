// Theme toggle (pins light/dark over the system preference) + copy-link button.
(() => {
  const meta = document.querySelector('meta[name="color-scheme"]');
  const btn = document.querySelector(".theme-toggle");
  const current = () => {
    if (meta.content === "dark" || meta.content === "light") return meta.content;
    return matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  };
  const sync = () => btn && btn.setAttribute("aria-pressed", String(current() === "dark"));
  sync();
  btn?.addEventListener("click", () => {
    const next = current() === "dark" ? "light" : "dark";
    meta.content = next;
    try { localStorage.setItem("color-scheme", next); } catch (e) {}
    sync();
  });
  addEventListener("storage", (e) => {
    if (e.key === "color-scheme") { meta.content = e.newValue ?? "light dark"; sync(); }
  });
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", sync);

  document.querySelectorAll("[data-copy]").forEach((el) => {
    el.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(el.dataset.copy); } catch (e) { return; }
      el.setAttribute("data-copied", "");
      setTimeout(() => el.removeAttribute("data-copied"), 1600);
    });
  });
})();
