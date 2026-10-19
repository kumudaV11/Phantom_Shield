import random

from automata import get_automata
from helpers import oracle, triples

nfa, dfa = get_automata()

CASES = [
    "", "x", "free", "FREE", "freefree", "winwon", "wonwin", "twin won", "windows won't",
    "click here here click here", "CLICK HERE", "urgenturgent", "verify your accountverify your account",
    "verify your account", "xxfree", "freexx", "ur gent", "fre e", "frfree", "wwinn",
    "Congratulations! You have WON a FREE iPhone. Click here now!",
    "Meeting at 3pm tomorrow to discuss the project roadmap.",
    "İfree ß won ǅ win", "free\nwin\r\nwon\ttab", "😀free😀", "verify your  account",
]


def test_nfa_dfa_oracle_agree_on_cases():
    for t in CASES:
        n, d = triples(nfa.run(t)[0]), triples(dfa.run(t)[0])
        assert n == d, t
        assert n == oracle(t), t


def test_random_strings_equivalent():
    rnd = random.Random(7)
    pieces = ["free", "win", "won", "click here", "urgent", "verify your account", " ", "x", "FREE",
              "Win", "é", "!", "c", "l", "ick", "here", "u", "rg"]
    for _ in range(300):
        t = "".join(rnd.choice(pieces) for _ in range(rnd.randint(0, 25)))
        assert triples(nfa.run(t)[0]) == triples(dfa.run(t)[0]) == oracle(t), t


def test_overlapping_and_adjacent():
    assert triples(dfa.run("freefree")[0]) == [(0, 4, "FREE"), (4, 8, "FREE")]
    assert triples(dfa.run("winon")[0]) == [(0, 3, "WIN_WON")]
    assert triples(dfa.run("wwon")[0]) == [(1, 4, "WIN_WON")]
    assert triples(dfa.run("winwon")[0]) == [(0, 3, "WIN_WON"), (3, 6, "WIN_WON")]


def test_one_branch_failure_does_not_block_others():
    t = "frxfree urgxurgent"
    assert triples(dfa.run(t)[0]) == oracle(t) == [(3, 7, "FREE"), (12, 18, "URGENT")]
