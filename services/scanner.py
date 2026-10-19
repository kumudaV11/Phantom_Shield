"""Scanning service: runs the NFA and/or DFA and builds one result object."""
import time
from collections import deque
from datetime import datetime

import config
from automata import get_automata
from automata.matching import build_occurrences, score_and_verdict, explain


class ScanError(ValueError):
    pass


class SessionStats:
    """In-memory counters for the current server session. Stores NO email text."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.total = 0
        self.spam = 0
        self.safe = 0
        self.recent = deque(maxlen=10)

    def record(self, result, label=""):
        self.total += 1
        if result["verdict"] == "SPAM DETECTED":
            self.spam += 1
        else:
            self.safe += 1
        self.recent.appendleft({
            "time": datetime.now().strftime("%H:%M:%S"), "label": label,
            "length": result["length"], "score": result["score"],
            "verdict": result["verdict"], "engine": result["engine"]})

    def snapshot(self):
        return {"total": self.total, "spam": self.spam, "safe": self.safe,
                "recent": list(self.recent)}


stats = SessionStats()


def validate_text(text):
    if not isinstance(text, str):
        raise ScanError("'text' must be a string.")
    if len(text) > config.MAX_EMAIL_CHARS:
        raise ScanError(f"Email is too long (limit {config.MAX_EMAIL_CHARS} characters).")
    return text


def validate_threshold(value):
    if value is None:
        return config.DEFAULT_THRESHOLD
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScanError("'threshold' must be an integer.")
    if not config.MIN_THRESHOLD <= value <= config.MAX_THRESHOLD:
        raise ScanError(f"'threshold' must be between {config.MIN_THRESHOLD} and {config.MAX_THRESHOLD}.")
    return value


def _timed(fn, text):
    t0 = time.perf_counter()
    matches, _ = fn(text)
    return matches, (time.perf_counter() - t0) * 1e6      # microseconds


def scan_text(text, engine="both", threshold=None, record=True, label=""):
    """Scan one email. engine: 'nfa', 'dfa' or 'both'."""
    text = validate_text(text)
    threshold = validate_threshold(threshold)
    if engine not in ("nfa", "dfa", "both"):
        raise ScanError("'engine' must be 'nfa', 'dfa' or 'both'.")
    nfa, dfa = get_automata()
    nfa_raw = dfa_raw = None
    nfa_us = dfa_us = None
    if engine in ("nfa", "both"):
        nfa_raw, nfa_us = _timed(nfa.run, text)
    if engine in ("dfa", "both"):
        dfa_raw, dfa_us = _timed(dfa.run, text)
    primary = nfa_raw if nfa_raw is not None else dfa_raw
    occurrences = build_occurrences(primary, text)
    equivalent = None
    if engine == "both":
        equivalent = sorted(set(nfa_raw)) == sorted(set(dfa_raw))
    cats, score, verdict = score_and_verdict(occurrences, threshold)
    result = {
        "engine": engine, "length": len(text), "threshold": threshold,
        "verdict": verdict, "score": score, "max_score": 5,
        "matched_categories": cats, "occurrences": occurrences,
        "nfa_time_us": nfa_us, "dfa_time_us": dfa_us, "equivalent": equivalent,
        "explanation": explain(cats, score, threshold, verdict, len(occurrences)),
        "disclaimer": "Educational keyword-based detector. SAFE does not prove an email is legitimate.",
    }
    if record:
        stats.record(result, label)
    return result


def trace_text(text, engine):
    """Step-by-step trace for the NFA or the DFA (limited length)."""
    text = validate_text(text)
    if len(text) > config.MAX_TRACE_CHARS:
        raise ScanError(f"Step-by-step traces are limited to {config.MAX_TRACE_CHARS} characters.")
    nfa, dfa = get_automata()
    sim = nfa if engine == "nfa" else dfa
    raw, steps = sim.run(text, trace=True)
    return {"engine": engine, "length": len(text), "steps": steps,
            "occurrences": build_occurrences(raw, text)}
