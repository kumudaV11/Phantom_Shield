"""Loads the built-in 20-email dataset and scans it with the real automata."""
import json

import config
from services.scanner import scan_text


def load_dataset():
    with open(config.DATASET_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["emails"]


def get_email(email_id):
    for e in load_dataset():
        if e["id"] == email_id:
            return e
    return None


def scan_dataset(engine="both", threshold=None, record=False):
    """Scan every dataset email; report agreement with the stored expectation."""
    results = []
    for e in load_dataset():
        r = scan_text(e["text"], engine=engine, threshold=threshold, record=record,
                      label=f"dataset #{e['id']}")
        results.append({
            "id": e["id"], "subject": e["subject"], "verdict": r["verdict"],
            "score": r["score"], "matched_categories": r["matched_categories"],
            "occurrence_count": len(r["occurrences"]), "equivalent": r["equivalent"],
            "expected_verdict": e["expected_verdict"],
            "expected_categories": e["expected_categories"],
            "matches_expectation": (r["matched_categories"] == _canon(e["expected_categories"])
                                    and (threshold is not None or r["verdict"] == e["expected_verdict"])),
            "nfa_time_us": r["nfa_time_us"], "dfa_time_us": r["dfa_time_us"]})
    return results


def _canon(cats):
    from automata.patterns import CATEGORIES
    return [c for c in CATEGORIES if c in cats]
