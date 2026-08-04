/* KI-Werkstatt client: polls /api/state, renders the active station,
 * sends control actions. Vanilla JS, fully offline, bilingual (see i18n.js —
 * all user-facing dynamic strings go through I18N.t()).
 *
 * Patterns used throughout:
 * - touched[]-guard: after a local interaction the poll must not snap the
 *   control back to the (older) server value for a short grace period.
 * - change-guard: live regions and rebuilt DOM are only written when their
 *   content actually changed (keeps focus, calms screen readers).
 * - optimistic switching: tiles switch the panel immediately; the poll
 *   confirms or corrects.
 */

"use strict";

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);
const t = (...args) => I18N.t(...args);

let state = null;
let lastLocalAction = 0; // suppress "someone else switched" toast after own clicks

// storage may THROW when the visitor blocks site data — never let that
// kill the script (see i18n.js store helper for the localStorage side)
let adminPin = null;
try { adminPin = sessionStorage.getItem("kiw-pin"); } catch (e) { /* blocked */ }

// ---------- helpers ---------------------------------------------------------

const touched = {};
const markTouched = (key) => { touched[key] = Date.now(); };
const isTouched = (key) => Date.now() - (touched[key] || 0) < 2000;

async function post(url, body) {
  try {
    return await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
  } catch (err) {
    toast(t("connError"));
    return { ok: false, status: 0 };
  }
}

let toastTimer = null;
function toast(msg) {
  // The toast stays in the layout permanently (opacity/visibility only) —
  // a display:none live region is not announced by screen readers.
  const el = $("#toast");
  el.classList.add("show");
  el.textContent = msg;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    el.classList.remove("show");
    el.textContent = "";
  }, 3800);
}

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => (
  { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// server strings that may need a client-side translation; the backend also
// emits dynamic variants like "Hailo nicht verfügbar (SomeError)" — handle
// the prefixes so the exception detail survives
const trStatus = (s) => {
  if (I18N.lang !== "en") return s;
  return t("status")[s] ||
    s.replace(/^Hailo nicht verfügbar/, "Hailo not available")
     .replace(/^Pose nicht verfügbar/, "pose model not available");
};
// default teachable slot names are German ("Ding A") — display-translate
// them; user-given names pass through untouched
const trSlotName = (name) =>
  I18N.lang === "en" ? String(name).replace(/^Ding( [A-C])$/, "Thing$1") : name;

function fmtDuration(sec) {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  return t("duration", h, m, sec % 60);
}

/* The note takes an i18n KEY (not text) so a language switch can repaint
 * a note that is currently on screen. */
let videoNoteKey = null;
function videoNote(key) {
  videoNoteKey = key || null;
  const el = $("#video-note");
  if (key) { el.textContent = t(key); el.classList.remove("hidden"); }
  else el.classList.add("hidden");
}

/* Destructive, room-wide actions need a second tap ("arm" pattern).
 * labelKey is resolved through i18n on every paint, so the button follows
 * the language switch. */
const armButtons = [];
function armButton(btn, labelKey, action) {
  let timer = null;
  const idle = () => { btn.classList.remove("armed"); btn.textContent = t(labelKey); };
  armButtons.push(idle);
  btn.addEventListener("click", async () => {
    if (!btn.classList.contains("armed")) {
      btn.classList.add("armed");
      btn.textContent = t("armWarn");
      timer = setTimeout(idle, 4000);
      return;
    }
    clearTimeout(timer);
    idle();
    await action();
  });
  idle();
}

// ---------- station switching ----------------------------------------------

let shownMode = null;   // what the DOM currently displays (may be optimistic)
function showMode(mode) {
  shownMode = mode;
  $$("#tiles .tile").forEach((tile) => {
    const on = tile.dataset.mode === mode;
    tile.classList.toggle("active", on);
    tile.setAttribute("aria-current", on ? "true" : "false");
  });
  $$(".station").forEach((s) =>
    s.classList.toggle("hidden", s.dataset.mode !== mode));
  $("#stream").alt = t("alt")[mode] || t("alt").start;
  // The video frame carries the active station's colour (accent ring) —
  // scoped to .video-wrap so header/footer stay neutral.
  const activeTile = document.querySelector(`#tiles .tile[data-mode="${mode}"]`);
  if (activeTile) {
    document.querySelector(".video-wrap").style.setProperty(
      "--accent", activeTile.style.getPropertyValue("--accent"));
  }
  // Bring the active tile into view (remote switches can land off-screen).
  // Compare viewport rects — offsetLeft is relative to .tiles-wrap, not to
  // the scrolling nav, so mixing it with scrollLeft misfires once scrolled.
  const tile = document.querySelector("#tiles .tile.active");
  if (tile) {
    const nav = $("#tiles").getBoundingClientRect();
    const box = tile.getBoundingClientRect();
    if (box.left < nav.left + 4 || box.right > nav.right - 4) {
      // Smooth scrolling needs animation frames, which don't run in a hidden
      // tab (phone in a pocket while others switch) — jump instantly there.
      const instant = document.hidden ||
        matchMedia("(prefers-reduced-motion: reduce)").matches;
      tile.scrollIntoView({ behavior: instant ? "auto" : "smooth",
                            inline: "center", block: "nearest" });
    }
  }
  if (typeof updateNavChrome === "function") updateNavChrome();
}

async function setMode(mode) {
  lastLocalAction = Date.now();
  markTouched("mode");
  showMode(mode); // optimistic — the next poll confirms or corrects
  // Phones: after a *local* tap, reveal the new station's top just under the
  // sticky video. Deliberately not in showMode() — remote/poll-driven
  // switches must never hijack a visitor's scroll position.
  if (matchMedia("(max-width: 920px)").matches) {
    const sec = document.querySelector(`.station[data-mode="${mode}"]`);
    const stickyBottom =
      document.querySelector(".video-wrap").getBoundingClientRect().bottom;
    if (sec && sec.getBoundingClientRect().top < stickyBottom) {
      window.scrollBy({
        top: sec.getBoundingClientRect().top - stickyBottom - 8,
        behavior: "auto",
      });
    }
  }
  const res = await post("/api/mode", { mode, pin: adminPin });
  if (!res.ok) {
    if (res.status === 403) toast(t("locked"));
    touched.mode = 0;                       // let the next poll reconcile
    if (state) showMode(state.mode);
  }
}

$$("#tiles .tile").forEach((tile) => {
  tile.addEventListener("click", () => setMode(tile.dataset.mode));
});

// ---------- header / banners ------------------------------------------------

$("#privacy-badge").addEventListener("click", () => toast(t("badgeToast")));

$("#shared-hint-ok").addEventListener("click", () => {
  $("#shared-hint").classList.add("hidden");   // DOM first, storage after
  I18N.store.set("kiw-shared-ok", "1");
});

// ---------- detektiv / trick ------------------------------------------------

const slider = $("#threshold");
// --fill drives the coloured part of the custom WebKit track (style.css);
// Firefox gets it natively via ::-moz-range-progress.
const setFill = () => slider.style.setProperty("--fill",
  `${(slider.value - slider.min) / (slider.max - slider.min) * 100}%`);
setFill();
slider.addEventListener("input", () => {
  markTouched("threshold");
  $("#threshold-val").textContent = `${slider.value} %`;
  setFill();
});
slider.addEventListener("change", () =>
  post("/api/params", { threshold: slider.value / 100 }));

function renderDetections(listEl, detections) {
  const en = I18N.lang === "en";
  const html = detections.length
    ? detections.map((d) =>
        `<li><span aria-hidden="true">${d.emoji}</span><strong>${en ? (d.name_en || d.name) : d.name}</strong>
         <span class="bar"><i style="width:${d.pct}%"></i></span>
         <span class="pct">${d.pct}%</span></li>`).join("")
    : `<li class="muted">${t("noDetections")}</li>`;
  if (listEl._html !== html) { listEl._html = html; listEl.innerHTML = html; }
}

// ---------- trainer ---------------------------------------------------------

function renderTeach(teach) {
  const slotsEl = $("#teach-slots");
  // Rebuild only when the slot set or the NAMES change (language switch
  // clears the cache). Counts are patched in place — rebuilding there would
  // throw away keyboard focus and the button's "saved!" feedback.
  const key = I18N.lang + JSON.stringify(teach.names);
  if (slotsEl._key !== key) {
    slotsEl._key = key;
    slotsEl.innerHTML = Object.keys(teach.names).map((s) => `
      <div class="slot" data-slot="${esc(s)}">
        <button type="button" class="name"
          aria-label="${t("renameAria")}${esc(trSlotName(teach.names[s]))}">${esc(trSlotName(teach.names[s]))}</button>
        <span class="count"></span>
        <button type="button" class="capture">${t("capture")}</button>
      </div>`).join("");

    slotsEl.querySelectorAll(".slot .capture").forEach((btn) => {
      btn.addEventListener("click", async (ev) => {
        const slot = ev.target.closest(".slot").dataset.slot;
        const res = await post("/api/teach/capture", { slot, pin: adminPin });
        btn.textContent = res.ok ? t("captureOk")
          : (res.status === 403 ? t("captureLocked") : t("captureRetry"));
        setTimeout(() => (btn.textContent = t("capture")), 700);
      });
    });
    slotsEl.querySelectorAll(".slot .name").forEach((el) => {
      el.addEventListener("click", async (ev) => {
        const slot = ev.target.closest(".slot").dataset.slot;
        const name = prompt(t("renamePrompt"), trSlotName(teach.names[slot]));
        if (name) await post("/api/teach/rename", { slot, name, pin: adminPin });
      });
    });
  }

  // patch counts/trained state in place (keeps focus and button feedback)
  slotsEl.querySelectorAll(".slot").forEach((el) => {
    const s = el.dataset.slot;
    const n = teach.counts[s] || 0;
    const trained = teach.trained.includes(s);
    const label = t("examples", n) + (trained ? " ✓" : t("minExamples", teach.min));
    const countEl = el.querySelector(".count");
    if (countEl.textContent !== label) countEl.textContent = label;
    el.classList.toggle("trained", trained);
  });

  const predEl = $("#teach-prediction");
  const txt = teach.prediction
    ? t("prediction", trSlotName(teach.prediction.name), teach.prediction.pct)
    : t("teachEmpty", teach.min);
  if (predEl._last !== txt) {
    predEl._last = txt;
    predEl.className = teach.prediction ? "prediction big" : "prediction muted";
    predEl.textContent = txt;
  }
}

armButton($("#teach-reset"), "teachResetLabel", async () => {
  const res = await post("/api/teach/reset", { pin: adminPin });
  if (res.ok) toast(t("teachResetToast"));
  else if (res.status === 403) toast(t("paramLocked"));
});

// ---------- schild ----------------------------------------------------------

$("#privacy-on").addEventListener("change", async (ev) => {
  markTouched("privacy_on");
  const res = await post("/api/params", { privacy_on: ev.target.checked, pin: adminPin });
  if (res.status === 403) toast(t("paramLocked"));
});

function paintStyleButtons(style) {
  $$("#privacy-style button").forEach((b) => {
    const on = b.dataset.style === style;
    b.classList.toggle("active", on);
    b.setAttribute("aria-pressed", String(on));
  });
}

$$("#privacy-style button").forEach((btn) => {
  btn.addEventListener("click", async () => {
    markTouched("privacy_style");
    paintStyleButtons(btn.dataset.style);   // instant feedback, no 2 s wait
    const res = await post("/api/params", { privacy_style: btn.dataset.style, pin: adminPin });
    if (!res.ok) {
      if (res.status === 403) toast(t("paramLocked"));
      touched.privacy_style = 0;
      if (state) paintStyleButtons(state.privacy.style);
    }
  });
});

// ---------- pose ------------------------------------------------------------

$("#pose-ghost").addEventListener("change", async (ev) => {
  markTouched("pose_ghost");
  const res = await post("/api/params", { pose_ghost: ev.target.checked, pin: adminPin });
  if (res.status === 403) toast(t("paramLocked"));
});

function renderPose(pose) {
  $("#pose-unavailable").classList.toggle("hidden", pose.available);
  $("#pose-content").classList.toggle("hidden", !pose.available);
  if (!pose.available) return;
  const ch = pose.challenge;
  $("#pose-ch-idx").textContent = ch.idx;
  $("#pose-ch-total").textContent = ch.total;
  $("#pose-ch-emoji").textContent = ch.emoji;
  const el = $("#pose-ch-text");
  // challenge text by index from the local dictionary (server text is German)
  const txt = t("poseCh")[ch.idx - 1] || ch.text;
  if (el._last !== txt) { el._last = txt; el.textContent = txt; }
  const pct = Math.round(ch.progress * 100);
  $("#pose-progress").style.width = `${pct}%`;
  $("#pose-holdbar").setAttribute("aria-valuenow", pct);
  $("#pose-done").textContent = ch.done;
  $("#pose-persons").textContent = pose.persons;
  if (!isTouched("pose_ghost")) $("#pose-ghost").checked = pose.ghost;
}

// ---------- spur ------------------------------------------------------------

armButton($("#heatmap-reset"), "heatResetLabel", async () => {
  const res = await post("/api/heatmap/reset", { pin: adminPin });
  if (res.ok) toast(t("heatResetToast"));
  else if (res.status === 403) toast(t("paramLocked"));
});

// ---------- admin -----------------------------------------------------------

$("#admin-link").addEventListener("click", (ev) => {
  ev.preventDefault();
  const pin = prompt(t("pinPrompt"));
  if (!pin) return;
  adminPin = pin;
  $("#admin-bar").classList.remove("hidden");  // DOM first, storage after
  toast(t("adminShown"));
  try { sessionStorage.setItem("kiw-pin", pin); } catch (e) { /* blocked */ }
});

$("#admin-lock").addEventListener("click", async () => {
  const action = state && state.locked ? "unlock" : "lock";
  const res = await post("/api/admin", { pin: adminPin, action });
  if (res.status === 403) toast(t("wrongPin"));
});

// Two-tap like the visitor resets — this is the most destructive button in
// the UI (wipes training data AND the heatmap for everyone).
armButton($("#admin-reset"), "adminResetLabel", async () => {
  const res = await post("/api/admin", { pin: adminPin, action: "reset_all" });
  if (res.status === 403) toast(t("wrongPin"));
  else if (res.ok) toast(t("adminResetToast"));
});

// ---------- render loop -----------------------------------------------------

let lastUptime = null;
function bumpStream() {
  $("#stream").src = "/stream.mjpg?" + Date.now();
}

function render(s) {
  const prevMode = state ? state.mode : null;
  state = s;

  // server restarted → the old MJPEG connection is dead, reconnect
  if (lastUptime !== null && s.uptime_s < lastUptime) bumpStream();
  lastUptime = s.uptime_s;

  // Compare against what is DISPLAYED, not against the previous server
  // value — otherwise a correction skipped during the touched-window would
  // never be retried and the panel stays desynced forever.
  if (s.mode !== shownMode && !isTouched("mode")) {
    showMode(s.mode);
    if (prevMode && s.mode !== prevMode && Date.now() - lastLocalAction > 3000) {
      toast(t("modeSwitched"));
    }
  }

  if (!isTouched("threshold")) {
    slider.value = Math.round(s.threshold * 100);
    $("#threshold-val").textContent = `${slider.value} %`;
    setFill();
  }
  $("#threshold-trick").textContent = `${Math.round(s.threshold * 100)} %`;

  renderDetections($("#detections"), s.detections);
  renderDetections($("#detections-trick"), s.detections);

  if (s.mode === "trainer") renderTeach(s.teach);
  if (s.mode === "pose" && s.pose) renderPose(s.pose);

  if (!isTouched("privacy_on")) $("#privacy-on").checked = s.privacy.on;
  if (!isTouched("privacy_style")) paintStyleButtons(s.privacy.style);
  $("#faces-now").textContent = s.privacy.current;
  $("#faces-events").textContent = s.privacy.events;
  $("#privacy-warn").classList.toggle("hidden", s.privacy.backend !== "none");

  $("#heatmap-since").textContent = fmtDuration(s.heatmap.since_s);

  // demo-mode notices on the two detection stations
  $$("[data-needs-ai]").forEach((el) => el.classList.toggle("hidden", s.ai.ok));

  // shared-control one-time hint (skip on the start station, it explains itself)
  $("#shared-hint").classList.toggle("hidden",
    s.mode === "start" || !!I18N.store.get("kiw-shared-ok"));

  // lock state: banner + dimmed tiles (moderators keep full contrast)
  const lockedForMe = s.locked && !adminPin;
  document.body.classList.toggle("locked", lockedForMe);
  $("#locked-banner").classList.toggle("hidden", !lockedForMe);

  // footer stats
  const ai = $("#stat-ai");
  ai.textContent = s.ai.ok ? t("aiOk", trStatus(s.ai.status))
                           : t("aiDemo", trStatus(s.ai.status));
  ai.className = s.ai.ok ? "chip good" : "chip warn";
  $("#stat-fps").textContent = `${s.fps} fps`;
  $("#stat-clients").textContent = t("devices", s.clients);
  const srcChip = $("#stat-source");
  srcChip.textContent = `📷 ${t("source")[s.source] || s.source}`;
  srcChip.className = "chip" + (s.camera_ok === false ? " warn" : "");
  const lockChip = $("#stat-lock");
  lockChip.textContent = t("lockedChip");
  lockChip.classList.toggle("hidden", !s.locked);
  $("#admin-lock").textContent = s.locked ? t("unlockBtn") : t("lockBtn");
}

// language switch: invalidate every change-guard cache, repaint idle labels,
// re-render the last known state in the new language
document.addEventListener("kiw:lang", () => {
  ["#detections", "#detections-trick"].forEach((sel) => { $(sel)._html = null; });
  $("#teach-slots")._key = null;
  $("#teach-prediction")._last = null;
  $("#pose-ch-text")._last = null;
  armButtons.forEach((idle) => idle());
  $("#admin-lock").textContent = t("lockBtn");
  if (videoNoteKey) videoNote(videoNoteKey);   // repaint a visible note
  if (state) render(state);
  if (shownMode) $("#stream").alt = t("alt")[shownMode] || t("alt").start;
});

let pollFailures = 0;
async function poll() {
  try {
    const res = await fetch("/api/state");
    if (res.ok) {
      render(await res.json());
      if (pollFailures >= 3) videoNote(null);
      pollFailures = 0;
    }
  } catch (err) {
    pollFailures += 1;
    if (pollFailures === 3) videoNote("connNote");
  }
  setTimeout(poll, 800);
}

// ---------- layout helpers --------------------------------------------------

/* Measure the real nav height for the sticky video offset, and show edge
   fades only where content is actually hidden. */
function updateNavChrome() {
  const nav = $("#tiles");
  const wrap = document.querySelector(".tiles-wrap");
  document.documentElement.style.setProperty("--nav-h", `${wrap.offsetHeight}px`);
  const max = nav.scrollWidth - nav.clientWidth;
  wrap.classList.toggle("fade-left", nav.scrollLeft > 4);
  wrap.classList.toggle("fade-right", nav.scrollLeft < max - 4);
}
$("#tiles").addEventListener("scroll", updateNavChrome, { passive: true });
window.addEventListener("resize", updateNavChrome);
updateNavChrome();

// stream self-healing: reconnect on load errors and — crucial on phones,
// which kill the connection whenever the screen locks — on tab re-focus
$("#stream").addEventListener("error", () => {
  videoNote("imgReload");
  setTimeout(bumpStream, 1500);
});
$("#stream").addEventListener("load", () => videoNote(null));
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) bumpStream();
});

poll();
