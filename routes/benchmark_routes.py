"""Benchmark execution and generated chart files."""
from flask import Blueprint, request, send_from_directory

import config
from routes import ok, fail
from services.benchmark import run_benchmark, BenchmarkError

bp = Blueprint("benchmark", __name__)

ALLOWED_CHARTS = {"benchmark_runtime.png", "benchmark_states.png", "benchmark_scaling.png"}


@bp.post("/api/benchmark")
def benchmark():
    d = request.get_json(silent=True)
    if d is None:
        d = {}
    if not isinstance(d, dict):
        return fail("Request body must be a JSON object.")
    try:
        result = run_benchmark(repetitions=d.get("repetitions", 30), warmup=d.get("warmup", 3),
                               include_scaling=bool(d.get("scaling", True)))
    except BenchmarkError as e:
        return fail(str(e))
    return ok(result=result)


@bp.get("/generated/<name>")
def generated(name):
    if name not in ALLOWED_CHARTS:
        return fail("Not found.", 404)
    resp = send_from_directory(config.GENERATED_DIR, name)
    resp.headers["Cache-Control"] = "no-store"
    return resp
