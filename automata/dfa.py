"""Phase 4: the DFA produced by subset construction, plus its simulator."""
from .patterns import to_symbols
from .subset_construction import subset_construction


class DFA:
    def __init__(self, nfa):
        self.nfa = nfa
        self.alphabet = list(nfa.alphabet)
        states, self.transitions, self.steps = subset_construction(nfa)
        self.states = states
        self.start = 0
        self.accepting = {s["id"] for s in states if s["accepting"]}
        # Accepting NFA states inside each DFA state: used for occurrence reporting.
        self.accept_info = {
            s["id"]: [nfa.accepting[q] for q in nfa.accepting_in(s["subset"])]
            for s in states if s["accepting"]}

    def name(self, sid):
        return f"D{sid}"

    def subset_names(self, sid):
        return self.nfa.names(self.states[sid]["subset"])

    def transition_count(self):
        return sum(len(t) for t in self.transitions.values())

    def run(self, text, trace=False):
        """Simulate the DFA: exactly ONE state transition per character."""
        symbols = to_symbols(text)
        cur = self.start
        matches = []
        steps = []
        if trace:
            steps.append({"step": 0, "position": None, "char": None, "symbol": None,
                          "from": None, "to": self.name(cur), "subset": self.subset_names(cur),
                          "accepting": cur in self.accepting, "matches": []})
        for i, sym in enumerate(symbols):
            prev = cur
            cur = self.transitions[cur][sym]
            found = []
            if cur in self.accepting:
                for info in self.accept_info[cur]:
                    found.append((i + 1 - info["length"], i + 1, info["category"], info["literal"]))
                matches.extend(found)
            if trace:
                steps.append({"step": i + 1, "position": i, "char": text[i], "symbol": sym,
                              "from": self.name(prev), "to": self.name(cur),
                              "subset": self.subset_names(cur), "accepting": cur in self.accepting,
                              "matches": [{"start": a, "end": b, "category": c} for a, b, c, _ in found]})
        return matches, steps

    def table_rows(self):
        """Complete transition table, generated from the real transition function."""
        rows = []
        for s in self.states:
            sid = s["id"]
            rows.append({"state": self.name(sid), "nfa_subset": self.subset_names(sid),
                         "is_start": sid == self.start, "is_accepting": sid in self.accepting,
                         "transitions": {sym: self.name(self.transitions[sid][sym])
                                         for sym in self.alphabet}})
        return rows


def build_dfa(nfa):
    return DFA(nfa)
