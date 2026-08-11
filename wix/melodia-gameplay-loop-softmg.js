/**
 * Gameplay-loop dossier · SoftMG breathe tell.
 * Reads/writes the same localStorage key as the Battle UI's Clef Code
 * (melodia-game-ui.js) so the SoftMG breathe choice carries between pages.
 * Also lets the Clef Code (G F C G) be typed right here to try it.
 */
(function () {
  "use strict";

  var STORAGE_KEY = "melodia_mg_breathe";
  var CLEF_CODE = ["g", "f", "c", "g"];
  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var flashTimer = null;

  function readStored() {
    try {
      return window.localStorage.getItem(STORAGE_KEY) === "soft" ? "soft" : "combat";
    } catch (e) {
      return "combat";
    }
  }

  function writeStored(mode) {
    try {
      window.localStorage.setItem(STORAGE_KEY, mode);
    } catch (e) {
      /* storage unavailable — breathe choice stays session-only on this page */
    }
  }

  function applyMode(mode, flash) {
    document.documentElement.setAttribute("data-mg-breathe", mode);
    var stateEl = document.querySelector("[data-softmg-state]");
    if (stateEl) {
      stateEl.textContent = mode === "soft"
        ? "SoftMG breathe — quieter, carried from the Battle UI."
        : "Combat breathe — full pace.";
    }
    if (flash) {
      var strip = document.querySelector("[data-softmg-strip]");
      if (strip) {
        window.clearTimeout(flashTimer);
        strip.setAttribute("data-softmg-flash", "1");
        flashTimer = window.setTimeout(function () {
          strip.removeAttribute("data-softmg-flash");
        }, reducedMotion ? 900 : 1400);
      }
    }
  }

  function toggleMode() {
    var next = readStored() === "soft" ? "combat" : "soft";
    writeStored(next);
    applyMode(next, true);
  }

  function initClefListener() {
    var buffer = [];
    document.addEventListener("keydown", function (e) {
      var key = (e.key || "").toLowerCase();
      if (key.length !== 1 || key < "a" || key > "z") return;
      buffer.push(key);
      if (buffer.length > CLEF_CODE.length) buffer.shift();
      if (buffer.length === CLEF_CODE.length && buffer.every(function (k, i) {
        return k === CLEF_CODE[i];
      })) {
        buffer.length = 0;
        toggleMode();
      }
    });
  }

  function init() {
    if (!document.querySelector("[data-softmg-strip]")) return;
    applyMode(readStored(), false);
    initClefListener();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
