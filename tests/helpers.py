"""Shared helpers: an independent str.find oracle (no automata, no regex)."""
LITERALS = [("FREE", "free"), ("WIN_WON", "win"), ("WIN_WON", "won"),
            ("CLICK_HERE", "click here"), ("URGENT", "urgent"),
            ("VERIFY_ACCOUNT", "verify your account")]


def oracle(text):
    """All (start, end, category) occurrences found with plain str.find on lowercase text."""
    low = "".join(c.lower() if len(c.lower()) == 1 else "\0" for c in text)
    found = set()
    for cat, lit in LITERALS:
        i = low.find(lit)
        while i != -1:
            found.add((i, i + len(lit), cat))
            i = low.find(lit, i + 1)
    return sorted(found)


def triples(raw):
    return sorted({(s, e, c) for s, e, c, _ in raw})
