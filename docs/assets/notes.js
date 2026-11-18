/* educatorsnotebook.com — visit notes
   Reports page views, which issue was on screen, which links readers followed
   (each article click is tagged with its issue), signups, and how far people
   read. No cookies. No personal data. Nothing leaves for a third party.
   Same design as the peternilsson.us, Schooled and Childhood Recovery trackers. */
(function () {
  "use strict";

  var EP = "https://ednotebook-notes.pbnilsson.workers.dev/p";

  var q = new URLSearchParams(window.location.search);
  var CAMPAIGN = q.get("utm_source") || q.get("ref") || "";

  // "/issues/2026-11-15/" and ".../index.html" are the same page. The github.io
  // address adds a /TheEducatorsNotebook prefix; drop it so both count as one.
  var PATH = window.location.pathname
    .replace(/^\/TheEducatorsNotebook(?=\/|$)/i, "")
    .replace(/index\.html?$/, "");
  if (!PATH) PATH = "/";
  if (!/\.[a-z0-9]{2,5}$/i.test(PATH) && PATH.slice(-1) !== "/") PATH += "/";

  // ---- silencing your own devices -----------------------------------------
  // Load any page with ?notrack=1 to stop this browser from ever reporting;
  // ?track=1 turns it back on. Arm it once in every browser you use (Chrome,
  // Safari, phone) so your own visits never land in the numbers.
  var OFF_KEY = "ten-off";

  function flag(val) {
    try {
      if (val === undefined) return localStorage.getItem(OFF_KEY);
      if (val === null) localStorage.removeItem(OFF_KEY);
      else localStorage.setItem(OFF_KEY, val);
    } catch (e) {}
    return null;
  }

  function toast(msg) {
    try {
      var el = document.createElement("div");
      el.textContent = msg;
      el.setAttribute("role", "status");
      el.style.cssText =
        "position:fixed;left:50%;bottom:24px;transform:translateX(-50%);z-index:9999;" +
        "background:#111;color:#fff;border-radius:2px;padding:.65rem 1.1rem;" +
        "box-shadow:0 6px 24px rgba(0,0,0,.2);" +
        "font:15px/1.2 'RoslindaleText',Georgia,serif;" +
        "opacity:0;transition:opacity .25s;";
      var place = function () {
        document.body.appendChild(el);
        setTimeout(function () { el.style.opacity = "1"; }, 20);
        setTimeout(function () {
          el.style.opacity = "0";
          setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 400);
        }, 4500);
      };
      if (document.body) place();
      else document.addEventListener("DOMContentLoaded", place);
    } catch (e) {}
  }

  var asked = q.has("notrack") || q.has("track");
  if (q.has("notrack")) flag(q.get("notrack") === "0" ? null : "1");
  if (q.has("track")) flag(q.get("track") === "0" ? "1" : null);
  var OFF = flag() === "1";

  if (asked) toast(OFF ? "Visit notes off for this browser." : "Visit notes on for this browser.");
  if (OFF || !EP) return;

  // A throwaway id that lives only for this browser tab, so we can tell
  // "one person read four pages" from "four people read one."
  var v = "";
  try {
    v = sessionStorage.getItem("ten");
    if (!v) {
      v = Math.random().toString(36).slice(2, 12);
      sessionStorage.setItem("ten", v);
    }
  } catch (e) {}

  // Report a rough width band, never the exact viewport (a fingerprint).
  function band(w) {
    if (!w) return 0;
    if (w < 480) return 480;
    if (w < 768) return 768;
    if (w < 1024) return 1024;
    if (w < 1440) return 1440;
    return 1441;
  }

  // Which issue is on screen. Issue pages (and the home page, which shows the
  // current issue) carry its date in <body data-issue="YYYY-MM-DD">.
  function issue() {
    var d = document.body ? document.body.getAttribute("data-issue") : "";
    return /^\d{4}-\d{2}-\d{2}$/.test(d || "") ? d : null;
  }

  function send(d) {
    d.v = v;
    d.w = band(window.innerWidth || 0);
    d.i = issue();
    var body = JSON.stringify(d);
    try {
      if (navigator.sendBeacon) {
        navigator.sendBeacon(EP, new Blob([body], { type: "text/plain" }));
        return;
      }
    } catch (e) {}
    try {
      fetch(EP, { method: "POST", body: body, keepalive: true }).catch(function () {});
    } catch (e) {}
  }

  // ---- the page view -------------------------------------------------------
  send({ k: "view", p: PATH, r: document.referrer || "", c: CAMPAIGN });

  // ---- links they follow ---------------------------------------------------
  // Every link, page-to-page included; the summary tells them apart. Article
  // links open in a new tab, and sendBeacon still delivers as the tab opens.
  document.addEventListener(
    "click",
    function (e) {
      var t = e.target;
      if (!t || !t.closest) return;
      var a = t.closest("a");
      if (!a || !a.getAttribute("href")) return;
      send({ k: "click", p: PATH, t: a.href.split("#")[0] });
    },
    true
  );

  // ---- signups (the subscribe form) ----------------------------------------
  document.addEventListener(
    "submit",
    function (e) {
      var f = e.target;
      if (f && f.classList && f.classList.contains("subscribe-form")) {
        send({ k: "signup", p: PATH, r: document.referrer || "", c: CAMPAIGN });
      }
    },
    true
  );

  // ---- how far they read, and how long they stayed -------------------------
  var started = Date.now();
  var deepest = 0;
  var closed = false;

  function measure() {
    var doc = document.documentElement;
    var height = Math.max(doc.scrollHeight, document.body ? document.body.scrollHeight : 0);
    if (!height) return;
    var seen = (window.scrollY || doc.scrollTop || 0) + window.innerHeight;
    var pct = Math.round((seen / height) * 100);
    if (pct > deepest) deepest = Math.max(0, Math.min(100, pct));
  }

  window.addEventListener("scroll", measure, { passive: true });
  window.addEventListener("resize", measure, { passive: true });
  measure();

  function close() {
    if (closed) return;
    closed = true;
    measure();
    send({ k: "end", p: PATH, d: deepest, s: Math.round((Date.now() - started) / 1000) });
  }

  // pagehide is the reliable one; visibilitychange catches tab switches
  // and mobile, where pagehide often never fires at all.
  window.addEventListener("pagehide", close);
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") close();
  });
})();
