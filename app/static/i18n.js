/* KI-Werkstatt i18n: German lives in the HTML (default, works without JS),
 * English lives here. The engine snapshots the German markup on load and
 * swaps innerHTML per data-i18n key; dynamic strings used by app.js come
 * from I18N.t(). The choice is per device (localStorage).
 *
 * Safety rule: elements that app.js addresses by id must never sit inside
 * a data-i18n block (the swap would destroy them) — split the markup
 * instead. See index.html header comment.
 */

"use strict";

window.I18N = (() => {

  // ---- English for every data-i18n key (German = the markup itself) -------
  const EN = {
    // NOTE: the leading aria-hidden emoji span must stay FIRST — on phones the
    // badge collapses to icon-only via font-size:0 and only that span survives.
    "ui.badge": '<span aria-hidden="true">🔒</span> 100&nbsp;% local — no cloud, no photos stored' +
      '<span class="sr-only">Tap for details: all computation happens on a small computer in this room.</span>',
    "ui.langAria": "Choose language",
    "ui.demoMode": "🐢 <strong>Demo mode:</strong> the AI chip is missing right now — " +
      "only faces are detected, as “person”. Ask the moderator!",
    "ui.nowDetected": "Detected right now:",
    "ui.howSummary": "🔧 How does this work?",
    "nav.aria": "Stations",

    "tile.start": "Start",
    "tile.detektiv": "Object Detective",
    "tile.trainer": "Train the AI",
    "tile.schild": "Privacy Shield",
    "tile.spur": "The Data Trail",
    "tile.trick": "Fool the AI",
    "tile.pose": "Skeleton Mirror",

    "banner.locked": "🔒 The moderator has locked the stations for a moment — just watch!",
    "banner.shared": "👥 Everyone here controls <strong>the same camera together</strong> — " +
      "don’t be surprised if things move “on their own”!",
    "banner.sharedOk": "Got it",

    "start.h2": "👋 Welcome to the KI-Werkstatt!",
    "start.intro": "The picture above is live from a camera in this room — processed " +
      "by a mini computer (Raspberry&nbsp;Pi&nbsp;5) with its own AI chip. Everything " +
      "happens <strong>right here</strong>: no image ever leaves this room.",
    "start.steps": "<li>Pick a <strong>station</strong> above.</li>" +
      "<li>Try everything — you can’t break anything.</li>" +
      "<li>Heads up: everyone sees the same picture. You control the stations <em>together</em>. 😉</li>",
    "start.think": "💭 <strong>Did you know?</strong> Most AI cameras send your images " +
      "to data centres somewhere in the world. This one doesn’t. The difference is " +
      "called <strong>“edge AI”</strong> — and that’s what today is about.",

    "det.h2": "🔍 Object Detective",
    "det.intro": "The AI searches every frame for <strong>80 things</strong> it knows: " +
      "people, cups, books, bananas… Hold something up to the camera — does it get it?",
    "det.thrLabel": "How sure does the AI have to be?",
    "det.thrHint": "⬅️ Low: the AI guesses more — including nonsense. &nbsp; High: it " +
      "only reports what it’s sure about — and misses things. ➡️<br>Real AI developers " +
      "weigh this trade-off all the time!",
    "det.howBody": "A <strong>neural network</strong> (YOLO) has seen millions of " +
      "example photos and learned patterns from them: edges, shapes, textures. It " +
      "doesn’t <em>understand</em> what a cup is — it recognises patterns that were " +
      "labelled “cup” in its training data. The maths runs on the " +
      "<strong>Hailo AI chip</strong> piggybacking on the Raspberry&nbsp;Pi — many " +
      "billions of operations per second.",
    "det.cardSummary": "📋 Model card (the AI’s fact sheet)",
    "det.cardBody": "<li><strong>Model:</strong> YOLOv8 (object detection)</li>" +
      "<li><strong>Trained on:</strong> COCO — about 330,000 photos from the internet</li>" +
      "<li><strong>Knows:</strong> exactly 80 everyday objects, nothing else</li>" +
      "<li><strong>Runs on:</strong> Hailo accelerator, fully offline</li>" +
      "<li><strong>Weak spots:</strong> unusual angles, rare objects, things that " +
      "hardly appeared in the training photos</li>",
    "det.think": "💭 <strong>Think about it:</strong> the AI knows only 80 things — " +
      "who actually decided <em>which</em> 80? What does an AI never “see”, and who " +
      "might that disadvantage?",

    "trainer.h2": "🧠 Train the AI",
    "trainer.intro": "Now <strong>you</strong> are the AI trainer! Teach the machine " +
      "to tell two things apart — in about a minute.",
    "trainer.steps": "<li>Hold object&nbsp;1 inside the <strong>frame</strong> in the " +
      "picture and press <em>Capture example</em> several times — from different angles!</li>" +
      "<li>Same for object&nbsp;2 (tip: tap the name to rename it).</li>" +
      "<li>Then show the camera one of the things — what does the AI say?</li>",
    "trainer.reset": "🗑️ Make it forget everything",
    "trainer.hint": "It’s your right: in Europe you can demand that your data be " +
      "deleted (“right to erasure”, GDPR). Here it’s one tap.",
    "trainer.howBody": "From every example the computer calculates a " +
      "<strong>number pattern</strong> (brightness edges, so-called HOG features) — " +
      "<em>no photo is stored!</em> To guess, the AI simply asks: which stored " +
      "patterns is the current image most similar to? That’s called " +
      "“k-nearest neighbours” — machine learning in its simplest form.",
    "trainer.think": "💭 <strong>Think about it:</strong> capture all examples of " +
      "thing&nbsp;1 against a bright background and thing&nbsp;2 against a dark one. " +
      "What does the AI <em>really</em> learn then? That’s exactly how " +
      "<strong>bias</strong> happens — distortion from one-sided training data. It " +
      "happens to big AI companies too!",

    "schild.h2": "🛡️ Privacy Shield",
    "schild.intro": "This camera makes faces unrecognisable <strong>before</strong> " +
      "the picture reaches your screens. That’s called <em>anonymisation at the source</em>.",
    "schild.warn": "⚠️ <strong>Warning:</strong> face detection is not available on " +
      "this device — <em>nothing</em> is being anonymised right now. Please tell " +
      "the moderator!",
    "schild.on": "Shield active",
    "schild.styleAria": "Type of anonymisation",
    "schild.pixel": "🟦 Pixelate",
    "schild.blur": "🌫️ Blur",
    "schild.smiley": "🙂 Smiley",
    "schild.hint": "The chosen shield applies at <strong>all</strong> stations, not just here.",
    "schild.stat1": "faces protected right now",
    "schild.stat2": "protection moments today",
    "schild.stat3": "photos stored — today or ever",
    "schild.recSummary": "🔧 Detection ≠ recognition — the crucial difference",
    "schild.recBody": "<strong>Face detection</strong> only says: “there is <em>a</em> " +
      "face.”<br><strong>Face recognition</strong> says: “that is <em>Anna Miller</em>.”<br>" +
      "This station only does the former — and even uses it to <em>protect</em> you. " +
      "So the same basic technology can surveil <em>or</em> preserve privacy. It all " +
      "depends on how it’s used.",
    "schild.limitSummary": "⚠️ Honest warning: the shield isn’t perfect",
    "schild.limitBody": "Turn your face sideways — the shield fails! The face finder " +
      "was mostly trained on frontal faces. That’s a lesson too: <strong>never " +
      "blindly trust an AI promise.</strong> Always ask: how well does it really " +
      "work, and for whom?",
    "schild.think": "💭 <strong>Think about it:</strong> where would a built-in " +
      "shield like this make sense? Doorbell cameras? Cameras at school? And who " +
      "should be allowed to switch it on or off?",

    "spur.h2": "🗺️ The Data Trail",
    "spur.intro": "Small surprise: while you were playing at the other stations, " +
      "this camera was <strong>quietly counting</strong> where in the room there was " +
      "movement. Without storing a single photo. You can see the result as a heat " +
      "map in the picture.",
    "spur.stat": "of collecting here so far",
    "spur.reset": "🧹 Erase the data trail",
    "spur.howBody": "No “clever” AI needed: the computer simply compares each frame " +
      "with the previous one and remembers <em>where</em> something changed. Such " +
      "side data is called <strong>metadata</strong> — data <em>about</em> your " +
      "behaviour instead of pictures <em>of</em> you.",
    "spur.think": "💭 <strong>Think about it:</strong> what does the map reveal about " +
      "this room — the most popular corner? Walking routes? Now imagine this over " +
      "weeks, in a supermarket or a school yard. Even <em>without</em> your face, " +
      "your behaviour says a lot about you. That’s why data protection says: " +
      "<strong>what isn’t collected can’t be abused.</strong>",

    "trick.h2": "🎭 Fool the AI",
    "trick.intro": "AI seems smart — until you find its limits. That’s your job now. " +
      "Can you crack one of these challenges?",
    "trick.hint1": "Shown from",
    "trick.hint2": "confidence — you’ll find the slider at the 🔍 Object Detective.",
    "trick.challenges": "<li>🥷 <strong>Invisible:</strong> stay in the picture, but " +
      "make sure the AI does <em>not</em> detect you as a person. (Hiding doesn’t " +
      "count — get creative!)</li>" +
      "<li>🎩 <strong>Mix-up:</strong> make the AI mistake one thing for something " +
      "completely different.</li>" +
      "<li>💯 <strong>Bullseye:</strong> get any object above 90&nbsp;% confidence. " +
      "What makes an object “easy to recognise”?</li>" +
      "<li>👻 <strong>Ghosts:</strong> make the AI report something that isn’t there " +
      "at all. (Tip: pictures on phones or t-shirts…)</li>",
    "trick.howSummary": "🔧 Why can AI be fooled?",
    "trick.howBody": "The AI never learned what a human <em>is</em> — only what " +
      "humans <em>looked like</em> in its training photos. Anything that deviates " +
      "(odd poses, costumes, pictures within pictures) throws it off. Researchers " +
      "call deliberate deceptions <strong>“adversarial attacks”</strong> — even a " +
      "printed sticker can trick some AIs.",
    "trick.think": "💭 <strong>Think about it:</strong> if a t-shirt print can " +
      "confuse an AI — how much responsibility should an AI carry on its own? In a " +
      "car? In policing? In a job interview?",

    "pose.h2": "🤸 Skeleton Mirror",
    "pose.intro": "The AI turns you into a stick figure: it estimates " +
      "<strong>17 body points</strong> — shoulders, elbows, knees… Step in front of " +
      "the camera and move!",
    "pose.unavailable": "The pose model is not available on this device — this " +
      "station needs the AI chip.",
    "pose.head": "Pose course · task",
    "pose.holdAria": "Pose held",
    "pose.foot": "Hold the pose still for a moment! Done so far:",
    "pose.ghost": "👻 Ghost mode: skeletons only, no camera image",
    "pose.hint": "Notice something? Even <em>without</em> video you can see exactly " +
      "who moves how. That’s how game-console cameras and fall sensors in care " +
      "homes work.",
    "pose.stat": "skeletons in the picture right now",
    "pose.howBody": "A neural network (YOLOv8-Pose) was trained on photos where " +
      "people were marked point by point. For every person it estimates 17 joint " +
      "positions plus a confidence — for you, dozens of times per second, straight " +
      "on the AI chip. A simple bit of maths then checks whether your wrists are " +
      "above your nose. No magic!",
    "pose.think": "💭 <strong>Think about it:</strong> in ghost mode no image of you " +
      "is shown — yet you could still be watched: how fast you walk, how much you " +
      "fidget, even your gait is as unique as a fingerprint. Is “just skeleton " +
      "data” really harmless? Who should get it — your doctor? An insurer? Your boss?",

    "foot.info": "medienbildung.team · " +
      "open source (MIT) · runs without internet",
    "foot.system": "System",
    "foot.admin": "Moderator",
    "foot.resetAll": "♻️ Reset everything",
  };

  // ---- dynamic strings used from app.js, per language ---------------------
  const DYN = {
    de: {
      badgeToast: "🔒 Alles läuft auf einem Raspberry Pi in diesem Raum — es gibt " +
        "nicht mal eine Internet-Verbindung. Der Quellcode ist offen.",
      locked: "🔒 Die Stationen sind gerade von der Moderation gesperrt.",
      paramLocked: "🔒 Gerade von der Moderation gesperrt.",
      connError: "📡 Verbindung wackelt — bitte nochmal versuchen.",
      connNote: "📡 Verbindung wackelt — einen Moment…",
      imgReload: "📷 Bild lädt neu…",
      modeSwitched: "👋 Jemand hat die Station gewechselt — ihr steuert gemeinsam!",
      armWarn: "⚠️ Wirklich? Das gilt für ALLE — nochmal tippen",
      teachResetLabel: "🗑️ Alles vergessen lassen",
      teachResetToast: "🗑️ Alle Trainingsdaten gelöscht. Recht auf Löschung ausgeübt!",
      heatResetLabel: "🧹 Datenspur löschen",
      adminResetLabel: "♻️ Alles zurücksetzen",
      heatResetToast: "🧹 Datenspur gelöscht — die Sammlung beginnt von vorn.",
      capture: "📸 Beispiel aufnehmen",
      captureOk: "✨ gespeichert!",
      captureLocked: "🔒 gesperrt",
      captureRetry: "❌ nochmal tippen",
      renameAria: "Umbenennen: ",
      renamePrompt: "Wie heißt dieses Ding?",
      examples: (n) => `${n} Beispiel${n === 1 ? "" : "e"}`,
      minExamples: (n) => ` (mind. ${n})`,
      teachEmpty: (n) => "Noch nicht genug Beispiele — die KI braucht mindestens " +
        `zwei Dinge mit je ${n} Beispielen.`,
      prediction: (name, pct) => `Ich glaube, das ist: ${name} (${pct} % sicher)`,
      noDetections: "Gerade nichts erkannt — halte etwas in die Kamera!",
      pinPrompt: "Moderations-PIN:",
      wrongPin: "❌ Falsche PIN.",
      adminShown: "🔧 Moderationsleiste eingeblendet.",
      adminResetToast: "♻️ Trainingsdaten, Datenspur und Zähler zurückgesetzt.",
      lockBtn: "🔒 Stationen sperren",
      unlockBtn: "🔓 Stationen freigeben",
      lockedChip: "🔒 Stationen gesperrt",
      aiOk: (m) => `⚡ KI-Chip aktiv (${m})`,
      aiDemo: (m) => `🐢 Demo-Modus ohne KI-Chip — ${m}`,
      devices: (n) => `👀 ${n} Gerät${n === 1 ? "" : "e"}`,
      duration: (h, m, s) => h ? `${h} Std ${m} Min` : (m ? `${m} Min ${s} Sek` : `${s} Sek`),
      poseCh: ["Heb eine Hand über den Kopf!", "Beide Hände hoch!",
               "Beide Hände vor der Brust zusammen!",
               "Mach ein T — Arme waagerecht zur Seite!"],
      status: {},
      alt: {
        start: "Live-Kamerabild",
        detektiv: "Live-Kamerabild mit markierten erkannten Objekten",
        trainer: "Live-Kamerabild mit Aufnahme-Rahmen und KI-Vermutung",
        schild: "Live-Kamerabild mit unkenntlich gemachten Gesichtern",
        spur: "Live-Kamerabild mit Wärmekarte der Bewegungen im Raum",
        trick: "Live-Kamerabild mit markierten erkannten Objekten",
        pose: "Live-Kamerabild mit erkannten Skelett-Punkten",
      },
      source: { "Pi-Kamera": "Pi-Kamera", "USB-Webcam": "USB-Webcam", "Testbild": "Testbild", "Keine Kamera": "Keine Kamera" },
    },
    en: {
      badgeToast: "🔒 Everything runs on a Raspberry Pi in this room — there isn’t " +
        "even an internet connection. The source code is open.",
      locked: "🔒 The stations are currently locked by the moderator.",
      paramLocked: "🔒 Currently locked by the moderator.",
      connError: "📡 Connection is shaky — please try again.",
      connNote: "📡 Connection is shaky — one moment…",
      imgReload: "📷 Reloading picture…",
      modeSwitched: "👋 Someone switched the station — you’re all controlling it together!",
      armWarn: "⚠️ Really? This affects EVERYONE — tap again",
      teachResetLabel: "🗑️ Make it forget everything",
      teachResetToast: "🗑️ All training data deleted. Right to erasure exercised!",
      heatResetLabel: "🧹 Erase the data trail",
      adminResetLabel: "♻️ Reset everything",
      heatResetToast: "🧹 Data trail erased — collection starts over.",
      capture: "📸 Capture example",
      captureOk: "✨ saved!",
      captureLocked: "🔒 locked",
      captureRetry: "❌ tap again",
      renameAria: "Rename: ",
      renamePrompt: "What is this thing called?",
      examples: (n) => `${n} example${n === 1 ? "" : "s"}`,
      minExamples: (n) => ` (min. ${n})`,
      teachEmpty: (n) => "Not enough examples yet — the AI needs at least two " +
        `things with ${n} examples each.`,
      prediction: (name, pct) => `I think this is: ${name} (${pct}% sure)`,
      noDetections: "Nothing detected right now — hold something up to the camera!",
      pinPrompt: "Moderator PIN:",
      wrongPin: "❌ Wrong PIN.",
      adminShown: "🔧 Moderator bar enabled.",
      adminResetToast: "♻️ Training data, data trail and counters reset.",
      lockBtn: "🔒 Lock stations",
      unlockBtn: "🔓 Unlock stations",
      lockedChip: "🔒 Stations locked",
      aiOk: (m) => `⚡ AI chip active (${m})`,
      aiDemo: (m) => `🐢 Demo mode without AI chip — ${m}`,
      devices: (n) => `👀 ${n} device${n === 1 ? "" : "s"}`,
      duration: (h, m, s) => h ? `${h} h ${m} min` : (m ? `${m} min ${s} s` : `${s} s`),
      poseCh: ["Raise one hand above your head!", "Both hands up!",
               "Bring both hands together in front of your chest!",
               "Make a T — arms straight out to the sides!"],
      alt: {
        start: "Live camera picture",
        detektiv: "Live camera picture with detected objects marked",
        trainer: "Live camera picture with capture frame and AI guess",
        schild: "Live camera picture with anonymised faces",
        spur: "Live camera picture with a heat map of movement in the room",
        trick: "Live camera picture with detected objects marked",
        pose: "Live camera picture with detected skeleton points",
      },
      source: { "Pi-Kamera": "Pi camera", "USB-Webcam": "USB webcam", "Testbild": "Test pattern", "Keine Kamera": "no camera" },
      status: {
        "Kein Hailo-Modell gefunden": "no Hailo model found",
        "Kein Pose-Modell gefunden": "no pose model found",
        "ohne KI-Chip": "no AI chip",
      },
    },
  };

  // ---- engine -------------------------------------------------------------

  // Storage access must never crash the page: privacy-minded visitors block
  // site data entirely (localStorage then THROWS on access). Falls back to
  // in-memory values — the choice then simply lasts for the page visit.
  const store = {
    mem: {},
    get(key) {
      try { return localStorage.getItem(key); } catch (e) { return this.mem[key] ?? null; }
    },
    set(key, value) {
      this.mem[key] = value;
      try { localStorage.setItem(key, value); } catch (e) { /* session-only */ }
    },
  };

  const german = new Map();   // element -> original German innerHTML
  const germanAria = new Map();
  let lang = store.get("kiw-lang") ||
    ((navigator.language || "de").toLowerCase().startsWith("de") ? "de" : "en");

  function snapshot() {
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      if (!german.has(el)) german.set(el, el.innerHTML);
    });
    document.querySelectorAll("[data-i18n-aria-label]").forEach((el) => {
      if (!germanAria.has(el)) germanAria.set(el, el.getAttribute("aria-label"));
    });
  }

  function apply() {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.dataset.i18n;
      el.innerHTML = lang === "de" ? german.get(el)
        : (EN[key] !== undefined ? EN[key] : german.get(el));
    });
    document.querySelectorAll("[data-i18n-aria-label]").forEach((el) => {
      const key = el.dataset.i18nAriaLabel;
      el.setAttribute("aria-label", lang === "de" ? germanAria.get(el)
        : (EN[key] !== undefined ? EN[key] : germanAria.get(el)));
    });
    document.querySelectorAll(".langswitch button").forEach((b) => {
      const on = b.dataset.lang === lang;
      b.classList.toggle("active", on);
      b.setAttribute("aria-pressed", String(on));
    });
  }

  function set(next) {
    if (next !== "de" && next !== "en") return;
    lang = next;
    apply();                                  // switch first …
    document.dispatchEvent(new CustomEvent("kiw:lang"));
    store.set("kiw-lang", lang);              // … persist best-effort after
  }

  snapshot();
  apply();
  document.querySelectorAll(".langswitch button").forEach((b) =>
    b.addEventListener("click", () => set(b.dataset.lang)));

  return {
    get lang() { return lang; },
    set,
    store,   // shared crash-safe storage helper (used by app.js too)
    t: (key, ...args) => {
      const entry = DYN[lang][key] !== undefined ? DYN[lang][key] : DYN.de[key];
      return typeof entry === "function" ? entry(...args) : entry;
    },
  };
})();
