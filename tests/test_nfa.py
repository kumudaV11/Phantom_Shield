from automata import get_automata
from automata.nfa import EPS
from helpers import triples

nfa, dfa = get_automata()


def test_single_start_state_with_self_loop_on_every_symbol():
    for sym in nfa.alphabet:
        assert nfa.start in nfa.transitions[nfa.start][sym]


def test_real_epsilon_transitions_to_each_branch():
    assert len(nfa.epsilon[nfa.start]) == 6
    assert EPS == "ε"


def test_epsilon_closure_of_start():
    closure = nfa.epsilon_closure({nfa.start})
    assert nfa.start in closure and len(closure) == 7   # q0 + six branch start states


def test_epsilon_closure_is_idempotent_and_contains_input():
    c = nfa.epsilon_closure({nfa.start})
    assert nfa.epsilon_closure(c) == c


def test_move_function():
    start = nfa.epsilon_closure({nfa.start})
    after_f = nfa.move(start, "f")
    assert nfa.start in after_f and len(after_f) == 2     # q0 loop + first state of 'free'


def test_each_category_detected():
    cases = {"free": "FREE", "win": "WIN_WON", "won": "WIN_WON", "click here": "CLICK_HERE",
             "urgent": "URGENT", "verify your account": "VERIFY_ACCOUNT"}
    for text, cat in cases.items():
        raw, _ = nfa.run(text)
        assert [m[2] for m in raw] == [cat], text


def test_case_insensitive():
    assert triples(nfa.run("FrEe")[0]) == [(0, 4, "FREE")]


def test_accepting_states_carry_metadata():
    assert len(nfa.accepting) == 6
    for info in nfa.accepting.values():
        assert info["length"] == len(info["literal"])


def test_empty_and_no_match():
    assert nfa.run("")[0] == []
    assert nfa.run("hello world 123")[0] == []
    assert nfa.accepts_suffix_pattern("xxfree") is True
    assert nfa.accepts_suffix_pattern("freexx") is False


def test_trace_structure():
    _, steps = nfa.run("win", trace=True)
    assert len(steps) == 4
    for key in ("step", "symbol", "before", "moved", "closure", "accepting"):
        assert key in steps[1]
    assert steps[3]["matches"][0]["category"] == "WIN_WON"
