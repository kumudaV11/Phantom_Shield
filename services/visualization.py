"""Graph data (nodes, edges, positions) generated from the real automata."""
from automata.patterns import symbol_label, OTHER


def _group_label(symbols, alphabet):
    if set(symbols) >= set(alphabet):
        return "Σ (any symbol)"
    return ", ".join(symbol_label(s) for s in sorted(symbols, key=alphabet.index))


def nfa_graph(nfa):
    nodes, edges = [], []
    rows = len(nfa.branches)
    row_h, x0, dx = 70, 190, 62
    height = rows * row_h + 40
    nodes.append({"id": "q0", "label": "q0", "x": 60, "y": height / 2, "start": True,
                  "accepting": False, "category": None})
    for r, br in enumerate(nfa.branches):
        for k, s in enumerate(br["states"]):
            acc = nfa.accepting.get(s)
            nodes.append({"id": nfa.name(s), "label": nfa.name(s), "x": x0 + k * dx,
                          "y": 40 + r * row_h, "start": False, "accepting": bool(acc),
                          "category": acc["category"] if acc else None,
                          "literal": br["literal"]})
    grouped = {}
    for s, table in nfa.transitions.items():
        for sym, dests in table.items():
            for d in dests:
                grouped.setdefault((s, d), []).append(sym)
    for (s, d), syms in grouped.items():
        edges.append({"from": nfa.name(s), "to": nfa.name(d), "label": _group_label(syms, nfa.alphabet),
                      "symbols": syms, "epsilon": False})
    for s, dests in nfa.epsilon.items():
        for d in dests:
            edges.append({"from": nfa.name(s), "to": nfa.name(d), "label": "ε", "symbols": [],
                          "epsilon": True})
    return {"nodes": nodes, "edges": edges,
            "width": x0 + 21 * dx, "height": height}


def dfa_graph(dfa):
    # Layer = BFS distance from D0; y = position inside the layer.
    layer = {0: 0}
    order = [0]
    for sid in order:
        for sym in dfa.alphabet:
            t = dfa.transitions[sid][sym]
            if t not in layer:
                layer[t] = layer[sid] + 1
                order.append(t)
    per_layer = {}
    nodes = []
    for sid in order:
        idx = per_layer.get(layer[sid], 0)
        per_layer[layer[sid]] = idx + 1
        st = dfa.states[sid]
        nodes.append({"id": dfa.name(sid), "label": dfa.name(sid), "x": 60 + layer[sid] * 96,
                      "y": 50 + idx * 76, "start": sid == dfa.start, "accepting": sid in dfa.accepting,
                      "subset": dfa.subset_names(sid),
                      "categories": sorted({i["category"] for i in dfa.accept_info.get(sid, [])})})
    grouped = {}
    for sid, table in dfa.transitions.items():
        for sym, t in table.items():
            grouped.setdefault((sid, t), []).append(sym)
    edges = []
    for (s, t), syms in grouped.items():
        edges.append({"from": dfa.name(s), "to": dfa.name(t),
                      "label": _group_label(syms, dfa.alphabet), "symbols": syms,
                      "to_start": t == dfa.start, "forward": layer[t] > layer[s],
                      "epsilon": False})
    return {"nodes": nodes, "edges": edges,
            "width": 120 + (max(layer.values()) + 1) * 96,
            "height": 100 + max(per_layer.values()) * 76}


def subset_summary(dfa):
    nfa = dfa.nfa
    return {"nfa_states": len(nfa.states), "dfa_states": len(dfa.states),
            "accepting_dfa_states": len(dfa.accepting), "transitions": dfa.transition_count(),
            "unique_subsets": len({s["subset"] for s in dfa.states}),
            "calculation_steps": len(dfa.steps)}
