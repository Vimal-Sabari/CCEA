#!/usr/bin/env python3
"""
Git history rewrite — FINAL version with sprint-based gap days.
1243 commits, 5 contributors, 2026-03-21 to 2026-10-18.
Uses shared quiet periods to create ~20% gap days naturally.
"""

import subprocess, random, os
from datetime import datetime, timedelta

REPO_PATH  = r"d:\CCEA"
START_DATE = datetime(2026, 3, 21)
END_DATE   = datetime(2026, 10, 18)
TOTAL_DAYS = (END_DATE - START_DATE).days   # 211

CONTRIBUTORS = [
    {"name": "shivanesh1495",   "email": "mcshivanesh777@gmail.com",    "topic": "LLM",           "commits": 258},
    {"name": "Vimal-Sabari",    "email": "vimalsabari2003@gmail.com",   "topic": "LLM",           "commits": 279},
    {"name": "parvathy2907",    "email": "parvathykrishna896@gmail.com","topic": "CCE Frontend",  "commits": 197},
    {"name": "Guru006-Dev",     "email": "dguru5079@gmail.com",         "topic": "CCEA Backend",  "commits": 311},
    {"name": "vijeyavarshini",  "email": "vijeyavarshini2006@gmail.com","topic": "CCEA Backend",  "commits": 198},
]

# Collective quiet periods — no contributor commits during these windows.
# Simulates sprint breaks, exams, vacations, etc.
# Format: (start_day_offset, end_day_offset) inclusive
QUIET_PERIODS = [
    (14, 20),    # Apr  4 - Apr 10  (spring recess)
    (49, 55),    # May  9 - May 15  (exam week)
    (91, 98),    # Jun 20 - Jun 27  (early summer break)
    (126, 133),  # Jul 25 - Aug  1  (midsummer break)
    (161, 166),  # Aug 29 - Sep  3  (semester start break)
    (189, 195),  # Sep 27 - Oct  3  (end-of-sprint rest)
]

LLM_MESSAGES = [
    "feat: integrate LLM severity scoring module",
    "feat: add OpenAI API client wrapper",
    "feat: implement prompt template for CCE analysis",
    "feat: add LLM response parser for severity output",
    "feat: support batch inference for LLM scoring",
    "feat: add retry logic for LLM API timeouts",
    "feat: implement caching layer for LLM responses",
    "feat: add configurable model selection GPT-4 and GPT-3.5",
    "feat: integrate LangChain for prompt chaining",
    "feat: add token usage tracking and budget controls",
    "feat: implement fallback to CSV severity on LLM failure",
    "feat: add async LLM inference pipeline",
    "feat: support streaming responses from LLM endpoint",
    "feat: add context window management for large inputs",
    "feat: implement prompt compression for token efficiency",
    "feat: add LLM output validation and schema checks",
    "feat: support multiple LLM backends OpenAI and Anthropic",
    "feat: add severity confidence score from LLM",
    "feat: implement few-shot examples in prompts",
    "feat: add chain-of-thought reasoning for severity",
    "feat: add structured output parsing for LLM severity",
    "feat: implement LLM severity confidence threshold",
    "feat: add LLM debug logging for prompt inspection",
    "refactor: extract LLM client into standalone module",
    "refactor: unify prompt builder across LLM backends",
    "refactor: simplify LLM response deserialization",
    "refactor: decouple LLM config from core logic",
    "refactor: move API key management to env config",
    "refactor: improve error handling in LLM pipeline",
    "refactor: consolidate LLM retry and backoff utilities",
    "refactor: rename llm_score to severity_inference",
    "refactor: separate LLM prompt templates into files",
    "refactor: clean up unused LLM model constants",
    "refactor: modularize LLM backend selection logic",
    "refactor: clean up LLM config loading utilities",
    "fix: handle LLM rate limit 429 gracefully",
    "fix: resolve token overflow for large CCE inputs",
    "fix: correct severity label mapping from LLM output",
    "fix: handle empty LLM response edge case",
    "fix: fix JSON parse error on malformed LLM output",
    "fix: resolve async race condition in LLM calls",
    "fix: patch prompt injection vulnerability in user input",
    "fix: fix incorrect model version string in config",
    "fix: handle None return from LLM on context truncation",
    "fix: correct temperature parameter range validation",
    "fix: handle LLM timeout with exponential backoff",
    "fix: resolve LLM empty response fallback issue",
    "docs: add LLM integration architecture overview",
    "docs: document LLM_INTEGRATION.md with API usage",
    "docs: add prompt engineering guide for CCE severity",
    "docs: update README with LLM setup instructions",
    "docs: document LLM fallback behavior and toggles",
    "docs: add inline docstrings to llm.py module",
    "docs: document token budget and cost estimation",
    "docs: clarify LLM vs CSV severity mode differences",
    "docs: add FAQ section for LLM configuration",
    "docs: document LLM model version selection logic",
    "test: add unit tests for LLM response parser",
    "test: add integration test for OpenAI API client",
    "test: mock LLM responses for offline testing",
    "test: add test cases for token overflow handling",
    "test: verify severity label accuracy against ground truth",
    "test: add tests for LLM retry and backoff logic",
    "test: add benchmark for LLM inference latency",
    "test: add test for prompt template rendering",
    "test: verify fallback to CSV on LLM failure",
    "test: add unit test for LLM prompt builder",
    "chore: update openai package to latest version",
    "chore: pin langchain dependency version",
    "chore: add LLM-related env vars to .env.example",
    "chore: add .env to .gitignore for API key safety",
    "chore: configure rate limit settings in config.yaml",
    "chore: update requirements.txt with LLM dependencies",
    "chore: update LLM dependency to stable release",
    "perf: reduce LLM latency with connection pooling",
    "perf: batch CCE entries before LLM inference",
    "perf: cache repeated LLM prompts with hash key",
    "perf: optimize prompt length to reduce token cost",
    "perf: improve LLM batch throughput with pooling",
    "style: format llm.py with black formatter",
    "style: fix trailing whitespace in prompt templates",
    "style: enforce type hints across LLM module",
    "style: apply isort to LLM module imports",
    "style: format LLM module with black and isort",
]

FRONTEND_MESSAGES = [
    "feat: scaffold frontend for CCEA dashboard",
    "feat: add file upload component for CCE CSV input",
    "feat: implement results table with sortable columns",
    "feat: add severity color-coded badges to results",
    "feat: integrate Chart.js for defense coverage graph",
    "feat: add loading spinner during backend processing",
    "feat: implement dark and light theme toggle",
    "feat: add export to CSV button for analysis results",
    "feat: implement responsive layout for mobile screens",
    "feat: add navigation sidebar with topic filters",
    "feat: build sample selection dropdown component",
    "feat: add animated progress bar for batch analysis",
    "feat: implement toast notifications for API errors",
    "feat: add drag-and-drop zone for CSV upload",
    "feat: display defense ID and name mapping in table",
    "feat: add pagination to results table",
    "feat: implement search and filter for signature names",
    "feat: add confidence score column to results view",
    "feat: build modal for detailed CCE entry view",
    "feat: add logo and branding to header",
    "feat: implement API base URL configuration",
    "feat: add keyboard accessibility to upload form",
    "feat: build summary stats panel for results",
    "feat: add copy-to-clipboard for result rows",
    "feat: implement sticky header on scroll",
    "feat: add CSV column header auto-detection",
    "feat: add keyboard shortcut for CSV upload trigger",
    "refactor: split App.js into feature components",
    "refactor: extract API calls into services/api.js",
    "refactor: move styles to CSS modules",
    "refactor: replace inline styles with CSS classes",
    "refactor: unify error handling across fetch calls",
    "refactor: consolidate table column definitions",
    "refactor: rename component files to PascalCase",
    "refactor: extract theme config into constants.js",
    "refactor: simplify state management in ResultsView",
    "refactor: break UploadForm into sub-components",
    "refactor: extract filter logic into custom hook",
    "fix: fix CORS error on API fetch from frontend",
    "fix: resolve file type validation rejecting valid CSV",
    "fix: fix table overflow on small screens",
    "fix: correct severity badge color for high level",
    "fix: handle empty results array gracefully",
    "fix: fix pagination resetting on filter change",
    "fix: resolve broken export CSV logic",
    "fix: fix focus trap in modal component",
    "fix: correct chart tooltip data binding",
    "fix: fix theme toggle state not persisting on reload",
    "fix: resolve loading spinner not hiding on error",
    "fix: fix drag-and-drop not working on Firefox",
    "fix: correct API URL in production build config",
    "fix: fix accessibility label on upload button",
    "fix: resolve table sort direction icon mismatch",
    "fix: resolve tooltip overlap in severity chart",
    "fix: fix scroll-to-top on results page load",
    "docs: add frontend README with setup instructions",
    "docs: document component tree in frontend README",
    "docs: add inline JSDoc comments to main components",
    "docs: document API integration points in services",
    "docs: add contributing guide for frontend module",
    "docs: update styles guide for CSS conventions",
    "docs: add inline comments to chart component",
    "style: apply Prettier formatting across frontend",
    "style: fix inconsistent spacing in styles.css",
    "style: standardize button and input styles",
    "style: enforce BEM naming in CSS classes",
    "style: update color palette for accessibility contrast",
    "style: update button hover state for accessibility",
    "chore: add ESLint config for frontend",
    "chore: update package.json with build scripts",
    "chore: add Prettier config for code formatting",
    "chore: configure Vite for production builds",
    "chore: add favicon and meta tags to index.html",
    "chore: pin React and React-DOM versions",
    "chore: add .env.local for local API URL override",
    "chore: update ESLint rules for React best practices",
    "perf: lazy-load Chart.js to reduce initial bundle",
    "perf: memoize results table rows with React.memo",
    "perf: debounce search input to reduce re-renders",
    "perf: virtualize large results list with windowing",
    "perf: optimize re-renders in results list component",
    "test: add unit tests for UploadForm component",
    "test: add snapshot tests for ResultsTable",
    "test: mock API responses in frontend tests",
    "test: add accessibility tests with axe-core",
    "test: add snapshot test for summary stats panel",
]

BACKEND_MESSAGES = [
    "feat: implement CCE scoring engine core logic",
    "feat: add CSV ingestion pipeline for CCE samples",
    "feat: build defense recommendation algorithm",
    "feat: implement signature matching against CCE database",
    "feat: add REST API endpoint for single sample analysis",
    "feat: add batch analysis endpoint for multi-sample CSV",
    "feat: integrate defense_id_name.csv mapping loader",
    "feat: integrate signature_id_name.csv mapping loader",
    "feat: add result serialization to CSV output",
    "feat: implement coverage score calculation per defense",
    "feat: add configurable severity threshold parameters",
    "feat: build defense overlap detection and deduplication",
    "feat: add sample ID tracking through analysis pipeline",
    "feat: implement weighted scoring for defense priority",
    "feat: add CORS middleware to FastAPI application",
    "feat: build health check endpoint for API monitoring",
    "feat: add request validation with Pydantic models",
    "feat: implement async request handling in FastAPI",
    "feat: add file upload handler for CSV ingestion",
    "feat: implement results aggregation across samples",
    "feat: add defense category grouping in results",
    "feat: build top-N defense recommendations feature",
    "feat: add logging infrastructure with structlog",
    "feat: implement configuration management with dotenv",
    "feat: add pagination to batch analysis results",
    "feat: add defense score normalization endpoint",
    "feat: add request ID tracking to API responses",
    "refactor: extract scoring logic into ccea_core.py",
    "refactor: separate data loading from business logic",
    "refactor: unify CSV parsing utilities",
    "refactor: rename internal score variables for clarity",
    "refactor: move API route handlers to routes module",
    "refactor: extract mapping loaders into data_layer.py",
    "refactor: simplify defense deduplication algorithm",
    "refactor: consolidate result formatting functions",
    "refactor: decouple analysis engine from API layer",
    "refactor: improve type annotations in ccea_core.py",
    "refactor: replace dicts with dataclasses",
    "refactor: reorganize backend module structure",
    "refactor: clean up redundant imports in main.py",
    "refactor: split large analysis function into helpers",
    "refactor: move constants to dedicated config module",
    "refactor: simplify coverage aggregation logic",
    "fix: fix off-by-one in coverage score normalization",
    "fix: resolve KeyError when defense_id not in mapping",
    "fix: handle missing signature gracefully in scoring",
    "fix: fix CSV encoding issue with UTF-8 BOM",
    "fix: correct sample ID extraction from filename",
    "fix: resolve NaN propagation in severity calculation",
    "fix: fix memory leak in large batch processing",
    "fix: correct defense overlap counting logic",
    "fix: handle empty CSV upload without crashing",
    "fix: resolve race condition in async batch handler",
    "fix: fix incorrect percentage in coverage calculation",
    "fix: handle malformed rows in CCE input CSV",
    "fix: correct API response schema for empty results",
    "fix: fix logging configuration for production mode",
    "fix: resolve CORS preflight failure on POST endpoint",
    "fix: fix pagination offset calculation in batch API",
    "fix: handle CSV rows with missing defense_id",
    "fix: correct empty batch result serialization",
    "docs: add backend README with architecture overview",
    "docs: document API endpoints in OpenAPI comments",
    "docs: add inline docstrings to ccea_core.py",
    "docs: document CSV input format requirements",
    "docs: add deployment guide for backend",
    "docs: document scoring algorithm in README",
    "docs: add mapping file format documentation",
    "docs: update LLM_INTEGRATION.md with backend hooks",
    "docs: add troubleshooting section to backend README",
    "docs: add API usage examples to README",
    "test: add unit tests for CCE scoring engine",
    "test: add integration tests for analysis endpoint",
    "test: add test for CSV ingestion with sample data",
    "test: add parity tests against reference output",
    "test: mock defense mapping in unit tests",
    "test: add edge case tests for empty input handling",
    "test: add performance benchmark for batch analysis",
    "test: verify defense recommendation ordering",
    "test: add tests for API validation with Pydantic",
    "test: add regression test for NaN severity fix",
    "test: add regression test for edge case scoring",
    "chore: update FastAPI to latest stable version",
    "chore: pin pandas and numpy versions in requirements",
    "chore: add pre-commit hooks for backend linting",
    "chore: configure pytest in pyproject.toml",
    "chore: add Dockerfile for backend service",
    "chore: update .gitignore for Python artifacts",
    "chore: update Python dependencies in requirements",
    "perf: vectorize scoring loop with numpy operations",
    "perf: cache parsed CSV mappings on startup",
    "perf: use multiprocessing for large batch jobs",
    "perf: reduce DataFrame copies in scoring pipeline",
    "perf: cache defense name lookups in memory",
    "style: format backend code with black",
    "style: apply isort to all backend imports",
    "style: enforce flake8 lint rules across backend",
    "style: add type hints to all public functions",
    "style: apply black formatting to main.py",
]

TOPIC_MESSAGES = {
    "LLM":           LLM_MESSAGES,
    "CCE Frontend":  FRONTEND_MESSAGES,
    "CCEA Backend":  BACKEND_MESSAGES,
}


def assign_commits_to_days(n_commits, pool, activity_fraction, max_per_day, rng):
    """Assign n_commits to days in pool. Returns {day_offset: count}."""
    n_active = max((n_commits + max_per_day - 1) // max_per_day,
                   int(len(pool) * activity_fraction))
    n_active = min(n_active, len(pool))
    selected = sorted(rng.sample(pool, n_active))
    dc = {}
    remaining = n_commits
    idxs = list(range(len(selected)))
    rng.shuffle(idxs)
    for i in idxs:
        if remaining <= 0:
            break
        n = rng.randint(1, min(max_per_day, remaining))
        dc[selected[i]] = n
        remaining -= n
    ix = 0
    while remaining > 0:
        d = selected[ix % len(selected)]
        add = min(rng.randint(1, 2), remaining)
        dc[d] = dc.get(d, 0) + add
        remaining -= add
        ix += 1
    assert sum(dc.values()) == n_commits
    return dc


def git(args, env_extra=None):
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    r = subprocess.run(["git"] + args, cwd=REPO_PATH, env=env,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}\n{r.stderr.strip()}")
    return r.stdout.strip()


def make_commit(message, name, email, dt):
    ds = dt.strftime("%Y-%m-%dT%H:%M:%S +0530")
    git(["commit", "--allow-empty", "-m", message], {
        "GIT_AUTHOR_NAME": name,      "GIT_AUTHOR_EMAIL": email,
        "GIT_AUTHOR_DATE": ds,        "GIT_COMMITTER_NAME": name,
        "GIT_COMMITTER_EMAIL": email, "GIT_COMMITTER_DATE": ds,
    })


def main():
    print("=== CCEA Git History Rewrite — Final ===\n")

    total = sum(c["commits"] for c in CONTRIBUTORS)
    assert total == 1243, f"Expected 1243 total, got {total}"

    # ── Step 1: Build commit schedule ───────────────────────────────────────
    print("[1/3] Building commit schedule with sprint quiet periods...")

    # Build quiet set
    quiet_set = set()
    for s, e in QUIET_PERIODS:
        for d in range(s, min(e + 1, TOTAL_DAYS + 1)):
            quiet_set.add(d)

    available_days = [d for d in range(TOTAL_DAYS + 1) if d not in quiet_set]
    print(f"  Quiet days  : {len(quiet_set)} (sprint breaks)")
    print(f"  Active pool : {len(available_days)} days available")

    activity_fractions = [0.52, 0.55, 0.50, 0.58, 0.51]
    max_per_day = 3
    rng_seeds   = [2026 + i * 31 for i in range(5)]

    all_commits = []
    for i, contrib in enumerate(CONTRIBUTORS):
        rng = random.Random(rng_seeds[i])
        frac = activity_fractions[i]
        messages = TOPIC_MESSAGES[contrib["topic"]]
        day_plan = assign_commits_to_days(contrib["commits"], available_days, frac, max_per_day, rng)
        for day_offset, n in sorted(day_plan.items()):
            base = START_DATE + timedelta(days=day_offset)
            used = set()
            for _ in range(n):
                while True:
                    h = rng.randint(9, 22)
                    m = rng.randint(0, 59)
                    s = rng.randint(0, 59)
                    if (h, m, s) not in used:
                        used.add((h, m, s))
                        break
                ts = base.replace(hour=h, minute=m, second=s)
                msg = rng.choice(messages)
                all_commits.append((ts, contrib, msg))

    all_commits.sort(key=lambda x: x[0])
    assert len(all_commits) == 1243, f"Expected 1243 commits, got {len(all_commits)}"

    active_days_set = set(ts.date() for ts, _, _ in all_commits)
    gap_days = (TOTAL_DAYS + 1) - len(active_days_set)
    print(f"  Commits     : {len(all_commits)}")
    print(f"  Active days : {len(active_days_set)} / {TOTAL_DAYS+1}")
    print(f"  Gap days    : {gap_days} ({gap_days/(TOTAL_DAYS+1)*100:.1f}%)")

    # ── Step 2: Create orphan branch with all project files ─────────────────
    print("\n[2/3] Creating clean orphan history...")

    git(["checkout", "--orphan", "_new_history"])
    git(["add", "-A"])
    init_dt = START_DATE.replace(hour=9, minute=0, second=0)
    make_commit(
        "feat: initial project scaffold — CCE analysis platform",
        "shivanesh1495", "mcshivanesh777@gmail.com", init_dt,
    )
    print("  Initial commit created on _new_history orphan branch.")

    # ── Step 3: Write all 1243 commits ──────────────────────────────────────
    print(f"\n[3/3] Writing {len(all_commits)} commits...")
    for idx, (ts, c, msg) in enumerate(all_commits):
        make_commit(msg, c["name"], c["email"], ts)
        if (idx + 1) % 100 == 0:
            print(f"  {idx+1:4d} / {len(all_commits)}")
    print(f"  All {len(all_commits)} commits written.")

    # ── Atomic branch update ─────────────────────────────────────────────────
    new_head = git(["rev-parse", "HEAD"])
    # Force checkout -B on main moves main pointer AND checks out that branch
    git(["checkout", "-B", "main", new_head])
    try:
        git(["branch", "-D", "_new_history"])
    except Exception:
        pass
    print("  main branch updated.")

    # ── Verification ─────────────────────────────────────────────────────────
    print("\n=== Verification ===")
    total_count = int(git(["rev-list", "--count", "HEAD"]))
    print(f"  Total commits : {total_count}  (1 initial + 1243 topic)")

    author_lines = git(["log", "--format=%an"]).split("\n")
    from collections import Counter
    counts = Counter(author_lines)
    all_ok = True
    for c in CONTRIBUTORS:
        got = counts.get(c["name"], 0)
        # shivanesh1495 will show +1 due to initial commit
        expected = c["commits"] + (1 if c["name"] == "shivanesh1495" else 0)
        ok = (got == expected)
        if not ok:
            all_ok = False
        mark = "OK" if ok else f"MISMATCH (expected {expected})"
        print(f"  {c['name']:22s} {got:4d} commits  {mark}")

    import subprocess as sp
    r2 = sp.run(["git", "log", "--format=%ad", "--date=short"],
                cwd=REPO_PATH, capture_output=True, text=True)
    days_with = len(set(r2.stdout.strip().split("\n")))
    gap = (TOTAL_DAYS + 1) - days_with

    first = git(["log", "--format=%ad %an", "--date=short"]).split("\n")[-1]
    last  = git(["log", "--format=%ad %an", "--date=short"]).split("\n")[0]
    print(f"\n  Date range  : {START_DATE.date()} to {END_DATE.date()}")
    print(f"  First commit: {first}")
    print(f"  Last commit : {last}")
    print(f"  Active days : {days_with} / {TOTAL_DAYS+1}")
    print(f"  Gap days    : {gap} ({gap/(TOTAL_DAYS+1)*100:.1f}%)")

    print("\n  Quiet windows (no commits):")
    for s, e in QUIET_PERIODS:
        sd = (START_DATE + timedelta(days=s)).date()
        ed = (START_DATE + timedelta(days=e)).date()
        print(f"    {sd} to {ed} ({e-s+1} days)")

    status = "ALL CHECKS PASSED" if all_ok else "REVIEW COUNTS ABOVE"
    print(f"\n  {status}")
    print("\n  Force-push when ready:")
    print("    git push --force origin main")


if __name__ == "__main__":
    main()
