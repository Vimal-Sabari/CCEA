/* ============================================================
   CCEA Optimizer  -  frontend logic
   ============================================================ */

const API_BASE = (localStorage.getItem("CCEA_API") || "http://localhost:8000").replace(/\/$/, "");

/* TODO: paste the GitHub repo URL here */
const GITHUB_URL = "https://github.com";

const $  = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const body = document.body;

let lastFile = null;      // keep the uploaded File for the CSV re-download
let lastResult = null;
let activeHash = null;
let chart = null;

/* ---------- view state ---------- */
function setView(v) { body.setAttribute("data-view", v); if (v !== "results") window.scrollTo(0, 0); }

/* ============================================================
   scroll FX  (results view only)
   ============================================================ */
const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

const progBar = document.createElement("div");
progBar.className = "scroll-prog";
document.body.appendChild(progBar);

const revealObserver = reduceMotion ? null : new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add("in"); revealObserver.unobserve(e.target); } });
}, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });

const rowObserver = reduceMotion ? null : new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add("in"); rowObserver.unobserve(e.target); } });
}, { threshold: 0.05 });

function wireScrollFx() {
  if (reduceMotion) {
    $$(".reveal").forEach(el => el.classList.add("in"));
    $$("table.combo tbody tr").forEach(tr => tr.classList.add("in"));
    return;
  }
  $$(".reveal:not(.in)").forEach(el => revealObserver.observe(el));
  $$("table.combo tbody tr:not(.in)").forEach(tr => rowObserver.observe(tr));
  // safety net: nothing stays invisible if an observer misses it
  clearTimeout(wireScrollFx._t);
  wireScrollFx._t = setTimeout(() => {
    $$(".reveal:not(.in)").forEach(el => el.classList.add("in"));
    $$("table.combo tbody tr:not(.in)").forEach(tr => tr.classList.add("in"));
  }, 2200);
}

function onScroll() {
  const se = document.scrollingElement || document.documentElement;
  const y = window.scrollY || se.scrollTop || 0;
  const max = se.scrollHeight - se.clientHeight;
  const p = max > 0 ? Math.min(1, y / max) : 0;
  progBar.style.width = (p * 100).toFixed(2) + "%";
  if (!reduceMotion) {
    document.documentElement.style.setProperty("--par", Math.min(32, y * 0.05).toFixed(1) + "px");
  }
}
window.addEventListener("scroll", onScroll, { passive: true });

/* ============================================================
   count-up stats
   ============================================================ */
const easeOutCubic = t => 1 - Math.pow(1 - t, 3);

function countUp(el, i) {
  const target = parseFloat(el.dataset.target);
  const decimals = parseInt(el.dataset.decimals || "0", 10);
  const suffix = el.dataset.suffix || "";
  const dur = 1500 + i * 80;
  const startAt = performance.now() + 480 + i * 90;

  function frame(now) {
    if (now < startAt) { requestAnimationFrame(frame); return; }
    const p = Math.min(1, (now - startAt) / dur);
    const val = target * easeOutCubic(p);
    el.textContent = val.toFixed(decimals) + suffix;
    if (p < 1) requestAnimationFrame(frame);
    else el.textContent = target.toFixed(decimals) + suffix;
  }
  requestAnimationFrame(frame);
}

const statObserver = new IntersectionObserver((entries, obs) => {
  entries.forEach(e => {
    if (!e.isIntersecting) return;
    $$(".stat-val").forEach((el, i) => countUp(el, i));
    obs.disconnect();
  });
}, { threshold: 0.25 });
if ($(".stats")) statObserver.observe($(".stats"));

/* ============================================================
   mobile menu
   ============================================================ */
const burger = $(".burger");
const overlay = $(".overlay");
const sheet = $("#mobile-menu");

function openMenu() {
  body.classList.add("menu-open");
  burger.setAttribute("aria-expanded", "true");
  overlay.hidden = false;
  sheet.hidden = false;
}
function closeMenu() {
  body.classList.remove("menu-open");
  burger.setAttribute("aria-expanded", "false");
  overlay.hidden = true;
  sheet.hidden = true;
}
burger?.addEventListener("click", () => (body.classList.contains("menu-open") ? closeMenu() : openMenu()));
overlay?.addEventListener("click", closeMenu);
$$(".sheet-link").forEach(l => l.addEventListener("click", closeMenu));
document.addEventListener("keydown", e => { if (e.key === "Escape") closeMenu(); });
window.addEventListener("resize", () => { if (window.innerWidth > 720) closeMenu(); });

/* ============================================================
   upload
   ============================================================ */
const fileInput = $("#file-input");
const errEl = $(".upload-error");

$$("[data-cta]").forEach(b => b.addEventListener("click", e => {
  e.preventDefault();
  closeMenu();
  fileInput.click();
}));

/* GitHub */
$$("[data-github]").forEach(a => a.addEventListener("click", e => {
  e.preventDefault();
  closeMenu();
  window.open(GITHUB_URL, "_blank", "noopener");
}));

/* How it works modal */
const howModal = $("#how-modal");
const modalOverlay = $(".modal-overlay");
function openHow() {
  closeMenu();
  modalOverlay.hidden = false;
  howModal.hidden = false;
  document.addEventListener("keydown", howEsc);
}
function closeHow() {
  modalOverlay.hidden = true;
  howModal.hidden = true;
  document.removeEventListener("keydown", howEsc);
}
function howEsc(e) { if (e.key === "Escape") closeHow(); }
$$("[data-open-how]").forEach(a => a.addEventListener("click", e => { e.preventDefault(); openHow(); }));
$(".modal-close")?.addEventListener("click", closeHow);
modalOverlay?.addEventListener("click", closeHow);

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) analyze(fileInput.files[0]);
  fileInput.value = "";
});

/* drag & drop onto the hero */
["dragenter", "dragover"].forEach(ev =>
  window.addEventListener(ev, e => { e.preventDefault(); body.classList.add("dragging"); }));
["dragleave", "drop"].forEach(ev =>
  window.addEventListener(ev, e => {
    e.preventDefault();
    if (ev === "dragleave" && e.relatedTarget) return;
    body.classList.remove("dragging");
  }));
window.addEventListener("drop", e => {
  const f = e.dataTransfer?.files?.[0];
  if (f) analyze(f);
});

function showError(msg) {
  errEl.textContent = msg;
  errEl.hidden = false;
  setView("landing");
}

/* ============================================================
   analyze  ->  call backend  ->  render
   ============================================================ */
async function analyze(file) {
  errEl.hidden = true;
  const isLlm = Boolean($("#use-llm")?.checked);
  $(".analyzing-text").textContent = isLlm 
    ? `Evaluating ${file.name} with Gemini 3.5 Flash-Lite (2 rounds, rate-limited)…` 
    : `Evaluating ${file.name}…`;
  setView("analyzing");

  const fd = new FormData();
  fd.append("file", file);
  const useLlm = $("#use-llm")?.checked ? "?use_llm=true" : "";

  let res, data;
  try {
    res = await fetch(`${API_BASE}/api/analyze${useLlm}`, { method: "POST", body: fd });
    data = await res.json();
  } catch (err) {
    showError(`Could not reach the backend at ${API_BASE}. Is it running?  (${err.message})`);
    return;
  }
  if (!res.ok) {
    showError(data?.error || `Request failed (${res.status}).`);
    return;
  }

  lastResult = data;
  activeHash = data.samples[0]?.hash || null;
  renderResults(data, file.name);
  setView("results");
}

/* ============================================================
   render
   ============================================================ */
const fmt = (n, d = 6) => Number(n).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: d });

function renderResults(data, filename) {
  $(".results-filename").textContent = filename;

  const a = data.aggregate.best_fitness;
  $("[data-agg]").innerHTML = [
    ["Samples", data.aggregate.n_samples],
    ["Mean best fitness", fmt(a.mean, 4)],
    ["Median", fmt(a.median, 4)],
    ["Min / Max", `${fmt(a.min, 3)} / ${fmt(a.max, 3)}`],
  ].map(([k, v], i) =>
    `<div class="agg-card reveal" style="--rv:${i * 0.06}s"><div class="k">${k}</div><div class="v">${v}</div></div>`
  ).join("");

  const tabs = $("[data-tabs]");
  tabs.innerHTML = data.samples.map(s => {
    const name = s.label || s.hash;
    return `<button class="tab" role="tab" data-hash="${s.hash}">${name}</button>`;
  }).join("");
  $$(".tab", tabs).forEach(t => t.addEventListener("click", () => {
    activeHash = t.dataset.hash;
    syncTabs();
    renderPanel();
  }));

  syncTabs();
  renderPanel();
}

function syncTabs() {
  $$(".tab").forEach(t => t.classList.toggle("is-active", t.dataset.hash === activeHash));
  const active = $(".tab.is-active");
  if (active) active.scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" });
}

function renderPanel() {
  const s = lastResult.samples.find(x => x.hash === activeHash);
  if (!s) return;
  const panel = $("[data-panel]");

  const stats = [
    ["Signatures", s.n_signatures],
    ["Candidates", s.n_candidates],
    ["Search space", Number(s.search_space).toExponential(2)],
    ["Generations run", s.generations_run],
    ["Best generation", s.best_generation],
    ["IS_Aggr", fmt(s.is_aggr, 6)],
    ["RS_Aggr", fmt(s.rs_aggr, 6)],
    ["Best fitness", fmt(s.best_fitness, 6)],
  ];

  panel.innerHTML = `
    <div class="panel-stats reveal">
      ${stats.map(([k, v]) => `<div class="mini"><div class="k">${k}</div><div class="v">${v}</div></div>`).join("")}
    </div>
    <div class="chart-box reveal" style="--rv:.06s"><canvas id="conv"></canvas></div>
    <div class="tbl-scroll reveal" style="--rv:.1s">
      <table class="combo">
        <thead><tr>
          <th>Candidate</th><th>Signature</th><th>Defense&nbsp;ID</th>
          <th>Attack</th><th>Attack&nbsp;[0-1]</th>
          <th>Reduced&nbsp;sev.</th><th>Reduced&nbsp;[0-1]</th>
          <th>Fitness</th>
        </tr></thead>
        <tbody>
          ${s.optimal_combination.map((c, i) => {
            const am = Number(c.attack_mapped);
            const rsm = Number(c.reduced_severity_mapped);
            const sigFitness = (c.fitness !== undefined && c.fitness !== null) 
              ? Number(c.fitness) 
              : (am > 0 ? ((am - rsm) / am) : 0);
            const fitnessDisplay = fmt(sigFitness, 6);
            const fitnessColor = sigFitness >= 0.7 ? '#4ade80' : sigFitness >= 0.3 ? '#facc15' : '#f87171';
            return `<tr style="--rd:${Math.min(i, 14) * 0.035}s">
              <td>${c.candidate_id}</td><td>${c.signature_id}</td><td>${c.defense_id}</td>
              <td>${c.attack_plan_score}</td><td>${fmt(c.attack_mapped, 6)}</td>
              <td>${c.reduced_severity}</td><td>${fmt(c.reduced_severity_mapped, 6)}</td>
              <td style="font-weight:600;color:${fitnessColor}">${fitnessDisplay}</td>
            </tr>`;
          }).join('')}
        </tbody>
      </table>
    </div>`;

  drawChart(s.generation_history);
  wireScrollFx();
}

function drawChart(history) {
  if (chart) chart.destroy();
  const ctx = $("#conv").getContext("2d");
  const labels = history.map(h => h.generation);
  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Best fitness so far",
          data: history.map(h => h.best_fitness_so_far),
          borderColor: "#ffffff",
          backgroundColor: "rgba(255,255,255,.08)",
          borderWidth: 2, pointRadius: 0, tension: 0, fill: true, stepped: true,
        },
        {
          label: "Generation fitness",
          data: history.map(h => h.generation_fitness),
          borderColor: "rgba(255,255,255,.28)",
          borderWidth: 1, pointRadius: 0, tension: 0,
        },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { labels: { color: "#b9b9b9", boxWidth: 12, font: { size: 11 } } },
        tooltip: { callbacks: { label: c => `${c.dataset.label}: ${Number(c.parsed.y).toFixed(6)}` } },
      },
      scales: {
        x: { title: { display: true, text: "Generation", color: "#8e8e8e" },
             ticks: { color: "#8e8e8e", maxTicksLimit: 12 }, grid: { color: "rgba(255,255,255,.06)" } },
        y: { title: { display: true, text: "Fitness", color: "#8e8e8e" },
             ticks: { color: "#8e8e8e" }, grid: { color: "rgba(255,255,255,.06)" } },
      },
    },
  });
}

/* ---------- back + download ---------- */
$("[data-back]")?.addEventListener("click", () => { setView("landing"); errEl.hidden = true; });

$("[data-download]")?.addEventListener("click", async () => {
  if (!lastFile) return;
  const fd = new FormData();
  fd.append("file", lastFile);
  const useLlm = $("#use-llm")?.checked ? "&use_llm=true" : "";
  const res = await fetch(`${API_BASE}/api/analyze?download=csv${useLlm}`, { method: "POST", body: fd });
  if (!res.ok) { alert("Download failed."); return; }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "optimal_defense_combinations.csv";
  a.click();
  URL.revokeObjectURL(url);
});
