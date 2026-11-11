import pytest

from services import scanner
from services.scanner import scan_text, ScanError
from helpers import oracle


def test_example_spam():
    r = scan_text("Congratulations! You have WON a FREE iPhone. Click here now!", record=False)
    assert r["matched_categories"] == ["FREE", "WIN_WON", "CLICK_HERE"]
    assert r["score"] == 3 and r["verdict"] == "SPAM DETECTED" and r["equivalent"] is True


def test_example_safe():
    r = scan_text("Meeting at 3pm tomorrow to discuss the project roadmap.", record=False)
    assert r["score"] == 0 and r["verdict"] == "SAFE" and r["occurrences"] == []


def test_score_counts_categories_not_occurrences():
    r = scan_text("free free free free", record=False)
    assert len(r["occurrences"]) == 4 and r["score"] == 1 and r["verdict"] == "SAFE"


def test_win_won_single_category():
    r = scan_text("win won", record=False)
    assert r["score"] == 1 and len(r["occurrences"]) == 2


def test_threshold_configurable():
    assert scan_text("free win", threshold=2, record=False)["verdict"] == "SPAM DETECTED"
    assert scan_text("free win", threshold=3, record=False)["verdict"] == "SAFE"
    assert scan_text("free", threshold=1, record=False)["verdict"] == "SPAM DETECTED"


@pytest.mark.parametrize("bad", [0, 6, "2", 2.5, True])
def test_invalid_threshold(bad):
    with pytest.raises(ScanError):
        scan_text("free", threshold=bad, record=False)


def test_invalid_inputs():
    with pytest.raises(ScanError):
        scan_text(123, record=False)
    with pytest.raises(ScanError):
        scan_text("x", engine="quantum", record=False)
    with pytest.raises(ScanError):
        scan_text("x" * 300_000, record=False)


def test_original_text_and_positions_preserved():
    text = "Hello, FrEe stuff"
    occ = scan_text(text, record=False)["occurrences"]
    assert occ[0]["text"] == "FrEe" and occ[0]["start"] == 7 and occ[0]["end"] == 11


def test_empty_input():
    r = scan_text("", record=False)
    assert r["verdict"] == "SAFE" and r["score"] == 0


def test_unseen_arbitrary_emails_match_oracle():
    emails = ["Dear Sir, URGENT: your prize — you WON! 🎉 Verify Your Account at once.",
              "ünïcödé text without triggers ☃", "Tabs\tand\nnewlines FREE\r\nCLICK HERE"]
    for t in emails:
        r = scan_text(t, record=False)
        got = sorted((o["start"], o["end"], o["category"]) for o in r["occurrences"])
        assert got == oracle(t)


def test_stats_record_counts_only():
    scanner.stats.reset()
    scan_text("free win click here")
    scan_text("hello")
    s = scanner.stats.snapshot()
    assert (s["total"], s["spam"], s["safe"]) == (2, 1, 1)
    assert "text" not in s["recent"][0]
    scanner.stats.reset()


def test_trace_limit():
    with pytest.raises(ScanError):
        scanner.trace_text("a" * 1000, "nfa")
    assert len(scanner.trace_text("win", "dfa")["steps"]) == 4
