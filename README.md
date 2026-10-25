# CCEA Optimizer

**Cooperative Coevolutionary Defense Optimizer** for selecting an effective
defense combination against the signatures triggered by a malware sample.

The project combines a Python/FastAPI backend, a lightweight browser frontend,
reference notebooks, and prepared signature/defense datasets. Upload a CSV or
multi-sheet Excel report and the optimizer returns one defense candidate per
triggered signature, the resulting fitness, and a generation-by-generation
convergence history.

> **Responsible-use notice:** This project is intended for defensive security
> research, malware-analysis education, and controlled laboratory environments.
> Do not use it to deploy malware, evade detection, or test systems without
> authorization.

## Contents

- [What the optimizer does](#what-the-optimizer-does)
- [Repository layout](#repository-layout)
- [Algorithm](#algorithm)
- [Input data](#input-data)
- [Quick start](#quick-start)
- [Using the API](#using-the-api)
- [Using the web interface](#using-the-web-interface)
- [Optional LLM severity estimation](#optional-llm-severity-estimation)
- [Reference notebooks and workflow diagram](#reference-notebooks-and-workflow-diagram)
- [Testing](#testing)
- [Configuration and limitations](#configuration-and-limitations)
- [Troubleshooting](#troubleshooting)

## What the optimizer does

For each malware sample, the CCEA:

1. Identifies the triggered signatures in the input report.
2. Creates one defense subpopulation for each signature.
3. Evolves a complete combination containing one candidate from every
   subpopulation.
4. Evaluates the combination using attack severity and reduced severity.
5. Credits the combination's fitness to its participating candidates.
6. Stops after all candidates have been explored and the result has not
   improved for the configured patience window, or after the generation limit.

The result is an **optimal defense strategy found by the configured search**;
it is not a proof that the global optimum has been exhaustively enumerated.

## Repository layout

| Path | Description |
| --- | --- |
| `backend/ccea_core.py` | Single source of truth for validation, CCEA search, scoring, and aggregation. |
| `backend/main.py` | FastAPI application, upload parsing, CORS configuration, and result download endpoint. |
| `backend/llm.py` | Optional reduced-severity adapter and cache. |
| `backend/README.md` | Backend-specific endpoint and implementation notes. |
| `backend/LLM_INTEGRATION.md` | Setup and integration guide for the optional evaluator harness. |
| `backend/tests/test_parity.py` | Reference-output, validation, multi-sample, and LLM-seam tests. |
| `backend/mappings/` | Signature and defense ID-to-name mappings used by the LLM adapter. |
| `backend/sample_data/` | Small backend fixtures used by tests. |
| `frontend/index.html` | Static application shell and upload UI. |
| `frontend/main.js` | Upload flow, API calls, results rendering, charts, and UI interactions. |
| `frontend/styles.css` | Frontend styling and responsive layout. |
| `data/CCE.csv` | Single-sample input for sample `15232`. |
| `data/CCE_AllSamples.xlsx` | Multi-sheet workbook containing 17 samples. |
| `data/CCE_AllSamples_long.csv` | The same sample set in one long-form CSV. |
| `data/samples/` | Individual CSV files for the 17 prepared samples. |
| `notebooks/` | Step-by-step single-sample and all-sample reference implementations. |
| `docs/CCEA_flowchart.md` | Mermaid workflow diagram for the optimizer. |

## Algorithm

### Parameters

The default parameters are defined in `backend/ccea_core.py` and are also
returned by the API:

| Parameter | Default | Meaning |
| --- | ---: | --- |
| `random_seed` | `42` | Seed used for reproducible single-sample runs. |
| `max_generations` | `150` | Maximum generations per sample. |
| `mutation_probability` | `0.20` | Probability of replacing a selected representative within its subpopulation. |
| `exploration_probability` | `0.25` | Probability of random exploration instead of best-so-far selection. |
| `patience` | `20` | Non-improving generations allowed after all candidates have been evaluated. |
| `min_mapped_score` | `0.03` | Lower bound used when mapping attack scores. |
| `max_attack_plan_score` | `35` | Maximum quantified attack-plan score. |
| `max_reduced_severity` | `10` | Maximum reduced-severity value. |

Each sample uses seed `random_seed + sample_index`, so the default CSV path is
repeatable when the input and parameters remain unchanged.

### Fitness

Attack-plan scores are mapped into the normalized range used by the optimizer.
Reduced severity is mapped relative to the selected attack score. The aggregate
values use root mean square (RMS):

```text
IS_Aggr = RMS(mapped attack severity)
RS_Aggr = RMS(mapped reduced severity)
Fitness = (IS_Aggr - RS_Aggr) / IS_Aggr
```

A higher fitness means greater estimated severity reduction. A fitness of `1`
represents complete reduction under the scoring model; the API rounds display
values to six decimal places and also includes `best_fitness_full`.

The implementation in `backend/ccea_core.py` is intentionally shared by the
backend and the notebooks so that the reference calculations do not diverge.

## Input data

### Required columns

Every CSV row represents one candidate defense for one signature:

| Column | Description |
| --- | --- |
| `Candidate_ID` | Unique candidate row identifier. |
| `Attack_Plan_Score` | Quantified signature severity, from `1` to `35`. |
| `Reduced_Severity` | Severity remaining after the defense, from `0` to `10`, used by the default CSV path. |

### Optional columns

| Column | Description |
| --- | --- |
| `Hash` | Sample identifier. If omitted, a placeholder is generated. |
| `Signature_ID` | Signature identifier. If omitted, `Signature_Name` is used. |
| `Defense_ID` | Defense identifier. If omitted, `Defenses` is used. |
| `Signature_Name` | Human-readable signature name and fallback signature identifier. |
| `Defense_Name` | Human-readable defense name. |
| `Initial_Severity` | Unquantified severity band (`1` to `6`) used by the LLM adapter. |
| `Tactics`, `Technique` | Contextual ATT&CK-style metadata for LLM evaluation. |
| `Signature_Description`, `Defense_Description` | Additional context for LLM evaluation. |

The validator normalizes identifiers and numeric fields and rejects empty input,
missing required columns, invalid ranges, and malformed values with an
actionable validation error.

## Quick start

### 1. Create a virtual environment

From the `CCEA/` project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate       # macOS/Linux
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
```

### 2. Install backend dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

### 3. Start the backend

```bash
python -m uvicorn main:app --reload --port 8000
```

The command above must be run from `CCEA/backend`, or use the equivalent:

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

### 4. Start the frontend

In a second terminal, from `CCEA/`:

```bash
python -m http.server 5500 --directory frontend
```

Open <http://localhost:5500>. The frontend defaults to
`http://localhost:8000` for the backend.

## Using the API

### Health check

```bash
curl http://localhost:8000/api/health
```

The response includes the current algorithm parameters and the active
reduced-severity source.

### Analyze a CSV

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@data/CCE.csv"
```

### Analyze an Excel workbook

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@data/CCE_AllSamples.xlsx"
```

The backend reads every non-metadata worksheet containing the expected columns
and combines the rows before running one optimization per sample hash.

### Control the generation count

For a quick experiment, pass `generations`:

```bash
curl -X POST "http://localhost:8000/api/analyze?generations=25" \
  -F "file=@data/CCE.csv"
```

### Download optimal combinations as CSV

```bash
curl -X POST "http://localhost:8000/api/analyze?download=csv" \
  -F "file=@data/CCE.csv" \
  -o optimal_defense_combinations.csv
```

### API response

The JSON response has this top-level shape:

```json
{
  "parameters": {},
  "reduced_severity_source": "csv_placeholder",
  "samples": [],
  "aggregate": {}
}
```

Each item in `samples` contains the sample hash and label, candidate and
signature counts, search-space size, generations run, aggregate attack and
reduced-severity values, best fitness, the `optimal_combination`, and
`generation_history`. The `aggregate` object reports the number of samples and
mean, standard deviation, minimum, median, and maximum best fitness.

## Using the web interface

The static frontend requires no JavaScript build step:

1. Start the backend on port `8000`.
2. Serve `frontend/` on port `5500`.
3. Click **Get Started** or drag a `.csv`/`.xlsx` report onto the page.
4. Review aggregate metrics, per-sample results, the convergence chart, and
   the selected defense combination.

To use a different backend URL, set it in the browser console and reload:

```javascript
localStorage.setItem("CCEA_API", "http://localhost:8000");
location.reload();
```

The frontend can export the currently analyzed combinations through the API's
CSV download behavior. Chart.js and other visual assets are loaded from CDNs,
so an internet connection may be required for every visual enhancement to
render correctly.

## Optional LLM severity estimation

The default and fully offline path uses the input file's `Reduced_Severity`
column. An optional evaluator can estimate reduced severity instead:

```bash
export LLM_ENABLED=1
```

Or enable it for one request:

```bash
curl -X POST "http://localhost:8000/api/analyze?use_llm=true" \
  -F "file=@data/CCE.csv"
```

Force the CSV path for a request with `use_llm=false`. The adapter calls the
external evaluator once per signature-defense pair where possible and caches
results. LLM mode requires the separate evaluator harness, its dependencies,
the required mapping/data files, and a configured `GEMINI_API_KEY`.

Read [backend/LLM_INTEGRATION.md](backend/LLM_INTEGRATION.md) before enabling
this mode. Never commit API keys or evaluator credentials. LLM results are
not guaranteed to match the deterministic CSV parity reference.

## Reference notebooks and workflow diagram

- `notebooks/CCE_single_sample.ipynb` walks through the optimizer for one
  sample.
- `notebooks/CCE_all_samples.ipynb` runs the workflow for all 17 samples and
  produces aggregate reporting.
- `docs/CCEA_flowchart.md` documents the attack population, defense
  subpopulations, generation loop, scoring, and output flow.

The notebooks are useful for research and inspection; the backend's
`ccea_core.py` remains the production implementation used by the API.

## Testing

Install the dependencies, activate the virtual environment, and run:

```bash
cd backend
pytest -q
```

The tests verify:

- parity with the published sample `15232` reference fitness
  (`0.8225830169154041`);
- identical output when the LLM seam is explicitly disabled;
- operation across all 17 samples;
- validation of out-of-range data;
- preservation of contextual fields and short generation runs.

## Configuration and limitations

- CORS is permissive for local development (`allow_origins=["*"]`). Restrict
  origins before deploying the API publicly.
- The frontend is a static development UI and has no authentication or
  authorization layer.
- The default API processes uploaded files in memory and does not persist
  uploads.
- The optimizer's search is stochastic but seeded for reproducibility.
- Aggregate evaluation baselines and multi-seed benchmarking are not yet part
  of the application output.
- The optional LLM path introduces external service availability, rate-limit,
  cost, and model-variation concerns.

## Troubleshooting

| Problem | Resolution |
| --- | --- |
| `ModuleNotFoundError` when starting the API | Activate `.venv` and install `backend/requirements.txt`. |
| Browser cannot reach the API | Confirm the backend is running on port `8000` and check `CCEA_API` in local storage. |
| `422` response from `/api/analyze` | Check required columns, numeric ranges, and that the file contains data rows. |
| Excel upload returns no samples | Ensure worksheets contain `Candidate_ID` and `Signature_ID` headers and are not metadata sheets prefixed with `_`. |
| LLM request returns an availability error | Follow the evaluator setup in `backend/LLM_INTEGRATION.md`; the normal CSV path does not require the LLM. |

## License and contribution

This repository does not currently declare a license. Confirm the intended
license with the project owners before redistributing the code or datasets.
Keep algorithm changes in `backend/ccea_core.py`, update the relevant tests and
documentation, and preserve the reference parity test when modifying scoring
or candidate-selection behavior.
