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
const lerp3 = (a, b, u) => [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
const mid = (a, b, u = 0.5) => lerp3(a, b, u);
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const scale = (a, s) => [a[0] * s, a[1] * s, a[2] * s];
const norm = (a) => {
  const n = Math.hypot(a[0], a[1], a[2]) || 1;
  return [a[0] / n, a[1] / n, a[2] / n];
};

function handPts(frame, ch) {
  const v = frame.pose[ch]?.joints?.values || [];
  const out = [];
  for (let i = 0; i < v.length; i += 3) out.push([v[i], v[i + 1], v[i + 2]]);
  return out;
}

function frameToPose(fr) {
  const gaze = fr.pose.gaze?.dir || [0, 0, 1];
  return { left: handPts(fr, "left_hand"), right: handPts(fr, "right_hand"), gaze: [...gaze] };
}

function lerpPose(a, b, u) {
  const n = Math.max(a.left.length, b.left.length);
  const left = [];
  const right = [];
  for (let i = 0; i < n; i++) {
    if (a.left[i] && b.left[i]) left.push(lerp3(a.left[i], b.left[i], u));
    if (a.right[i] && b.right[i]) right.push(lerp3(a.right[i], b.right[i], u));
  }
  return { left, right, gaze: lerp3(a.gaze, b.gaze, u) };
}

function samplePose(t) {
  const f = doc.timeline;
  if (t <= f[0].t) return frameToPose(f[0]);
  if (t >= f[f.length - 1].t) return frameToPose(f[f.length - 1]);
  for (let i = 0; i < f.length - 1; i++) {
    const a = f[i];
    const b = f[i + 1];
    if (a.t <= t && t <= b.t) return lerpPose(frameToPose(a), frameToPose(b), (t - a.t) / (b.t - a.t));
  }
  return frameToPose(f[0]);
}

function rig(pose) {
  const head = [0, 1.58, 0.03];
  const ls = [-0.22, 1.36, 0.08];
  const rs = [0.22, 1.36, 0.08];
  const lw = pose.left[0] || mid(ls, [0.1, 1.1, 0.3], 0.5);
  const rw = pose.right[0] || mid(rs, [-0.1, 1.1, 0.3], 0.5);
  return {
    lw,
    rw,
    gazeEnd: add(head, scale(norm(pose.gaze), 0.55)),
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
    bytecodeEl.innerHTML = GestSgm.formatBytecodeHex(sgmBytes, pulse);
  }
}

function render(now) {
  let rigPose = null;
  if (doc) {
    const max = doc.timeline[doc.timeline.length - 1].t || 1;
    const t = playing ? (((now - start) / 1000 + offset) % max) : Number(scrub.value);
    scrub.value = t;
    updatePipeline(t, max);
    rigPose = rig(samplePose(t));
  }
  stage.render(now, rigPose);
  requestAnimationFrame(render);
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
requestAnimationFrame(render);
