// Floraison: an opt-in, flower-height first-person composition camera.
// Presentation only. Gameplay state, save position and existing world input
// ownership remain unchanged; normal camera restores instantly on exit.
// No extra render targets/postprocessing, so this also works on phone Safari.

const TAU = Math.PI * 2;
export function povMoveVector(x, z, yaw) {
  // Legacy keys: W is local -z. Rotate forward/strafe into world axes.
  // Forward in the world is (sin(yaw), cos(yaw)).
  const forward = -z;
  return {
    x: Math.sin(yaw) * forward + Math.cos(yaw) * x,
    z: Math.cos(yaw) * forward - Math.sin(yaw) * x,
  };
}
export function povLookVector(yaw, pitch) {
  const flat = Math.cos(pitch);
  return { x: Math.sin(yaw) * flat, y: Math.sin(pitch), z: Math.cos(yaw) * flat };
}
const clamp = (x, lo, hi) => Math.min(hi, Math.max(lo, x));

export class FloraisonPOV {
  constructor(game) {
    this.game = game;
    this.yaw = game.player.facing;
    this.pitch = -0.09; // glance slightly downward into the blossoms
    this.enabled = !!game.world.botanyEnabled
      && new URLSearchParams(window.location.search).get('pov') === '1';
    this.dragSensitivity = 0.0036;
    this.eyeHeight = 1.48; // among bellflower heads, not overhead
  }

  set(on) {
    const g = this.game;
    if (on && (!g.world.botanyEnabled || g.world.inRift || g.player.dead)) return false;
    const next = !!on;
    if (this.enabled === next) return next;
    if (next) {
      this.yaw = g.player.facing;
      this.pitch = -0.09;
    }
    this.enabled = next;
    g.player.m.group.visible = !next && !g.player.dead;
    g.player.m.shadow.visible = !next && !g.player.dead;
    g.resize(); // restores exact third-person lens and near plane on exit
    g.ui?.syncFloraisonPOV?.();
    return next;
  }

  toggle() { return this.set(!this.enabled); }

  look(dx, dy) {
    if (!this.enabled) return;
    this.yaw = ((this.yaw + dx * this.dragSensitivity) % TAU + TAU) % TAU;
    this.pitch = clamp(this.pitch - dy * this.dragSensitivity, -0.66, 0.40);
  }

  update(dt) {
    if (!this.enabled) return false;
    const g = this.game, p = g.player;
    if (g.world.inRift || p.dead) { this.set(false); return false; }
    // Stable flower-height lens with a very small, non-violent walking sway.
    const moving = Math.hypot(p.vel.x, p.vel.z) > 0.4;
    const bob = moving && !g.paused ? Math.sin(g.time * 9) * 0.017 : 0;
    const eyeY = p.pos.y + this.eyeHeight + bob;
    const v = povLookVector(this.yaw, this.pitch);
    g.camera.position.set(p.pos.x, eyeY, p.pos.z);
    g.camera.lookAt(p.pos.x + v.x * 10, eyeY + v.y * 10, p.pos.z + v.z * 10);
    p.m.group.visible = false;
    p.m.shadow.visible = false;
    g.sun.position.set(p.pos.x + 40, p.pos.y + 80, p.pos.z + 30);
    g.sun.target.position.copy(p.pos);
    g.sun.target.updateMatrixWorld();
    return true;
  }
}
