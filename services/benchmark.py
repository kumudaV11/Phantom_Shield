"""Performance Lab: measures the real NFA and DFA simulators with perf_counter."""
import os
import statistics
import time

import matplotlib
matplotlib.use("Agg")                      # no GUI needed
import matplotlib.pyplot as plt

import config
from automata import get_automata
from services.dataset_service import load_dataset

MAX_REPETITIONS = 200
MAX_WARMUP = 50


class BenchmarkError(ValueError):
    pass


def _time_batch(fn, texts):
    t0 = time.perf_counter()
    for t in texts:
        fn(t)
    return time.perf_counter() - t0


def _stats(samples_s, n_emails):
    us = [s * 1e6 for s in samples_s]
    return {"median_us": statistics.median(us), "mean_us": statistics.fmean(us),
            "min_us": min(us), "max_us": max(us),
            "per_email_median_us": statistics.median(us) / n_emails,
            "samples": len(us)}


def _measure(fn, texts, repetitions, warmup):
    for _ in range(warmup):
        _time_batch(fn, texts)
    return [_time_batch(fn, texts) for _ in range(repetitions)]


def _check_equivalent(nfa, dfa, texts):
    for t in texts:
        if sorted(set(nfa.run(t)[0])) != sorted(set(dfa.run(t)[0])):
            raise BenchmarkError("NFA and DFA results differ; benchmark aborted.")


def _chart_runtime(path, nfa_s, dfa_s, reps):
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = ["NFA", "DFA"]
    vals = [nfa_s["median_us"], dfa_s["median_us"]]
    bars = ax.bar(labels, vals, color=["#8b5cf6", "#22d3ee"])
    ax.set_ylabel("Median batch time (microseconds)")
    ax.set_title(f"Runtime for the full batch ({reps} repetitions)")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,.0f}", ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def _chart_states(path, nfa, dfa):
    fig, ax = plt.subplots(figsize=(6, 4))
    vals = [len(nfa.states), len(dfa.states)]
    bars = ax.bar(["NFA", "DFA"], vals, color=["#8b5cf6", "#22d3ee"])
    ax.set_ylabel("Number of states")
    ax.set_title("State count")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v, str(v), ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def _chart_scaling(path, rows):
    fig, ax = plt.subplots(figsize=(6, 4))
    xs = [r["chars"] for r in rows]
    ax.plot(xs, [r["nfa_us"] for r in rows], "o-", color="#8b5cf6", label="NFA")
    ax.plot(xs, [r["dfa_us"] for r in rows], "o-", color="#22d3ee", label="DFA")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Input size (characters)")
    ax.set_ylabel("Median time (microseconds)")
    ax.set_title("Runtime versus input size")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def run_benchmark(repetitions=30, warmup=3, texts=None, include_scaling=True):
    if not isinstance(repetitions, int) or isinstance(repetitions, bool) or not 1 <= repetitions <= MAX_REPETITIONS:
        raise BenchmarkError(f"'repetitions' must be an integer from 1 to {MAX_REPETITIONS}.")
    if not isinstance(warmup, int) or isinstance(warmup, bool) or not 0 <= warmup <= MAX_WARMUP:
        raise BenchmarkError(f"'warmup' must be an integer from 0 to {MAX_WARMUP}.")
    nfa, dfa = get_automata()
    if texts is None:
        texts = [e["text"] for e in load_dataset()]
    if not texts:
        raise BenchmarkError("No emails to benchmark.")
    _check_equivalent(nfa, dfa, texts)

    nfa_s = _stats(_measure(nfa.run, texts, repetitions, warmup), len(texts))
    dfa_s = _stats(_measure(dfa.run, texts, repetitions, warmup), len(texts))
    ratio = nfa_s["median_us"] / dfa_s["median_us"] if dfa_s["median_us"] > 0 else None

    scaling = []
    if include_scaling:
        base = " ".join(texts)
        for target in (1_000, 10_000, 100_000):
            big = (base * (target // max(len(base), 1) + 1))[:target]
            n = _stats(_measure(nfa.run, [big], 5, 1), 1)["median_us"]
            d = _stats(_measure(dfa.run, [big], 5, 1), 1)["median_us"]
            scaling.append({"chars": target, "nfa_us": n, "dfa_us": d})

    os.makedirs(config.GENERATED_DIR, exist_ok=True)
    _chart_runtime(os.path.join(config.GENERATED_DIR, "benchmark_runtime.png"), nfa_s, dfa_s, repetitions)
    _chart_states(os.path.join(config.GENERATED_DIR, "benchmark_states.png"), nfa, dfa)
    charts = {"runtime": "benchmark_runtime.png", "states": "benchmark_states.png"}
    if scaling:
        _chart_scaling(os.path.join(config.GENERATED_DIR, "benchmark_scaling.png"), scaling)
        charts["scaling"] = "benchmark_scaling.png"

    if ratio is None:
        verdict = "Timing too small to compare."
    elif 0.9 <= ratio <= 1.1:
        verdict = "The two simulators were within 10% of each other in this run."
    elif ratio > 1:
        verdict = f"The DFA was {ratio:.2f}x faster than the NFA in this run."
    else:
        verdict = f"The NFA was {1 / ratio:.2f}x faster than the DFA in this run."

    return {
        "emails": len(texts), "characters": sum(len(t) for t in texts),
        "repetitions": repetitions, "warmup": warmup, "unit": "microseconds (batch of all emails)",
        "nfa": nfa_s, "dfa": dfa_s, "speedup_nfa_over_dfa": ratio, "summary": verdict,
        "states": {"nfa": len(nfa.states), "dfa": len(dfa.states)},
        "equivalent": True, "scaling": scaling, "charts": charts,
        "methodology": ("Each repetition times one pass over all emails with time.perf_counter(). "
                        "Warm-up passes are discarded. Both simulators produce the same match list; "
                        "equivalence is verified before timing. Results depend on this computer and "
                        "Python's interpreter overhead."),
    }
