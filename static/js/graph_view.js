/* Reusable SVG automaton viewer (pan, zoom, fit, highlight) and the step-by-step TraceView. */
"use strict";

const SVG_NS = "http://www.w3.org/2000/svg";
const NODE_R = 18;

function svgEl(tag, attrs, ...children) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs || {})) node.setAttribute(k, v);
  for (const c of children) if (c) node.append(c);
  return node;
}

PS.GraphView = class {
  constructor(container, graph, options) {
    this.container = container;
    this.graph = graph;
    this.options = Object.assign({ curve: 0, tools: true, onSelect: null, interactive: true }, options || {});
    this.view = { x: 0, y: 0, k: 1 };
    this.nodes = {};
    this.edgeEls = {};
    this.selected = null;
    this._build();
    this.fit();
  }

  _build() {
    PS.clear(this.container);
    this.container.classList.add("graph-box");
    const svg = svgEl("svg", { role: "img", "aria-label": "Automaton diagram" });
    const marker = svgEl("marker", { id: "arrow-" + (PS._gid = (PS._gid || 0) + 1), viewBox: "0 0 10 10", refX: "9", refY: "5",
      markerWidth: "7", markerHeight: "7", orient: "auto-start-reverse" },
      svgEl("path", { d: "M0 0 L10 5 L0 10 z", class: "arrow-head" }));
    this.markerId = marker.getAttribute("id");
    svg.append(svgEl("defs", {}, marker));
    this.viewport = svgEl("g", {});
    svg.append(this.viewport);
    this.svg = svg;

    const byId = {};
    this.graph.nodes.forEach((n) => { byId[n.id] = n; });
    this.byId = byId;

    const edgeLayer = svgEl("g", {});
    const nodeLayer = svgEl("g", {});
    this.viewport.append(edgeLayer, nodeLayer);

    this.graph.edges.forEach((e) => {
      const g = this._edge(e, byId);
      if (!g) return;
      edgeLayer.append(g);
      const key = e.from + "->" + e.to;
      (this.edgeEls[key] = this.edgeEls[key] || []).push({ el: g, data: e });
    });
    this.graph.nodes.forEach((n) => {
      const g = svgEl("g", { class: "node" + (n.accepting ? " accepting" : ""), transform: `translate(${n.x},${n.y})`,
        tabindex: this.options.interactive ? "0" : "-1", "data-id": n.id });
      g.append(svgEl("circle", { class: "body", r: NODE_R }));
      if (n.accepting) g.append(svgEl("circle", { class: "ring", r: NODE_R - 4 }));
      const label = svgEl("text", {}); label.textContent = n.label;
      g.append(label);
      const tip = svgEl("title", {});
      tip.textContent = n.label + (n.accepting ? " (accepting)" : "") + (n.category ? " — " + n.category : "")
        + (n.categories && n.categories.length ? " — " + n.categories.join(", ") : "");
      g.append(tip);
      if (n.start) {
        g.append(svgEl("path", { d: `M${-NODE_R - 26} 0 L${-NODE_R - 2} 0`, stroke: "#22d3ee", "stroke-width": "2", fill: "none",
          "marker-end": `url(#${this.markerId})` }));
      }
      nodeLayer.append(g);
      this.nodes[n.id] = g;
      if (this.options.interactive) {
        const choose = () => { this.select(n.id); if (this.options.onSelect) this.options.onSelect(n.id); };
        g.addEventListener("click", (ev) => { ev.stopPropagation(); choose(); });
        g.addEventListener("keydown", (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); choose(); } });
      }
    });

    this.container.append(svg);
    if (this.options.interactive) this._interactions();
    if (this.options.tools) this._tools();
  }

  _edge(e, byId) {
    const a = byId[e.from], b = byId[e.to];
    if (!a || !b) return null;
    let d, lx, ly;
    if (a === b) {
      d = `M${a.x - 8} ${a.y - NODE_R} C${a.x - 24} ${a.y - NODE_R - 36}, ${a.x + 24} ${a.y - NODE_R - 36}, ${a.x + 8} ${a.y - NODE_R - 1}`;
      lx = a.x; ly = a.y - NODE_R - 30;
    } else {
      const dx = b.x - a.x, dy = b.y - a.y, dist = Math.hypot(dx, dy) || 1;
      const off = this.options.curve * dist;
      const cx = (a.x + b.x) / 2 + (-dy / dist) * off, cy = (a.y + b.y) / 2 + (dx / dist) * off;
      const sdx = cx - a.x, sdy = cy - a.y, sl = Math.hypot(sdx, sdy) || 1;
      const edx = b.x - cx, edy = b.y - cy, el = Math.hypot(edx, edy) || 1;
      const sx = a.x + (sdx / sl) * NODE_R, sy = a.y + (sdy / sl) * NODE_R;
      const ex = b.x - (edx / el) * (NODE_R + 3), ey = b.y - (edy / el) * (NODE_R + 3);
      d = off === 0 ? `M${sx} ${sy} L${ex} ${ey}` : `M${sx} ${sy} Q${cx} ${cy} ${ex} ${ey}`;
      lx = 0.25 * a.x + 0.5 * cx + 0.25 * b.x; ly = 0.25 * a.y + 0.5 * cy + 0.25 * b.y;
    }
    const g = svgEl("g", { class: "edge" + (e.epsilon ? " epsilon" : "") });
    g.append(svgEl("path", { d, "marker-end": `url(#${this.markerId})` }));
    const text = svgEl("text", { x: lx, y: ly - 3 });
    text.textContent = e.label.length > 16 ? `${e.symbols.length} symbols` : e.label;
    g.append(text);
    const tip = svgEl("title", {}); tip.textContent = `${e.from} → ${e.to}: ${e.label}`;
    g.append(tip);
    return g;
  }

  _tools() {
    const tools = PS.el("div", { class: "graph-tools" },
      PS.el("button", { class: "btn small", "aria-label": "Zoom in", onclick: () => this.zoomBy(1.25), text: "+" }),
      PS.el("button", { class: "btn small", "aria-label": "Zoom out", onclick: () => this.zoomBy(0.8), text: "−" }),
      PS.el("button", { class: "btn small", onclick: () => this.fit(), text: "Fit" }),
      PS.el("button", { class: "btn small", onclick: () => this.reset(), text: "Reset" }));
    this.container.append(tools);
  }

  _interactions() {
    const svg = this.svg;
    svg.addEventListener("wheel", (ev) => {
      ev.preventDefault();
      const rect = svg.getBoundingClientRect();
      this.zoomBy(ev.deltaY < 0 ? 1.12 : 0.89, ev.clientX - rect.left, ev.clientY - rect.top);
    }, { passive: false });
    let drag = null;
    svg.addEventListener("pointerdown", (ev) => {
      if (ev.target.closest(".node")) return;
      drag = { x: ev.clientX, y: ev.clientY, vx: this.view.x, vy: this.view.y };
      svg.classList.add("dragging"); svg.setPointerCapture(ev.pointerId);
    });
    svg.addEventListener("pointermove", (ev) => {
      if (!drag) return;
      this.view.x = drag.vx + (ev.clientX - drag.x);
      this.view.y = drag.vy + (ev.clientY - drag.y);
      this._apply();
    });
    const end = () => { drag = null; svg.classList.remove("dragging"); };
    svg.addEventListener("pointerup", end); svg.addEventListener("pointercancel", end);
  }

  _apply() {
    const v = this.view;
    this.viewport.setAttribute("transform", `translate(${v.x},${v.y}) scale(${v.k})`);
  }
  zoomBy(factor, cx, cy) {
    const rect = this.svg.getBoundingClientRect();
    cx = cx === undefined ? rect.width / 2 : cx; cy = cy === undefined ? rect.height / 2 : cy;
    const k = Math.max(0.15, Math.min(4, this.view.k * factor));
    const real = k / this.view.k;
    this.view.x = cx - (cx - this.view.x) * real;
    this.view.y = cy - (cy - this.view.y) * real;
    this.view.k = k;
    this._apply();
  }
  fit() {
    const rect = this.container.getBoundingClientRect();
    const w = rect.width || 600, h = rect.height || 400;
    const gw = this.graph.width + 40, gh = this.graph.height + 40;
    const k = Math.min(w / gw, h / gh, 1.6);
    this.view = { k, x: (w - gw * k) / 2 + 20 * k, y: (h - gh * k) / 2 + 20 * k };
    this._apply();
  }
  reset() { this.view = { x: 20, y: 20, k: 1 }; this._apply(); this.clearHighlight(); this.select(null); }

  select(id) {
    if (this.selected && this.nodes[this.selected]) this.nodes[this.selected].classList.remove("selected");
    this.selected = id;
    if (id && this.nodes[id]) this.nodes[id].classList.add("selected");
  }
  centerOn(id) {
    const n = this.byId[id]; if (!n) return;
    const rect = this.container.getBoundingClientRect();
    this.view.x = rect.width / 2 - n.x * this.view.k; this.view.y = rect.height / 2 - n.y * this.view.k;
    this._apply();
  }
  clearHighlight() {
    Object.values(this.nodes).forEach((g) => g.classList.remove("active", "hit"));
    Object.values(this.edgeEls).flat().forEach((o) => o.el.classList.remove("traversed"));
  }
  highlight({ active = [], hits = [], edges = [] }) {
    this.clearHighlight();
    active.forEach((id) => this.nodes[id] && this.nodes[id].classList.add("active"));
    hits.forEach((id) => this.nodes[id] && this.nodes[id].classList.add("hit"));
    edges.forEach((key) => (this.edgeEls[key] || []).forEach((o) => o.el.classList.add("traversed")));
  }
  setEdgeFilter(predicate) {
    Object.values(this.edgeEls).flat().forEach((o) => o.el.classList.toggle("hidden", !predicate(o.data)));
  }
};

/* ---------- TraceView: graph + input strip + player + step card + log ---------- */
PS.TraceView = class {
  constructor(container, options) {
    this.engine = options.engine;                       // "nfa" or "dfa"
    this.graphData = options.graph;
    this.graphOptions = options.graphOptions || {};
    this.withInput = options.withInput !== false;
    this.onSelect = options.onSelect || null;
    this.steps = [];
    this.text = "";
    this.container = PS.clear(container);
    this._build();
  }

  _build() {
    const c = this.container;
    if (this.withInput) {
      this.input = PS.el("input", { type: "text", "aria-label": "Test string", placeholder: "Type a test string, e.g.  you WON a free gift",
        value: "You WON a free gift" });
      this.input.addEventListener("keydown", (e) => { if (e.key === "Enter") this.runFromInput(); });
      c.append(PS.el("div", { class: "trace-input" }, this.input,
        PS.el("button", { class: "btn primary", onclick: () => this.runFromInput(), text: "Simulate" })));
    }
    c.append(PS.el("div", { class: "graph-legend" },
      PS.el("span", { class: "legend-item", text: "◯ state" }),
      PS.el("span", { class: "legend-item", text: "◎ accepting (double circle)" }),
      PS.el("span", { class: "legend-item", text: "→ start arrow marks the initial state" }),
      this.engine === "nfa" ? PS.el("span", { class: "legend-item", text: "- - ε transition (dashed)" }) : null,
      PS.el("span", { class: "legend-item", text: "cyan glow = active / traversed" }),
      PS.el("span", { class: "legend-item", text: "scroll to zoom · drag to pan" })));
    const box = PS.el("div", {});
    this.box = box;
    c.append(box);
    this.graph = new PS.GraphView(box, this.graphData, Object.assign({ onSelect: this.onSelect }, this.graphOptions));
    this.strip = PS.el("div", { class: "symbol-strip", "aria-label": "Input characters" });
    c.append(this.strip);
    this.playerEl = PS.el("div", { class: "player" },
      PS.el("button", { class: "btn small", "data-act": "reset", text: "Reset" }),
      PS.el("button", { class: "btn small", "data-act": "prev", text: "Previous Step" }),
      PS.el("button", { class: "btn small primary", "data-act": "play", text: "Play" }),
      PS.el("button", { class: "btn small", "data-act": "pause", text: "Pause" }),
      PS.el("button", { class: "btn small", "data-act": "next", text: "Next Step" }),
      (this.counter = PS.el("span", { class: "hint" })));
    c.append(this.playerEl);
    this.player = new PS.Player(this.playerEl, { onStep: (i) => this.render(i), getInterval: () => 650 });
    this.card = PS.el("div", { class: "step-card" }, PS.el("span", { class: "hint", text: "Enter a string and press Simulate to see the real " + this.engine.toUpperCase() + " trace." }));
    c.append(this.card);
    this.logWrap = PS.el("div", { class: "log-wrap" });
    c.append(this.logWrap);
  }

  runFromInput() { return this.load(this.input.value).catch(PS.fail); }

  async load(text, note) {
    const data = await PS.api("/api/simulate/" + this.engine, { json: { text } });
    this.text = text;
    this.steps = data.trace.steps;
    this.occurrences = data.trace.occurrences;
    if (this.input) this.input.value = text;
    this._buildStrip();
    this._buildLog();
    this.player.setCount(this.steps.length);
    if (note) this.card.prepend(PS.el("p", { class: "hint", text: note }));
    return data.trace;
  }

  _buildStrip() {
    PS.clear(this.strip);
    Array.from(this.text).forEach((ch, i) => this.strip.append(PS.el("span", { "data-i": i, title: "position " + i, text: PS.showChar(ch) })));
  }

  _buildLog() {
    const head = this.engine === "nfa"
      ? ["Step", "Input", "Active before", "After move", "ε-closure", "Accepting"]
      : ["Step", "Input", "From", "To", "NFA subset", "Accepting"];
    const rows = this.steps.map((s) => {
      const cells = this.engine === "nfa"
        ? [s.step, s.char === null ? "(start)" : PS.showChar(s.char) + " → " + PS.symLabel(s.symbol), s.before.join(" "), s.moved.join(" "), s.closure.join(" "), s.accepting.join(" ") || "–"]
        : [s.step, s.char === null ? "(start)" : PS.showChar(s.char) + " → " + PS.symLabel(s.symbol), s.from || "–", s.to, s.subset.join(" "), s.accepting ? "yes" : "no"];
      return PS.el("tr", { "data-step": s.step }, cells.map((v) => PS.el("td", { class: "mono", text: String(v) })));
    });
    PS.clear(this.logWrap).append(PS.el("table", { class: "data" },
      PS.el("thead", {}, PS.el("tr", {}, head.map((h) => PS.el("th", { text: h })))), PS.el("tbody", {}, rows)));
  }

  render(i) {
    const s = this.steps[i];
    this.counter.textContent = `Step ${s.step} of ${this.steps.length - 1}`;
    Array.from(this.strip.children).forEach((span, idx) => {
      span.classList.toggle("done", idx < s.step); span.classList.toggle("current", idx === s.step - 1);
    });
    Array.from(this.logWrap.querySelectorAll("tr[data-step]")).forEach((tr) => {
      const cur = Number(tr.dataset.step) === s.step; tr.classList.toggle("current", cur);
      if (cur) tr.scrollIntoView({ block: "nearest" });
    });
    const matches = s.matches.length ? s.matches.map((m) => `${m.category} [${m.start}, ${m.end})`).join("; ") : "none at this step";
    const rows = [["Step", String(s.step)],
      ["Input symbol", s.char === null ? "(none — initial state)" : `${PS.showChar(s.char)}  → class ${PS.symLabel(s.symbol)}`],
      ["Position", s.position === null ? "–" : String(s.position)]];
    if (this.engine === "nfa") {
      rows.push(["Active states before", s.before.join(", ") || "–"], ["States after move", s.moved.join(", ") || "–"],
        ["After ε-closure", s.closure.join(", ")], ["Accepting states", s.accepting.join(", ") || "none"]);
    } else {
      rows.push(["Previous DFA state", s.from || "–"], ["Current DFA state", s.to],
        ["Underlying NFA subset", s.subset.join(", ")], ["Accepting", s.accepting ? "yes" : "no"]);
    }
    rows.push(["Matches ending here", matches]);
    const dl = PS.el("dl", {});
    rows.forEach(([k, v]) => dl.append(PS.el("dt", { text: k }), PS.el("dd", { text: v })));
    PS.clear(this.card).append(dl);
    this._highlight(s);
  }

  _highlight(s) {
    const g = this.graph;
    if (this.engine === "nfa") {
      const edges = [];
      if (s.symbol) {
        for (const [key, list] of Object.entries(g.edgeEls)) {
          const [from, to] = key.split("->");
          if (s.before.includes(from) && s.moved.includes(to) && list.some((o) => !o.data.epsilon && o.data.symbols.includes(s.symbol))) edges.push(key);
        }
      }
      for (const [key, list] of Object.entries(g.edgeEls)) {
        const [from, to] = key.split("->");
        if (list.some((o) => o.data.epsilon) && (s.moved.includes(from) || (!s.symbol && from === "q0")) && s.closure.includes(to)) edges.push(key);
      }
      g.highlight({ active: s.closure, hits: s.accepting, edges });
    } else {
      g.highlight({ active: [s.to], hits: s.accepting ? [s.to] : [], edges: s.from ? [s.from + "->" + s.to] : [] });
      g.centerOn(s.to);
    }
  }
};

/* Graph data is fetched once and cached. */
PS._graphs = {};
PS.getGraph = function (kind) {
  if (!PS._graphs[kind]) {
    PS._graphs[kind] = PS.api(`/api/${kind}/graph`).then((d) => d.graph);
  }
  return PS._graphs[kind];
};
