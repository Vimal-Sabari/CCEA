# CCEA Optimizer - frontend

Static `index.html` / `styles.css` / `main.js`. No build step.

## Run

```bash
# 1. start the backend (separate terminal)
cd ../backend && uvicorn main:app --reload --port 8000

# 2. serve the frontend
cd cce-app/frontend
python -m http.server 5500
# open http://localhost:5500
```

`Get Started` / drag-drop a `.csv` (CCE.csv schema) or the multi-sheet `.xlsx`
onto the page -> the backend runs the CCEA -> results view with per-sample
tabs, convergence chart and the optimal defense combination.

## Config

Backend URL defaults to `http://localhost:8000`. Override in the browser console:

```js
localStorage.setItem("CCEA_API", "http://my-host:8000"); location.reload();
```

**GitHub link:** set `GITHUB_URL` at the top of `main.js` to the repo URL. The
`GitHub` nav item opens it in a new tab.

**How it works:** the `How it works` nav item opens a modal describing the CCEA
flow (7 steps). Edit the `<ol class="flow">` in `index.html` to change the copy.

## Scroll motion (results view)

The landing is a locked single viewport (no scroll, per spec). The results view has:

- **Scroll progress bar** — thin white bar at the top.
- **Reveal-on-scroll** — aggregate cards, panel stats, chart and table fade/rise
  in as they enter the viewport (`.reveal` class, `IntersectionObserver`).
- **Table row cascade** — combo-table rows stagger in (`--rd` per row).
- **Sticky sample tabs** — the tab bar pins under the top while you scroll a long table.
- **Parallax** — the blurred background video drifts slightly (capped at 32px).

All disabled under `prefers-reduced-motion`, with a 2.2s safety net so nothing
can stay hidden if an observer misses.

## Assets

| File | Notes |
|---|---|
| `assets/logo.webp` | generated circular mark |
| `fonts/GeistPixel-Circle.woff2` | **optional** fallback display font. Missing = harmless 404; the CDN font `BubbledotICG-FinePos` is primary, `monospace` is the final fallback. |

External (CDN): Inter (Google Fonts), BubbledotICG-FinePos (OnlineWebFonts),
Font Awesome 6.5.2 (cdnjs), Chart.js 4.4.1 (cdnjs), background video (CloudFront).
