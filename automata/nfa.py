"""Phase 2: a genuine character-level epsilon-NFA.

Formal definition  N = (Q, Sigma, delta, q0, F)
  Q      : q0 plus, for every literal of length L, L+1 branch states
           (branch start state b0 ... final state bL).
  Sigma  : the symbols in patterns.ALPHABET (pattern characters + OTHER).
  delta  : q0 --a--> q0 for every a in Sigma   (self loop: skip any prefix)
           q0 --eps--> b0 of each branch        (explicit epsilon moves)
           b(k) --literal[k]--> b(k+1)          (character transitions)
  q0     : state 0
  F      : the final state of every branch (carries category + length).
"""
from .patterns import PATTERNS, ALPHABET, to_symbols

EPS = "ε"


class NFA:
    def __init__(self):
        self.alphabet = list(ALPHABET)
        self.start = 0
        self.state_names = {0: "q0"}
        self.transitions = {}      # state -> {symbol: set(states)}
        self.epsilon = {}          # state -> set(states)
        self.accepting = {}        # state -> {"category", "literal", "length"}
        self.branches = []         # info about every pattern branch
        self._build()

    # ------------------------------------------------------------------ build
    def _new_state(self):
        sid = len(self.state_names)
        self.state_names[sid] = f"q{sid}"
        return sid

    def _add(self, src, sym, dst):
        self.transitions.setdefault(src, {}).setdefault(sym, set()).add(dst)

    def _build(self):
        for sym in self.alphabet:               # shared start state self-loop
            self._add(self.start, sym, self.start)
        for category, literal in PATTERNS:
            first = self._new_state()
            self.epsilon.setdefault(self.start, set()).add(first)
            states = [first]
            for ch in literal:
                nxt = self._new_state()
                self._add(states[-1], ch, nxt)
                states.append(nxt)
            self.accepting[states[-1]] = {
                "category": category, "literal": literal, "length": len(literal)}
            self.branches.append({"category": category, "literal": literal,
                                  "states": states})

    # --------------------------------------------------------------- queries
    @property
    def states(self):
        return sorted(self.state_names)

    def name(self, s):
        return self.state_names[s]

    def names(self, states):
        return [self.state_names[s] for s in sorted(states)]

    def epsilon_closure(self, states):
        """All states reachable from `states` using epsilon moves only."""
        closure = set(states)
        stack = list(states)
        while stack:
            s = stack.pop()
            for t in self.epsilon.get(s, ()):
                if t not in closure:
                    closure.add(t)
                    stack.append(t)
        return closure

    def move(self, states, symbol):
        """States reachable from `states` by consuming one symbol."""
        result = set()
        for s in states:
            result |= self.transitions.get(s, {}).get(symbol, set())
        return result

    def accepting_in(self, states):
        return sorted(s for s in states if s in self.accepting)

    def transition_count(self):
        n = sum(len(d) for t in self.transitions.values() for d in t.values())
        return n + sum(len(v) for v in self.epsilon.values())

    # ------------------------------------------------------------ simulation
    def run(self, text, trace=False):
        """Simulate the NFA over text. Returns (raw_matches, trace_steps).

        raw_matches are (start, end, category, literal); the start comes from
        the accepting state's stored length: start = end - length.
        """
        symbols = to_symbols(text)
        current = self.epsilon_closure({self.start})
        steps = []
        matches = []
        if trace:
            steps.append({"step": 0, "position": None, "char": None, "symbol": None,
                          "before": self.names(set()), "moved": [],
                          "closure": self.names(current),
                          "accepting": [self.name(s) for s in self.accepting_in(current)],
                          "matches": []})
        for i, sym in enumerate(symbols):
            before = current
            moved = self.move(before, sym)
            current = self.epsilon_closure(moved)
            found = []
            for s in self.accepting_in(current):
                info = self.accepting[s]
                found.append((i + 1 - info["length"], i + 1, info["category"], info["literal"]))
            matches.extend(found)
            if trace:
                steps.append({"step": i + 1, "position": i, "char": text[i], "symbol": sym,
                              "before": self.names(before), "moved": self.names(moved),
                              "closure": self.names(current),
                              "accepting": [self.name(s) for s in self.accepting_in(current)],
                              "matches": [{"start": a, "end": b, "category": c} for a, b, c, _ in found]})
        return matches, steps

    def accepts_suffix_pattern(self, text):
        """Acceptance in the classic sense: is some accepting state active at the END?"""
        current = self.epsilon_closure({self.start})
        for sym in to_symbols(text):
            current = self.epsilon_closure(self.move(current, sym))
        return bool(self.accepting_in(current))


def build_nfa():
    return NFA()
