# CCEA backend

FastAPI wrapper around the Cooperative Coevolutionary Algorithm. `ccea_core.py`
is the single implementation; the parity test pins its output to the reference
value (`15232 -> 0.8225830169154041`).

## Run

```bash
cd cce-app/backend
python -m venv .venv
.venv\Scripts\activate            # Windows   (source .venv/bin/activate on mac/linux)
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `/api/health` | params + LLM status |
| POST | `/api/analyze` | multipart `file=` a `.csv` (CCE.csv schema) or the multi-sheet `.xlsx`; returns JSON |
| POST | `/api/analyze?download=csv` | same, but returns the optimal combinations as a CSV file |
| POST | `/api/analyze?use_llm=true` / `false` | force / skip the LLM estimator for this request |

Response: `{ parameters, reduced_severity_source, samples[], aggregate }`.
Each sample has `best_fitness`, `best_generation`, `is_aggr`, `rs_aggr`,
`optimal_combination[]`, `generation_history[]`.

## Files

| File | Purpose |
|---|---|
| `ccea_core.py` | the algorithm — single source of truth, do not fork |
| `main.py` | FastAPI routes + CSV/XLSX parsing |
| `llm.py` | **the only file to edit for LLM integration** |
| `LLM_INTEGRATION.md` | step-by-step for wiring the LLM |
| `tests/test_parity.py` | asserts `15232 → 0.8225830169154041` and that the LLM seam is a no-op when off |
| `sample_data/` | `CCE_single_sample.csv`, `CCE_all_samples.csv`, `CCE_all_samples.xlsx` |

## Test

```bash
pytest -q
```
