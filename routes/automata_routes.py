"""Automata metadata, graphs, subset-construction steps and the transition table."""
import csv
import io
import json

from flask import Blueprint, Response

import config
from automata import get_automata
from automata.patterns import PATTERNS, CATEGORIES, ALPHABET, symbol_label
from routes import ok
from services import visualization

bp = Blueprint("automata", __name__, url_prefix="/api")


@bp.get("/meta")
def meta():
    nfa, dfa = get_automata()
    return ok(meta={
        "patterns": [{"category": c, "literal": l} for c, l in PATTERNS],
        "categories": CATEGORIES, "alphabet": ALPHABET,
        "alphabet_labels": {s: symbol_label(s) for s in ALPHABET},
        "nfa_states": len(nfa.states), "nfa_transitions": nfa.transition_count(),
        "dfa_states": len(dfa.states), "dfa_transitions": dfa.transition_count(),
        "dfa_accepting": len(dfa.accepting),
        "default_threshold": config.DEFAULT_THRESHOLD,
        "min_threshold": config.MIN_THRESHOLD, "max_threshold": config.MAX_THRESHOLD,
        "max_trace_chars": config.MAX_TRACE_CHARS, "email_delimiter": config.EMAIL_DELIMITER,
        "nfa_definition": {
            "states": [nfa.name(s) for s in nfa.states], "start": "q0",
            "accepting": [{"state": nfa.name(s), **info} for s, info in sorted(nfa.accepting.items())],
            "alphabet": ALPHABET, "epsilon_transitions": nfa.transition_count()
                         - sum(len(d) for t in nfa.transitions.values() for d in t.values())}})


@bp.get("/nfa/graph")
def nfa_graph():
    nfa, _ = get_automata()
    return ok(graph=visualization.nfa_graph(nfa))


@bp.get("/dfa/graph")
def dfa_graph():
    _, dfa = get_automata()
    return ok(graph=visualization.dfa_graph(dfa))


@bp.get("/subset/steps")
def subset_steps():
    _, dfa = get_automata()
    return ok(steps=dfa.steps, summary=visualization.subset_summary(dfa))


@bp.get("/dfa/table")
def dfa_table():
    _, dfa = get_automata()
    return ok(alphabet=ALPHABET, alphabet_labels={s: symbol_label(s) for s in ALPHABET},
              rows=dfa.table_rows())


def _download(body, mimetype, name):
    return Response(body, mimetype=mimetype,
                    headers={"Content-Disposition": f"attachment; filename={name}"})


@bp.get("/dfa/table.csv")
def table_csv():
    _, dfa = get_automata()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["state", "start", "accepting", "nfa_subset"] + [symbol_label(s) for s in ALPHABET])
    for r in dfa.table_rows():
        w.writerow([r["state"], r["is_start"], r["is_accepting"], " ".join(r["nfa_subset"])]
                   + [r["transitions"][s] for s in ALPHABET])
    return _download(buf.getvalue(), "text/csv", "dfa_transition_table.csv")


@bp.get("/dfa/table.json")
def table_json():
    _, dfa = get_automata()
    return _download(json.dumps({"alphabet": ALPHABET, "rows": dfa.table_rows()}, indent=2),
                     "application/json", "dfa_transition_table.json")
