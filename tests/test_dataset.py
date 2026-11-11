import json

import config
from automata.patterns import CATEGORIES
from services.dataset_service import load_dataset, scan_dataset
from helpers import oracle

from app import app


def test_exactly_20_unique_emails_with_required_fields():
    emails = load_dataset()
    assert len(emails) == 20 and len({e["id"] for e in emails}) == 20
    for e in emails:
        for key in ("id", "subject", "text", "expected_categories", "expected_verdict"):
            assert key in e
        assert set(e["expected_categories"]) <= set(CATEGORIES)


def test_expected_values_verified_independently_of_automata():
    threshold = json.load(open(config.DATASET_PATH, encoding="utf-8"))["threshold"]
    for e in load_dataset():
        cats = {c for _, _, c in oracle(e["text"])}
        assert cats == set(e["expected_categories"]), e["id"]
        verdict = "SPAM DETECTED" if len(cats) >= threshold else "SAFE"
        assert verdict == e["expected_verdict"], e["id"]


def test_scanner_agrees_with_dataset_and_engines_equivalent():
    for r in scan_dataset():
        assert r["matches_expectation"], r["id"]
        assert r["equivalent"] is True


def test_dataset_variety():
    emails = load_dataset()
    assert any(e["expected_verdict"] == "SAFE" for e in emails)
    assert any(e["expected_verdict"] == "SPAM DETECTED" for e in emails)
    assert any(len(e["expected_categories"]) == 5 for e in emails)
    assert any(not e["expected_categories"] for e in emails)


def test_dataset_endpoints():
    c = app.test_client()
    assert len(c.get("/api/dataset").get_json()["emails"]) == 20
    assert len(c.post("/api/dataset/scan", json={"engine": "dfa"}).get_json()["results"]) == 20
    assert c.get("/api/dataset/export.csv").status_code == 200
    assert c.post("/api/dataset/scan", json={"threshold": 77}).status_code == 400


def test_other_endpoints_and_exports():
    c = app.test_client()
    meta = c.get("/api/meta").get_json()["meta"]
    assert meta["nfa_states"] == 52 and meta["dfa_states"] > 0
    g = c.get("/api/nfa/graph").get_json()["graph"]
    assert len(g["nodes"]) == meta["nfa_states"]
    d = c.get("/api/dfa/graph").get_json()["graph"]
    assert len(d["nodes"]) == meta["dfa_states"]
    t = c.get("/api/dfa/table").get_json()
    assert len(t["rows"]) == meta["dfa_states"]
    assert c.get("/api/dfa/table.json").status_code == 200
    assert c.get("/api/dfa/table.csv").data.decode().count("\n") == meta["dfa_states"] + 1
    st = c.get("/api/subset/steps").get_json()
    assert st["summary"]["dfa_states"] == meta["dfa_states"]
