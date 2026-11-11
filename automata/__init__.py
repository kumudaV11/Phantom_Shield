"""Automata package: patterns, NFA, subset construction, DFA, matching."""
from .nfa import build_nfa
from .dfa import build_dfa

_nfa = None
_dfa = None


def get_automata():
    """Build the NFA and DFA once and reuse them (they never change at runtime)."""
    global _nfa, _dfa
    if _nfa is None:
        _nfa = build_nfa()
        _dfa = build_dfa(_nfa)
    return _nfa, _dfa
