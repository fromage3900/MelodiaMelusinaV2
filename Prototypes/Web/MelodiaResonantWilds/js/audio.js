// Procedural score + beat clock. Everything that is graded is graded against
// the beats this scheduler puts on the audio timeline, mapped to the moment
// they are actually audible (output latency) so taps line up with the ear.

import { midiToFreq, clamp } from './util.js';

const SCALES = { major: [0, 2, 4, 5, 7, 9, 11], minor: [0, 2, 3, 5, 7, 8, 10] };
const ALL16 = [...Array(16).keys()];

// Step lists are 16th notes inside one bar. Tone patterns index chord tones
// [root, third, fifth, octave, ninth].
const STYLES = {
  morning: {
    kick: [0, 8], snare: [], rim: [4, 12], hat: [2, 6, 10, 14],
    bass: { steps: [0, 8], len: 7, tones: [0, 2] },
    arp: { steps: [0, 3, 6, 8, 11, 14], tones: [0, 2, 3, 1, 2, 4], oct: 12, voice: 'box' },
    pad: 'soft', leadVoice: 'box',
  },
  waltz: {
    kick: [0], snare: [], rim: [4, 8], hat: [2, 6, 10],
    bass: { steps: [0, 4, 8], len: 3, tones: [0, 2, 2] },
    arp: { steps: [0, 2, 4, 6, 8, 10], tones: [0, 1, 2, 3, 2, 1], oct: 12, voice: 'box' },
    pad: 'soft', leadVoice: 'bell',
  },
  cathedral: {
    kick: [0, 8], snare: [12], rim: [4], hat: [4, 12],
    bass: { steps: [0, 8], len: 8, tones: [0, 2] },
    arp: { steps: [0, 4, 8, 12], tones: [0, 1, 2, 3], oct: 12, voice: 'bell' },
    pad: 'organ', leadVoice: 'bell',
  },
  fugue: {
    kick: [0, 6, 8], snare: [4, 12], rim: [], hat: [0, 2, 4, 6, 8, 10, 12, 14],
    bass: { steps: [0, 2, 4, 6, 8, 10, 12, 14], len: 2, tones: [0, 2, 3, 2, 0, 2, 1, 2] },
    arp: { steps: [0, 6, 8, 14], tones: [3, 2, 1, 2], oct: 12, voice: 'pluck' },
    pad: 'dark', leadVoice: 'pluck', canon: 7,
  },
  toccata: {
    kick: [0, 4, 8, 12], snare: [4, 12], rim: [], hat: ALL16,
    bass: { steps: [0, 2, 4, 6, 8, 10, 12, 14], len: 1, tones: [0, 3, 0, 3, 0, 3, 0, 3] },
    arp: { steps: ALL16, tones: [0, 1, 2, 3, 4, 3, 2, 1, 0, 1, 2, 3, 4, 3, 2, 1], oct: 12, voice: 'organlead' },
    pad: 'organ', leadVoice: 'organlead',
  },
  glacial: {
    kick: [0, 10], snare: [8], rim: [], hat: [4, 12], shimmer: [2, 6, 10, 14],
    bass: { steps: [0], len: 15, tones: [0] },
    arp: { steps: [0, 3, 6, 8, 11, 14], tones: [0, 2, 4, 3, 2, 1], oct: 24, voice: 'bell' },
    pad: 'ice', leadVoice: 'bell', chordBars: 2,
  },
  rift: {
    kick: [0, 4, 8, 11, 12], snare: [4, 12], rim: [14], hat: [0, 2, 4, 6, 8, 10, 12, 14],
    bass: { steps: [0, 3, 6, 8, 11, 14], len: 2, tones: [0, 0, 3, 0, 2, 1] },
    arp: { steps: ALL16, tones: [0, 2, 3, 2, 1, 2, 3, 4, 0, 2, 3, 2, 1, 2, 4, 3], oct: 12, voice: 'pluck' },
    pad: 'dark', leadVoice: 'organlead',
  },
};

// Layer mix per intensity: 0 explore, 1 combat, 2 encore.
const MIX = [
  { drums: 0.55, bass: 0.35, pad: 0.9, arp: 0.7, lead: 0.0 },
  { drums: 1.0, bass: 1.0, pad: 0.6, arp: 0.85, lead: 0.45 },
  { drums: 1.15, bass: 1.1, pad: 0.7, arp: 1.0, lead: 1.0 },
];

export class AudioEngine {
  constructor() {
    this.ctx = null;
    this.beats = [];
    this.firedIndex = -1;
    this.beatCount = 0;
    this.bar = 0;
    this.stepInBar = 0;
    this.lookahead = 0.14;
    this.def = null;
    this.pending = null;
    this.intensity = 0;
    this.volumes = { music: 0.75, sfx: 0.9 };
    this._sfxBudget = 0;
    this._budgetReset = 0;
  }

  get running() { return !!this.ctx && this.ctx.state === 'running'; }

  start(def) {
    if (this.ctx) { this.ctx.resume(); return; }
    const AC = window.AudioContext || window.webkitAudioContext;
    const ctx = new AC({ latencyHint: 'interactive' });
    this.ctx = ctx;
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -16; comp.ratio.value = 4; comp.attack.value = 0.004; comp.release.value = 0.2;
    this.master = ctx.createGain(); this.master.gain.value = 0.85;
    this.master.connect(comp).connect(ctx.destination);
    this.musicBus = ctx.createGain(); this.musicBus.gain.value = this.volumes.music; this.musicBus.connect(this.master);
    this.sfxBus = ctx.createGain(); this.sfxBus.gain.value = this.volumes.sfx; this.sfxBus.connect(this.master);
    this.reverb = ctx.createConvolver(); this.reverb.buffer = this._impulse(2.2);
    this.reverbSend = ctx.createGain(); this.reverbSend.gain.value = 0.32;
    this.reverbSend.connect(this.reverb).connect(this.master);
    this.layers = {};
    for (const k of ['drums', 'bass', 'pad', 'arp', 'lead']) {
      const g = ctx.createGain(); g.gain.value = MIX[0][k]; g.connect(this.musicBus); this.layers[k] = g;
    }
    this.noise = this._noiseBuffer();
    this._applyDef(def);
    this.nextStepTime = ctx.currentTime + 0.12;
    this._timer = setInterval(() => this._schedule(), 25);
    ctx.resume();
  }

  setVolumes(music, sfx) {
    this.volumes = { music, sfx };
    if (!this.ctx) return;
    this.musicBus.gain.setTargetAtTime(music, this.ctx.currentTime, 0.05);
    this.sfxBus.gain.setTargetAtTime(sfx, this.ctx.currentTime, 0.05);
  }

  suspend() { if (this.ctx && this.ctx.state === 'running') this.ctx.suspend(); }
  resume() { if (this.ctx && this.ctx.state !== 'running') this.ctx.resume(); }

  // Request a new score (biome/rift/hub). Applied on the next bar line so the
  // groove never skips mid-bar.
  setScore(def) {
    if (!this.def) { this._applyDef(def); return; }
    if (this.def.id === def.id && this.def.bpm === def.bpm) { this.pending = null; return; }
    this.pending = def;
  }

  setIntensity(level) {
    level = clamp(level | 0, 0, 2);
    if (level === this.intensity || !this.ctx) return;
    this.intensity = level;
    const t = this.ctx.currentTime;
    for (const k in this.layers) this.layers[k].gain.setTargetAtTime(MIX[level][k], t, 0.6);
  }

  get bpm() { return this.def ? this.def.bpm : 100; }
  get spb() { return 60 / this.bpm; }
  get meter() { return this.def ? this.def.meter : 4; }

  // Context time the listener is hearing at performance time `perfMs`.
  audibleTime(perfMs = performance.now()) {
    const ctx = this.ctx;
    if (!ctx) return 0;
    if (ctx.getOutputTimestamp) {
      const ts = ctx.getOutputTimestamp();
      if (ts && ts.contextTime > 0 && ts.performanceTime > 0) {
        const t = ts.contextTime + (perfMs - ts.performanceTime) / 1000;
        if (t > ctx.currentTime - 0.6 && t < ctx.currentTime + 0.2) return t;
      }
    }
    return ctx.currentTime - (ctx.outputLatency || ctx.baseLatency || 0.02) + (perfMs - performance.now()) / 1000;
  }

  nearestBeat(t) {
    let best = null, bestD = Infinity;
    const n = this.beats.length;
    for (let i = n - 1; i >= 0; i--) {
      const b = this.beats[i];
      const d = Math.abs(t - b.time);
      if (d < bestD) { bestD = d; best = b; }
      if (b.time < t - 2) break;
    }
    const last = this.beats[n - 1];
    if (last) {
      for (let k = 1; k <= 2; k++) {
        const pt = last.time + last.spb * k;
        const d = Math.abs(t - pt);
        if (d < bestD) {
          bestD = d;
          const inBar = (last.inBar + k) % last.meter;
          best = { time: pt, index: last.index + k, inBar, bar: last.bar + (last.inBar + k >= last.meter ? 1 : 0), spb: last.spb, meter: last.meter, predicted: true };
        }
      }
    }
    return best;
  }

  lastBeatAt(t) {
    for (let i = this.beats.length - 1; i >= 0; i--) if (this.beats[i].time <= t) return this.beats[i];
    return null;
  }

  pollBeats(t) {
    const out = [];
    for (const b of this.beats) {
      if (b.index > this.firedIndex && b.time <= t) { out.push(b); this.firedIndex = b.index; }
    }
    return out;
  }

  // ---------------------------------------------------------------- scheduler
  _applyDef(def) {
    this.def = def;
    this.style = STYLES[def.style] || STYLES.morning;
    this.scale = SCALES[def.mode] || SCALES.major;
  }

  _schedule() {
    const ctx = this.ctx;
    if (!ctx || ctx.state !== 'running') return;
    if (this.nextStepTime < ctx.currentTime - 0.2) this.nextStepTime = ctx.currentTime + 0.05;
    const horizon = ctx.currentTime + this.lookahead;
    while (this.nextStepTime < horizon) {
      this._step(this.nextStepTime);
      this.stepInBar++;
      if (this.stepInBar >= this.meter * 4) { this.stepInBar = 0; this.bar++; }
      this.nextStepTime += this.spb / 4;
    }
  }

  _chord() {
    const def = this.def;
    const per = this.style.chordBars || 1;
    const [semi, q] = def.prog[Math.floor(this.bar / per) % def.prog.length];
    const root = def.key + semi;
    const third = q === 'maj' ? 4 : 3;
    return [root, root + third, root + 7, root + 12, root + 14];
  }

  _step(t) {
    if (this.stepInBar === 0 && this.pending) { this._applyDef(this.pending); this.pending = null; }
    const s = this.stepInBar;
    const st = this.style;
    const spb = this.spb;
    const stepDur = spb / 4;
    if (s % 4 === 0) {
      this.beats.push({ time: t, index: this.beatCount++, inBar: s / 4, bar: this.bar, spb, meter: this.meter });
      if (this.beats.length > 48) this.beats.shift();
    }
    const chord = this._chord();
    const D = this.layers.drums;
    if (st.kick.includes(s)) this._kick(t, s === 0 ? 1 : 0.8, D);
    if (st.snare.includes(s)) this._snare(t, 0.55, D);
    if (st.rim.includes(s)) this._rim(t, 0.35, D);
    if (st.hat.includes(s)) this._hat(t, s % 4 === 2 ? 0.22 : 0.13, D);
    if (st.shimmer && st.shimmer.includes(s)) this._voice('box', t, chord[(s / 2) % 5 | 0] + 24, stepDur * 3, 0.05, this.layers.arp, true);
    // Beat click keeps the grid audible in every style (rhythm is the verb).
    if (s % 4 === 0) this._rim(t, s === 0 ? 0.3 : 0.18, D, s === 0 ? 1800 : 1400);

    const bi = st.bass.steps.indexOf(s);
    if (bi >= 0) this._bass(t, chord[st.bass.tones[bi % st.bass.tones.length]] - 24, stepDur * st.bass.len);

    if (s === 0) this._pad(t, chord.slice(0, 3), spb * this.meter * (st.chordBars || 1), st.pad);

    const ai = st.arp.steps.indexOf(s);
    if (ai >= 0) this._voice(st.arp.voice, t, chord[st.arp.tones[ai % st.arp.tones.length]] + st.arp.oct, stepDur * 2.5, 0.12, this.layers.arp, true);

    // Leitmotif: 8th notes over the first half of the bar; odd bars answer
    // (fugue style answers at the fifth, like a real subject/answer pair).
    const motif = this.def.motif;
    if (motif && s % 2 === 0 && s / 2 < motif.length) {
      const odd = this.bar % 2 === 1;
      const shift = odd ? (st.canon || 12) : 0;
      const deg = motif[s / 2];
      this._voice(st.leadVoice, t, this.def.key + 12 + deg + shift, stepDur * 1.8, 0.16, this.layers.lead, true);
    }
  }

  // ---------------------------------------------------------------- voices
  _env(g, t, peak, a, d) {
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(Math.max(0.0002, peak), t + a);
    g.gain.exponentialRampToValueAtTime(0.0001, t + a + d);
  }

  _kick(t, v, out) {
    const ctx = this.ctx;
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.frequency.setValueAtTime(150, t);
    o.frequency.exponentialRampToValueAtTime(42, t + 0.14);
    this._env(g, t, 0.9 * v, 0.004, 0.28);
    o.connect(g).connect(out);
    o.start(t); o.stop(t + 0.32);
  }

  _noiseHit(t, v, out, type, freq, dur, q = 0.8) {
    const ctx = this.ctx;
    const src = ctx.createBufferSource(); src.buffer = this.noise;
    const f = ctx.createBiquadFilter(); f.type = type; f.frequency.value = freq; f.Q.value = q;
    const g = ctx.createGain();
    this._env(g, t, v, 0.002, dur);
    src.connect(f).connect(g).connect(out);
    src.start(t, Math.random() * 0.5); src.stop(t + dur + 0.02);
  }

  _snare(t, v, out) {
    this._noiseHit(t, v, out, 'bandpass', 1900, 0.16, 0.7);
    const ctx = this.ctx;
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = 'triangle'; o.frequency.setValueAtTime(220, t);
    this._env(g, t, v * 0.5, 0.002, 0.08);
    o.connect(g).connect(out); o.start(t); o.stop(t + 0.1);
  }

  _hat(t, v, out) { this._noiseHit(t, v, out, 'highpass', 8000, 0.045, 0.5); }

  _rim(t, v, out, freq = 1400) {
    const ctx = this.ctx;
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = 'sine'; o.frequency.setValueAtTime(freq, t);
    this._env(g, t, v, 0.001, 0.04);
    o.connect(g).connect(out); o.start(t); o.stop(t + 0.06);
  }

  _bass(t, midi, dur) {
    const ctx = this.ctx;
    const o = ctx.createOscillator(), sub = ctx.createOscillator(), f = ctx.createBiquadFilter(), g = ctx.createGain();
    o.type = 'sawtooth'; o.frequency.value = midiToFreq(midi);
    sub.type = 'sine'; sub.frequency.value = midiToFreq(midi);
    f.type = 'lowpass'; f.frequency.setValueAtTime(900, t); f.frequency.exponentialRampToValueAtTime(260, t + Math.min(0.3, dur));
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.22, t + 0.01);
    g.gain.setValueAtTime(0.2, t + Math.max(0.02, dur - 0.04));
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur + 0.05);
    o.connect(f); sub.connect(f); f.connect(g).connect(this.layers.bass);
    o.start(t); sub.start(t); o.stop(t + dur + 0.08); sub.stop(t + dur + 0.08);
  }

  _pad(t, notes, dur, kind) {
    const ctx = this.ctx;
    const f = ctx.createBiquadFilter(); f.type = 'lowpass';
    f.frequency.value = kind === 'organ' ? 1800 : kind === 'ice' ? 2600 : kind === 'dark' ? 700 : 1100;
    const g = ctx.createGain();
    const atk = kind === 'organ' ? 0.06 : 0.5;
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(0.05, t + atk);
    g.gain.setValueAtTime(0.05, t + Math.max(atk, dur - 0.3));
    g.gain.linearRampToValueAtTime(0.0001, t + dur + 0.2);
    f.connect(g); g.connect(this.layers.pad); g.connect(this.reverbSend);
    for (const n of notes) {
      for (const det of [-7, 7]) {
        const o = ctx.createOscillator();
        o.type = kind === 'organ' ? 'square' : kind === 'ice' ? 'triangle' : 'sawtooth';
        o.frequency.value = midiToFreq(n); o.detune.value = det;
        o.connect(f); o.start(t); o.stop(t + dur + 0.3);
      }
    }
  }

  // Tonal voices shared by music and SFX.
  _voice(kind, t, midi, dur, vol, out, verb = false) {
    const ctx = this.ctx;
    const freq = midiToFreq(midi);
    const g = ctx.createGain();
    g.connect(out);
    if (verb) g.connect(this.reverbSend);
    if (kind === 'box' || kind === 'bell') {
      const car = ctx.createOscillator(), mod = ctx.createOscillator(), mg = ctx.createGain();
      car.frequency.value = freq; mod.frequency.value = freq * (kind === 'box' ? 3.5 : 2.76);
      const decay = kind === 'box' ? 0.55 : 1.6;
      mg.gain.setValueAtTime(freq * 2.2, t);
      mg.gain.exponentialRampToValueAtTime(freq * 0.05, t + decay);
      mod.connect(mg).connect(car.frequency);
      this._env(g, t, vol, 0.003, decay);
      car.connect(g);
      car.start(t); mod.start(t); car.stop(t + decay + 0.05); mod.stop(t + decay + 0.05);
      return;
    }
    const o = ctx.createOscillator();
    const f = ctx.createBiquadFilter(); f.type = 'lowpass';
    if (kind === 'organlead') { o.type = 'square'; f.frequency.value = 2400; }
    else if (kind === 'soft') { o.type = 'sine'; f.frequency.value = 3000; }
    else if (kind === 'saw') { o.type = 'sawtooth'; f.frequency.setValueAtTime(4000, t); f.frequency.exponentialRampToValueAtTime(500, t + dur); }
    else { o.type = 'triangle'; f.frequency.setValueAtTime(5000, t); f.frequency.exponentialRampToValueAtTime(900, t + dur); }
    o.frequency.value = freq;
    this._env(g, t, vol, 0.004, Math.max(0.06, dur));
    o.connect(f).connect(g);
    o.start(t); o.stop(t + dur + 0.1);
  }

  // ---------------------------------------------------------------- SFX
  _budget(n = 1) {
    const now = performance.now();
    if (now - this._budgetReset > 60) { this._budgetReset = now; this._sfxBudget = 0; }
    if (this._sfxBudget + n > 14) return false;
    this._sfxBudget += n;
    return true;
  }

  get now() { return this.ctx ? this.ctx.currentTime + 0.004 : 0; }

  // Snap any midi note into the current key/scale.
  inKey(midi) {
    const key = this.def ? this.def.key : 60;
    const rel = ((midi - key) % 12 + 12) % 12;
    let best = 0, bd = 99;
    for (const s of this.scale || SCALES.major) { const d = Math.abs(s - rel); if (d < bd) { bd = d; best = s; } }
    return midi - rel + best;
  }

  degree(n, oct = 0) {
    const sc = this.scale || SCALES.major;
    const i = ((n % 7) + 7) % 7;
    return (this.def ? this.def.key : 60) + sc[i] + 12 * (Math.floor(n / 7) + oct);
  }

  grade(grade) {
    if (!this.running || !this._budget(3)) return;
    const t = this.now, root = this._chord()[0] + 12;
    if (grade === 'Perfect') {
      this._voice('bell', t, root + 12, 0.5, 0.16, this.sfxBus, true);
      this._voice('bell', t + 0.03, this.inKey(root + 16), 0.5, 0.12, this.sfxBus, true);
      this._voice('bell', t + 0.06, root + 19, 0.5, 0.1, this.sfxBus, true);
    } else if (grade === 'Great') {
      this._voice('box', t, root + 12, 0.3, 0.14, this.sfxBus, true);
      this._voice('box', t + 0.04, root + 19, 0.3, 0.1, this.sfxBus, true);
    } else if (grade === 'Good') {
      this._voice('box', t, root + 7, 0.25, 0.12, this.sfxBus);
    } else {
      this._voice('pluck', t, root - 11, 0.12, 0.12, this.sfxBus);
      this._noiseHit(t, 0.08, this.sfxBus, 'lowpass', 400, 0.08);
    }
  }

  swing(step) {
    if (!this.running || !this._budget()) return;
    this._noiseHit(this.now, 0.1, this.sfxBus, 'bandpass', 2400 + step * 600, 0.07, 1.5);
  }

  hit(crit = false) {
    if (!this.running || !this._budget()) return;
    const t = this.now;
    this._noiseHit(t, crit ? 0.28 : 0.16, this.sfxBus, 'bandpass', crit ? 3200 : 1500, 0.06, 1.2);
    if (crit) this._voice('pluck', t, this.degree(Math.floor(Math.random() * 7), 2), 0.12, 0.08, this.sfxBus);
  }

  skill(skill) {
    if (!this.running) return;
    const t = this.now, stepDur = this.spb / 4;
    const notes = skill.pitches.slice(0, 8);
    const base = this.def ? this.def.key - 60 : 0;
    const voice = { Forte: 'saw', Tide: 'soft', Gale: 'pluck', Radiant: 'bell', Stone: 'pluck', Arcane: 'box', Umbral: 'soft' }[skill.element] || 'box';
    notes.forEach((p, i) => {
      if (this._budget()) this._voice(voice, t + i * stepDur * 0.5, this.inKey(p + base), stepDur * 0.9, 0.09, this.sfxBus, true);
    });
  }

  kill(boss = false) {
    if (!this.running || !this._budget(2)) return;
    const t = this.now;
    const n = this.degree(Math.floor(Math.random() * 5) + 2, 1);
    this._voice('bell', t, n, 0.8, boss ? 0.25 : 0.1, this.sfxBus, true);
    if (boss) for (let i = 0; i < 5; i++) this._voice('bell', t + i * 0.09, this.degree(i * 2, 1), 1.2, 0.14, this.sfxBus, true);
  }

  loot(rarityIndex) {
    if (!this.running) return;
    const t = this.now;
    const n = [1, 2, 3, 4, 7][rarityIndex];
    for (let i = 0; i < n; i++) this._voice(rarityIndex >= 3 ? 'bell' : 'box', t + i * 0.07, this.degree(i * 2, 1 + (i > 3 ? 1 : 0)), 0.9, 0.08 + rarityIndex * 0.02, this.sfxBus, true);
    if (rarityIndex === 4) this._pad(t, [this.degree(0), this.degree(2), this.degree(4)].map((x) => x + 12), 2.2, 'ice');
  }

  pickup() {
    if (!this.running || !this._budget()) return;
    this._voice('box', this.now, this.degree(Math.floor(Math.random() * 4) + 4, 1), 0.2, 0.06, this.sfxBus);
  }

  chime(i) {
    if (!this.running || !this._budget()) return;
    this._voice('bell', this.now, this.degree(i % 8, 1), 1.2, 0.08, this.sfxBus, true);
  }

  levelUp() {
    if (!this.running) return;
    const t = this.now;
    [0, 2, 4, 7, 9, 11, 14].forEach((d, i) => this._voice('bell', t + i * 0.08, this.degree(d, 0), 1.2, 0.14, this.sfxBus, true));
  }

  encore() {
    if (!this.running) return;
    const t = this.now;
    for (let i = 0; i < 8; i++) this._voice('saw', t + i * 0.05, this.degree(i, 0), 0.4, 0.08, this.sfxBus, true);
    this._pad(t, [this.degree(0, 1), this.degree(2, 1), this.degree(4, 1)], 3, 'ice');
  }

  hurt() {
    if (!this.running || !this._budget()) return;
    const t = this.now;
    this._kick(t, 0.6, this.sfxBus);
    this._noiseHit(t, 0.2, this.sfxBus, 'lowpass', 600, 0.12);
  }

  dodge() {
    if (!this.running || !this._budget()) return;
    this._noiseHit(this.now, 0.12, this.sfxBus, 'bandpass', 900, 0.18, 0.6);
  }

  tick(high = false, t = null) {
    if (!this.running || !this._budget()) return;
    this._rim(t ?? this.now, high ? 0.35 : 0.22, this.sfxBus, high ? 2600 : 1900);
  }

  ui() {
    if (!this.running || !this._budget()) return;
    this._voice('box', this.now, this.degree(4, 1), 0.15, 0.06, this.sfxBus);
  }

  fail() {
    if (!this.running) return;
    const t = this.now;
    this._voice('pluck', t, this.degree(4, -1), 0.3, 0.14, this.sfxBus);
    this._voice('pluck', t + 0.12, this.degree(3, -1) - 1, 0.5, 0.14, this.sfxBus);
  }

  // ---------------------------------------------------------------- buffers
  _noiseBuffer() {
    const ctx = this.ctx;
    const b = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate);
    const d = b.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    return b;
  }

  _impulse(seconds) {
    const ctx = this.ctx;
    const len = Math.floor(ctx.sampleRate * seconds);
    const b = ctx.createBuffer(2, len, ctx.sampleRate);
    for (let c = 0; c < 2; c++) {
      const d = b.getChannelData(c);
      for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 2.6);
    }
    return b;
  }
}
