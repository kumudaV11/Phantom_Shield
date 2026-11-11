from automata.patterns import PATTERNS, CATEGORIES, ALPHABET, OTHER, to_symbols, char_to_symbol


def test_five_categories():
    assert CATEGORIES == ["FREE", "WIN_WON", "CLICK_HERE", "URGENT", "VERIFY_ACCOUNT"]
    assert {c for c, _ in PATTERNS} == set(CATEGORIES)


def test_win_won_are_two_literals_one_category():
    lits = [l for c, l in PATTERNS if c == "WIN_WON"]
    assert sorted(lits) == ["win", "won"]


def test_alphabet_contains_every_pattern_char_and_other():
    for _, lit in PATTERNS:
        for ch in lit:
            assert ch in ALPHABET
    assert ALPHABET[-1] == OTHER and ALPHABET.count(OTHER) == 1


def test_case_insensitive_symbols_and_other_class():
    assert to_symbols("FrEe") == ["f", "r", "e", "e"]
    assert char_to_symbol("!") == OTHER
    assert char_to_symbol("é") == OTHER
    assert char_to_symbol("İ") == OTHER      # lower() has length 2 -> must not shift indices


def test_normalization_keeps_length():
    text = "İSTANBUL FREE ß ǅ"
    assert len(to_symbols(text)) == len(text)
