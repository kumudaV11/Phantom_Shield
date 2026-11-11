/* Subset Construction workspace: replays the real algorithm steps from the backend. */
"use strict";

PS.pages.subset = {
  async init() {
    const data = await PS.api("/api/subset/steps");
    this.steps = data.steps;
    const s = data.summary;
    const stats = [["NFA states", s.nfa_states], ["Reachable DFA states", s.dfa_states], ["Accepting DFA states", s.accepting_dfa_states],
      ["DFA transitions", s.transitions], ["Unique subsets", s.unique_subsets], ["Calculation steps", s.calculation_steps]];
    const grid = PS.clear(PS.$("#ss-summary"));
    stats.forEach(([k, v]) => grid.append(PS.el("div", { class: "stat" }, PS.el("span", { class: "stat-label", text: k }), PS.el("strong", { text: String(v) }))));
    this.player = new PS.Player(PS.$("#ss-player"), {
      onStep: (i) => this.render(i), getInterval: () => Number(PS.$("#ss-speed").value),
    });
    PS.$("#ss-next-new").addEventListener("click", () => {
      this.player.pause();
      for (let i = this.player.index + 1; i < this.steps.length; i++) {
        if (this.steps[i].is_new && this.steps[i].kind === "transition") { this.player.goto(i); return; }
      }
      PS.toast("No more new DFA states are created.");
    });
    this.player.setCount(this.steps.length);
  },

  render(i) {
    const s = this.steps[i];
    PS.$("#ss-counter").textContent = `Step ${i + 1} of ${this.steps.length}`;
    const dl = PS.el("dl", {});
    const rows = s.kind === "start"
      ? [["Action", s.text], ["ε-closure of q0", s.nfa_subset.join(", ")], ["DFA start state", s.destination], ["Accepting", s.accepting ? "yes" : "no"]]
      : [["Current DFA state", `${s.dfa_state}  =  { ${s.nfa_subset.join(", ")} }`], ["Input symbol class", PS.symLabel(s.symbol)],
        ["NFA move result", s.move.length ? "{ " + s.move.join(", ") + " }" : "{ } (empty)"], ["ε-closure of result", "{ " + s.closure.join(", ") + " }"],
        ["Destination DFA state", `${s.destination}  (${s.is_new ? "NEW subset, state created" : "existing subset reused"})`],
        ["Destination accepting", s.accepting ? "yes" : "no"]];
    rows.forEach(([k, v]) => dl.append(PS.el("dt", { text: k }), PS.el("dd", { text: v })));
    PS.clear(PS.$("#ss-current")).append(dl);

    // discovered states (re-count when stepping backwards too)
    const found = ["D0"];
    for (let j = 1; j <= i; j++) if (this.steps[j].is_new && this.steps[j].kind === "transition") found.push(this.steps[j].destination);
    const chips = PS.clear(PS.$("#ss-discovered"));
    found.forEach((d, idx) => chips.append(PS.el("span", { class: "chip" + (idx === found.length - 1 && s.is_new ? " new" : ""), text: d })));

    const from = Math.max(0, i - 9);
    const table = PS.clear(PS.$("#ss-log"));
    table.append(PS.el("thead", {}, PS.el("tr", {}, ["From", "Symbol", "To", "New?"].map((h) => PS.el("th", { text: h })))));
    const body = PS.el("tbody", {});
    for (let j = i; j >= from; j--) {
      const t = this.steps[j];
      body.append(PS.el("tr", { class: j === i ? "current" : "" }, PS.el("td", { class: "mono", text: t.dfa_state }),
        PS.el("td", { class: "mono", text: t.symbol ? PS.symLabel(t.symbol) : "start" }),
        PS.el("td", { class: "mono", text: t.destination }), PS.el("td", { text: t.is_new ? "yes" : "no" })));
    }
    table.append(body);
  },
};
