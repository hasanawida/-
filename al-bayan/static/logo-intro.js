// Al-Bayan cinematic logo intro for the landing page.
// Include as the FIRST element inside <body>:  <script src="/static/logo-intro.js"></script>
// Plays once per browser session, skips on any tap/key, and never runs for
// prefers-reduced-motion, Data Saver, or a tab opened in the background.
// Add ?intro=1 to the URL to force it (for testing).
(function () {
  "use strict";

  var force = /[?&]intro=1\b/.test(location.search);
  var SEEN = "ab-intro-seen";
  function store(fn) { try { return fn(window.sessionStorage); } catch (e) { return null; } }

  if (!force) {
    if (store(function (s) { return s.getItem(SEEN); })) return;
    if (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (navigator.connection && navigator.connection.saveData) return;
    if (document.hidden) return;
  }
  if (!document.body || !Element.prototype.animate) return;
  store(function (s) { s.setItem(SEEN, "1"); });

  // Start the Amiri download now so the wordmark doesn't swap fonts mid-reveal.
  if (document.fonts && document.fonts.load) document.fonts.load("700 64px Amiri", "البيان").catch(function () {});

  var css = [
    "#abi{position:fixed;top:0;right:0;bottom:0;left:0;z-index:2147483000;overflow:hidden;cursor:pointer;touch-action:none;overscroll-behavior:contain;-webkit-tap-highlight-color:transparent;direction:rtl}",
    "#abi .abi-backdrop{position:absolute;inset:0;background:radial-gradient(120% 80% at 50% 42%,#1d2142 0%,#0c0e1b 55%,#05060b 100%)}",
    "#abi canvas{position:absolute;inset:0;width:100%;height:100%}",
    "#abi .abi-grain{position:absolute;inset:-50%;opacity:.07;mix-blend-mode:overlay;pointer-events:none;" +
      "background-image:url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>\");" +
      "animation:abi-grain .5s steps(4) infinite}",
    "@keyframes abi-grain{0%{transform:translate(0,0)}25%{transform:translate(-3%,2%)}50%{transform:translate(2%,-3%)}75%{transform:translate(-2%,-1%)}100%{transform:translate(0,0)}}",
    "#abi .abi-bar{position:absolute;left:0;right:0;height:9vh;background:#000;z-index:3}",
    "#abi .abi-bar.t{top:0;transform:translateY(-100%)}#abi .abi-bar.b{bottom:0;transform:translateY(100%)}",
    "#abi .abi-stage{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:clamp(14px,3.5vh,26px);z-index:2;padding:0 16px;text-align:center}",
    "#abi .abi-fly{position:relative;width:clamp(104px,32vw,150px);height:clamp(104px,32vw,150px);perspective:700px}",
    "#abi .abi-logo{position:absolute;inset:0;transform-style:preserve-3d;opacity:0}",
    "#abi .abi-logo svg{display:block;width:100%;height:100%;overflow:visible;filter:drop-shadow(0 18px 40px rgba(88,86,214,.45))}",
    "#abi .abi-glow{position:absolute;inset:-70%;border-radius:50%;opacity:0;pointer-events:none;" +
      "background:radial-gradient(circle,rgba(88,86,214,.55) 0%,rgba(26,115,232,.28) 32%,rgba(200,160,77,.14) 52%,transparent 70%)}",
    "#abi .abi-ring{position:absolute;inset:0;border-radius:50%;border:2px solid rgba(232,200,122,.85);opacity:0;pointer-events:none}",
    "#abi .abi-flare{position:absolute;top:50%;left:50%;width:140vmax;height:2px;margin:-1px 0 0 -70vmax;opacity:0;z-index:2;pointer-events:none;" +
      "background:linear-gradient(90deg,transparent,rgba(120,150,255,.25) 30%,#fff 50%,rgba(120,150,255,.25) 70%,transparent);" +
      "box-shadow:0 0 18px 3px rgba(130,150,255,.55)}",
    "#abi .abi-ar{font-family:Amiri,'Times New Roman',serif;font-weight:700;font-size:clamp(46px,14vw,78px);line-height:1.15;" +
      "background:linear-gradient(100deg,#8a6a2c 0%,#c8a04d 30%,#fff4d2 48%,#c8a04d 62%,#f1d898 100%);background-size:250% 100%;" +
      "-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-clip-path:inset(0 0 0 100%);clip-path:inset(0 0 0 100%);opacity:0;padding:0 .1em}",
    "#abi .abi-en{font:600 clamp(11px,3.2vw,14px)/1 Heebo,system-ui,sans-serif;letter-spacing:.38em;color:rgba(214,222,255,.82);opacity:0;direction:ltr;margin-top:-4px}",
    "#abi .abi-verse{font-family:Amiri,serif;font-size:clamp(14px,4vw,17px);color:rgba(232,200,122,.62);opacity:0}",
    "#abi .abi-skip{position:absolute;bottom:calc(9vh + 14px);inset-inline-end:18px;z-index:4;background:none;border:1px solid rgba(255,255,255,.18);" +
      "color:rgba(255,255,255,.6);font:500 13px/1 Heebo,system-ui,sans-serif;padding:9px 14px;border-radius:999px;opacity:0;cursor:pointer}",
  ].join("\n");

  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  var root = document.createElement("div");
  root.id = "abi";
  root.setAttribute("aria-hidden", "true");
  root.innerHTML =
    '<div class="abi-backdrop"></div><canvas></canvas><div class="abi-grain"></div>' +
    '<div class="abi-bar t"></div><div class="abi-bar b"></div><div class="abi-flare"></div>' +
    '<div class="abi-stage">' +
      '<div class="abi-fly"><div class="abi-glow"></div><div class="abi-ring"></div><div class="abi-logo">' +
        '<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg"><defs>' +
          '<linearGradient id="abi-bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1a73e8"/><stop offset=".5" stop-color="#5856d6"/><stop offset="1" stop-color="#c8a04d"/></linearGradient>' +
          '<linearGradient id="abi-sh" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".3"/><stop offset=".5" stop-color="#fff" stop-opacity=".05"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>' +
          '<linearGradient id="abi-sw" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".6"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>' +
          '<clipPath id="abi-clip"><rect x="4" y="4" width="120" height="120" rx="28"/></clipPath></defs>' +
          '<rect x="4" y="4" width="120" height="120" rx="28" fill="url(#abi-bg)"/>' +
          '<rect x="4" y="4" width="120" height="60" rx="28" fill="url(#abi-sh)"/>' +
          '<g clip-path="url(#abi-clip)"><rect class="abi-sweep" x="34" y="-20" width="60" height="170" fill="url(#abi-sw)"/></g>' +
          '<path class="abi-ba" d="M30 56Q30 78 50 80L78 80Q98 78 98 56" pathLength="1" stroke="#fff" stroke-width="8" stroke-linecap="round" fill="none" stroke-dasharray="1" stroke-dashoffset="1"/>' +
          '<circle class="abi-dot" cx="64" cy="100" r="5.5" fill="#fff" opacity="0"/>' +
          '<g stroke="#fff" stroke-opacity=".6" stroke-width="3" stroke-linecap="round">' +
            '<line class="abi-w" x1="42" y1="36" x2="42" y2="30"/><line class="abi-w" x1="64" y1="34" x2="64" y2="26"/><line class="abi-w" x1="86" y1="36" x2="86" y2="30"/></g>' +
        "</svg></div></div>" +
      '<div class="abi-ar">البَيَان</div><div class="abi-en">AL-BAYAN</div><div class="abi-verse">﴿ عَلَّمَهُ الْبَيَان ﴾</div>' +
    "</div>" +
    '<button class="abi-skip" type="button" tabindex="-1">דלג</button>';
  document.body.appendChild(root);

  var html = document.documentElement;
  var prevOverflow = html.style.overflow;
  html.style.overflow = "hidden";

  function $(sel) { return root.querySelector(sel); }
  var EASE_OUT = "cubic-bezier(.16,1,.3,1)";
  var EASE_IO = "cubic-bezier(.65,0,.35,1)";
  var running = [];
  function A(el, frames, delay, duration, easing, extra) {
    var opts = { delay: delay, duration: duration, easing: easing || EASE_OUT, fill: "both" };
    if (extra) for (var k in extra) opts[k] = extra[k];
    var a = el.animate(frames, opts);
    running.push(a);
    return a;
  }

  // ---- gold dust: drifts upward, briefly pulled to the centre as the logo forms ----
  var canvas = $("canvas"), ctx = canvas.getContext && canvas.getContext("2d");
  var dpr = Math.min(window.devicePixelRatio || 1, 2), W = 0, H = 0, motes = [], t0 = performance.now(), raf = 0;
  function resize() { W = canvas.width = innerWidth * dpr; H = canvas.height = innerHeight * dpr; }
  if (ctx) {
    resize();
    for (var i = 0; i < 70; i++) {
      motes.push({
        x: Math.random() * W, y: Math.random() * H,
        r: (0.4 + Math.random() * 1.5) * dpr,
        vy: -(0.15 + Math.random() * 0.45) * dpr,
        ph: Math.random() * 6.28,
        gold: Math.random() < 0.75,
      });
    }
    (function frame(now) {
      var t = now - t0, cx = W / 2, cy = H * 0.42;
      var pull = t > 250 && t < 1300 ? Math.sin(((t - 250) / 1050) * Math.PI) * 0.018 : 0;
      ctx.clearRect(0, 0, W, H);
      ctx.globalAlpha = Math.min(1, t / 600);
      for (var j = 0; j < motes.length; j++) {
        var m = motes[j];
        m.x += Math.sin(t / 900 + m.ph) * 0.25 * dpr + (cx - m.x) * pull;
        m.y += m.vy + (cy - m.y) * pull;
        if (m.y < -10) { m.y = H + 10; m.x = Math.random() * W; }
        var a = 0.35 + 0.65 * Math.abs(Math.sin(t / 500 + m.ph));
        ctx.fillStyle = m.gold ? "rgba(232,200,122," + a + ")" : "rgba(150,165,255," + a * 0.8 + ")";
        ctx.beginPath(); ctx.arc(m.x, m.y, m.r, 0, 6.283); ctx.fill();
      }
      raf = requestAnimationFrame(frame);
    })(t0);
    addEventListener("resize", resize);
  }

  // ---- timeline (ms) ----
  var logo = $(".abi-logo"), fly = $(".abi-fly"), ar = $(".abi-ar");
  A($(".abi-bar.t"), [{ transform: "translateY(-100%)" }, { transform: "translateY(0)" }], 0, 600, EASE_IO);
  A($(".abi-bar.b"), [{ transform: "translateY(100%)" }, { transform: "translateY(0)" }], 0, 600, EASE_IO);
  A($(".abi-glow"), [{ opacity: 0, transform: "scale(.35)" }, { opacity: 1, transform: "scale(1.15)", offset: 0.6 }, { opacity: 0.7, transform: "scale(1)" }], 150, 1300);
  A(logo, [
    { opacity: 0, transform: "rotateX(38deg) rotateY(-28deg) scale(.55) translateZ(-120px)", filter: "blur(14px)" },
    { opacity: 1, transform: "rotateX(0) rotateY(0) scale(1) translateZ(0)", filter: "blur(0)" },
  ], 200, 1150);
  A($(".abi-ba"), [{ strokeDashoffset: 1 }, { strokeDashoffset: 0 }], 750, 650, EASE_IO);
  A($(".abi-dot"), [
    { opacity: 0, transform: "translateY(-34px)" },
    { opacity: 1, transform: "translateY(0)", offset: 0.65 },
    { opacity: 1, transform: "translateY(-5px)", offset: 0.82 },
    { opacity: 1, transform: "translateY(0)" },
  ], 1300, 480, "cubic-bezier(.5,0,.75,0)");
  // The dot lands → shockwave ring and a small punch on the tile.
  A($(".abi-ring"), [{ opacity: 0, transform: "scale(.7)" }, { opacity: 0.9, offset: 0.08 }, { opacity: 0, transform: "scale(2.3)" }], 1610, 750);
  A(fly, [{ transform: "scale(1)" }, { transform: "scale(1.045)" }, { transform: "scale(1)" }], 1600, 320, "ease-out", { fill: "none" });
  var waves = root.querySelectorAll(".abi-w");
  for (var w = 0; w < waves.length; w++) {
    waves[w].style.transformBox = "fill-box";
    waves[w].style.transformOrigin = "50% 100%";
    A(waves[w], [{ transform: "scaleY(0)" }, { transform: "scaleY(2.1)", offset: 0.45 }, { transform: "scaleY(1)" }], 1450 + w * 110, 520);
    A(waves[w], [{ transform: "scaleY(1)" }, { transform: "scaleY(" + (1.5 + w * 0.25) + ")" }, { transform: "scaleY(1)" }],
      2100 + w * 140, 620, "ease-in-out", { iterations: Infinity, fill: "none" });
  }
  A($(".abi-sweep"), [{ transform: "translateX(-110px) skewX(-18deg)" }, { transform: "translateX(170px) skewX(-18deg)" }], 1750, 850, EASE_IO);
  A($(".abi-flare"), [{ opacity: 0, transform: "scaleX(.05)" }, { opacity: 0.9, transform: "scaleX(1)", offset: 0.35 }, { opacity: 0, transform: "scaleX(1.15)" }], 1800, 900);
  // Right-to-left wipe, following the direction the word is written.
  A(ar, [
    { opacity: 0, clipPath: "inset(0 0 0 100%)", webkitClipPath: "inset(0 0 0 100%)", filter: "blur(10px)", transform: "translateY(8px) scale(.96)" },
    { opacity: 1, offset: 0.3 },
    { opacity: 1, clipPath: "inset(0 0 0 0)", webkitClipPath: "inset(0 0 0 0)", filter: "blur(0)", transform: "translateY(0) scale(1)" },
  ], 1950, 900);
  A(ar, [{ backgroundPosition: "100% 0" }, { backgroundPosition: "0% 0" }], 2300, 1300, "ease-in-out");
  A($(".abi-en"), [{ opacity: 0, letterSpacing: ".9em" }, { opacity: 1, letterSpacing: ".38em" }], 2250, 900);
  A($(".abi-verse"), [{ opacity: 0, transform: "translateY(6px)" }, { opacity: 1, transform: "translateY(0)" }], 2450, 800);
  A($(".abi-skip"), [{ opacity: 0 }, { opacity: 1 }], 900, 500);

  // ---- exit: the logo flies into its spot in the header while the page fades up ----
  var target = document.querySelector(".landing-brand img");
  var done = false, exitTimer = setTimeout(exit, 3450), failsafe = setTimeout(cleanup, 7000);

  function revealPage(delay) {
    var els = document.querySelectorAll(".landing-hero > *, .landing-nav-links");
    for (var k = 0; k < els.length; k++) {
      els[k].animate([{ opacity: 0, transform: "translateY(18px)" }, { opacity: 1, transform: "none" }],
        { delay: delay + k * 110, duration: 750, easing: EASE_OUT, fill: "backwards" });
    }
  }

  function exit() {
    if (done) return;
    done = true;
    clearTimeout(exitTimer);
    var r = target && target.getBoundingClientRect();
    var visible = r && r.width && r.bottom > 0 && r.top < innerHeight;
    if (visible) target.style.visibility = "hidden";
    var D = 900;
    if (visible) {
      var f = fly.getBoundingClientRect();
      var dx = r.left + r.width / 2 - (f.left + f.width / 2), dy = r.top + r.height / 2 - (f.top + f.height / 2);
      fly.animate([{ transform: "none" }, { transform: "translate(" + dx + "px," + dy + "px) scale(" + r.width / f.width + ")" }],
        { duration: D, easing: EASE_IO, fill: "forwards" });
      $(".abi-glow").animate([{ opacity: 0.7 }, { opacity: 0 }], { duration: D * 0.5, fill: "forwards" });
    } else {
      fly.animate([{ opacity: 1, transform: "none" }, { opacity: 0, transform: "scale(.6)" }], { duration: D * 0.6, easing: EASE_IO, fill: "forwards" });
    }
    var fade = [{ opacity: 1 }, { opacity: 0 }];
    [".abi-ar", ".abi-en", ".abi-verse", ".abi-skip", ".abi-flare", "canvas", ".abi-grain"].forEach(function (s) {
      var el = $(s); if (el) el.animate(fade, { duration: 350, fill: "forwards" });
    });
    $(".abi-bar.t").animate([{ transform: "translateY(0)" }, { transform: "translateY(-100%)" }], { duration: 600, easing: EASE_IO, fill: "forwards" });
    $(".abi-bar.b").animate([{ transform: "translateY(0)" }, { transform: "translateY(100%)" }], { duration: 600, easing: EASE_IO, fill: "forwards" });
    $(".abi-backdrop").animate(fade, { delay: 150, duration: D - 150, easing: "ease-in-out", fill: "forwards" });
    revealPage(250);
    setTimeout(cleanup, D + 30);
  }

  function skip() {
    if (done) return;
    done = true;
    clearTimeout(exitTimer);
    root.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 320, fill: "forwards" });
    revealPage(0);
    setTimeout(cleanup, 340);
  }

  // Removing the overlay while a finger is still down would let the release
  // "click" whatever sits underneath, so wait for the pointer to lift.
  var pressing = false;
  function release() { pressing = false; }
  addEventListener("pointerup", release, true);
  addEventListener("pointercancel", release, true);

  function cleanup() {
    if (pressing) { setTimeout(cleanup, 60); return; }
    removeEventListener("pointerup", release, true);
    removeEventListener("pointercancel", release, true);
    done = true;
    clearTimeout(exitTimer);
    clearTimeout(failsafe);
    cancelAnimationFrame(raf);
    removeEventListener("resize", resize);
    removeEventListener("keydown", skip);
    running.forEach(function (a) { try { a.cancel(); } catch (e) {} });
    if (target) target.style.visibility = "";
    html.style.overflow = prevOverflow;
    if (root.parentNode) root.parentNode.removeChild(root);
    if (style.parentNode) style.parentNode.removeChild(style);
  }

  root.addEventListener("pointerdown", function () { pressing = true; skip(); });
  addEventListener("keydown", skip);
})();
