/* Performance Lab: runs the real benchmark and shows measured values only. */
"use strict";

PS.pages.perf = {
  init() {
    PS.$("#pf-run").addEventListener("click", () => this.run());
  },
  async run() {
    const btn = PS.$("#pf-run");
    const out = PS.clear(PS.$("#pf-output"));
    out.append(PS.el("div", { class: "panel scanning" }, PS.el("div", { class: "scan-line" }), PS.el("span", { text: "Benchmarking the NFA and DFA simulators…" })));
    btn.disabled = true;
    try {
      const reps = Number(PS.$("#pf-reps").value), warmup = Number(PS.$("#pf-warm").value);
      const r = (await PS.api("/api/benchmark", { json: { repetitions: reps, warmup, scaling: PS.$("#pf-scaling").checked } })).result;
      this.render(r);
    } catch (err) {
      PS.clear(out).append(PS.el("div", { class: "panel empty", text: err.message }));
      PS.fail(err);
    } finally { btn.disabled = false; }
  },
  render(r) {
    const out = PS.clear(PS.$("#pf-output"));
    const row = (label, key) => PS.el("tr", {}, PS.el("td", { text: label }), PS.el("td", { class: "mono", text: PS.fmtUs(r.nfa[key]) }), PS.el("td", { class: "mono", text: PS.fmtUs(r.dfa[key]) }));
    out.append(PS.el("div", { class: "panel" }, PS.el("h2", { text: "Result" }),
      PS.el("p", {}, PS.el("strong", { text: r.summary })),
      PS.el("p", { class: "hint", text: `${r.emails} emails (${r.characters} characters), ${r.repetitions} repetitions after ${r.warmup} warm-up runs. Times are for one pass over all emails. Output equivalence checked before timing: ${r.equivalent ? "identical" : "DIFFERENT"}.` }),
      PS.el("div", { class: "table-wrap" }, PS.el("table", { class: "data" },
        PS.el("thead", {}, PS.el("tr", {}, ["Measure", "NFA", "DFA"].map((h) => PS.el("th", { text: h })))),
        PS.el("tbody", {}, row("Median", "median_us"), row("Mean", "mean_us"), row("Minimum", "min_us"), row("Maximum", "max_us"), row("Median per email", "per_email_median_us"),
          PS.el("tr", {}, PS.el("td", { text: "States" }), PS.el("td", { class: "mono", text: r.states.nfa }), PS.el("td", { class: "mono", text: r.states.dfa })),
          PS.el("tr", {}, PS.el("td", { text: "NFA ÷ DFA (median)" }), PS.el("td", { class: "mono", colspan: 2, text: r.speedup_nfa_over_dfa === null ? "n/a" : r.speedup_nfa_over_dfa.toFixed(2) })))))));
    const stamp = Date.now();
    const imgs = Object.entries(r.charts).map(([k, name]) => PS.el("div", { class: "panel img-card" }, PS.el("h2", { text: { runtime: "NFA vs DFA runtime", states: "State count", scaling: "Runtime vs input size" }[k] }),
      PS.el("img", { src: `/generated/${name}?t=${stamp}`, alt: `Matplotlib chart: ${k}` })));
    out.append(PS.el("div", { class: "grid-2" }, imgs.slice(0, 2)));
    if (imgs[2]) out.append(imgs[2]);
    if (r.scaling.length) {
      out.append(PS.el("div", { class: "panel" }, PS.el("h2", { text: "Input-size test (median of 5 runs)" }),
        PS.el("div", { class: "table-wrap" }, PS.el("table", { class: "data" },
          PS.el("thead", {}, PS.el("tr", {}, ["Characters", "NFA", "DFA"].map((h) => PS.el("th", { text: h })))),
          PS.el("tbody", {}, r.scaling.map((s) => PS.el("tr", {}, PS.el("td", { class: "mono", text: s.chars.toLocaleString() }), PS.el("td", { class: "mono", text: PS.fmtUs(s.nfa_us) }), PS.el("td", { class: "mono", text: PS.fmtUs(s.dfa_us) }))))))));
    }
    out.append(PS.el("div", { class: "panel prose" }, PS.el("h2", { text: "Methodology" }), PS.el("p", { text: r.methodology }),
      PS.el("p", { text: "The DFA does one table lookup per character, while the NFA tracks a set of states, so the DFA usually does less work per character. In exchange it may need more states and memory. If a run shows otherwise, the numbers above are reported as measured." })));
  },
};
