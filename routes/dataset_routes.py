"""Dataset browsing and scanning."""
import csv
import io

from flask import Blueprint, request, Response

from routes import ok, fail
from services import dataset_service, scanner

bp = Blueprint("dataset", __name__, url_prefix="/api/dataset")


@bp.get("")
def dataset():
    return ok(emails=dataset_service.load_dataset())


@bp.post("/scan")
def scan_all():
    d = request.get_json(silent=True) or {}
    if not isinstance(d, dict):
        return fail("Request body must be a JSON object.")
    try:
        results = dataset_service.scan_dataset(engine=d.get("engine", "both"),
                                               threshold=d.get("threshold"), record=True)
    except scanner.ScanError as e:
        return fail(str(e))
    return ok(results=results)


@bp.get("/export.csv")
def export_csv():
    results = dataset_service.scan_dataset()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "subject", "score", "verdict", "matched_categories", "occurrences",
                "expected_verdict", "expected_categories", "agrees_with_expectation"])
    for r in results:
        w.writerow([r["id"], r["subject"], r["score"], r["verdict"], " ".join(r["matched_categories"]),
                    r["occurrence_count"], r["expected_verdict"], " ".join(r["expected_categories"]),
                    r["matches_expectation"]])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=dataset_results.csv"})
