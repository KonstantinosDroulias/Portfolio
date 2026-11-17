// Show/hide eye on every password field.
(() => {
  const eye = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>';
  const eyeOff = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="square"><path d="M3 3l18 18M10.6 5.1A10.9 10.9 0 0 1 12 5c6.4 0 10 7 10 7a17.7 17.7 0 0 1-3.2 4.2M6.6 6.6C3.8 8.5 2 12 2 12s3.6 7 10 7a10 10 0 0 0 5.4-1.6M9.9 9.9a3 3 0 0 0 4.2 4.2"/></svg>';
  document.querySelectorAll('input[type="password"]').forEach((input) => {
    const wrap = document.createElement("div");
    wrap.className = "pw";
    input.before(wrap);
    wrap.append(input);
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "pw__eye";
    btn.setAttribute("aria-label", "Show password");
    btn.setAttribute("aria-pressed", "false");
    btn.innerHTML = eye;
    btn.addEventListener("click", () => {
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.innerHTML = show ? eyeOff : eye;
      btn.setAttribute("aria-pressed", String(show));
      btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
      input.focus({ preventScroll: true });
    });
    input.form?.addEventListener("submit", () => { input.type = "password"; });
    wrap.append(btn);
  });
})();

// Live checks on new-password fields: 8+ characters, upper, lower, number, both match.
(() => {
  const fields = [...document.querySelectorAll('input[autocomplete="new-password"]')];
  if (!fields.length) return;
  const main = fields.find((f) => !/2$/.test(f.name)) || fields[0];
  const confirm = fields.find((f) => f !== main);

  const list = document.createElement("ul");
  list.className = "pw-checks";
  list.setAttribute("aria-live", "polite");
  const rules = [
    ["At least 8 characters", (v) => v.length >= 8],
    ["One uppercase letter", (v) => /\p{Lu}/u.test(v)],
    ["One lowercase letter", (v) => /\p{Ll}/u.test(v)],
    ["One number", (v) => /\d/.test(v)],
  ].map(([text, test]) => ({ li: item(text), test }));
  const match = confirm ? item("Both passwords match") : null;
  main.closest(".pw").after(list);

  function item(text) {
    const li = document.createElement("li");
    li.dataset.state = "idle";
    li.innerHTML = `<span class="pw-checks__box" aria-hidden="true"></span><span>${text}</span><span class="visually-hidden" data-sr></span>`;
    list.append(li);
    return li;
  }
  const set = (li, state) => {
    li.dataset.state = state;
    li.querySelector("[data-sr]").textContent = state === "ok" ? " (done)" : state === "bad" ? " (not yet)" : "";
  };
  const run = () => {
    const v = main.value;
    rules.forEach(({ li, test }) => set(li, !v ? "idle" : test(v) ? "ok" : "bad"));
    if (match) set(match, !confirm.value ? "idle" : confirm.value === v ? "ok" : "bad");
  };
  main.addEventListener("input", run);
  confirm?.addEventListener("input", run);
})();
