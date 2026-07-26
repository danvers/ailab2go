/* KI-Werkstatt client: polls /api/state, renders the active station,
 * sends control actions. Vanilla JS, fully offline.
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

let state = null;
let lastLocalAction = 0; // suppress "someone else switched" toast after own clicks
let adminPin = sessionStorage.getItem("kiw-pin") || null;

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
    toast("📡 Verbindung wackelt — bitte nochmal versuchen.");
    return { ok: false, status: 0 };
  }
}

let toastTimer = null;
function toast(msg) {
  // The toast stays in the layout permanently (opacity/visibility only) —
  // a display:none live region is not announced by screen readers, and
  // unhiding + writing in the same task is too fast to count as a change.
  const el = $("#toast");
  el.classList.add("show");
  el.textContent = msg;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    el.classList.remove("show");
    el.textContent = "";
  }, 3800);
}

const esc = (t) => String(t).replace(/[&<>"']/g, (c) => (
  { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function fmtDuration(s) {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (h) return `${h} Std ${m} Min`;
  if (m) return `${m} Min ${s % 60} Sek`;
  return `${s} Sek`;
}

function videoNote(msg) {
  const el = $("#video-note");
  if (msg) { el.textContent = msg; el.classList.remove("hidden"); }
  else el.classList.add("hidden");
}

/* Destructive, room-wide actions need a second tap ("arm" pattern). */
function armButton(btn, label, action) {
  let timer = null;
  btn.addEventListener("click", async () => {
    if (!btn.classList.contains("armed")) {
      btn.classList.add("armed");
      btn.textContent = "⚠️ Wirklich? Das gilt für ALLE — nochmal tippen";
      timer = setTimeout(() => {
        btn.classList.remove("armed");
        btn.textContent = label;
      }, 4000);
      return;
    }
    clearTimeout(timer);
    btn.classList.remove("armed");
    btn.textContent = label;
    await action();
  });
}

// ---------- station switching ----------------------------------------------

const STREAM_ALT = {
  start: "Live-Kamerabild",
  detektiv: "Live-Kamerabild mit markierten erkannten Objekten",
  trainer: "Live-Kamerabild mit Aufnahme-Rahmen und KI-Vermutung",
  schild: "Live-Kamerabild mit unkenntlich gemachten Gesichtern",
  spur: "Live-Kamerabild mit Wärmekarte der Bewegungen im Raum",
  trick: "Live-Kamerabild mit markierten erkannten Objekten",
  pose: "Live-Kamerabild mit erkannten Skelett-Punkten",
};

let shownMode = null;   // what the DOM currently displays (may be optimistic)
function showMode(mode) {
  shownMode = mode;
  $$("#tiles .tile").forEach((t) => {
    const on = t.dataset.mode === mode;
    t.classList.toggle("active", on);
    t.setAttribute("aria-current", on ? "true" : "false");
  });
  $$(".station").forEach((s) =>
    s.classList.toggle("hidden", s.dataset.mode !== mode));
  $("#stream").alt = STREAM_ALT[mode] || STREAM_ALT.start;
  // Bring the active tile into view (remote switches can land off-screen).
  // Compare viewport rects — offsetLeft is relative to .tiles-wrap, not to
  // the scrolling nav, so mixing it with scrollLeft misfires once scrolled.
  const tile = document.querySelector("#tiles .tile.active");
  if (tile) {
    const nav = $("#tiles").getBoundingClientRect();
    const box = tile.getBoundingClientRect();
    if (box.left < nav.left + 4 || box.right > nav.right - 4) {
      // Smooth scrolling is driven by animation frames, which do not run in
      // a hidden tab (phone in a pocket while others switch stations) — jump
      // instantly there, and whenever reduced motion is requested.
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
  const res = await post("/api/mode", { mode, pin: adminPin });
  if (!res.ok) {
    if (res.status === 403) {
      toast("🔒 Die Stationen sind gerade von der Moderation gesperrt.");
    }
    touched.mode = 0;                       // let the next poll reconcile
    if (state) showMode(state.mode);
  }
}

$$("#tiles .tile").forEach((tile) => {
  tile.addEventListener("click", () => setMode(tile.dataset.mode));
});

// ---------- header / banners ------------------------------------------------

$("#privacy-badge").addEventListener("click", () =>
  toast("🔒 Alles läuft auf einem Raspberry Pi in diesem Raum — es gibt " +
        "nicht mal eine Internet-Verbindung. Der Quellcode ist offen."));

$("#shared-hint-ok").addEventListener("click", () => {
  localStorage.setItem("kiw-shared-ok", "1");
  $("#shared-hint").classList.add("hidden");
});

// ---------- detektiv / trick ------------------------------------------------

const slider = $("#threshold");
slider.addEventListener("input", () => {
  markTouched("threshold");
  $("#threshold-val").textContent = `${slider.value} %`;
});
slider.addEventListener("change", () =>
  post("/api/params", { threshold: slider.value / 100 }));

function renderDetections(listEl, detections) {
  const html = detections.length
    ? detections.map((d) =>
        `<li><span aria-hidden="true">${d.emoji}</span><strong>${d.name}</strong>
         <span class="bar"><i style="width:${d.pct}%"></i></span>
         <span class="pct">${d.pct}%</span></li>`).join("")
    : '<li class="muted">Gerade nichts erkannt — halte etwas in die Kamera!</li>';
  if (listEl._html !== html) { listEl._html = html; listEl.innerHTML = html; }
}

// ---------- trainer ---------------------------------------------------------

function renderTeach(teach) {
  const slotsEl = $("#teach-slots");
  // Rebuild only when the slot set or the NAMES change. Counts change on
  // every capture and are patched in place — rebuilding there would throw
  // away keyboard focus and the button's "gespeichert!" feedback.
  const key = JSON.stringify(teach.names);
  if (slotsEl._key !== key) {
    slotsEl._key = key;
    slotsEl.innerHTML = Object.keys(teach.names).map((s) => `
      <div class="slot" data-slot="${esc(s)}">
        <button type="button" class="name"
          aria-label="Umbenennen: ${esc(teach.names[s])}">${esc(teach.names[s])}</button>
        <span class="count"></span>
        <button type="button" class="capture">📸 Beispiel aufnehmen</button>
      </div>`).join("");

    slotsEl.querySelectorAll(".slot .capture").forEach((btn) => {
      btn.addEventListener("click", async (ev) => {
        const slot = ev.target.closest(".slot").dataset.slot;
        const res = await post("/api/teach/capture", { slot, pin: adminPin });
        btn.textContent = res.ok ? "✨ gespeichert!"
          : (res.status === 403 ? "🔒 gesperrt" : "❌ nochmal tippen");
        setTimeout(() => (btn.textContent = "📸 Beispiel aufnehmen"), 700);
      });
    });
    slotsEl.querySelectorAll(".slot .name").forEach((el) => {
      el.addEventListener("click", async (ev) => {
        const slot = ev.target.closest(".slot").dataset.slot;
        const name = prompt("Wie heißt dieses Ding?", teach.names[slot]);
        if (name) await post("/api/teach/rename", { slot, name, pin: adminPin });
      });
    });
  }

  // patch counts/trained state in place (keeps focus and button feedback)
  slotsEl.querySelectorAll(".slot").forEach((el) => {
    const s = el.dataset.slot;
    const n = teach.counts[s] || 0;
    const trained = teach.trained.includes(s);
    const label = `${n} Beispiel${n === 1 ? "" : "e"}` +
      (trained ? " ✓" : ` (mind. ${teach.min})`);
    const countEl = el.querySelector(".count");
    if (countEl.textContent !== label) countEl.textContent = label;
    el.classList.toggle("trained", trained);
  });

  const predEl = $("#teach-prediction");
  const txt = teach.prediction
    ? `Ich glaube, das ist: ${teach.prediction.name} (${teach.prediction.pct} % sicher)`
    : `Noch nicht genug Beispiele — die KI braucht mindestens zwei Dinge ` +
      `mit je ${teach.min} Beispielen.`;
  if (predEl._last !== txt) {
    predEl._last = txt;
    predEl.className = teach.prediction ? "prediction big" : "prediction muted";
    predEl.textContent = txt;  // textContent only: no #teach-min to destroy
  }
}

armButton($("#teach-reset"), "🗑️ Alles vergessen lassen", async () => {
  const res = await post("/api/teach/reset", { pin: adminPin });
  if (res.ok) toast("🗑️ Alle Trainingsdaten gelöscht. Recht auf Löschung ausgeübt!");
  else if (res.status === 403) toast("🔒 Gerade von der Moderation gesperrt.");
});

// ---------- schild ----------------------------------------------------------

$("#privacy-on").addEventListener("change", async (ev) => {
  markTouched("privacy_on");
  const res = await post("/api/params", { privacy_on: ev.target.checked, pin: adminPin });
  if (res.status === 403) toast("🔒 Der Schutz-Schalter ist gerade gesperrt.");
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
      if (res.status === 403) toast("🔒 Gerade von der Moderation gesperrt.");
      touched.privacy_style = 0;
      if (state) paintStyleButtons(state.privacy.style);
    }
  });
});

// ---------- pose ------------------------------------------------------------

$("#pose-ghost").addEventListener("change", async (ev) => {
  markTouched("pose_ghost");
  const res = await post("/api/params", { pose_ghost: ev.target.checked, pin: adminPin });
  if (res.status === 403) toast("🔒 Gerade von der Moderation gesperrt.");
});

function renderPose(pose) {
  $("#pose-unavailable").classList.toggle("hidden", pose.available);
  $("#pose-content").classList.toggle("hidden", !pose.available);
  if (!pose.available) return;
  const ch = pose.challenge;
  $("#pose-ch-idx").textContent = ch.idx;
  $("#pose-ch-total").textContent = ch.total;
  $("#pose-ch-emoji").textContent = ch.emoji;
  const t = $("#pose-ch-text");
  if (t._last !== ch.text) { t._last = ch.text; t.textContent = ch.text; }
  const pct = Math.round(ch.progress * 100);
  $("#pose-progress").style.width = `${pct}%`;
  $("#pose-holdbar").setAttribute("aria-valuenow", pct);
  $("#pose-done").textContent = ch.done;
  $("#pose-persons").textContent = pose.persons;
  if (!isTouched("pose_ghost")) $("#pose-ghost").checked = pose.ghost;
}

// ---------- spur ------------------------------------------------------------

armButton($("#heatmap-reset"), "🧹 Datenspur löschen", async () => {
  const res = await post("/api/heatmap/reset", { pin: adminPin });
  if (res.ok) toast("🧹 Datenspur gelöscht — die Sammlung beginnt von vorn.");
  else if (res.status === 403) toast("🔒 Gerade von der Moderation gesperrt.");
});

// ---------- admin -----------------------------------------------------------

$("#admin-link").addEventListener("click", (ev) => {
  ev.preventDefault();
  const pin = prompt("Moderations-PIN:");
  if (!pin) return;
  adminPin = pin;
  sessionStorage.setItem("kiw-pin", pin);
  $("#admin-bar").classList.remove("hidden");
  toast("🔧 Moderationsleiste eingeblendet.");
});

$("#admin-lock").addEventListener("click", async () => {
  const action = state && state.locked ? "unlock" : "lock";
  const res = await post("/api/admin", { pin: adminPin, action });
  if (res.status === 403) toast("❌ Falsche PIN.");
});

$("#admin-reset").addEventListener("click", async () => {
  const res = await post("/api/admin", { pin: adminPin, action: "reset_all" });
  if (res.status === 403) toast("❌ Falsche PIN.");
  else if (res.ok) toast("♻️ Trainingsdaten, Datenspur und Zähler zurückgesetzt.");
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
      toast("👋 Jemand hat die Station gewechselt — ihr steuert gemeinsam!");
    }
  }

  if (!isTouched("threshold")) {
    slider.value = Math.round(s.threshold * 100);
    $("#threshold-val").textContent = `${slider.value} %`;
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
    s.mode === "start" || !!localStorage.getItem("kiw-shared-ok"));

  // lock state: banner + dimmed tiles (moderators keep full contrast)
  const lockedForMe = s.locked && !adminPin;
  document.body.classList.toggle("locked", lockedForMe);
  $("#locked-banner").classList.toggle("hidden", !lockedForMe);

  // footer stats
  const ai = $("#stat-ai");
  if (s.ai.ok) {
    ai.textContent = `⚡ KI-Chip aktiv (${s.ai.status})`;
    ai.className = "chip good";
  } else {
    ai.textContent = `🐢 Demo-Modus ohne KI-Chip — ${s.ai.status}`;
    ai.className = "chip warn";
  }
  $("#stat-fps").textContent = `${s.fps} fps`;
  $("#stat-clients").textContent = `👀 ${s.clients} Gerät${s.clients === 1 ? "" : "e"}`;
  $("#stat-source").textContent = `📷 ${s.source}`;
  $("#stat-lock").classList.toggle("hidden", !s.locked);
  $("#admin-lock").textContent = s.locked ? "🔓 Stationen freigeben" : "🔒 Stationen sperren";
}

let pollFailures = 0;
async function poll() {
  try {
    const res = await fetch("/api/state");
    if (res.ok) {
      render(await res.json());
      if (pollFailures >= 3) videoNote("");
      pollFailures = 0;
    }
  } catch (err) {
    pollFailures += 1;
    if (pollFailures === 3) videoNote("📡 Verbindung wackelt — einen Moment…");
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
  videoNote("📷 Bild lädt neu…");
  setTimeout(bumpStream, 1500);
});
$("#stream").addEventListener("load", () => videoNote(""));
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) bumpStream();
});

poll();
