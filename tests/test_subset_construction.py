from automata import get_automata

nfa, dfa = get_automata()


def test_start_state_is_closure_of_nfa_start():
    assert dfa.states[0]["subset"] == frozenset(nfa.epsilon_closure({nfa.start}))


def test_every_subset_is_unique_and_reachable():
    subsets = [s["subset"] for s in dfa.states]
    assert len(set(subsets)) == len(subsets)
    seen, stack = {0}, [0]
    while stack:
        s = stack.pop()
        for t in dfa.transitions[s].values():
            if t not in seen:
                seen.add(t)
                stack.append(t)
    assert seen == {s["id"] for s in dfa.states}


def test_transitions_recomputed_independently():
    for s in dfa.states:
        for sym in nfa.alphabet:
            expected = frozenset(nfa.epsilon_closure(nfa.move(s["subset"], sym)))
            assert dfa.states[dfa.transitions[s["id"]][sym]]["subset"] == expected


def test_accepting_iff_subset_has_accepting_nfa_state():
    for s in dfa.states:
        assert s["accepting"] == any(q in nfa.accepting for q in s["subset"])


def test_total_function_and_no_dead_state():
    for s in dfa.states:
        assert set(dfa.transitions[s["id"]]) == set(nfa.alphabet)
        assert s["subset"]               # empty subset unreachable


def test_steps_cover_every_transition():
    transition_steps = [x for x in dfa.steps if x["kind"] == "transition"]
    assert len(transition_steps) == len(dfa.states) * len(nfa.alphabet)
    assert sum(1 for x in transition_steps if x["is_new"]) == len(dfa.states) - 1
