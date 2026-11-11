/* Email Scanner page + live demonstration mode. All results come from the backend. */
"use strict";

PS.scanner = {
  lastText: null,
  lastResult: null,
  views: {},
  batch: [],
  busy: false,
};

PS.pages.scanner = {
  async init() {
    const S = PS.scanner;
    const $ = (id) => PS.$("#" + id);
    S.input = $("sc-input");

    // threshold + example choices
    const th = $("sc-threshold");
    for (let i = PS.meta.min_threshold; i <= PS.meta.max_threshold; i++) {
      th.append(PS.el("option", { value: i, text: `${i} or more`, selected: i === PS.meta.default_threshold }));
    }
    $("sc-delim").textContent = PS.meta.email_delimiter;
    const ex = $("sc-example");
    S.examples = [
      { label: "Spec example: WON a FREE iPhone", text: "Congratulations! You have WON a FREE iPhone. Click here now!" },
      { label: "Spec example: meeting roadmap", text: "Meeting at 3pm tomorrow to discuss the project roadmap." },
    ];
    try {
      const ds = (await PS.api("/api/dataset")).emails;
      ds.forEach((e) => S.examples.push({ label: `Dataset #${e.id}: ${e.subject}`, text: e.text }));
    } catch (err) { PS.fail(err); }
    S.examples.forEach((e, i) => ex.append(PS.el("option", { value: i, text: e.label })));

    $("sc-load").addEventListener("click", () => { S.input.value = S.examples[Number(ex.value)].text; S.onInputChange(); S.input.focus(); });
    $("sc-clear").addEventListener("click", () => { S.input.value = ""; S.onInputChange(); S.input.focus(); });
    $("sc-reset").addEventListener("click", () => S.resetResults());
    $("sc-analyze").addEventListener("click", () => S.run("both", "input"));
    $("sc-run-nfa").addEventListener("click", () => S.run("nfa", "input"));
    $("sc-run-dfa").addEventListener("click", () => S.run("dfa", "input"));
    $("sc-compare").addEventListener("click", () => S.run("both", "compare"));
    S.input.addEventListener("input", () => S.onInputChange());
    $("sc-upload").addEventListener("click", () => $("sc-file").click());
    $("sc-file").addEventListener("change", (ev) => S.upload(ev.target.files[0]).finally(() => { ev.target.value = ""; }));
    $("sc-batch-all").addEventListener("click", () => S.scanBatch());
    $("sc-demo-toggle").addEventListener("click", () => S.toggleDemo());
    PS.$$("#sc-tabs button").forEach((b) => b.addEventListener("click", () => S.tab(b.dataset.tab)));
    $("sc-show-states").addEventListener("click", () => S.loadTrace("nfa", true));
    $("sc-step-nfa").addEventListener("click", () => S.loadTrace("nfa", false));
    $("sc-step-dfa").addEventListener("click", () => S.loadTrace("dfa", false));

    // trace views (graphs come from the real automata)
    const [ng, dg] = await Promise.all([PS.getGraph("nfa"), PS.getGraph("dfa")]);
    S.views.nfa = new PS.TraceView($("sc-nfa-view"), { engine: "nfa", graph: ng, withInput: false });
    S.views.dfa = new PS.TraceView($("sc-dfa-view"), { engine: "dfa", graph: dg, withInput: false, graphOptions: { curve: 0.15 } });
    S.views.dfa.graph.setEdgeFilter((e) => e.forward);
  },
  show() {
    // graphs are laid out while hidden on first init, so refit when the page is visible
    const S = PS.scanner;
    requestAnimationFrame(() => Object.values(S.views).forEach((v) => v.graph.fit()));
  },
};

Object.assign(PS.scanner, {
  tab(name) {
    PS.$$("#sc-tabs button").forEach((b) => {
      const on = b.dataset.tab === name;
      b.classList.toggle("active", on); b.setAttribute("aria-selected", String(on));
    });
    PS.$$("[id^=sc-tab-]").forEach((p) => { p.hidden = p.id !== "sc-tab-" + name; });
    if (name === "nfa" || name === "dfa") requestAnimationFrame(() => this.views[name] && this.views[name].graph.fit());
  },

  threshold() { return Number(PS.$("#sc-threshold").value); },

  /* Any edit makes old results stale: never show them against new input. */
  onInputChange() {
    if (this.lastText !== null && this.input.value !== this.lastText) {
      this.resetResults(true);
    }
  },

  resetResults(stale) {
    this.lastText = null; this.lastResult = null;
    PS.$("#sc-results").hidden = true; PS.clear(PS.$("#sc-results"));
    const empty = PS.$("#sc-empty");
    empty.hidden = false;
    empty.textContent = stale ? "The input changed. Run an analysis to see fresh results." : "Run an analysis to see the verdict, matched patterns and positions.";
    PS.clear(PS.$("#sc-compare-body")).append(PS.el("div", { class: "empty", text: "Use “Compare Both” to run NFA and DFA on the current email." }));
    PS.clear(PS.$("#sc-perf-body")).append(PS.el("div", { class: "empty", text: "Use “Compare Both” to see timings for the current email." }));
    ["nfa", "dfa"].forEach((k) => {
      const v = this.views[k];
      if (v) { v.player.pause(); v.steps = []; v.graph.clearHighlight(); PS.clear(v.strip); PS.clear(v.logWrap); PS.clear(v.card).append(PS.el("span", { class: "hint", text: "No trace loaded for the current input." })); v.counter.textContent = ""; }
    });
    if (!stale) PS.toast("Results reset.");
  },

  async run(engine, tab) {
    if (this.busy) return;
    this.busy = true;
    const text = this.input.value;
    PS.$("#sc-empty").hidden = true; PS.$("#sc-results").hidden = true; PS.$("#sc-scanning").hidden = false;
    const started = performance.now();
    try {
      const data = await PS.api("/api/scan", { json: { text, engine, threshold: this.threshold() } });
      const wait = 350 - (performance.now() - started);       // brief visual only; result is the real one
      if (wait > 0) await new Promise((r) => setTimeout(r, wait));
      this.lastText = text; this.lastResult = data.result;
      this.render(data.result, text);
      this.renderCompare(data.result);
      this.tab(tab);
      if (!text.trim()) PS.toast("The input was empty, so nothing could match.");
    } catch (err) {
      PS.$("#sc-empty").hidden = false;
      PS.fail(err);
    } finally {
      PS.$("#sc-scanning").hidden = true; this.busy = false;
    }
  },

  /* Highlighted text built from DOM nodes (no innerHTML) */
  highlighted(text, occurrences) {
    const cats = PS.meta.categories;
    const cps = Array.from(text);             // Python indices count code points, not UTF-16 units
    const points = new Set([0, cps.length]);
    occurrences.forEach((o) => { points.add(o.start); points.add(o.end); });
    const sorted = Array.from(points).sort((a, b) => a - b);
    const box = PS.el("div", { class: "email-view", tabindex: "0", "aria-label": "Email text with matches highlighted" });
    for (let i = 0; i < sorted.length - 1; i++) {
      const a = sorted[i], b = sorted[i + 1];
      if (a === b) continue;
      const covering = occurrences.filter((o) => o.start <= a && o.end >= b);
      const piece = cps.slice(a, b).join("");
      if (!covering.length) { box.append(document.createTextNode(piece)); continue; }
      const idx = cats.indexOf(covering[0].category) % 5;
      box.append(PS.el("mark", { class: `hit c${idx}`, title: covering.map((o) => o.category).join(", "), text: piece }));
    }
    if (!cps.length) box.append(PS.el("span", { class: "hint", text: "(empty input)" }));
    return box;
  },

  render(r, text) {
    const root = PS.clear(PS.$("#sc-results"));
    root.hidden = false;
    const meter = PS.el("div", { class: "score-meter" + (r.verdict === "SAFE" ? "" : " spam-score"), "aria-label": `Score ${r.score} of 5` });
    for (let i = 0; i < 5; i++) meter.append(PS.el("i", { class: i < r.score ? "on" : "" }));
    root.append(PS.el("div", { class: "verdict" }, PS.verdictBadge(r.verdict),
      PS.el("strong", { text: `Score ${r.score} / ${r.max_score}` }), meter,
      PS.el("span", { class: "hint", text: `threshold ${r.threshold}` })));
    root.append(PS.el("h3", { text: "Matched categories" }),
      r.matched_categories.length
        ? PS.el("div", { class: "chips" }, r.matched_categories.map((c) => PS.el("span", { class: "chip active", text: c })))
        : PS.el("p", { class: "hint", text: "None" }));
    root.append(PS.el("h3", { text: "Highlighted email" }), this.highlighted(text, r.occurrences));
    root.append(PS.el("h3", { text: `Occurrences (${r.occurrences.length})` }));
    if (r.occurrences.length) {
      root.append(PS.el("div", { class: "table-wrap" }, PS.el("table", { class: "data" },
        PS.el("thead", {}, PS.el("tr", {}, ["Category", "Matched text", "Start", "End (excl.)"].map((h) => PS.el("th", { text: h })))),
        PS.el("tbody", {}, r.occurrences.map((o) => PS.el("tr", {},
          PS.el("td", { text: o.category }), PS.el("td", { class: "mono", text: JSON.stringify(o.text) }),
          PS.el("td", { class: "mono", text: o.start }), PS.el("td", { class: "mono", text: o.end })))))));
    } else root.append(PS.el("p", { class: "hint", text: "No occurrences." }));
    root.append(PS.el("div", { class: "row wrap gap", style: "margin-top:10px" },
      PS.el("span", { class: "chip", text: "NFA " + PS.fmtUs(r.nfa_time_us) }),
      PS.el("span", { class: "chip", text: "DFA " + PS.fmtUs(r.dfa_time_us) }),
      r.equivalent === null ? null : PS.el("span", { class: "chip " + (r.equivalent ? "" : "new"), text: r.equivalent ? "NFA ≡ DFA results" : "MISMATCH" })));
    root.append(PS.el("h3", { text: "Why this verdict?" }), PS.el("p", { text: r.explanation }),
      PS.el("p", { class: "hint", text: r.disclaimer }),
      PS.el("div", { class: "row wrap gap" },
        PS.el("button", { class: "btn small", onclick: () => this.loadTrace("nfa", true), text: "Show Matching States" }),
        PS.el("button", { class: "btn small", onclick: () => this.loadTrace("nfa", false), text: "Step Through Automaton" }),
        PS.el("button", { class: "btn small", onclick: () => this.loadTrace("dfa", false), text: "Step Through DFA" })));
  },

  renderCompare(r) {
    const card = (name, time, other) => PS.el("div", { class: "compare-card" }, PS.el("h3", { text: name }),
      time === null ? PS.el("p", { class: "hint", text: "Not run. Use Analyze or Compare Both." }) : [
        PS.el("p", {}, "Time: ", PS.el("strong", { text: PS.fmtUs(time) })),
        PS.el("p", { text: `Occurrences: ${r.occurrences.length}` }),
        PS.el("p", { text: `Categories: ${r.matched_categories.join(", ") || "none"}` })]);
    const body = PS.clear(PS.$("#sc-compare-body"));
    body.append(PS.el("div", { class: "compare-grid" }, card("NFA", r.nfa_time_us), card("DFA", r.dfa_time_us)));
    if (r.equivalent !== null) {
      body.append(PS.el("p", { class: r.equivalent ? "ok-text" : "bad-text",
        text: r.equivalent ? "Both automata reported identical match intervals and categories." : "The automata disagree (this should never happen)." }));
    } else body.append(PS.el("p", { class: "hint", text: "Only one engine was run; use Compare Both to verify equivalence." }));
    const perf = PS.clear(PS.$("#sc-perf-body"));
    if (r.nfa_time_us !== null && r.dfa_time_us !== null) {
      const ratio = r.dfa_time_us > 0 ? r.nfa_time_us / r.dfa_time_us : null;
      perf.append(PS.el("div", { class: "table-wrap" }, PS.el("table", { class: "data" },
        PS.el("thead", {}, PS.el("tr", {}, ["Engine", "Time (single run)", "Characters"].map((h) => PS.el("th", { text: h })))),
        PS.el("tbody", {}, PS.el("tr", {}, PS.el("td", { text: "NFA" }), PS.el("td", { text: PS.fmtUs(r.nfa_time_us) }), PS.el("td", { text: r.length })),
          PS.el("tr", {}, PS.el("td", { text: "DFA" }), PS.el("td", { text: PS.fmtUs(r.dfa_time_us) }), PS.el("td", { text: r.length }))))));
      perf.append(PS.el("p", { class: "hint", text: (ratio ? `NFA/DFA time ratio in this single run: ${ratio.toFixed(2)}. ` : "") + "Single scans are very short and noisy; use the Performance Lab for repeated, warmed-up measurements." }));
    } else perf.append(PS.el("div", { class: "empty", text: "Run “Compare Both” to measure both engines." }));
  },

  /* Trace window: traces are limited in length, so centre on the first match. */
  traceWindow(text) {
    const max = PS.meta.max_trace_chars;
    const cps = Array.from(text);
    if (cps.length <= max) return { text, offset: 0 };
    const first = this.lastResult && this.lastText === text && this.lastResult.occurrences[0];
    const start = first ? Math.max(0, first.start - 40) : 0;
    const end = Math.min(cps.length, start + 160);
    return { text: cps.slice(start, end).join(""), offset: start };
  },

  async loadTrace(engine, jumpToMatch) {
    const text = this.input.value;
    if (!text) { PS.toast("Enter or load an email first.", "error"); return; }
    if (this.lastText !== text) {
      await this.run("both", engine);       // keep results fresh for this input before tracing
      if (this.lastText !== text) return;
    }
    const win = this.traceWindow(text);
    const view = this.views[engine];
    try {
      const note = win.offset || Array.from(win.text).length < Array.from(text).length
        ? `Showing characters ${win.offset}–${win.offset + Array.from(win.text).length} of the email (traces are limited to ${PS.meta.max_trace_chars} characters). Positions below are relative to that window.` : null;
      const trace = await view.load(win.text, note);
      this.tab(engine);
      const first = trace.occurrences[0];
      if (jumpToMatch && first) view.player.goto(first.end);
      else if (jumpToMatch) PS.toast("No matches in this email: nothing to show.");
    } catch (err) { PS.fail(err); }
  },

  /* ----- uploads ----- */
  async upload(file) {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    try {
      const data = await PS.api("/api/upload", { method: "POST", body: fd });
      this.batch = data.emails;
      if (data.count === 1) {
        this.input.value = data.emails[0].text; this.onInputChange();
        PS.$("#sc-batch").hidden = true;
        PS.toast(`Loaded ${data.filename}.`, "success");
      } else {
        this.renderBatch();
        PS.toast(`Parsed ${data.count} emails from ${data.filename}.`, "success");
      }
    } catch (err) { PS.fail(err); }
  },

  renderBatch() {
    PS.$("#sc-batch").hidden = false;
    PS.$("#sc-batch-count").textContent = this.batch.length;
    PS.clear(PS.$("#sc-batch-results"));
    const list = PS.clear(PS.$("#sc-batch-list"));
    this.batch.forEach((e, i) => {
      const label = e.subject || e.text.replace(/\s+/g, " ").slice(0, 48);
      list.append(PS.el("li", { "data-i": i },
        PS.el("span", { text: `${i + 1}. ${label}` }),
        PS.el("span", { class: "row gap" }, PS.el("span", { class: "verdict-tag", "data-slot": "tag", text: "not scanned" }),
          PS.el("button", { class: "btn small", onclick: () => this.pickBatch(i), text: "Load & scan" }))));
    });
  },

  async pickBatch(i) {
    this.input.value = this.batch[i].text;
    this.lastText = null;
    await this.run("both", "input");
  },

  async scanBatch() {
    try {
      const data = await PS.api("/api/scan/batch", { json: { emails: this.batch.map((e) => e.text), threshold: this.threshold() } });
      PS.$$("#sc-batch-list li").forEach((li, i) => {
        const r = data.results[i], tag = PS.$("[data-slot=tag]", li);
        tag.textContent = `${r.verdict} · ${r.score}/5`;
        tag.className = "verdict-tag " + (r.verdict === "SAFE" ? "safe" : "spam");
      });
      PS.toast(`Scanned ${data.results.length} emails.`, "success");
    } catch (err) { PS.fail(err); }
  },

  /* ----- demonstration mode ----- */
  toggleDemo() {
    const on = document.body.classList.toggle("demo");
    const btn = PS.$("#sc-demo-toggle");
    btn.setAttribute("aria-pressed", String(on));
    btn.textContent = on ? "Exit demonstration mode" : "Demonstration mode";
    const head = PS.$("#page-scanner .page-head");
    let reset = PS.$("#sc-demo-reset");
    if (on && !reset) {
      reset = PS.el("button", { class: "btn", id: "sc-demo-reset", text: "Reset Demonstration", onclick: () => {
        this.input.value = ""; this.batch = []; PS.$("#sc-batch").hidden = true; this.resetResults(); this.tab("input");
      } });
      head.append(reset);
    } else if (!on && reset) reset.remove();
    Object.values(this.views).forEach((v) => requestAnimationFrame(() => v.graph.fit()));
  },
});
