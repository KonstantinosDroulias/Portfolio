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

// Accessibility options: text size, contrast, link underlines, spacing, motion. Kept in this browser only.
(() => {
  const root = document.documentElement;
  const panel = document.getElementById("a11y");
  if (!panel) return;
  let prefs = {};
  try { prefs = JSON.parse(localStorage.getItem("a11y") || "{}"); } catch (e) {}
  const attr = (k) => "a11y" + k[0].toUpperCase() + k.slice(1);
  const apply = () => {
    ["size", "contrast", "links", "spacing", "motion"].forEach((k) => {
      if (prefs[k]) root.dataset[attr(k)] = prefs[k]; else delete root.dataset[attr(k)];
    });
    panel.querySelectorAll("[data-pick-size]").forEach((b) => b.setAttribute("aria-pressed", String((prefs.size || "0") === b.dataset.pickSize)));
    panel.querySelectorAll("[data-pick]").forEach((b) => b.setAttribute("aria-pressed", String(!!prefs[b.dataset.pick])));
    try { localStorage.setItem("a11y", JSON.stringify(prefs)); } catch (e) {}
  };
  panel.addEventListener("click", (e) => {
    const size = e.target.closest("[data-pick-size]");
    const toggle = e.target.closest("[data-pick]");
    if (size) prefs.size = size.dataset.pickSize === "0" ? "" : size.dataset.pickSize;
    else if (toggle) prefs[toggle.dataset.pick] = prefs[toggle.dataset.pick] ? "" : "on";
    else if (e.target.closest("[data-pick-reset]")) prefs = {};
    else return;
    apply();
  });
  // Closing from inside the panel: give focus back to the trigger.
  panel.addEventListener("toggle", (e) => { if (e.newState === "closed" && panel.contains(document.activeElement)) document.querySelector(".a11y-btn")?.focus(); });
  apply();
})();

// Cookie notice. Without an analytics ID it's a one-time notice; with one, nothing loads until "Accept".
(() => {
  const bar = document.getElementById("consent");
  if (!bar) return;
  const id = bar.dataset.analytics;
  let choice = null;
  try { choice = localStorage.getItem("consent"); } catch (e) {}
  const loadAnalytics = () => {
    if (!id || window.gtag) return;
    const s = document.createElement("script");
    s.async = true; s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(id);
    document.head.append(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { dataLayer.push(arguments); };
    gtag("js", new Date()); gtag("config", id, { anonymize_ip: true });
  };
  const valid = id ? ["accepted", "rejected"] : ["necessary", "accepted", "rejected"];
  if (!valid.includes(choice)) bar.hidden = false;
  else if (id && choice === "accepted") loadAnalytics();
  bar.addEventListener("click", (e) => {
    const b = e.target.closest("[data-consent]");
    if (!b) return;
    try { localStorage.setItem("consent", b.dataset.consent); } catch (e) {}
    bar.hidden = true;
    if (b.dataset.consent === "accepted") loadAnalytics();
    if (b.dataset.consent === "rejected" && window.gtag) location.reload();
  });
  document.querySelectorAll("[data-consent-open]").forEach((b) => b.addEventListener("click", () => { bar.hidden = false; bar.querySelector("button")?.focus(); }));
})();
