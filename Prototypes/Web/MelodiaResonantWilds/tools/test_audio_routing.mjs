// Resonant Wilds audio graph contract: independent dry+wet buses and SFX cue routing.
// Node-only; does not claim a device-speaker listening test.
import assert from 'node:assert/strict';
import { AudioEngine } from '../js/audio.js';
class Param {
  constructor(value = 0) { this.value = value; }
  setValueAtTime(v) { this.value = v; }
  exponentialRampToValueAtTime(v) { this.value = v; }
  linearRampToValueAtTime(v) { this.value = v; }
  setTargetAtTime(v) { this.value = v; }
}
class Node {
  constructor() {
    this.connections = []; this.gain = new Param(1);
    this.frequency = new Param(440); this.detune = new Param(0); this.Q = new Param(1);
  }
  connect(node) { this.connections.push(node); return node; }
  start() {} stop() {}
}
class FakeContext {
  constructor() { this.state = 'running'; this.currentTime = 1; this.sampleRate = 8000; this.nodes = []; this.destination = new Node(); }
  node() { const n = new Node(); this.nodes.push(n); return n; }
  createDynamicsCompressor() { const n=this.node(); n.threshold=new Param(); n.ratio=new Param(); n.attack=new Param(); n.release=new Param(); return n; }
  createGain() { return this.node(); }
  createConvolver() { return this.node(); }
  createOscillator() { return this.node(); }
  createBiquadFilter() { return this.node(); }
  createBufferSource() { return this.node(); }
  createBuffer(channels, length, rate) { return {length, sampleRate:rate, getChannelData:()=>new Float32Array(length)}; }
  resume() { this.state='running'; return Promise.resolve(); }
  suspend() { this.state='suspended'; return Promise.resolve(); }
}
globalThis.window={AudioContext:FakeContext};
const a = new AudioEngine();
const def = {id:'hub', ambience:'hub', bpm:100, meter:4, style:'morning', key:60, mode:'major', prog:[[0,'maj']], motif:[0,2,4,7]};
try {
  a.start(def);
  assert.ok(a.ctx && a.layers.ambience, 'region ambience scheduler is present');
  assert.ok(a.reverb.connections.includes(a.musicBus), 'music reverb terminates at music bus');
  assert.ok(a.sfxReverb.connections.includes(a.sfxBus), 'SFX reverb terminates at SFX bus');
  assert.ok(!a.reverb.connections.includes(a.master), 'no wet-signal bypass around volume sliders');
  a.setVolumes(0.33, 0);
  assert.equal(a.musicBus.gain.value, 0.33);
  assert.equal(a.sfxBus.gain.value, 0);
  a._voice('bell', a.now, 72, .2, .1, a.sfxBus, true);
  a._pad(a.now, [60,64,67], .8, 'ice', a.sfxBus);
  assert.ok(a.ctx.nodes.some(n=>n.connections.includes(a.sfxBus) && n.connections.includes(a.sfxReverbSend)), 'SFX chords send both wet and dry through SFX bus');
  assert.ok(a.ctx.nodes.some(n=>n.connections.includes(a.sfxBus) && n.connections.includes(a.sfxReverbSend) && n.gain.value<0.1), 'SFX voices preserve independent reverb routing');
  a.setVolumes(0, 0.65);
  assert.equal(a.musicBus.gain.value, 0);
  assert.equal(a.sfxBus.gain.value, 0.65);
  a._ambiencePulse(a.now);
  assert.equal(a._ambienceId, 'hub');
  console.log('PASS: ethereal ambience, independent SFX/music dry-wet buses, SFX pad routing, and volume controls');
} finally {
  if (a._timer) clearInterval(a._timer);
}
