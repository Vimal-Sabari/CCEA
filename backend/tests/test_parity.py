"""
Parity tests - the CCEA core must reproduce the notebook's published numbers,
and the LLM seam must not change anything when it is off.

Run:  cd cce-app/backend && pytest -q
"""

import csv
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import ccea_core  # noqa: E402

HERE = os.path.dirname(__file__)
SINGLE = os.path.join(HERE, "..", "sample_data", "CCE_single_sample.csv")
ALL = os.path.join(HERE, "..", "sample_data", "CCE_all_samples.csv")

# Reference value from CCE_1 _sample.ipynb (sample 15232, best generation 81).
NOTEBOOK_BEST_FITNESS = 0.8225830169154041
NOTEBOOK_IS_AGGR = 0.5952743027728105
NOTEBOOK_RS_AGGR = 0.10561177090573833
NOTEBOOK_BEST_GENERATION = 81


def _rows(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def test_single_sample_matches_notebook():
    result = ccea_core.run_all(_rows(SINGLE))
    s = result["samples"][0]
    assert s["hash"] == "15232"
    assert s["best_generation"] == NOTEBOOK_BEST_GENERATION
    assert s["best_fitness_full"] == pytest.approx(NOTEBOOK_BEST_FITNESS, abs=1e-12)
    assert s["is_aggr"] == pytest.approx(round(NOTEBOOK_IS_AGGR, 6), abs=1e-9)
    assert s["rs_aggr"] == pytest.approx(round(NOTEBOOK_RS_AGGR, 6), abs=1e-9)


def test_llm_seam_off_is_identical():
    """reduced_severity_fn=None must give byte-identical output to the default path."""
    a = ccea_core.run_all(_rows(SINGLE), reduced_severity_fn=None)
    b = ccea_core.run_all(_rows(SINGLE))
    assert a == b


def test_llm_seam_receives_whole_combination_and_can_reproduce_placeholder():
    """A trivial estimator that just echoes each candidate's CSV value must
    reproduce the no-LLM result exactly - proving the seam is wired correctly."""
    rows = ccea_core.validate_and_normalise(_rows(SINGLE))
    rs_lookup = {(r["Hash"], r["Candidate_ID"]): r["Reduced_Severity"] for r in rows}

    def echo_estimator(ctx: ccea_core.CombinationContext) -> dict:
        assert len(ctx.entries) >= 1
        return {
            e.signature_id: rs_lookup[(ctx.sample_hash, e.candidate_id)]
            for e in ctx.entries
        }

    with_fn = ccea_core.run_all(_rows(SINGLE), reduced_severity_fn=echo_estimator)
    without = ccea_core.run_all(_rows(SINGLE))
    assert with_fn["samples"][0]["best_fitness_full"] == pytest.approx(
        without["samples"][0]["best_fitness_full"], abs=1e-12
    )


def test_all_samples_run():
    result = ccea_core.run_all(_rows(ALL))
    assert result["aggregate"]["n_samples"] == 17
    assert result["samples"][0]["best_fitness_full"] == pytest.approx(
        NOTEBOOK_BEST_FITNESS, abs=1e-12
    )
    for s in result["samples"]:
        assert 0.0 <= s["best_fitness"] <= 1.0
        assert len(s["optimal_combination"]) == s["n_signatures"]


def test_validation_rejects_bad_data():
    bad = [{"Candidate_ID": "C1", "Hash": "h", "Signature_ID": "1",
            "Defense_ID": "17", "Attack_Plan_Score": "999", "Reduced_Severity": "1"}]
    with pytest.raises(ccea_core.ValidationError):
        ccea_core.run_all(bad)


def test_sample1_csv_schema_and_2_generations():
    sample1_path = os.path.join(HERE, "..", "..", "SAMPLE1.csv")
    rows = _rows(sample1_path)
    norm = ccea_core.validate_and_normalise(rows)
    assert len(norm) == len(rows)

    # Verify context fields are preserved
    c1 = norm[0]
    assert c1["Initial_Severity"] == 1
    assert "Discovery" in c1["Tactics"]
    assert "Debugger Evasion" in c1["Technique"]
    assert c1["has_initial_severity"] is True

    c14 = norm[13]
    assert c14["Attack_Plan_Score"] == 20.0  # Quantified 1..35
    assert c14["Initial_Severity"] == 2      # Unquantified 1..6

    # Test running 2 generations
    res = ccea_core.run_all(rows, max_generations=2)
    s = res["samples"][0]
    assert s["generations_run"] <= 2
    assert len(s["generation_history"]) <= 2
    assert len(s["optimal_combination"]) == s["n_signatures"]

