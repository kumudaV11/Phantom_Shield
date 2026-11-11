import pytest

from app import app
from services.benchmark import run_benchmark, BenchmarkError


def test_structure_and_real_numbers():
    r = run_benchmark(repetitions=3, warmup=1, include_scaling=False)
    for engine in ("nfa", "dfa"):
        for key in ("median_us", "mean_us", "min_us", "max_us", "per_email_median_us"):
            assert r[engine][key] > 0
        assert r[engine]["min_us"] <= r[engine]["median_us"] <= r[engine]["max_us"]
    assert r["states"]["nfa"] == 52 and r["states"]["dfa"] > 0
    assert r["equivalent"] is True and r["emails"] == 20
    assert r["repetitions"] == 3 and "perf_counter" in r["methodology"]


def test_charts_written():
    import os, config
    r = run_benchmark(repetitions=2, warmup=0, include_scaling=True)
    for name in r["charts"].values():
        assert os.path.getsize(os.path.join(config.GENERATED_DIR, name)) > 1000
    assert len(r["scaling"]) == 3


@pytest.mark.parametrize("kw", [{"repetitions": 0}, {"repetitions": 10_000}, {"repetitions": "5"},
                                {"warmup": -1}, {"warmup": 999}])
def test_invalid_parameters(kw):
    with pytest.raises(BenchmarkError):
        run_benchmark(**kw)


def test_endpoint():
    c = app.test_client()
    r = c.post("/api/benchmark", json={"repetitions": 2, "warmup": 0, "scaling": False})
    assert r.status_code == 200 and r.get_json()["result"]["charts"]["runtime"]
    assert c.get("/generated/benchmark_runtime.png").status_code == 200
    assert c.post("/api/benchmark", json={"repetitions": 0}).status_code == 400
