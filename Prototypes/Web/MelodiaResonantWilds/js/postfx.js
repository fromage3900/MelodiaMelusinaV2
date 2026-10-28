// Three.js OutlinePass pipeline (r170 addons, vendored).
// EffectComposer → RenderPass → OutlinePass → OutputPass → optional FXAA.
// Selected objects are combat threats / interact targets — presentation only.

import { Vector2 } from 'three';
import { EffectComposer } from '../vendor/postprocessing/EffectComposer.js';
import { RenderPass } from '../vendor/postprocessing/RenderPass.js';
import { OutlinePass } from '../vendor/postprocessing/OutlinePass.js';
import { OutputPass } from '../vendor/postprocessing/OutputPass.js';
import { ShaderPass } from '../vendor/postprocessing/ShaderPass.js';
import { FXAAShader } from '../vendor/shaders/FXAAShader.js';

export class PostFX {
  constructor(game) {
    this.g = game;
    this.enabled = true;
    this._want = true;
    const r = game.renderer;
    const size = new Vector2();
    r.getSize(size);
    this.composer = new EffectComposer(r);
    this.renderPass = new RenderPass(game.scene, game.camera);
    this.outline = new OutlinePass(new Vector2(size.x, size.y), game.scene, game.camera);
    this.outline.edgeStrength = 2.6;
    this.outline.edgeGlow = 0.55;
    this.outline.edgeThickness = 1.4;
    this.outline.pulsePeriod = 1.6;
    this.outline.visibleEdgeColor.set('#ff7a9a');
    this.outline.hiddenEdgeColor.set('#5a2038');
    this.output = new OutputPass();
    this.fxaa = new ShaderPass(FXAAShader);
    this.composer.addPass(this.renderPass);
    this.composer.addPass(this.outline);
    this.composer.addPass(this.output);
    this.composer.addPass(this.fxaa);
    this._selected = [];
    this._threatColor = { x: 1, y: 0.48, z: 0.6 };
    this._selectColor = { x: 1, y: 0.85, z: 0.47 };
    this.resize();
  }

  setEnabled(on) {
    this._want = !!on;
    this.enabled = this._want && this.g.profile.settings.quality !== 'low';
  }

  resize() {
    const r = this.g.renderer;
    const pr = r.getPixelRatio();
    const w = innerWidth;
    const h = innerHeight;
    this.composer.setPixelRatio(pr);
    this.composer.setSize(w, h);
    this.fxaa.material.uniforms.resolution.value.set(1 / (w * pr), 1 / (h * pr));
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
    if (threat) {
      this.outline.visibleEdgeColor.setRGB(1, 0.42, 0.55);
      this.outline.pulsePeriod = 0.85;
      this.outline.edgeStrength = 3.2;
    } else if (it) {
      this.outline.visibleEdgeColor.setRGB(1, 0.85, 0.47);
      this.outline.pulsePeriod = 2.2;
      this.outline.edgeStrength = 2.4;
    } else {
      this.outline.visibleEdgeColor.setRGB(1, 0.55, 0.72);
      this.outline.pulsePeriod = 1.6;
      this.outline.edgeStrength = 2.6;
    }
  }

  render() {
    if (!this.enabled) {
      this.g.renderer.render(this.g.scene, this.g.camera);
      return;
    }
    this.syncSelection();
    this.composer.render();
  }
}
