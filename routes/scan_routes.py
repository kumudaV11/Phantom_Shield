"""Scanning, tracing, uploads and session statistics."""
from flask import Blueprint, request

import config
from routes import ok, fail
from services import scanner
from services.email_parser import parse_upload, ParseError

bp = Blueprint("scan", __name__, url_prefix="/api")


def _json():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise scanner.ScanError("Request body must be a JSON object.")
    return data


@bp.errorhandler(scanner.ScanError)
def _scan_error(e):
    return fail(str(e))


@bp.errorhandler(ParseError)
def _parse_error(e):
    return fail(str(e))


@bp.get("/health")
def health():
    return ok(status="ready", engine="local")


@bp.post("/scan")
def scan():
    d = _json()
    if "text" not in d:
        return fail("Missing 'text'.")
    result = scanner.scan_text(d["text"], engine=d.get("engine", "both"),
                               threshold=d.get("threshold"), label="manual")
    return ok(result=result)


@bp.post("/scan/batch")
def scan_batch():
    d = _json()
    emails = d.get("emails")
    if not isinstance(emails, list) or not emails:
        return fail("'emails' must be a non-empty list.")
    if len(emails) > config.MAX_EMAILS_PER_FILE:
        return fail(f"Too many emails (limit {config.MAX_EMAILS_PER_FILE}).")
    out = []
    for i, text in enumerate(emails):
        if not isinstance(text, str):
            return fail(f"Email {i + 1} must be a string.")
        out.append(scanner.scan_text(text, engine=d.get("engine", "both"),
                                     threshold=d.get("threshold"), label=f"batch #{i + 1}"))
    return ok(results=out)


@bp.post("/simulate/<engine>")
def simulate(engine):
    if engine not in ("nfa", "dfa"):
        return fail("Engine must be 'nfa' or 'dfa'.", 404)
    d = _json()
    if "text" not in d:
        return fail("Missing 'text'.")
    return ok(trace=scanner.trace_text(d["text"], engine))


@bp.post("/upload")
def upload():
    f = request.files.get("file")
    if f is None:
        return fail("No file was uploaded (field name must be 'file').")
    raw = f.read(config.MAX_UPLOAD_BYTES + 1)
    emails = parse_upload(f.filename or "", raw)
    return ok(filename=f.filename, count=len(emails), emails=emails)


@bp.get("/stats")
def stats():
    return ok(stats=scanner.stats.snapshot())


@bp.post("/stats/reset")
def stats_reset():
    scanner.stats.reset()
    return ok(stats=scanner.stats.snapshot())
