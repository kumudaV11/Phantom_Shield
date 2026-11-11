/* PHANTOM SHIELD — core helpers: API, DOM builder, toasts, router, step player. */
"use strict";

const PS = {
  meta: null,
  pages: {},      // name -> { init(), show() }
  _inited: {},
};

/* ---------- DOM helper: strings become text nodes, never HTML ---------- */
PS.el = function (tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value === true ? "" : value);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
};
PS.$ = (sel, root) => (root || document).querySelector(sel);
PS.$$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));
PS.clear = (node) => { while (node.firstChild) node.removeChild(node.firstChild); return node; };

/* ---------- API ---------- */
PS.api = async function (path, options) {
  const opts = Object.assign({ headers: {} }, options || {});
  if (opts.json !== undefined) {
    opts.method = opts.method || "POST";
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(opts.json);
    delete opts.json;
  }
  let response;
  try {
    response = await fetch(path, opts);
  } catch (err) {
    PS.setEngine(false);
    throw new Error("Cannot reach the local engine. Is the Flask server running?");
  }
  let data = null;
  try { data = await response.json(); } catch (err) { /* non-JSON */ }
  if (!response.ok || !data || data.ok === false) {
    throw new Error((data && data.error) || `Request failed (${response.status}).`);
  }
  return data;
};

PS.toast = function (message, kind) {
  const box = PS.$("#toasts");
  const node = PS.el("div", { class: "toast " + (kind || ""), role: "status", text: message });
  box.append(node);
  setTimeout(() => node.remove(), 4500);
};
PS.fail = (err) => PS.toast(err.message || String(err), "error");

PS.setEngine = function (ok) {
  const box = PS.$("#engine-status");
  box.classList.toggle("ok", ok);
  box.classList.toggle("bad", !ok);
  PS.$("#engine-text").textContent = ok ? "Local engine ready" : "Engine offline";
};

/* ---------- display helpers ---------- */
PS.showChar = function (ch) {
  if (ch === " ") return "␣";
  if (ch === "\n") return "↵";
  if (ch === "\r") return "⏎";
  if (ch === "\t") return "⇥";
  return ch;
};
PS.symLabel = (sym) => (PS.meta && PS.meta.alphabet_labels[sym]) || sym;
PS.fmtUs = (us) => (us === null || us === undefined ? "–" : us >= 1000 ? (us / 1000).toFixed(2) + " ms" : us.toFixed(1) + " µs");
PS.verdictBadge = (verdict) =>
  PS.el("span", { class: "badge " + (verdict === "SAFE" ? "safe" : "spam"), text: verdict });
PS.download = function (filename, text, type) {
  const url = URL.createObjectURL(new Blob([text], { type: type || "text/plain" }));
  const a = PS.el("a", { href: url, download: filename });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};
PS.copy = async function (text) {
  try { await navigator.clipboard.writeText(text); PS.toast("Copied to clipboard.", "success"); }
  catch (err) {
    const ta = PS.el("textarea", { style: "position:fixed;left:-999px" });
    ta.value = text; document.body.append(ta); ta.select();
    try { document.execCommand("copy"); PS.toast("Copied to clipboard.", "success"); }
    catch (e2) { PS.toast("Copy failed in this browser.", "error"); }
    ta.remove();
  }
};

/* ---------- Step player (Next / Previous / Play / Pause / Reset) ---------- */
PS.Player = class {
  constructor(root, options) {
    this.root = root;
    this.onStep = options.onStep;
    this.getInterval = options.getInterval || (() => 700);
    this.count = 0;
    this.index = 0;
    this.timer = null;
    root.addEventListener("click", (event) => {
      const btn = event.target.closest("[data-act]");
      if (btn && root.contains(btn)) this[btn.dataset.act]();
    });
  }
  setCount(n) { this.pause(); this.count = n; this.index = 0; this._update(); }
  goto(i) {
    if (this.count === 0) return;
    this.index = Math.max(0, Math.min(this.count - 1, i));
    this._update();
  }
  next() { if (this.index < this.count - 1) this.goto(this.index + 1); else this.pause(); }
  prev() { this.goto(this.index - 1); }
  reset() { this.pause(); this.goto(0); }
  play() {
    if (this.count === 0 || this.timer) return;
    if (this.index >= this.count - 1) this.index = 0;
    const tick = () => {
      if (this.index >= this.count - 1) { this.pause(); return; }
      this.goto(this.index + 1);
      this.timer = setTimeout(tick, this.getInterval());
    };
    this.timer = setTimeout(tick, 0);
  }
  pause() { if (this.timer) { clearTimeout(this.timer); this.timer = null; } }
  _update() { if (this.count > 0) this.onStep(this.index); }
};

/* ---------- router ---------- */
PS.go = function (name) {
  if (!PS.$("#page-" + name)) name = "overview";
  PS.$$(".page").forEach((p) => { p.hidden = p.id !== "page-" + name; });
  PS.$$("[data-nav]").forEach((a) => a.classList.toggle("active", a.dataset.nav === name));
  PS.$("#page-title").textContent = PS.$("#page-" + name).dataset.title;
  const page = PS.pages[name];
  if (page) {
    if (!PS._inited[name]) { PS._inited[name] = true; Promise.resolve(page.init && page.init()).catch(PS.fail); }
    if (page.show) Promise.resolve(page.show()).catch(PS.fail);
  }
  if (window.innerWidth <= 900) PS.$("#shell").classList.add("collapsed");
};

PS.start = async function () {
  const shell = PS.$("#shell");
  const toggle = PS.$("#sidebar-toggle");
  if (window.innerWidth <= 900) shell.classList.add("collapsed");
  toggle.addEventListener("click", () => {
    shell.classList.toggle("collapsed");
    toggle.setAttribute("aria-expanded", String(!shell.classList.contains("collapsed")));
  });
  window.addEventListener("hashchange", () => PS.go(location.hash.slice(1)));
  try {
    PS.meta = (await PS.api("/api/meta")).meta;
    PS.setEngine(true);
  } catch (err) {
    PS.setEngine(false);
    PS.fail(err);
  }
  PS.go(location.hash.slice(1) || "overview");
};
