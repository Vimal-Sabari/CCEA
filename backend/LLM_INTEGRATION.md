# Reduced_Severity: CSV vs LLM

`Reduced_Severity` (how much attack severity is LEFT after a defense) has **two
sources**, switchable at runtime.

| | source |
|---|---|
| **OFF** (default) | the `Reduced_Severity` value in the uploaded CSV / XLSX |
| **ON** | an LLM — the Gemini evaluator in `AG Cuckoo Very new/evaluate.py`, run per `(signature, defense)` pair |

## The toggle

- env: `LLM_ENABLED=1`
- per request: `POST /api/analyze?use_llm=true`  (`?use_llm=false` forces OFF)
- `GET /api/health` → `reduced_severity` block shows which source is active and
  whether the evaluator folder was found.
- Notebooks: a `USE_LLM = False` flag near the top (loads the `*_llm.csv` variant
  when `True`).

Everything downstream is identical either way; only the number changes.

## How the LLM path is wired

`llm.py` is a thin **adapter**. It does not talk to Gemini itself — it calls
`evaluate.py`:

```
_call_llm(ctx):
    for each signature in the combination:
        Signature_ID -> name   (mappings/signature_id_name.csv)
        Defense_ID   -> name   (mappings/defense_id_name.csv)
        Initial_Severity       (from <CUCKOO_EVAL_DIR>/data.csv)
        evaluate.evaluate_row(CsvRow(name, defense, IS), sig_source) -> llm_value
    return {signature_id: llm_value}
```

Results are cached by the set of `(signature_id, candidate_id)` so a full CCEA
run makes only ~one Gemini call per distinct pair.

## Setup (owner of evaluate.py — points 4 & 5)

1. Put the harness folder where the adapter can find it:
   - default: `<repo>/AG Cuckoo Very new/` (kept out of git), or
   - set `CUCKOO_EVAL_DIR=/path/to/AG Cuckoo Very new`
   It must contain `evaluate.py`, `windows/`, `data.csv`.
2. Deps for `evaluate.py`: `pip install google-genai python-dotenv requests`
3. `GEMINI_API_KEY` in `AG Cuckoo Very new/.env` (never commit it). Remove the
   literal default in `evaluate.py`.
4. `data.csv` currently covers sample `15232` only. Extend it with an
   `Initial_Severity` row for every `(signature, defense)` pair of the other
   samples so the adapter can look the band up.
5. Confirm the model id (`gemini-3.6-flash`).

## Notes

- Parity ("matches the reference `0.8225830169154041`") holds only with the CSV
  source. With the LLM on, results are as stable as the model + cache.
- `llm.LLMUnavailable` is raised with an actionable message if the LLM path is
  requested before the harness is set up; the API returns it as a 400.
