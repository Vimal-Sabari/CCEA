"""
LLM option for `Reduced_Severity`.

The CCEA needs one number it does not compute itself: **reduced severity** - how
much attack severity is LEFT after a defense is applied.

There are two sources, chosen with a toggle:

  * OFF (default)  -> use the `Reduced_Severity` value already in the CSV
  * ON             -> ask an LLM, via the Gemini evaluator in `evaluate.py`
                      (per signature-defense pair, with rate limiting and caching)

Toggle it with:
  - env  LLM_ENABLED=1
  - or per request:  POST /api/analyze?use_llm=true   (?use_llm=false forces OFF)

This module is a thin ADAPTER between the CCEA seam and that evaluator.
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import ccea_core
from ccea_core import CombinationContext

# ----------------------------------------------------------------------
# config
# ----------------------------------------------------------------------
LLM_ENABLED = os.getenv("LLM_ENABLED", "0").lower() in ("1", "true", "yes", "on")

_BACKEND_DIR = Path(__file__).resolve().parent
_MAP_DIR = _BACKEND_DIR / "mappings"
_WINDOWS_DIR = _BACKEND_DIR / "windows" if (_BACKEND_DIR / "windows").is_dir() else _BACKEND_DIR.parent / "windows"


class LLMUnavailable(RuntimeError):
    """Raised when the LLM option is requested but the harness is not set up."""


# ----------------------------------------------------------------------
# lazy loaders  (nothing runs until the LLM option is actually used)
# ----------------------------------------------------------------------
_evaluate_mod = None
_sig_index = None
_sig_id2name: dict[str, str] = {}
_def_id2name: dict[str, str] = {}
_initial_sev: dict[str, int] = {}
_PAIR_CACHE: dict[tuple[str, str], float] = {}


def _load_id_maps() -> None:
    if _sig_id2name and _def_id2name:
        return
    for fn, tgt, kcol, vcol in (
        ("signature_id_name.csv", _sig_id2name, "Signature_ID", "Signature_Name"),
        ("defense_id_name.csv", _def_id2name, "Defense_ID", "Defense_Name"),
    ):
        path = _MAP_DIR / fn
        if not path.exists():
            raise LLMUnavailable(f"missing id->name map: {path}")
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                tgt[str(row[kcol]).strip()] = str(row[vcol]).strip()


def _load_initial_severity() -> None:
    """Fallback Initial_Severity (1..6 band) per signature from data.csv if present."""
    if _initial_sev:
        return
    data_csv = _BACKEND_DIR / "data.csv" if (_BACKEND_DIR / "data.csv").exists() else _BACKEND_DIR.parent / "data.csv"
    if not data_csv.exists():
        return
    with open(data_csv, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = [h.strip() for h in next(reader, [])]
        col = {h: i for i, h in enumerate(header) if h}
        if "Signature_Name" in col and "Initial_Severity" in col:
            si, vi = col["Signature_Name"], col["Initial_Severity"]
            for r in reader:
                if len(r) > max(si, vi) and r[si].strip():
                    try:
                        _initial_sev[r[si].strip()] = int(r[vi].strip())
                    except ValueError:
                        pass


def _load_evaluator():
    global _evaluate_mod, _sig_index
    if _evaluate_mod is not None:
        return _evaluate_mod

    sys.path.insert(0, str(_BACKEND_DIR))
    try:
        import evaluate as _ev
    except Exception as exc:
        raise LLMUnavailable(
            f"could not import evaluate.py: {exc}. "
            "Install its dependencies (pip install google-genai python-dotenv requests) and "
            "set GEMINI_API_KEY."
        ) from exc

    _evaluate_mod = _ev
    if _WINDOWS_DIR.exists():
        _sig_index = _ev.build_signature_index(_WINDOWS_DIR)
    else:
        _sig_index = {}
    return _ev


# ======================================================================
# the estimator passed to ccea_core.run_all(reduced_severity_fn=...)
# ======================================================================
_CACHE: dict[tuple, dict] = {}


def _cache_key(ctx: CombinationContext) -> tuple:
    return tuple(sorted((e.signature_id, e.candidate_id) for e in ctx.entries))


def _call_llm(ctx: CombinationContext) -> dict:
    """One (signature, defense) LLM evaluation per entry -> {signature_id: reduced_severity}."""
    ev = _load_evaluator()
    _load_initial_severity()

    out: dict[str, float] = {}
    ev.init_results_csv(ev.RESULTS_CSV)

    for e in ctx.entries:
        # Prefer names embedded in the context entry (populated from the CSV row).
        # Only fall back to the id->name lookup files when the inline name is absent.
        sig_name = getattr(e, "signature_name", "") or ""
        def_name = getattr(e, "defense_name", "") or ""

        if not sig_name or not def_name:
            # Try to load the mapping files as a fallback
            try:
                _load_id_maps()
            except LLMUnavailable:
                pass  # no mapping file - we'll rely on inline names or raise below
            if not sig_name:
                sig_name = _sig_id2name.get(str(e.signature_id), str(e.signature_id))
            if not def_name:
                def_name = _def_id2name.get(str(e.defense_id), str(e.defense_id))

        if not sig_name:
            raise LLMUnavailable(f"no signature name for Signature_ID={e.signature_id}")
        if not def_name:
            raise LLMUnavailable(f"no defense name for Defense_ID={e.defense_id}")

        pair_key = (str(e.signature_id), str(e.defense_id))
        if pair_key in _PAIR_CACHE:
            cached_val = _PAIR_CACHE[pair_key]
            out[str(e.signature_id)] = cached_val
            print(f"  [CACHE HIT] Sig {e.signature_id} ({sig_name}) vs Def {e.defense_id} ({def_name}) -> RS={cached_val}")
            continue

        # Unquantified initial severity (1..6) for LLM
        if e.has_initial_severity or getattr(e, "initial_severity", None):
            is_band = int(e.initial_severity)
        else:
            _load_initial_severity()
            is_band = _initial_sev.get(sig_name)
            if is_band is None:
                is_band = max(1, min(6, int(round(1 + 5 * (e.attack_plan_score - 1) / 34))))

        row = ev.CsvRow(
            signature_name=sig_name,
            defense=def_name,
            initial_severity=is_band,
            signature_description=e.signature_description,
            tactics=e.tactics,
            technique=e.technique,
            defense_description=e.defense_description,
        )
        sig_info = _sig_index.get(sig_name) if _sig_index else None
        print(f"  [LLM CALL] Gen {ctx.generation} | Sig: {sig_name} | Def: {def_name} | IS={is_band}...")
        res = ev.evaluate_row(row, sig_info, run_id="ccea")
        val = float(res.llm_value)
        _PAIR_CACHE[pair_key] = val
        out[str(e.signature_id)] = val
        print(f"    -> LLM returned RS={val} ({res.mitigation_label}) | {res.blocked_trigger_paths}/{res.total_trigger_paths} paths blocked")
        ev.append_result(ev.RESULTS_CSV, res)

    return out


def estimate_reduced_severity(ctx: CombinationContext) -> dict:
    """Cached LLM estimator. Same (signature, defense) set -> same result."""
    key = _cache_key(ctx)
    if key not in _CACHE:
        result = {str(k): float(v) for k, v in _call_llm(ctx).items()}
        _CACHE[key] = result
    return _CACHE[key]


def clear_cache() -> None:
    _CACHE.clear()
    _PAIR_CACHE.clear()


# ======================================================================
# factory  -  used by main.py
# ======================================================================
def get_estimator(force: bool | None = None):
    """Return the LLM estimator, or None to use the CSV Reduced_Severity.

    force=True  -> LLM  (ignores LLM_ENABLED)
    force=False -> CSV
    force=None  -> follow the LLM_ENABLED env var
    """
    use = LLM_ENABLED if force is None else force
    return estimate_reduced_severity if use else None


def status() -> dict:
    """Small dict for /api/health."""
    return {
        "llm_enabled": LLM_ENABLED,
        "source": "llm (Gemini via evaluate.py)" if LLM_ENABLED else "csv (Reduced_Severity column)",
        "eval_dir": str(_BACKEND_DIR),
        "windows_dir_found": _WINDOWS_DIR.is_dir(),
    }
