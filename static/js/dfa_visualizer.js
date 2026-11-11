/* DFA Explorer: real subset-construction DFA, state search, details, simulation. */
"use strict";

PS.pages.dfa = {
  async init() {
    const graph = await PS.getGraph("dfa");
    this.graphData = graph;
    const root = PS.clear(PS.$("#dfa-view"));
    this.search = PS.el("input", { type: "search", placeholder: "Search state (D12) or NFA state (q5)…", "aria-label": "Search DFA states" });
    this.hint = PS.el("span", { class: "hint" });
    const toggle = PS.el("input", { type: "checkbox", id: "dfa-return" });
    toggle.addEventListener("change", () => this.view.graph.setEdgeFilter((e) => toggle.checked || e.forward));
    root.append(PS.el("div", { class: "row wrap gap", style: "margin-bottom:10px" }, this.search,
      PS.el("label", { class: "inline" }, toggle, " Show fallback edges (transitions back to earlier states)"), this.hint,
      PS.el("span", { class: "hint", text: "Hidden edges still exist in the DFA; the Transition Table lists every transition." })));
    const holder = PS.el("div", {});
    root.append(holder);
    this.view = new PS.TraceView(holder, { engine: "dfa", graph, graphOptions: { curve: 0.15 }, onSelect: (id) => this.details(id) });
    this.view.graph.setEdgeFilter((e) => e.forward);
    this.search.addEventListener("input", () => this.find(this.search.value));
    this.search.addEventListener("keydown", (e) => { if (e.key === "Enter") this.find(this.search.value); });
  },
  show() { if (this.view) requestAnimationFrame(() => this.view.graph.fit()); },

  find(query) {
    const q = query.trim().toLowerCase();
    if (!q) { this.hint.textContent = ""; return; }
    const hit = this.graphData.nodes.find((n) => n.id.toLowerCase() === q)
      || this.graphData.nodes.find((n) => n.subset.some((s) => s.toLowerCase() === q));
    if (!hit) { this.hint.textContent = "No matching state."; return; }
    this.hint.textContent = `Found ${hit.id}`;
    this.view.graph.select(hit.id); this.view.graph.centerOn(hit.id); this.details(hit.id);
  },

  details(id) {
    const node = this.graphData.nodes.find((n) => n.id === id);
    if (!node) return;
    const box = PS.clear(PS.$("#dfa-details"));
    box.classList.remove("empty");
    box.append(PS.el("h3", { text: `${node.id}${node.start ? " (start)" : ""}${node.accepting ? " (accepting)" : ""}` }),
      PS.el("p", {}, "Underlying NFA subset: ", PS.el("span", { class: "chips" }, node.subset.map((s) => PS.el("span", { class: "chip", text: s })))));
    if (node.categories.length) box.append(PS.el("p", { text: "Recognises: " + node.categories.join(", ") }));
    const out = this.graphData.edges.filter((e) => e.from === id);
    box.append(PS.el("div", { class: "table-wrap" }, PS.el("table", { class: "data" },
      PS.el("thead", {}, PS.el("tr", {}, ["Destination", "On symbols"].map((h) => PS.el("th", { text: h })))),
      PS.el("tbody", {}, out.map((e) => PS.el("tr", {}, PS.el("td", { class: "mono", text: e.to }),
        PS.el("td", { class: "mono", text: e.symbols.map(PS.symLabel).join(", ") })))))));
  },
};
