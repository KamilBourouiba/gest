import { createHumanoidStage } from "./gest_humanoid.js";

const DEMO = "/demo/";
const SCENARIOS = [
  { slug: "xr_pinch_grasp", title: "XR pinch & grasp", tag: "flagship" },
  { slug: "assembly_pick_place", title: "Pick & place", tag: "assembly" },
  { slug: "presentation_sweep", title: "Presentation", tag: "sweep" },
  { slug: "robot_teleop_reach", title: "Robot teleop", tag: "teleop" },
  { slug: "rehab_symmetry_loop", title: "Rehab symmetry", tag: "rehab" },
];

const canvas = document.getElementById("gl");
const intro = document.getElementById("intro");
const playBtn = document.getElementById("play");
const scrub = document.getElementById("scrub");
const statusEl = document.getElementById("status");
const bytecodeEl = document.getElementById("bytecode");
const metricsEl = document.getElementById("metrics");
const industryEl = document.getElementById("industry");
const scenariosEl = document.getElementById("scenarios");
const webglDecodeEl = document.getElementById("webgl-decode");
const webglBytesEl = document.getElementById("webgl-bytes");
const stages = ["gest", "val", "compile", "sgm", "decode", "avatar"].map((s) => document.getElementById(`st-${s}`));
const srcSgmBtn = document.getElementById("src-sgm");
const srcJsonBtn = document.getElementById("src-json");

let doc = null;
let playing = true;
let start = performance.now();
let offset = 0;
let sourceMode = "sgm";
let activeSlug = SCENARIOS[0].slug;
let sgmBytes = null;
let decodeUs = 0;
let comparisonStats = null;
let frameId = 0;
let lastBytecodePulse = -1;
let running = true;

const stage = createHumanoidStage(canvas);

const FALLBACK_DOC = {
  fps: 60,
  timeline: [
    {
      t: 0.0,
      pose: {
        left_hand: { joints: { values: [-0.28, 1.12, 0.32, -0.32, 1.16, 0.33, -0.29, 1.20, 0.34, -0.25, 1.19, 0.33, -0.22, 1.16, 0.32] } },
        right_hand: { joints: { values: [0.28, 1.10, 0.34, 0.32, 1.14, 0.35, 0.29, 1.18, 0.36, 0.25, 1.17, 0.35, 0.22, 1.14, 0.34] } },
        gaze: { dir: [0.0, -0.25, 0.96] },
      },
    },
    {
      t: 1.2,
      pose: {
        left_hand: { joints: { values: [-0.10, 1.15, 0.28, -0.13, 1.19, 0.29, -0.10, 1.23, 0.30, -0.07, 1.22, 0.29, -0.04, 1.19, 0.28] } },
        right_hand: { joints: { values: [0.06, 1.22, 0.26, 0.10, 1.26, 0.27, 0.06, 1.30, 0.28, 0.02, 1.29, 0.27, -0.01, 1.26, 0.26] } },
        gaze: { dir: [0.08, -0.30, 0.95] },
      },
    },
  ],
};

function applyDoc(next, note) {
  doc = next;
  scrub.max = doc.timeline[doc.timeline.length - 1].t || 1;
  scrub.value = 0;
  offset = 0;
  start = performance.now();
  playing = true;
  playBtn.textContent = "Pause";
  statusEl.textContent = note;
}

const lerp = (a, b, u) => a + (b - a) * u;
const lerp3into = (a, b, u, out) => {
  out[0] = lerp(a[0], b[0], u);
  out[1] = lerp(a[1], b[1], u);
  out[2] = lerp(a[2], b[2], u);
  return out;
};
const scaleInto = (a, s, out) => {
  out[0] = a[0] * s;
  out[1] = a[1] * s;
  out[2] = a[2] * s;
  return out;
};
const normInto = (a, out) => {
  const n = Math.hypot(a[0], a[1], a[2]) || 1;
  out[0] = a[0] / n;
  out[1] = a[1] / n;
  out[2] = a[2] / n;
  return out;
};

const _gazeEnd = [0, 0, 0];
const _la = [0, 0, 0];
const _lb = [0, 0, 0];
const _ra = [0, 0, 0];
const _rb = [0, 0, 0];
const _ga = [0, 0, 0];
const _gb = [0, 0, 0];
const _outLw = [0, 0, 0];
const _outRw = [0, 0, 0];
const _outGaze = [0, 0, 0];
const _fallbackL = [-0.22, 1.36, 0.08];
const _fallbackR = [0.22, 1.36, 0.08];

function wristFromFrame(frame, ch, out) {
  const v = frame.pose[ch]?.joints?.values;
  if (!v || v.length < 3) return false;
  out[0] = v[0];
  out[1] = v[1];
  out[2] = v[2];
  return true;
}

function gazeFromFrame(frame, out) {
  const g = frame.pose.gaze?.dir;
  if (!g) {
    out[0] = 0;
    out[1] = 0;
    out[2] = 1;
  } else {
    out[0] = g[0];
    out[1] = g[1];
    out[2] = g[2];
  }
  return out;
}

function samplePose(t) {
  const f = doc.timeline;
  let a = f[0];
  let b = f[f.length - 1];
  let u = 0;

  if (t <= f[0].t) {
    a = f[0];
    b = f[0];
    u = 0;
  } else if (t >= f[f.length - 1].t) {
    a = f[f.length - 1];
    b = f[f.length - 1];
    u = 0;
  } else {
    for (let i = 0; i < f.length - 1; i++) {
      const left = f[i];
      const right = f[i + 1];
      if (left.t <= t && t <= right.t) {
        a = left;
        b = right;
        u = (t - left.t) / (right.t - left.t);
        break;
      }
    }
  }

  if (!wristFromFrame(a, "left_hand", _la)) {
    _la[0] = _fallbackL[0];
    _la[1] = _fallbackL[1];
    _la[2] = _fallbackL[2];
  }
  if (!wristFromFrame(b, "left_hand", _lb)) {
    _lb[0] = _la[0];
    _lb[1] = _la[1];
    _lb[2] = _la[2];
  }
  if (!wristFromFrame(a, "right_hand", _ra)) {
    _ra[0] = _fallbackR[0];
    _ra[1] = _fallbackR[1];
    _ra[2] = _fallbackR[2];
  }
  if (!wristFromFrame(b, "right_hand", _rb)) {
    _rb[0] = _ra[0];
    _rb[1] = _ra[1];
    _rb[2] = _ra[2];
  }
  gazeFromFrame(a, _ga);
  gazeFromFrame(b, _gb);

  return {
    lw: lerp3into(_la, _lb, u, _outLw),
    rw: lerp3into(_ra, _rb, u, _outRw),
    gaze: lerp3into(_ga, _gb, u, _outGaze),
  };
}

function rig(pose) {
  normInto(pose.gaze, _gazeEnd);
  scaleInto(_gazeEnd, 0.55, _gazeEnd);
  _gazeEnd[0] += 0;
  _gazeEnd[1] += 1.58;
  _gazeEnd[2] += 0.03;
  return {
    lw: pose.lw,
    rw: pose.rw,
    gazeEnd: _gazeEnd,
  };
}

function fmtBytes(n) {
  return n >= 1024 ? `${(n / 1024).toFixed(1)} KB` : `${n} B`;
}

function fetchFirst(paths, asJson = true) {
  return paths.reduce(
    (chain, p) => chain.catch(() => fetch(p).then((r) => { if (!r.ok) throw new Error(p); return asJson ? r.json() : r.arrayBuffer(); })),
    Promise.reject(),
  );
}

async function loadScenario(slug) {
  activeSlug = slug;
  document.querySelectorAll(".scenario-btn").forEach((btn) => btn.classList.toggle("on", btn.dataset.slug === slug));
  statusEl.textContent = `loading ${slug}…`;
  try {
    if (sourceMode === "sgm") {
      const buf = await fetchFirst([`${DEMO}data/clips/${slug}.sgm`, `${DEMO}out/${slug}.sgm`], false);
      const t0 = performance.now();
      const decoded = GestSgm.decodeSgmBytes(new Uint8Array(buf));
      const timeline = GestSgm.decodedToTimeline(decoded);
      decodeUs = Math.round(performance.now() - t0);
      sgmBytes = decoded.bytes;
      lastBytecodePulse = -1;
      applyDoc({ fps: decoded.fps, timeline }, `SGM decoded · ${slug} · ${decodeUs} µs`);
      webglDecodeEl.textContent = `${decodeUs.toLocaleString()} µs`;
      webglBytesEl.textContent = `${sgmBytes.length.toLocaleString()} B SGM · ${timeline.length} frames`;
      bytecodeEl.innerHTML = GestSgm.formatBytecodeHex(sgmBytes, 4);
    } else {
      const json = await fetchFirst([
        `${DEMO}data/clips/${slug}.gest.json`,
        `${DEMO}generated/${slug}.gest.json`,
        `${DEMO}${slug}.gest.json`,
      ]);
      applyDoc({ fps: json.fps || 60, timeline: json.timeline }, `JSON loaded · ${slug}`);
      sgmBytes = null;
      webglDecodeEl.textContent = "JSON path";
      webglBytesEl.textContent = `${JSON.stringify(json).length.toLocaleString()} B JSON`;
      bytecodeEl.textContent = "JSON source — switch to .sgm to see real bytecode";
    }
  } catch (e) {
    console.error(e);
    applyDoc(FALLBACK_DOC, `fallback clip (${e.message})`);
  }
}

function renderStats() {
  if (!comparisonStats) return;
  const art = (n) => comparisonStats.artifacts?.find((x) => x.name === n);
  const rows = [".sgm v1 bytecode", ".gest JSON compact", "Landmark JSON baseline", "BVH-like text baseline"].map(art).filter(Boolean);
  const maxB = Math.max(...rows.map((r) => r.bytes));
  metricsEl.innerHTML = rows
    .map((r) => {
      const pct = Math.max(4, (r.bytes / maxB) * 100);
      return `<div class="metric"><span>${r.name.replace(".gest JSON compact", ".gest")}</span><div class="bar"><span style="width:${pct}%"></span></div><strong>${fmtBytes(r.bytes)}</strong></div>`;
    })
    .join("");
}

function renderIndustry(stats) {
  const wins = stats.scenarios.reduce((s, sc) => s + sc.sgm_smaller_than.length, 0);
  const total = stats.scenarios.reduce((s, sc) => s + sc.artifacts.length - 1, 0);
  industryEl.innerHTML = `<div class="proof"><strong>${wins}/${total}</strong> SGM wins vs industry-like baselines</div>
    <div class="muted" style="margin-top:6px">Exception documented: pose7 BVH-like microclip.</div>
    <div style="margin-top:6px"><a href="/docs/industry-benchmark">Full benchmark →</a></div>`;
}

SCENARIOS.forEach((sc) => {
  const btn = document.createElement("button");
  btn.className = `scenario-btn${sc.slug === activeSlug ? " on" : ""}`;
  btn.dataset.slug = sc.slug;
  btn.textContent = `${sc.title} · ${sc.tag}`;
  btn.onclick = () => loadScenario(sc.slug);
  scenariosEl.appendChild(btn);
});

function updatePipeline(t, max) {
  const phase = Math.min(stages.length - 1, Math.floor((t / max) * stages.length));
  stages.forEach((el, i) => el.classList.toggle("on", i <= phase));
  if (sgmBytes) {
    const pulse = 4 + Math.floor((t / max) * (sgmBytes.length - 5));
    if (pulse !== lastBytecodePulse) {
      lastBytecodePulse = pulse;
      bytecodeEl.innerHTML = GestSgm.formatBytecodeHex(sgmBytes, pulse);
    }
  }
}

function render(now) {
  if (!running) return;
  let rigPose = null;
  if (doc) {
    const max = doc.timeline[doc.timeline.length - 1].t || 1;
    const t = playing ? (((now - start) / 1000 + offset) % max) : Number(scrub.value);
    if (playing || Math.abs(Number(scrub.value) - t) > 1e-4) scrub.value = t;
    updatePipeline(t, max);
    rigPose = rig(samplePose(t));
  }
  stage.render(now, rigPose);
  frameId = requestAnimationFrame(render);
}

function startRender() {
  if (running) return;
  running = true;
  frameId = requestAnimationFrame(render);
}

function stopRender() {
  running = false;
  cancelAnimationFrame(frameId);
}

document.getElementById("enter").onclick = () => intro.classList.add("hide");
setTimeout(() => intro.classList.add("hide"), 4500);

playBtn.onclick = () => {
  playing = !playing;
  playBtn.textContent = playing ? "Pause" : "Play";
  offset = Number(scrub.value);
  start = performance.now();
};
scrub.oninput = () => {
  playing = false;
  playBtn.textContent = "Play";
};

function setSource(mode) {
  sourceMode = mode;
  srcSgmBtn.classList.toggle("on", mode === "sgm");
  srcJsonBtn.classList.toggle("on", mode === "json");
  srcSgmBtn.classList.toggle("ghost", mode !== "sgm");
  srcJsonBtn.classList.toggle("ghost", mode !== "json");
  loadScenario(activeSlug);
}
srcSgmBtn.onclick = () => setSource("sgm");
srcJsonBtn.onclick = () => setSource("json");

addEventListener("resize", () => stage.resize());
fetchFirst([`${DEMO}data/comparison-stats.json`, `${DEMO}out/comparison-stats.json`])
  .then((s) => {
    comparisonStats = s;
    renderStats();
  })
  .catch(() => {});
fetchFirst([`${DEMO}data/industry-benchmark.json`, `${DEMO}out/industry-benchmark.json`])
  .then(renderIndustry)
  .catch(() => {});

try {
  await stage.loadModel(`${DEMO}assets/mannequin.glb`);
  statusEl.textContent = "Xbot humanoid loaded — loading clip…";
} catch (e) {
  console.error(e);
  statusEl.textContent = `mannequin load failed: ${e.message}`;
}

loadScenario(activeSlug);
startRender();

document.addEventListener("visibilitychange", () => {
  if (document.hidden) stopRender();
  else startRender();
});

addEventListener("pagehide", () => {
  stopRender();
  stage.dispose();
}, { once: true });
