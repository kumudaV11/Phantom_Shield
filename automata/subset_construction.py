"""Phase 3: the subset-construction algorithm (NFA -> DFA).

Every intermediate calculation is recorded in `steps` so the UI can replay it.
Design choice: the empty subset would be a DEAD state. Because the NFA start
state loops on every symbol, the empty subset is never reachable, so no dead
state appears in the DFA.
"""
from collections import deque


def subset_construction(nfa):
    """Return (dfa_states, transitions, steps).

    dfa_states : list of dicts {id, name, subset(frozenset), accepting}
    transitions: {dfa_id: {symbol: dfa_id}}
    steps      : ordered list describing each calculation
    """
    start_subset = frozenset(nfa.epsilon_closure({nfa.start}))
    index = {start_subset: 0}
    subsets = [start_subset]
    transitions = {}
    steps = [{
        "kind": "start", "dfa_state": "D0", "nfa_subset": nfa.names(start_subset),
        "symbol": None, "move": [], "closure": nfa.names(start_subset),
        "destination": "D0", "is_new": True,
        "accepting": bool(nfa.accepting_in(start_subset)),
        "text": "ε-closure of the NFA start state q0 becomes the DFA start state D0.",
    }]
    queue = deque([0])
    while queue:
        cur = queue.popleft()
        subset = subsets[cur]
        transitions[cur] = {}
        for sym in nfa.alphabet:
            moved = nfa.move(subset, sym)
            closure = frozenset(nfa.epsilon_closure(moved))
            is_new = closure not in index
            if is_new:
                index[closure] = len(subsets)
                subsets.append(closure)
                queue.append(index[closure])
            dest = index[closure]
            transitions[cur][sym] = dest
            steps.append({
                "kind": "transition", "dfa_state": f"D{cur}",
                "nfa_subset": nfa.names(subset), "symbol": sym,
                "move": nfa.names(moved), "closure": nfa.names(closure),
                "destination": f"D{dest}", "is_new": is_new,
                "accepting": bool(nfa.accepting_in(closure)),
                "text": (f"move({{{', '.join(nfa.names(subset))}}}, {sym}) then ε-closure gives "
                         f"a {'NEW' if is_new else 'known'} subset -> D{dest}."),
            })
    dfa_states = [{"id": i, "name": f"D{i}", "subset": s,
                   "accepting": bool(nfa.accepting_in(s))}
                  for i, s in enumerate(subsets)]
    return dfa_states, transitions, steps
