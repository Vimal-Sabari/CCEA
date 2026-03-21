# CCEA — Cooperative Coevolutionary Defense Optimizer

Given a malware sample's triggered signatures and a pool of candidate defensive
controls, the CCEA searches for the **best defense per signature** — the
combination that neutralises the most attack severity.

```
Attack severity per signature   ─┐
Defense candidates per signature ─┼─►  CCEA  ─►  optimal defense combination + fitness
Reduced severity (per candidate) ─┘            (per malware sample)
```

## Layout

| Path | What |
|---|---|
| `notebooks/CCE_single_sample.ipynb` | reference implementation, one sample, step by step |
| `notebooks/CCE_all_samples.ipynb` | generalised to all 17 samples + aggregate reporting; evaluation-metrics section is a stub |
| `data/CCE.csv` | one sample (`15232`) |
| `data/CCE_AllSamples.xlsx` | 17 samples, one sheet each |
| `data/CCE_AllSamples_long.csv` | 17 samples stacked (2,823 rows) |
| `data/samples/` | the 17 samples as individual CSVs |
| `backend/` | FastAPI service wrapping the algorithm (`ccea_core.py`) |
| `frontend/` | static upload → results web UI |
| `docs/CCEA_flowchart.*` | the workflow diagram |

## Dataset columns

`Candidate_ID, Hash, Signature_ID, Defense_ID, Attack_Plan_Score, Reduced_Severity`

- **`Defense_ID`** — the chosen defensive control (catalog id `1..42`).
- **`Attack_Plan_Score`** — signature severity (`1..35`), from the analyst rubric.
- **`Reduced_Severity`** — severity left after the defense (`0..10`). Currently
  taken from the data; an LLM is meant to produce it later — see
  `backend/LLM_INTEGRATION.md`.

## The algorithm (per sample)

1. Split defense candidates into subpopulations, one per triggered signature.
2. Each generation: pick one representative defense per signature
   (unexplored → random exploration → best-so-far) with occasional mutation →
   a complete defense combination.
3. Score it: `Fitness = (IS_Aggr − RS_Aggr) / IS_Aggr`, where `IS_Aggr` /
   `RS_Aggr` are the RMS of mapped attack severity / mapped reduced severity
   across all signatures.
4. The combination's fitness is credited to every participating candidate.
5. Stop when every candidate has been tried and the best hasn't improved for
   20 generations.

Deterministic: `RANDOM_SEED = 42`. Reference value — sample `15232` →
best fitness `0.8225830169154041` at generation 81 (pinned by
`backend/tests/test_parity.py`).

## Run

**Backend**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --port 8000
pytest -q          # 5 parity tests
```

**Frontend**
```bash
cd frontend
python -m http.server 5500      # open http://localhost:5500
```

Upload a `.csv` (the schema above) or the multi-sheet `.xlsx`; the backend runs
the CCEA and returns the optimal defense combination per sample with a
convergence chart.
