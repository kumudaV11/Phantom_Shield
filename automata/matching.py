"""Phase 5: occurrences, scoring and verdict (application-specific rules).

The automata only say WHICH accepting states are active after each character.
Each accepting state stores its literal length, so the start index of a match
is end - length. No regular-expression engine is used here.
"""
from .patterns import CATEGORIES


def build_occurrences(raw_matches, original_text):
    """Turn raw (start, end, category, literal) tuples into sorted occurrence dicts."""
    unique = sorted(set(raw_matches), key=lambda m: (m[0], m[1], m[2]))
    return [{"start": s, "end": e, "category": c, "pattern": lit,
             "text": original_text[s:e]} for s, e, c, lit in unique]


def matched_categories(occurrences):
    found = {o["category"] for o in occurrences}
    return [c for c in CATEGORIES if c in found]      # canonical order


def score_and_verdict(occurrences, threshold):
    cats = matched_categories(occurrences)
    score = len(cats)                  # distinct categories, NOT occurrences
    verdict = "SPAM DETECTED" if score >= threshold else "SAFE"
    return cats, score, verdict


def explain(cats, score, threshold, verdict, total_occurrences):
    if not cats:
        return (f"No pattern categories matched (score 0/5, threshold {threshold}). "
                "SAFE only means the configured rules found nothing; it does not prove the email is legitimate.")
    names = ", ".join(cats)
    extra = ""
    if total_occurrences > len(cats):
        extra = (f" There are {total_occurrences} occurrences in total, but each category "
                 "counts only once toward the score.")
    if verdict == "SPAM DETECTED":
        return (f"{score} of 5 categories matched ({names}), which reaches the threshold of {threshold}, "
                f"so the verdict is SPAM DETECTED.{extra}")
    return (f"{score} of 5 categories matched ({names}), below the threshold of {threshold}, "
            f"so the verdict is SAFE.{extra} A SAFE result does not prove the email is legitimate.")
