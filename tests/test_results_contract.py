import json
from pathlib import Path

import pytest

from ai.evaluate_triage import wilson_interval


ROOT = Path(__file__).resolve().parents[1]


def test_wilson_interval_for_baseline_result():
    lower, upper = wilson_interval(23, 26)
    assert lower == pytest.approx(0.7102409679)
    assert upper == pytest.approx(0.9599675538)


@pytest.mark.parametrize("correct,total", [(-1, 26), (27, 26), (0, 0)])
def test_wilson_interval_rejects_invalid_counts(correct, total):
    with pytest.raises(ValueError):
        wilson_interval(correct, total)


def test_readme_results_match_versioned_evaluation():
    """Prevent recruiter-facing numbers from drifting from versioned results."""
    results = json.loads((ROOT / "ai" / "triage_results.json").read_text(encoding="utf-8"))
    tickets = json.loads((ROOT / results["dataset"]).read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert results["fictional_data"] is True
    assert results["total_tickets"] == len(tickets) == 26
    for run in results["runs"]:
        lower, upper = wilson_interval(run["correct"], results["total_tickets"])
        assert run["accuracy"] == pytest.approx(run["correct"] / results["total_tickets"])
        assert run["accuracy_95_ci"] == pytest.approx([lower, upper], abs=0.0005)
        claim = (
            f"| {run['prompt_version']} | **{run['correct']} / {results['total_tickets']}** | "
            f"{run['accuracy']:.1%} ({run['accuracy_95_ci'][0]:.1%}–{run['accuracy_95_ci'][1]:.1%}) |"
        )
        assert claim in readme
