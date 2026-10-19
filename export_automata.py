"""Prints the real NFA and DFA so teammates can copy them into the written report.

Run:  python export_automata.py            (prints to the screen)
      python export_automata.py > automata.txt
"""
from automata import get_automata
from automata.patterns import PATTERNS, ALPHABET, symbol_label

nfa, dfa = get_automata()
print("PATTERNS:", [(c, l) for c, l in PATTERNS])
print("ALPHABET:", [symbol_label(s) for s in ALPHABET])
print(f"\nNFA: {len(nfa.states)} states, {nfa.transition_count()} transitions (incl. epsilon)")
print("Accepting:", {nfa.name(s): i["category"] + ':' + i["literal"] for s, i in nfa.accepting.items()})
print("\nNFA transitions:")
for s in nfa.states:
    for sym, dests in sorted(nfa.transitions.get(s, {}).items()):
        if s == 0:
            continue                                  # q0 loops on every symbol (printed below)
        print(f"  {nfa.name(s)} --{symbol_label(sym)}--> {', '.join(nfa.names(dests))}")
    for d in sorted(nfa.epsilon.get(s, ())):
        print(f"  {nfa.name(s)} --ε--> {nfa.name(d)}")
print("  q0 --(every symbol)--> q0")
print(f"\nDFA: {len(dfa.states)} states, {len(dfa.accepting)} accepting, {dfa.transition_count()} transitions")
print("DFA states (id = NFA subset):")
for s in dfa.states:
    flag = (" START" if s["id"] == 0 else "") + (" ACCEPT" if s["accepting"] else "")
    print(f"  D{s['id']} = {{{', '.join(dfa.subset_names(s['id']))}}}{flag}")
