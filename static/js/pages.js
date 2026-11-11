/* Overview, DFA transition table, Dataset and About pages. */
"use strict";

/* ===================== Overview ===================== */
PS.pages.overview = {
  async init() {
    const m = PS.meta;
    PS.$("#ov-cats").textContent = m.categories.length;
    PS.$("#ov-nfa").textContent = m.nfa_states;
    PS.$("#ov-dfa").textContent = m.dfa_states;
    const list = PS.clear(PS.$("#ov-patterns"));
    m.categories.forEach((c) => {
      const lits = m.patterns.filter((p) => p.category === c).map((p) => `“${p.literal}”`).join(" or ");
      list.append(PS.el("div", { class: "pattern-row" }, PS.el("strong", { text: c }), PS.el("span", { class: "mono", text: lits })));
    });
    list.append(PS.el("p", { class: "hint", text: "Case-insensitive literal substring matching. Each category scores at most one point." }));
    const [ng, dg] = await Promise.all([PS.getGraph("nfa"), PS.getGraph("dfa")]);
    this.nfaView = new PS.GraphView(PS.$("#ov-nfa-graph"), ng, { interactive: false, tools: false });
    this.dfaView = new PS.GraphView(PS.$("#ov-dfa-graph"), dg, { interactive: false, tools: false, curve: 0.15 });
    this.dfaView.setEdgeFilter((e) => e.forward);
  },
  async show() {
    const s = (await PS.api("/api/stats")).stats;
    PS.$("#ov-total").textContent = s.total;
    PS.$("#ov-spam").textContent = s.spam;
    PS.$("#ov-safe").textContent = s.safe;
    const box = PS.clear(PS.$("#ov-recent"));
    box.classList.toggle("empty", s.recent.length === 0);
    if (!s.recent.length) { box.textContent = "No emails scanned yet in this session."; }
    s.recent.forEach((r) => box.append(PS.el("div", { class: "recent-item" },
      PS.el("span", { text: `${r.time} · ${r.label || "scan"} · ${r.length} chars` }),
      PS.el("span", { class: "verdict-tag " + (r.verdict === "SAFE" ? "safe" : "spam"), text: `${r.verdict} ${r.score}/5` }))));
    if (this.nfaView) requestAnimationFrame(() => { this.nfaView.fit(); this.dfaView.fit(); });
  },
};

/* ===================== DFA transition table ===================== */
PS.pages.table = {
  async init() {
    this.data = await PS.api("/api/dfa/table");
    ["tt-search", "tt-accepting", "tt-subset"].forEach((id) => PS.$("#" + id).addEventListener("input", () => this.render()));
    PS.$("#tt-copy").addEventListener("click", () => PS.copy(this.tsv()));
    this.render();
  },
  visibleRows() {
    const q = PS.$("#tt-search").value.trim().toLowerCase();
    const onlyAcc = PS.$("#tt-accepting").checked;
    return this.data.rows.filter((r) => (!onlyAcc || r.is_accepting)
      && (!q || r.state.toLowerCase().includes(q) || r.nfa_subset.some((s) => s.toLowerCase() === q)));
  },
  columns() { return this.data.alphabet; },
  render() {
    const rows = this.visibleRows();
    const showSubset = PS.$("#tt-subset").checked;
    const head = ["DFA state", "Start", "Accepting"].concat(showSubset ? ["NFA subset"] : [], this.columns().map((s) => PS.data_label(this.data, s)));
    const table = PS.clear(PS.$("#tt-table"));
    table.append(PS.el("thead", {}, PS.el("tr", {}, head.map((h) => PS.el("th", { text: h })))));
    const body = PS.el("tbody", {});
    rows.forEach((r) => body.append(PS.el("tr", {},
      PS.el("td", { class: "mono", text: r.state }), PS.el("td", { text: r.is_start ? "→" : "" }), PS.el("td", { text: r.is_accepting ? "✓" : "" }),
      showSubset ? PS.el("td", { class: "mono", text: r.nfa_subset.join(" ") }) : null,
      this.columns().map((s) => PS.el("td", { class: "mono", text: r.transitions[s] })))));
    table.append(body);
    PS.$("#tt-count").textContent = `${rows.length} of ${this.data.rows.length} states · ${this.columns().length} symbol classes`;
    if (!rows.length) body.append(PS.el("tr", {}, PS.el("td", { colspan: head.length, text: "No states match the filter." })));
  },
  tsv() {
    const rows = this.visibleRows(), showSubset = PS.$("#tt-subset").checked;
    const head = ["state", "start", "accepting"].concat(showSubset ? ["nfa_subset"] : [], this.columns().map((s) => PS.data_label(this.data, s)));
    const lines = [head.join("\t")];
    rows.forEach((r) => lines.push([r.state, r.is_start, r.is_accepting].concat(showSubset ? [r.nfa_subset.join(" ")] : [], this.columns().map((s) => r.transitions[s])).join("\t")));
    return lines.join("\n");
  },
};
PS.data_label = (data, sym) => data.alphabet_labels[sym] || sym;

/* ===================== Dataset ===================== */
PS.pages.dataset = {
  async init() {
    this.emails = (await PS.api("/api/dataset")).emails;
    PS.$("#ds-filter").addEventListener("change", () => this.renderList());
    PS.$("#ds-scan-all").addEventListener("click", () => this.scanAll());
    this.renderList();
  },
  renderList() {
    const f = PS.$("#ds-filter").value;
    const list = PS.clear(PS.$("#ds-list"));
    this.emails.filter((e) => !f || e.expected_verdict === f).forEach((e) => {
      const li = PS.el("li", { tabindex: "0", "data-id": e.id, onclick: () => this.select(e.id), onkeydown: (ev) => { if (ev.key === "Enter") this.select(e.id); } },
        PS.el("span", { text: `#${e.id} ${e.subject}` }),
        PS.el("span", { class: "verdict-tag " + (e.expected_verdict === "SAFE" ? "safe" : "spam"), text: e.expected_verdict }));
      if (this.current === e.id) li.classList.add("sel");
      list.append(li);
    });
  },
  select(id) {
    this.current = id;
    this.renderList();
    const e = this.emails.find((x) => x.id === id);
    const box = PS.clear(PS.$("#ds-preview"));
    box.append(PS.el("h2", { text: `#${e.id} ${e.subject}` }), PS.el("p", { class: "hint", text: e.note }),
      PS.scanner.highlighted(e.text, []),
      PS.el("p", { class: "hint", text: `Expected: ${e.expected_categories.join(", ") || "no categories"} → ${e.expected_verdict}` }),
      PS.el("div", { class: "row wrap gap" },
        PS.el("button", { class: "btn small", onclick: () => this.scanOne(e, "nfa"), text: "Run NFA" }),
        PS.el("button", { class: "btn small", onclick: () => this.scanOne(e, "dfa"), text: "Run DFA" }),
        PS.el("button", { class: "btn small primary", onclick: () => this.scanOne(e, "both"), text: "Compare Both" }),
        PS.el("button", { class: "btn small", onclick: () => this.openInScanner(e.text), text: "Open in scanner" })),
      PS.el("div", { id: "ds-one" }));
  },
  async openInScanner(text) {
    location.hash = "#scanner";
    // the scanner page initialises lazily; wait for its textarea to exist and fill it
    for (let i = 0; i < 50 && !(PS.scanner.input); i++) await new Promise((r) => setTimeout(r, 40));
    if (PS.scanner.input) { PS.scanner.input.value = text; PS.scanner.onInputChange(); }
  },
  async scanOne(e, engine) {
    try {
      const r = (await PS.api("/api/scan", { json: { text: e.text, engine } })).result;
      const out = PS.clear(PS.$("#ds-one"));
      out.append(PS.el("div", { class: "verdict", style: "margin-top:12px" }, PS.verdictBadge(r.verdict), PS.el("strong", { text: `${r.score}/5` }),
        PS.el("span", { class: "hint", text: `NFA ${PS.fmtUs(r.nfa_time_us)} · DFA ${PS.fmtUs(r.dfa_time_us)}${r.equivalent === null ? "" : r.equivalent ? " · equivalent" : " · MISMATCH"}` })),
        PS.scanner.highlighted(e.text, r.occurrences),
        PS.el("p", { text: r.explanation }));
    } catch (err) { PS.fail(err); }
  },
  async scanAll() {
    try {
      const results = (await PS.api("/api/dataset/scan", { json: { engine: "both" } })).results;
      const box = PS.$("#ds-results"); box.hidden = false; PS.clear(box);
      const ok = results.filter((r) => r.matches_expectation).length;
      box.append(PS.el("h2", { text: "Full dataset scan" }),
        PS.el("p", {}, PS.el("strong", { text: `${ok} of ${results.length} results agree with the stored expectations.` }),
          ` ${results.filter((r) => r.equivalent).length} of ${results.length} had identical NFA and DFA output.`),
        PS.el("div", { class: "table-wrap" }, PS.el("table", { class: "data" },
          PS.el("thead", {}, PS.el("tr", {}, ["ID", "Subject", "Score", "Verdict", "Categories", "Occurrences", "Expected", "Agrees"].map((h) => PS.el("th", { text: h })))),
          PS.el("tbody", {}, results.map((r) => PS.el("tr", {}, PS.el("td", { text: r.id }), PS.el("td", { text: r.subject }), PS.el("td", { text: `${r.score}/5` }),
            PS.el("td", { text: r.verdict }), PS.el("td", { class: "mono", text: r.matched_categories.join(" ") || "–" }), PS.el("td", { text: r.occurrence_count }),
            PS.el("td", { text: r.expected_verdict }), PS.el("td", { class: r.matches_expectation ? "ok-text" : "bad-text", text: r.matches_expectation ? "yes" : "NO" })))))),
        PS.el("div", { class: "row gap", style: "margin-top:10px" },
          PS.el("button", { class: "btn small", text: "Export JSON", onclick: () => PS.download("dataset_results.json", JSON.stringify(results, null, 2), "application/json") }),
          PS.el("a", { class: "btn small", href: "/api/dataset/export.csv", download: true, text: "Export CSV" })));
    } catch (err) { PS.fail(err); }
  },
};

/* ===================== About ===================== */
PS.pages.about = {
  init() {
    const ul = PS.clear(PS.$("#about-patterns"));
    PS.meta.categories.forEach((c) => {
      const lits = PS.meta.patterns.filter((p) => p.category === c).map((p) => p.literal);
      ul.append(PS.el("li", {}, PS.el("strong", { text: c }), ": ", PS.el("code", { text: lits.join("  |  ") })));
    });
  },
};
