// Admin: Markdown toolbar, preview, image upload, cover preview, unsaved-changes guard.
(() => {
  const csrf = document.querySelector("[name=csrfmiddlewaretoken]")?.value;

  // ----- unsaved changes: explicit Save + Discard + leave prompt -----
  document.querySelectorAll("form[data-guard], #editor").forEach((form) => {
    let dirty = false;
    const discard = form.querySelector("[data-discard]");
    const state = form.querySelector("[data-state]");
    const original = state?.textContent;
    const mark = () => {
      if (dirty) return;
      dirty = true;
      if (discard) discard.hidden = false;
      if (state) { state.textContent = "Unsaved changes"; state.classList.add("is-dirty"); }
    };
    form.addEventListener("input", mark);
    form.addEventListener("change", mark);
    form.addEventListener("submit", () => { dirty = false; });
    discard?.addEventListener("click", () => { dirty = false; });
    addEventListener("beforeunload", (e) => { if (dirty) { e.preventDefault(); e.returnValue = ""; } });
    form.markDirty = mark;
  });

  const editor = document.getElementById("editor");
  if (!editor) return;
  const body = editor.querySelector("#id_body");
  const title = editor.querySelector("#id_title");
  const excerpt = editor.querySelector("#id_excerpt");
  const pane = editor.querySelector("[data-preview-pane]");

  // auto-grow fallbacks for browsers without field-sizing
  if (!CSS.supports("field-sizing", "content")) {
    [title, excerpt].forEach((el) => {
      const fit = () => { el.style.height = "auto"; el.style.height = el.scrollHeight + "px"; };
      el.addEventListener("input", fit); fit();
    });
  }

  // Enter in a one-line field must not submit (the first button may be "Unpublish").
  editor.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && e.target.matches("input:not([type=submit]):not([type=checkbox])")) e.preventDefault();
  });

  // ----- word count -----
  const words = editor.querySelector("[data-words]");
  const minutes = editor.querySelector("[data-minutes]");
  const count = () => {
    const n = (body.value.replace(/```[\s\S]*?```/g, " ").match(/\w+/g) || []).length;
    words.textContent = `${n.toLocaleString()} word${n === 1 ? "" : "s"}`;
    minutes.textContent = `${Math.max(1, Math.ceil(n / 200))} min read`;
  };
  body.addEventListener("input", count); count();

  // ----- toolbar -----
  const wrap = (before, after = before, placeholder = "text") => {
    const { selectionStart: s, selectionEnd: e, value } = body;
    const sel = value.slice(s, e) || placeholder;
    body.setRangeText(before + sel + after, s, e, "end");
    body.selectionStart = s + before.length; body.selectionEnd = s + before.length + sel.length;
    body.focus(); body.dispatchEvent(new Event("input", { bubbles: true }));
  };
  const linePrefix = (prefix) => {
    const { selectionStart: s, selectionEnd: e, value } = body;
    const start = value.lastIndexOf("\n", s - 1) + 1;
    const block = value.slice(start, e).split("\n").map((l) => prefix + l.replace(/^(#{1,6} |> |- )/, "")).join("\n");
    body.setRangeText(block, start, e, "end");
    body.focus(); body.dispatchEvent(new Event("input", { bubbles: true }));
  };
  const insert = (text) => {
    const { selectionStart: s, selectionEnd: e, value } = body;
    const pre = s > 0 && value[s - 1] !== "\n" ? "\n\n" : "";
    body.setRangeText(pre + text + "\n", s, e, "end");
    body.focus(); body.dispatchEvent(new Event("input", { bubbles: true }));
  };
  const actions = {
    h2: () => linePrefix("## "), h3: () => linePrefix("### "),
    bold: () => wrap("**"), italic: () => wrap("_"),
    link: () => {
      const url = prompt("Link address (https://…)");
      if (url) wrap("[", `](${url})`, "link text");
    },
    ul: () => linePrefix("- "), quote: () => linePrefix("> "),
    code: () => wrap("```\n", "\n```", "code"),
    image: () => editor.querySelector("[data-image-input]").click(),
  };
  editor.querySelectorAll("[data-md]").forEach((b) => b.addEventListener("click", () => actions[b.dataset.md]()));
  body.addEventListener("keydown", (e) => {
    if (!(e.metaKey || e.ctrlKey)) return;
    const k = e.key.toLowerCase();
    if (k === "b") { e.preventDefault(); actions.bold(); }
    else if (k === "i") { e.preventDefault(); actions.italic(); }
    else if (k === "k") { e.preventDefault(); actions.link(); }
    else if (k === "s") { e.preventDefault(); editor.querySelector("[data-save]:last-of-type")?.click(); }
  });

  // ----- image upload (button, drop, paste) -----
  const upload = async (file) => {
    if (!file || !file.type.startsWith("image/")) return;
    const marker = `![Uploading ${file.name}…]()`;
    insert(marker);
    const data = new FormData();
    data.append("file", file);
    try {
      const res = await fetch(editor.dataset.upload, { method: "POST", body: data, headers: { "X-CSRFToken": csrf } });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || "Upload failed");
      const alt = file.name.replace(/\.[^.]+$/, "").replace(/[-_]+/g, " ");
      body.value = body.value.replace(marker, `![${alt}](${json.url} "Caption")`);
    } catch (err) {
      body.value = body.value.replace(marker, "");
      alert(err.message);
    }
    body.dispatchEvent(new Event("input", { bubbles: true }));
  };
  editor.querySelector("[data-image-input]").addEventListener("change", (e) => { [...e.target.files].forEach(upload); e.target.value = ""; });
  body.addEventListener("dragover", (e) => { e.preventDefault(); body.classList.add("is-drop"); });
  body.addEventListener("dragleave", () => body.classList.remove("is-drop"));
  body.addEventListener("drop", (e) => {
    body.classList.remove("is-drop");
    const files = [...(e.dataTransfer?.files || [])].filter((f) => f.type.startsWith("image/"));
    if (files.length) { e.preventDefault(); files.forEach(upload); }
  });
  body.addEventListener("paste", (e) => {
    const files = [...(e.clipboardData?.files || [])].filter((f) => f.type.startsWith("image/"));
    if (files.length) { e.preventDefault(); files.forEach(upload); }
  });

  // ----- preview -----
  editor.querySelectorAll("[data-tab]").forEach((tab) => tab.addEventListener("click", async () => {
    const preview = tab.dataset.tab === "preview";
    editor.querySelectorAll("[data-tab]").forEach((t) => t.setAttribute("aria-selected", String(t === tab)));
    editor.querySelector(".md__tools").hidden = preview;
    body.hidden = preview; pane.hidden = !preview;
    if (preview) {
      pane.innerHTML = '<p class="muted">Rendering…</p>';
      const data = new FormData(); data.append("body", body.value);
      const res = await fetch(editor.dataset.preview, { method: "POST", body: data, headers: { "X-CSRFToken": csrf } });
      pane.innerHTML = (await res.json()).html || '<p class="muted">Nothing to preview yet.</p>';
    }
  }));

  // ----- cover preview -----
  const coverInput = editor.querySelector("[data-cover-input]");
  const coverImg = editor.querySelector("[data-cover-img]");
  const coverEmpty = editor.querySelector("[data-cover-empty]");
  coverInput.addEventListener("change", () => {
    const f = coverInput.files[0];
    if (!f) return;
    coverImg.src = URL.createObjectURL(f); coverImg.hidden = false; coverEmpty.hidden = true;
    const rm = editor.querySelector("[data-remove-cover]"); if (rm) rm.checked = false;
  });
  editor.querySelector("[data-remove-cover]")?.addEventListener("change", (e) => {
    coverImg.hidden = e.target.checked; coverEmpty.hidden = !e.target.checked;
  });

  // ----- search snippet -----
  const seoT = editor.querySelector("#id_seo_title"), seoD = editor.querySelector("#id_seo_description");
  const serpT = editor.querySelector("[data-serp-title]"), serpD = editor.querySelector("[data-serp-desc]");
  const serp = () => {
    serpT.textContent = seoT.value || (title.value ? `${title.value} — Konstantinos Droulias` : "Post title");
    serpD.textContent = (seoD.value || excerpt.value || "The summary shows here.").slice(0, 170);
  };
  [seoT, seoD, title, excerpt].forEach((el) => el.addEventListener("input", serp)); serp();

  // Publish on a draft with an old date: publish now.
  editor.querySelector("[data-publish]")?.addEventListener("click", () => {
    const h = document.createElement("input"); h.type = "hidden"; h.name = "publish_now"; h.value = "1";
    const d = editor.querySelector("#id_published_at");
    if (d.value && new Date(d.value) > new Date()) return; // scheduled
    editor.append(h);
  });
})();
