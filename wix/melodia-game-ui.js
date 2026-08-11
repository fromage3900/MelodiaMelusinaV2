(function () {
  "use strict";

  var MOVEMENTS = [
    "Prelude", "Andante", "Allegro", "Adagio", "Scherzo", "Finale",
    "Nocturne", "Rondo", "Cadenza", "Interlude", "Ballade", "March",
    "Etude", "Caprice", "Sonata", "Fugue", "Aria", "Chorale",
    "Minuet", "Gigue", "Toccata", "Pastorale", "Requiem", "Overture",
    "Serenade", "Waltz", "Hymn", "Fanfare", "Elegy", "Coda"
  ];

  var BPM = 120;
  var BEAT_MS = 60000 / BPM;
  var WINDOWS = { perfect: 90, great: 120, good: 160 };
  var LANE_KEYS = { d: 0, f: 1, j: 2, k: 3, a: 0, s: 1 };

  var CHART = [
    0, 1, 2, 3, 0, 2, 1, 3, 0, 1, 2, 3,
    1, 0, 3, 2, 0, 1, 3, 2, 1, 0, 2, 3,
    0, 0, 2, 2, 1, 3, 1, 3
  ];

  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function applyRhythmConfig(cfg) {
    if (!cfg || !cfg.rhythm) return;
    var w = cfg.rhythm.windows_ms || {};
    if (w.perfect != null) WINDOWS.perfect = Number(w.perfect);
    if (w.great != null) WINDOWS.great = Number(w.great);
    if (w.good != null) WINDOWS.good = Number(w.good);
    if (cfg.rhythm.default_bpm) {
      BPM = Number(cfg.rhythm.default_bpm);
      BEAT_MS = 60000 / BPM;
    }
    var el;
    el = document.querySelector("[data-window-perfect]");
    if (el) el.textContent = "±" + WINDOWS.perfect + "ms";
    el = document.querySelector("[data-window-great]");
    if (el) el.textContent = "±" + WINDOWS.great + "ms";
    el = document.querySelector("[data-window-good]");
    if (el) el.textContent = "±" + WINDOWS.good + "ms";
    el = document.querySelector("[data-window-miss]");
    if (el) el.textContent = ">" + WINDOWS.good + "ms";
    document.querySelectorAll("[data-rhythm-bpm]").forEach(function (node) {
      node.textContent = "♩ = " + BPM;
    });
  }

  function loadRhythmConfig() {
    return fetch("../generated/melodia_rhythm_web_config.json", { cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (cfg) {
        applyRhythmConfig(cfg);
        return cfg;
      })
      .catch(function () { return null; });
  }

  function initPhaseSwitch() {
    var switcher = document.querySelector("[data-phase-switch]");
    var stage = document.querySelector("[data-battle-stage]");
    if (!switcher || !stage) return;
    var buttons = switcher.querySelectorAll("[data-phase]");
    function setPhase(phase) {
      stage.setAttribute("data-active-phase", phase);
      stage.querySelectorAll("[data-phase-panel]").forEach(function (panel) {
        var on = panel.getAttribute("data-phase-panel") === phase;
        panel.classList.toggle("is-active", on);
        panel.hidden = !on;
      });
      buttons.forEach(function (btn) {
        var on = btn.getAttribute("data-phase") === phase;
        btn.setAttribute("aria-selected", on ? "true" : "false");
      });
    }
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        setPhase(btn.getAttribute("data-phase"));
      });
    });
    setPhase(stage.getAttribute("data-active-phase") || "rhythm");
  }

  function pad(n) {
    return n < 10 ? "0" + n : String(n);
  }

  function fillCodexGrid(root) {
    if (!root) return;
    root.innerHTML = "";
    MOVEMENTS.forEach(function (label, i) {
      var chip = document.createElement("span");
      chip.className = "game-ui-codex-chip";
      chip.textContent = pad(i + 1) + " · " + label;
      root.appendChild(chip);
    });
  }

  function gradeFromError(ms) {
    var e = Math.abs(ms);
    if (e <= WINDOWS.perfect) return "perfect";
    if (e <= WINDOWS.great) return "great";
    if (e <= WINDOWS.good) return "good";
    return "miss";
  }

  function gradeLabel(grade) {
    return grade.charAt(0).toUpperCase() + grade.slice(1);
  }

  function streakTier(combo) {
    if (combo >= 8) return "8";
    if (combo >= 5) return "5";
    if (combo >= 3) return "3";
    return "0";
  }

  function applyReactivity(root, opts) {
    if (!root || reducedMotion) return;
    opts = opts || {};
    if (opts.grade) {
      root.setAttribute("data-react-grade", opts.grade);
      window.clearTimeout(root._gradeReactTimer);
      root._gradeReactTimer = window.setTimeout(function () {
        root.removeAttribute("data-react-grade");
      }, 420);
    }
    if (typeof opts.streak === "number") {
      root.setAttribute("data-react-streak", streakTier(opts.streak));
    }
    if (opts.ult) {
      root.setAttribute("data-react-ult", "1");
    } else if (opts.ult === false) {
      root.removeAttribute("data-react-ult");
    }
  }

  var SHRINE_STORAGE_KEY = "melodia_shrine_remembers";
  var SHRINE_FLOURISH_MS = 2400;

  function shrineTattooUnlocked() {
    try {
      return window.localStorage.getItem(SHRINE_STORAGE_KEY) === "1";
    } catch (e) {
      return false;
    }
  }

  function unlockShrineTattoo() {
    try {
      window.localStorage.setItem(SHRINE_STORAGE_KEY, "1");
    } catch (e) {
      /* storage unavailable — tattoo stays session-only */
    }
  }

  function restoreShrineTattoo(root) {
    if (!root || !shrineTattooUnlocked()) return;
    root.setAttribute("data-shrine-awake", "1");
  }

  function setShrineBoardLit(lit) {
    var board = document.querySelector("[data-shrine-board]");
    if (!board) return;
    if (lit) board.setAttribute("data-shrine-lit", "1");
    else board.removeAttribute("data-shrine-lit");
  }

  function triggerShrineRemembers(root) {
    if (!root) return;
    unlockShrineTattoo();
    root.setAttribute("data-shrine-awake", "1");
    if (root._shrineFired) return;
    root._shrineFired = true;
    root.setAttribute("data-shrine-flourish", "1");
    setShrineBoardLit(true);
    window.clearTimeout(root._shrineFlourishTimer);
    var holdMs = reducedMotion ? 1200 : SHRINE_FLOURISH_MS;
    root._shrineFlourishTimer = window.setTimeout(function () {
      root.removeAttribute("data-shrine-flourish");
      setShrineBoardLit(false);
    }, holdMs);
  }

  function clearShrineFlourish(root) {
    if (!root) return;
    root._shrineFired = false;
    window.clearTimeout(root._shrineFlourishTimer);
    root.removeAttribute("data-shrine-flourish");
    setShrineBoardLit(false);
    /* data-shrine-awake tattoo intentionally persists past combo breaks */
  }

  /* ── Clef Code · type the clef letters (G F C G) to swap the rhythm
     strip between Combat breathe (default, fast ornate) and SoftMG
     breathe (slow, quiet). Also lights the SoftMG_Baroque reactivity
     board strip so the lookbook can prove the channel fired. ── */
  var CLEF_CODE = ["g", "f", "c", "g"];
  var MG_BREATHE_STORAGE_KEY = "melodia_mg_breathe";

  function storedBreatheMode() {
    try {
      return window.localStorage.getItem(MG_BREATHE_STORAGE_KEY) === "soft" ? "soft" : null;
    } catch (e) {
      return null;
    }
  }

  function persistBreatheMode(mode) {
    try {
      window.localStorage.setItem(MG_BREATHE_STORAGE_KEY, mode);
    } catch (e) {
      /* storage unavailable — breathe choice stays session-only */
    }
  }

  function clefBreatheMode(root) {
    return root.getAttribute("data-mg-breathe") === "soft" ? "soft" : "combat";
  }

  function setClefBoardLit(lit) {
    var board = document.querySelector('[data-strip="softmg-baroque"]');
    if (!board) return;
    if (lit) board.setAttribute("data-clef-lit", "1");
    else board.removeAttribute("data-clef-lit");
  }

  function announceClef(root, mode) {
    var note = root.querySelector("[data-clef-status]");
    if (!note) return;
    window.clearTimeout(root._clefNoteTimer);
    note.innerHTML = '<span class="speaker">MELUSINA</span> ' + (mode === "soft"
      ? "There — a quieter measure. SoftMG breathe."
      : "Back to the beat. Combat breathe.");
    note.hidden = false;
    root._clefNoteTimer = window.setTimeout(function () {
      note.hidden = true;
    }, reducedMotion ? 1600 : 2600);
  }

  function toggleClefBreathe(root) {
    if (!root) return;
    var next = clefBreatheMode(root) === "soft" ? "combat" : "soft";
    root.setAttribute("data-mg-breathe", next);
    document.documentElement.setAttribute("data-mg-breathe", next);
    persistBreatheMode(next);
    setClefBoardLit(next === "soft");
    announceClef(root, next);
  }

  function initClefCode() {
    var root = document.querySelector("[data-rhythm-playground]");
    if (!root) return;
    if (storedBreatheMode() === "soft") {
      root.setAttribute("data-mg-breathe", "soft");
      document.documentElement.setAttribute("data-mg-breathe", "soft");
      setClefBoardLit(true);
    }
    var buffer = [];
    document.addEventListener("keydown", function (e) {
      var key = e.key.toLowerCase();
      if (key.length !== 1 || key < "a" || key > "z") return;
      buffer.push(key);
      if (buffer.length > CLEF_CODE.length) buffer.shift();
      if (buffer.length === CLEF_CODE.length && buffer.every(function (k, i) {
        return k === CLEF_CODE[i];
      })) {
        buffer.length = 0;
        toggleClefBreathe(root);
      }
    });
  }

  // BreakCrestReveal channel — one-shot 500ms pulse at the toughness-break/finale peak.
  function pulseBreak(root) {
    if (!root) return;
    root.setAttribute("data-react-break", "1");
    window.clearTimeout(root._breakTimer);
    root._breakTimer = window.setTimeout(function () {
      root.removeAttribute("data-react-break");
    }, 500);
  }

  function startBeatBus(root) {
    if (!root || reducedMotion) return;
    var bassPhase = 0;
    function tick() {
      if (!document.body.contains(root)) return;
      root.setAttribute("data-react-beat", "1");
      window.setTimeout(function () {
        root.removeAttribute("data-react-beat");
      }, 120);
      bassPhase = (bassPhase + 1) % 2;
      if (bassPhase === 0) {
        root.setAttribute("data-react-bass", "1");
        window.setTimeout(function () {
          root.removeAttribute("data-react-bass");
        }, 280);
      }
      root._beatTimer = window.setTimeout(tick, BEAT_MS);
    }
    tick();
  }

  function RhythmStrip(root) {
    this.root = root;
    this.highway = root.querySelector(".game-ui-highway");
    this.lanes = this.highway ? Array.prototype.slice.call(this.highway.querySelectorAll(".game-ui-lane")) : [];
    this.comboEl = root.querySelector("[data-rhythm-combo]");
    this.comboNumEl = root.querySelector("[data-rhythm-combo-num]");
    this.gradeEl = root.querySelector("[data-rhythm-grade]");
    this.sheetEl = root.querySelector(".game-ui-sheet");
    this.playbackHead = root.querySelector(".game-ui-playback-head");
    this.statusEl = root.querySelector("[data-rhythm-status]");
    this.startBtn = root.querySelector("[data-rhythm-start]");
    this.scrollBeats = 2.2;
    this.combo = 0;
    this.maxCombo = 0;
    this.notes = [];
    this.noteEls = {};
    this.running = false;
    this.startTime = 0;
    this.raf = 0;
    this.hitLineRatio = 0.78;
    this.bind();
    restoreShrineTattoo(this.root);
  }

  RhythmStrip.prototype.bind = function () {
    var self = this;
    if (this.startBtn) {
      this.startBtn.addEventListener("click", function () {
        self.toggle();
      });
    }
    if (!this.highway) return;
    this.lanes.forEach(function (lane, index) {
      lane.setAttribute("tabindex", "0");
      lane.setAttribute("role", "button");
      lane.setAttribute("aria-label", "Lane " + lane.getAttribute("data-lane"));
      lane.addEventListener("pointerdown", function (e) {
        e.preventDefault();
        self.onLaneInput(index);
        lane.classList.add("lane-pressed", "lane-press-flash");
        setTimeout(function () {
          lane.classList.remove("lane-pressed", "lane-press-flash");
        }, 180);
      });
    });
    document.addEventListener("keydown", function (e) {
      if (!self.running) return;
      var key = e.key.toLowerCase();
      if (Object.prototype.hasOwnProperty.call(LANE_KEYS, key)) {
        e.preventDefault();
        self.onLaneInput(LANE_KEYS[key]);
        var lane = self.lanes[LANE_KEYS[key]];
        if (lane) {
          lane.classList.add("lane-pressed", "lane-press-flash");
          setTimeout(function () {
            lane.classList.remove("lane-pressed", "lane-press-flash");
          }, 180);
        }
      }
    });
  };

  RhythmStrip.prototype.buildChart = function () {
    var leadInBeats = 4;
    this.notes = CHART.map(function (lane, i) {
      return {
        id: "n" + i,
        lane: lane,
        hitMs: (leadInBeats + i * 0.5) * BEAT_MS,
        beam: i % 4 === 2,
        judged: false
      };
    });
    this.durationMs = this.notes[this.notes.length - 1].hitMs + BEAT_MS * 3;
  };

  RhythmStrip.prototype.toggle = function () {
    if (this.running) {
      this.stop();
    } else {
      this.start();
    }
  };

  RhythmStrip.prototype.start = function () {
    this.buildChart();
    this.combo = 0;
    this.maxCombo = 0;
    this.running = true;
    this.startTime = performance.now();
    this.noteEls = {};
    if (this.highway) {
      this.highway.querySelectorAll(".rhythm-note").forEach(function (n) { n.remove(); });
      this.highway.classList.add("is-playing");
    }
    if (this.startBtn) this.startBtn.textContent = "Stop demo";
    this.setStatus("Play! Keys D F J K or tap lanes");
    this.updateCombo();
    this.showGrade("", "");
    var self = this;
    function tick(now) {
      if (!self.running) return;
      var elapsed = now - self.startTime;
      self.spawnAndMove(elapsed);
      self.updatePlaybackHead(elapsed);
      self.autoMiss(elapsed);
      if (elapsed >= self.durationMs) {
        self.finish();
        return;
      }
      self.raf = requestAnimationFrame(tick);
    }
    this.raf = requestAnimationFrame(tick);
  };

  RhythmStrip.prototype.stop = function () {
    this.running = false;
    if (this.raf) cancelAnimationFrame(this.raf);
    if (this.highway) this.highway.classList.remove("is-playing");
    if (this.playbackHead) this.playbackHead.classList.remove("is-live");
    if (this.startBtn) this.startBtn.textContent = "Play rhythm strip";
    this.setStatus("Stopped");
  };

  RhythmStrip.prototype.finish = function () {
    this.running = false;
    if (this.raf) cancelAnimationFrame(this.raf);
    if (this.highway) this.highway.classList.remove("is-playing");
    if (this.playbackHead) {
      this.playbackHead.classList.remove("is-live");
      this.updatePlaybackHead(this.durationMs);
    }
    if (this.startBtn) this.startBtn.textContent = "Play again";
    this.setStatus("Complete — max combo ×" + this.maxCombo);
  };

  RhythmStrip.prototype.updatePlaybackHead = function (elapsed) {
    if (!this.playbackHead || reducedMotion) return;
    var staff = this.playbackHead.closest(".game-ui-staff");
    if (!staff) return;
    var max = Math.max(staff.clientWidth - 28, 40);
    var t = this.durationMs > 0 ? Math.min(1, Math.max(0, elapsed / this.durationMs)) : 0;
    this.playbackHead.style.left = (10 + t * max) + "px";
    this.playbackHead.classList.toggle("is-live", true);
  };

  RhythmStrip.prototype.spawnAndMove = function (elapsed) {
    var highwayH = this.highway.clientHeight;
    var hitY = highwayH * this.hitLineRatio;
    var scrollPx = highwayH * 0.85;

    this.notes.forEach(function (note) {
      if (note.judged) return;
      var timeToHit = note.hitMs - elapsed;
      var progress = 1 - timeToHit / (this.scrollBeats * BEAT_MS);
      if (progress < -0.15) return;

      var el = this.noteEls[note.id];
      if (!el) {
        el = document.createElement("span");
        el.className = "rhythm-note" + (note.beam ? " is-beam" : "");
        el.setAttribute("data-lane-index", String(note.lane));
        this.lanes[note.lane].appendChild(el);
        this.noteEls[note.id] = el;
      }
      var y = progress * scrollPx;
      el.style.top = Math.min(y, hitY + 40) + "px";
      el.style.opacity = progress > 1.05 ? "0.35" : "1";
    }, this);
  };

  RhythmStrip.prototype.onLaneInput = function (laneIndex) {
    if (!this.running) return;
    var elapsed = performance.now() - this.startTime;
    var best = null;
    var bestErr = Infinity;

    this.notes.forEach(function (note) {
      if (note.judged || note.lane !== laneIndex) return;
      var err = elapsed - note.hitMs;
      if (Math.abs(err) < Math.abs(bestErr)) {
        bestErr = err;
        best = note;
      }
    });

    if (!best || Math.abs(bestErr) > WINDOWS.good + 80) {
      this.registerJudgment("miss", null);
      return;
    }

    var grade = gradeFromError(bestErr);
    best.judged = true;
    var el = this.noteEls[best.id];
    if (el) {
      el.classList.add("judged-" + grade);
      setTimeout(function () { if (el.parentNode) el.remove(); }, 200);
    }
    this.registerJudgment(grade, bestErr);
  };

  RhythmStrip.prototype.autoMiss = function (elapsed) {
    this.notes.forEach(function (note) {
      if (note.judged) return;
      if (elapsed - note.hitMs > WINDOWS.good + 40) {
        note.judged = true;
        var el = this.noteEls[note.id];
        if (el) el.remove();
        this.registerJudgment("miss", null);
      }
    }, this);
  };

  RhythmStrip.prototype.registerJudgment = function (grade) {
    if (grade === "miss") {
      this.combo = 0;
      clearShrineFlourish(this.root);
    } else {
      this.combo += 1;
      if (this.combo > this.maxCombo) this.maxCombo = this.combo;
      if (this.combo >= 8) {
        triggerShrineRemembers(this.root);
      }
      if (this.combo === 8) {
        pulseBreak(this.root);
      }
    }
    this.updateCombo();
    this.showGrade(grade, grade !== "miss" ? WINDOWS[grade] : null);
    applyReactivity(this.root, {
      grade: grade,
      streak: this.combo,
      ult: this.combo >= 8
    });
  };

  RhythmStrip.prototype.updateCombo = function () {
    var label = this.combo > 0 ? "× " + this.combo : "× 0";
    if (this.comboNumEl) {
      this.comboNumEl.textContent = label;
    } else if (this.comboEl && !this.comboEl.querySelector("[data-rhythm-combo-num]")) {
      this.comboEl.textContent = this.combo > 0 ? "COMBO × " + this.combo : "COMBO × 0";
    }
    if (this.root) {
      this.root.setAttribute("data-react-streak", streakTier(this.combo));
      if (this.combo >= 8) this.root.setAttribute("data-react-ult", "1");
      else this.root.removeAttribute("data-react-ult");
    }
  };

  RhythmStrip.prototype.showGrade = function (grade, windowMs) {
    if (!this.gradeEl) return;
    if (!grade) {
      this.gradeEl.className = "grade-pop game-ui-floating-grade is-luxury is-flourish";
      this.gradeEl.innerHTML = "READY<small>tap D F J K</small>";
      return;
    }
    this.gradeEl.className = "grade-pop game-ui-floating-grade is-luxury is-flourish grade-flash " + grade;
    var sub = grade === "miss" ? "miss" : "±" + windowMs + "ms";
    this.gradeEl.innerHTML = gradeLabel(grade).toUpperCase() + "<small>" + sub + "</small>";
    var el = this.gradeEl;
    var sheet = this.sheetEl;
    if (sheet) {
      sheet.classList.add("grade-flash-sheet");
      window.clearTimeout(sheet._flashTimer);
      sheet._flashTimer = window.setTimeout(function () {
        sheet.classList.remove("grade-flash-sheet");
      }, 420);
    }
    window.clearTimeout(el._flashTimer);
    el._flashTimer = window.setTimeout(function () {
      el.classList.remove("grade-flash");
    }, 450);
  };

  RhythmStrip.prototype.setStatus = function (text) {
    if (this.statusEl) this.statusEl.textContent = text;
  };

  function animatePlaybackHead(head) {
    if (!head || reducedMotion) return;
    var staff = head.closest(".game-ui-staff");
    if (!staff || staff.closest("[data-rhythm-playground]")) return;
    var max = staff.clientWidth - 24;
    var duration = 2400;
    var startTime = null;
    function step(ts) {
      if (!startTime) startTime = ts;
      var t = ((ts - startTime) % duration) / duration;
      var eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
      head.style.left = (8 + eased * max) + "px";
      requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  function initDecorativeNotes() {
    document.querySelectorAll(".game-ui-highway[data-animated-notes]").forEach(function (highway) {
      if (highway.closest("[data-rhythm-playground]")) return;
      var lanes = highway.querySelectorAll(".game-ui-lane");
      lanes.forEach(function (lane, laneIndex) {
        for (var i = 0; i < 3; i++) {
          var glyph = document.createElement("span");
          glyph.className = "game-ui-note-glyph" + (i === 1 ? " is-beam" : "");
          glyph.setAttribute("aria-hidden", "true");
          glyph.style.setProperty("--glyph-delay", (laneIndex * 0.4 + i * 0.7) + "s");
          glyph.style.top = (12 + i * 28) + "%";
          lane.appendChild(glyph);
        }
      });
    });
  }

  function fillAssetGrid(root) {
    if (!root) return;
    var assets = [
      "T_Melodia_SoftMG_Parchment.png",
      "T_Melodia_SoftMG_SealSP.png",
      "T_Melodia_SoftMG_SealULT.png",
      "T_Melodia_SoftMG_Hitline.png",
      "T_Melodia_SoftMG_LaneInk.png",
      "T_Melodia_SoftMG_ScrollEdge.png",
      "T_Melodia_SoftMG_PillowChip.png",
      "T_Melodia_FiligreeCornerBaroque.png",
      "T_Melodia_FiligreeDividerScroll.png",
      "T_Melodia_FiligreeCrestBaroque.png",
      "T_Melodia_FiligreeMedallionRosette.png",
      "T_Melodia_FiligreeBraceVolute.png",
      "T_Melodia_FiligreeBatchO_Baroque.png",
      "T_Melodia_FiligreeGradeHalo.png",
      "T_Melodia_FiligreeGradeHalo_Perfect.png",
      "T_Melodia_FiligreeGradeHalo_Great.png",
      "T_Melodia_FiligreeGradeHalo_Good.png",
      "T_Melodia_FiligreeGradeHalo_Miss.png",
      "T_Melodia_SkillRing.png",
      "T_Melodia_ComboBurst.png",
      "T_Melodia_GothicFrameCorner.png",
      "T_Melodia_GothicFrameRail.png",
      "T_Melodia_ScrollBorderRail.png",
      "T_Melodia_SheetParchment.png",
      "T_Melodia_IriOverlay.png",
      "T_Melodia_EnemyGlow.png",
      "T_Melodia_ElementWheel.png",
      "T_Melodia_StaffTile.png",
      "T_Melodia_SheenSweep.png",
      "T_Melodia_GradePerfect.png",
      "T_Melodia_GradeGreat.png",
      "T_Melodia_GradeGood.png",
      "T_Melodia_GradeMiss.png",
      "T_Melodia_LanePress.png",
      "T_Melodia_SkillChipBG.png",
      "T_Melodia_SafeAreaMask.png",
      "T_Melodia_MobileTopBar.png"
    ];
    var base = "../generated/assets/melodia-game-ui/";
    root.innerHTML = "";
    assets.forEach(function (file) {
      var tile = document.createElement("figure");
      tile.className = "game-ui-asset-tile";
      var img = document.createElement("img");
      img.src = base + file;
      img.alt = file.replace(".png", "");
      img.loading = "lazy";
      var cap = document.createElement("figcaption");
      cap.textContent = file;
      tile.appendChild(img);
      tile.appendChild(cap);
      root.appendChild(tile);
    });
  }

  function initIosPhaseSwitch(root) {
    if (!root) return;
    var switcher = root.querySelector("[data-ios-phase-switch]");
    if (!switcher) return;
    var buttons = switcher.querySelectorAll("[data-ios-set-phase]");
    function setPhase(phase) {
      root.setAttribute("data-ios-phase", phase);
      root.querySelectorAll("[data-ios-panel]").forEach(function (panel) {
        var id = panel.getAttribute("data-ios-panel");
        var show =
          (phase === "rhythm" && id === "rhythm") ||
          (phase === "command" && (id === "command" || id === "rhythm")) ||
          (phase === "enemy" && id === "enemy") ||
          (phase === "results" && id === "results");
        if (id === "rhythm") {
          panel.hidden = phase === "results" || phase === "enemy";
          return;
        }
        if (id === "command") {
          panel.hidden = false;
          return;
        }
        panel.hidden = !show;
      });
      buttons.forEach(function (btn) {
        var on = btn.getAttribute("data-ios-set-phase") === phase;
        if (on) btn.setAttribute("aria-current", "true");
        else btn.removeAttribute("aria-current");
      });
    }
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        setPhase(btn.getAttribute("data-ios-set-phase"));
      });
    });
    setPhase(root.getAttribute("data-ios-phase") || "rhythm");

    root.querySelectorAll("[data-ios-skills] .game-ui-skill-chip").forEach(function (chip) {
      chip.addEventListener("click", function () {
        root.querySelectorAll("[data-ios-skills] .game-ui-skill-chip").forEach(function (c) {
          c.classList.remove("is-selected");
        });
        chip.classList.add("is-selected");
        setPhase("command");
      });
    });
  }

  function applyIosMode() {
    var params = new URLSearchParams(window.location.search);
    var ios = params.get("mode") === "ios";
    if (ios) {
      document.body.classList.add("ios-mode");
      var play = document.querySelector("[data-ios-play]");
      if (play) play.setAttribute("data-show-safe", "1");
      var target = document.getElementById("ios-battle");
      if (target && !window.location.hash) {
        target.scrollIntoView({ block: "start" });
      }
    }
  }

  function init() {
    applyIosMode();
    document.querySelectorAll("[data-codex-grid]").forEach(fillCodexGrid);
    document.querySelectorAll("[data-game-ui-assets]").forEach(fillAssetGrid);
    document.querySelectorAll(".game-ui-playback-head").forEach(animatePlaybackHead);
    initDecorativeNotes();
    initPhaseSwitch();
    initClefCode();
    document.querySelectorAll("[data-ios-play]").forEach(initIosPhaseSwitch);
    loadRhythmConfig().then(function () {
      document.querySelectorAll("[data-rhythm-playground], [data-ios-rhythm]").forEach(function (el) {
        new RhythmStrip(el);
        startBeatBus(el);
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
