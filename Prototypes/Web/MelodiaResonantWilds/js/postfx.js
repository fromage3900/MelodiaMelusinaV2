// Three.js post pipeline (r170 addons, vendored).
// EffectComposer → RenderPass → OutlinePass → Bloom → OutputPass → optional full-res crisp Kuwahara → FXAA.
// The paint pass samples the ALREADY cel-shaded output, preserving the canonical hard RGB lighting.
// Bloom is selective by luminance threshold (emissive sparks / dew / crystals).

import { Vector2 } from 'three';
import { EffectComposer } from '../vendor/postprocessing/EffectComposer.js';
import { RenderPass } from '../vendor/postprocessing/RenderPass.js';
import { OutlinePass } from '../vendor/postprocessing/OutlinePass.js';
import { UnrealBloomPass } from '../vendor/postprocessing/UnrealBloomPass.js';
import { OutputPass } from '../vendor/postprocessing/OutputPass.js';
import { ShaderPass } from '../vendor/postprocessing/ShaderPass.js';
import { FXAAShader } from '../vendor/shaders/FXAAShader.js';

export class PostFX {
  constructor(game, { worldEffects = true } = {}) {
    this.g = game;
    this.worldEffects = !!worldEffects;
    this.enabled = !!worldEffects;
    this._want = !!worldEffects;
    this.painterly = game.painterly || null;
    const r = game.renderer;
    const size = new Vector2();
    r.getSize(size);
    this.composer = new EffectComposer(r);
    this.renderPass = new RenderPass(game.scene, game.camera);
    this.outline = new OutlinePass(new Vector2(size.x, size.y), game.scene, game.camera);
    this.outline.edgeStrength = 4.5;
    this.outline.edgeGlow = 0.85;
    this.outline.edgeThickness = 2.2;
    this.outline.pulsePeriod = 1.6;
    this.outline.visibleEdgeColor.set('#ff7a9a');
    this.outline.hiddenEdgeColor.set('#ff3a68');
    // Soft selective bloom: high threshold so only bright emissives / Encore trails contribute.
    this.bloom = new UnrealBloomPass(new Vector2(size.x, size.y), 0.35, 0.35, 0.88);
    this.output = new OutputPass();
    this.fxaa = new ShaderPass(FXAAShader);
    this.composer.addPass(this.renderPass);
    this.composer.addPass(this.outline);
    this.composer.addPass(this.bloom);
    this.composer.addPass(this.output);
    // Final-image paint: outline and bloom stay crisp underneath; no half-res
    // scene capture and no second independent renderer/composer.
    if (this.painterly) this.composer.addPass(this.painterly.pass);
    this.composer.addPass(this.fxaa);
    this._selected = [];
    this.setEnabled(this.worldEffects);
    this.resize();
  }

  setEnabled(on) {
    this._want = !!on;
    this.enabled = this.worldEffects && this._want && this.g.profile.settings.quality !== 'low';
    this.outline.enabled = this.enabled;
    this.bloom.enabled = this.enabled;
    // FXAA is intentionally disabled with paint to prevent a second softening
    // pass; the game already renders its source at the quality DPR.
    this.fxaa.enabled = this.enabled && !this.painterly?.pass.enabled;
  }

  resize() {
    const r = this.g.renderer;
    const pr = r.getPixelRatio();
    const w = innerWidth;
    const h = innerHeight;
    this.composer.setPixelRatio(pr);
    this.composer.setSize(w, h);
    this.fxaa.material.uniforms.resolution.value.set(1 / (w * pr), 1 / (h * pr));
    this.painterly?.resize(w * pr, h * pr);
  }

  /** Refresh which meshes get the glow outline this frame. */
  syncSelection() {
    const g = this.g;
    const list = this._selected;
    list.length = 0;
    let threat = false;
    for (const e of g.enemies) {
      if (e.dead || !e.mesh) continue;
      if (e.aggro || e.strikes.length || e.boss || e.elite) {
        list.push(e.mesh);
        if (e.strikes.length || e.windup > 0) threat = true;
      }
    }
    const it = g._outlineInteract;
    if (it?.mesh) list.push(it.mesh);
    this.outline.selectedObjects = list;
    // Beat-breathe the outline with the score meter.
    const meter = Math.max(1, g.audio?.meter || 4);
    const beatPulse = 1.2 + (g.beatPhase || 0) * 0.6;
    // Encore / biome accent tints selection edges (presentation only).
    const accent = g.encoreSys?.accentColor?.();
    if (threat) {
      this.outline.visibleEdgeColor.setRGB(1, 0.35, 0.5);
      this.outline.pulsePeriod = Math.max(0.45, beatPulse * 0.55);
      this.outline.edgeStrength = 5.5;
      this.outline.edgeThickness = 2.6;
    } else if (it) {
      this.outline.visibleEdgeColor.setRGB(1, 0.85, 0.4);
      this.outline.pulsePeriod = Math.max(1.2, beatPulse);
      this.outline.edgeStrength = 4.0;
      this.outline.edgeThickness = 2.0;
    } else if (accent) {
      this.outline.visibleEdgeColor.set(accent);
      this.outline.pulsePeriod = meter * 0.35;
      this.outline.edgeStrength = 4.2;
      this.outline.edgeThickness = 2.1;
    } else {
      this.outline.visibleEdgeColor.setRGB(1, 0.5, 0.68);
      this.outline.pulsePeriod = 1.4;
      this.outline.edgeStrength = 4.5;
      this.outline.edgeThickness = 2.2;
    }
  }

  render() {
    const paintOn = !!this.painterly?.pass.enabled;
    if (!this.enabled && !paintOn) {
      this.g.renderer.render(this.g.scene, this.g.camera);
      return;
    }
    this.fxaa.enabled = this.enabled && !paintOn;
    if (this.enabled) this.syncSelection();
    this.composer.render();
  }
}
