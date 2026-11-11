/* NFA Explorer: real graph + step-by-step simulation from the backend. */
"use strict";

PS.pages.nfa = {
  async init() {
    const graph = await PS.getGraph("nfa");
    this.view = new PS.TraceView(PS.$("#nfa-view"), { engine: "nfa", graph });
    this.renderDefinition();
  },
  show() { if (this.view) requestAnimationFrame(() => this.view.graph.fit()); },

  renderDefinition() {
    const d = PS.meta.nfa_definition;
    const box = PS.clear(PS.$("#nfa-definition"));
    const grid = PS.el("div", { class: "def-grid" });
    const add = (k, v) => grid.append(PS.el("div", {}, PS.el("strong", { text: k + ": " }), v));
    add("N", PS.el("span", { text: "(Q, Σ, δ, q0, F)" }));
    add(`Q (${d.states.length} states)`, PS.el("code", { text: d.states.join(", ") }));
    add(`Σ (${d.alphabet.length} symbols)`, PS.el("code", { text: d.alphabet.map(PS.symLabel).join(", ") }));
    add("OTHER", PS.el("span", { text: "a symbolic class standing for every character not used in any pattern literal; it is not a literal character." }));
    add("δ", PS.el("span", { text: `q0 loops on every symbol of Σ; ${d.epsilon_transitions} ε-transitions lead from q0 to the first state of each pattern branch; each branch then moves one literal character at a time.` }));
    add("q0", PS.el("code", { text: d.start }));
    add("F", PS.el("code", { text: d.accepting.map((a) => `${a.state} (${a.category}: "${a.literal}")`).join("; ") }));
    box.append(grid, PS.el("p", { class: "hint", text: "win and won are separate branches that map to the same category WIN_WON. The match start is computed as end − literal length of the accepting state." }));
  },
};
