"""Phase 1: patterns, symbolic alphabet and normalization.

Matching semantics (documented in the README):
  * Literal substring matching, case-insensitive. No word boundaries.
  * Normalization is done CHARACTER BY CHARACTER so that string indices never
    shift: each original character c becomes the symbol of c.lower() when that
    is a single character in the alphabet, otherwise the symbolic class OTHER.
  * Indices are zero-based; the end index is exclusive.
"""

# (category, literal). win and won are two branches of ONE category.
PATTERNS = [
    ("FREE", "free"),
    ("WIN_WON", "win"),
    ("WIN_WON", "won"),
    ("CLICK_HERE", "click here"),
    ("URGENT", "urgent"),
    ("VERIFY_ACCOUNT", "verify your account"),
]

CATEGORIES = ["FREE", "WIN_WON", "CLICK_HERE", "URGENT", "VERIFY_ACCOUNT"]

OTHER = "OTHER"  # symbolic class: every character not used by any literal


def build_alphabet():
    """Every distinct character used in the literals (sorted), then OTHER."""
    chars = sorted({ch for _, literal in PATTERNS for ch in literal})
    return chars + [OTHER]


ALPHABET = build_alphabet()
_CHAR_SET = set(ALPHABET) - {OTHER}


def symbol_label(sym):
    """Human readable label for a symbol (space is shown as SPACE)."""
    return "SPACE" if sym == " " else sym


def char_to_symbol(ch):
    """Map one ORIGINAL character to its symbolic input class."""
    low = ch.lower()
    if len(low) == 1 and low in _CHAR_SET:
        return low
    return OTHER


def to_symbols(text):
    """Normalize a whole text to a list of symbols (same length as text)."""
    return [char_to_symbol(ch) for ch in text]
