from automata import get_automata
from helpers import triples

nfa, dfa = get_automata()


def test_dfa_follows_exactly_one_transition_per_char():
    _, steps = dfa.run("free money", trace=True)
    assert len(steps) == len("free money") + 1


def test_table_matches_simulator():
    rows = {r["state"]: r for r in dfa.table_rows()}
    assert len(rows) == len(dfa.states)
    for sid in range(len(dfa.states)):
        for sym in dfa.alphabet:
            assert rows[f"D{sid}"]["transitions"][sym] == f"D{dfa.transitions[sid][sym]}"


def test_table_flags():
    rows = dfa.table_rows()
    assert sum(r["is_start"] for r in rows) == 1
    assert sum(r["is_accepting"] for r in rows) == len(dfa.accepting)


def test_dfa_detects_all_categories():
    text = "free win won click here urgent verify your account"
    assert {m[2] for m in dfa.run(text)[0]} == {"FREE", "WIN_WON", "CLICK_HERE", "URGENT", "VERIFY_ACCOUNT"}


def test_dfa_trace_matches():
    _, steps = dfa.run("xxurgent", trace=True)
    assert steps[-1]["accepting"] and steps[-1]["matches"][0]["start"] == 2
