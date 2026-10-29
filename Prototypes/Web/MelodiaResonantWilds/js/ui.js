// HUD, touch controls, keyboard, and menu panels.

import * as THREE from 'three';
import { SLOTS, SLOT_BY_ID, RARITIES, SKILLS, SKILL_BY_ID, ELEMENT_STYLE, ARIA_BY_ID, BIOMES, BLESSINGS, DIFFICULTY, xpToNext, HONE_MAX, honeChance, TUTORIAL, WORLD_RADIUS, RULES, MOTIF_BY_ID, AFFIX_BY_KEY } from './design.js';
import { ABILITY_OUTFITS } from './openworld.js';
import { fmt, clamp } from './util.js';

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function stamp(e) {
  const now = performance.now();
  const t = e && e.timeStamp;
  return t && t > now - 5000 && t <= now + 5 ? t : now;
}

export class UI {
  constructor(game) {
    this.g = game;
    this.joy = { id: null, cx: 0, cy: 0, x: 0, y: 0 };
    this.keys = new Set();
    this.attackHeld = false;
    this.panel = null;
    this.sel = null;
    this.loadSel = 0;
    this.forgeSel = null;
    this.synthSlots = [];
    this._t = 0;
    this._mm = 0;
    this.metroN = 0;
    this.spN = 0;
    this.skillIds = [];
    this.bindControls();
    this.bindKeys();
  }

  // ================================================================ input
  bindControls() {
    const g = this.g;
    const zone = $('joyzone'), joy = $('joy'), knob = $('joyknob');
    zone.addEventListener('pointerdown', (e) => {
      if (this.joy.id !== null) return;
      e.preventDefault();
      zone.setPointerCapture(e.pointerId);
      this.joy = { id: e.pointerId, cx: e.clientX, cy: e.clientY, x: 0, y: 0 };
      joy.style.left = e.clientX + 'px'; joy.style.top = e.clientY + 'px';
      joy.classList.remove('hidden');
      knob.style.transform = 'translate(0,0)';
    });
    zone.addEventListener('pointermove', (e) => {
      if (e.pointerId !== this.joy.id) return;
      let dx = e.clientX - this.joy.cx, dy = e.clientY - this.joy.cy;
      const d = Math.hypot(dx, dy), R = 52;
      if (d > R) { dx = (dx / d) * R; dy = (dy / d) * R; }
      this.joy.x = dx / R; this.joy.y = dy / R;
      knob.style.transform = `translate(${dx}px, ${dy}px)`;
    });
    const endJoy = (e) => {
      if (e.pointerId !== this.joy.id) return;
      this.joy = { id: null, cx: 0, cy: 0, x: 0, y: 0 };
      joy.classList.add('hidden');
    };
    zone.addEventListener('pointerup', endJoy);
    zone.addEventListener('pointercancel', endJoy);

    const press = (el, fn, holdFlag) => {
      el.addEventListener('pointerdown', (e) => {
        e.preventDefault(); e.stopPropagation();
        el.classList.add('pressed');
        if (holdFlag) this[holdFlag] = true;
        fn(stamp(e));
      });
      const up = () => { el.classList.remove('pressed'); if (holdFlag) this[holdFlag] = false; };
      el.addEventListener('pointerup', up);
      el.addEventListener('pointercancel', up);
      el.addEventListener('pointerleave', up);
    };
    press($('btnAttack'), (t) => g.attack(t), 'attackHeld');
    document.querySelectorAll('.skill').forEach((b) => press(b, (t) => g.skill(+b.dataset.i, t)));
    press($('btnDodge'), (t) => g.dodge(t));
    {
      const enc = $('btnEncore');
      let holdTimer = null, cycled = false;
      const clearHold = () => { if (holdTimer) { clearTimeout(holdTimer); holdTimer = null; } };
      enc.addEventListener('pointerdown', (e) => {
        e.preventDefault();
        cycled = false;
        clearHold();
        holdTimer = setTimeout(() => { cycled = true; g.encore(true); }, 380);
      });
      enc.addEventListener('pointerup', (e) => {
        e.preventDefault();
        clearHold();
        if (!cycled) g.encore(false);
      });
      enc.addEventListener('pointercancel', clearHold);
      enc.addEventListener('pointerleave', clearHold);
    }
    press($('shrinetap'), (t) => g.activities.shrineTap(t));
    $('btnInteract').addEventListener('pointerdown', (e) => { e.preventDefault(); g.interact(); });
    document.querySelectorAll('#menu button').forEach((b) => b.addEventListener('click', () => this.open(b.dataset.panel)));
    $('mapwrap').addEventListener('click', () => this.open('map'));
    $('closepanel').addEventListener('click', () => this.close());
    $('respawn').addEventListener('click', () => g.respawn());

    const canvas = $('game');
    canvas.addEventListener('pointerdown', (e) => {
      if (e.pointerType !== 'mouse' || g.paused) return;
      g.aimAt(e.clientX, e.clientY);
      if (e.button === 0) { this.attackHeld = true; g.attack(stamp(e)); }
      else if (e.button === 2) g.dodge(stamp(e));
    });
    canvas.addEventListener('pointerup', (e) => { if (e.pointerType === 'mouse' && e.button === 0) this.attackHeld = false; });
    canvas.addEventListener('pointermove', (e) => { if (e.pointerType === 'mouse' && this.attackHeld) g.aimAt(e.clientX, e.clientY); });
    window.addEventListener('contextmenu', (e) => e.preventDefault());
  }

  bindKeys() {
    const g = this.g;
    const skillKeys = { Digit1: 0, Digit2: 1, Digit3: 2, Digit4: 3, KeyQ: 0, KeyE: 1, KeyR: 2, KeyF: 3 };
    window.addEventListener('keydown', (e) => {
      if (e.target && e.target.tagName === 'INPUT') return;
      const c = e.code;
      if (c === 'Escape') { if (this.panel) this.close(); return; }
      if (this.panel) return;
      this.keys.add(c);
      if (e.repeat) return;
      const t = stamp(e);
      if (c === 'Space' || c === 'KeyJ') { e.preventDefault(); this.attackHeld = true; if (g.activities.shrine) g.activities.shrineTap(t); else g.attack(t); }
      else if (c in skillKeys) g.skill(skillKeys[c], t);
      else if (c === 'ShiftLeft' || c === 'ShiftRight' || c === 'KeyL') g.dodge(t);
      else if (c === 'KeyT' || c === 'KeyC') {
        if (e.altKey || e.shiftKey) g.encore(true);
        else g.encore(false);
      }
      else if (c === 'BracketLeft') g.encore(true);
      else if (c === 'BracketRight') { g.encoreSys.cycle(-1); }
      else if (c === 'KeyH') {
        g.sheep.setConcertHold(true);
        g.sheep.harmonize(false);
      }
      else if (c === 'KeyV') {
        // Playground sheep weapon: V = charge; Shift+V toggles mode.
        if (e.shiftKey) g.sheep.toggleWeapon();
        else g.sheep.startCharge();
      }
      else if (c === 'KeyG' && g.megaGown) g.megaGown.toggle();
      else if (c === 'KeyX' || c === 'Enter') g.interact();
      else if (c === 'KeyI') this.open('wardrobe');
      else if (c === 'KeyK') this.open('skills');
      else if (c === 'KeyM') this.open('map');
      else if (c === 'KeyB') this.open('bounties');
    });
    window.addEventListener('keyup', (e) => {
      this.keys.delete(e.code);
      if (e.code === 'Space' || e.code === 'KeyJ') this.attackHeld = false;
      if (e.code === 'KeyH') g.sheep.setConcertHold(false);
    });
    window.addEventListener('blur', () => { this.keys.clear(); this.attackHeld = false; });
  }

  // Camera-relative move vector (camera looks toward -z).
  move() {
    let x = this.joy.x, z = this.joy.y;
    const k = this.keys;
    if (k.has('KeyA') || k.has('ArrowLeft')) x -= 1;
    if (k.has('KeyD') || k.has('ArrowRight')) x += 1;
    if (k.has('KeyW') || k.has('ArrowUp')) z -= 1;
    if (k.has('KeyS') || k.has('ArrowDown')) z += 1;
    const d = Math.hypot(x, z);
    if (d > 1) { x /= d; z /= d; }
    if (d < 0.15) return { x: 0, z: 0 };
    return { x, z };
  }

  // ================================================================ HUD
  show() { $('hud').classList.remove('hidden'); }

  buildMetro(meter) {
    if (meter === this.metroN) return;
    this.metroN = meter;
    $('metro').innerHTML = Array.from({ length: meter }, (_, i) => `<i class="${i === 0 ? 'down' : ''}"></i>`).join('');
  }

  beat(b) {
    this.buildMetro(b.meter);
    const dots = $('metro').children;
    for (let i = 0; i < dots.length; i++) dots[i].classList.toggle('on', i === b.inBar);
    const a = $('btnAttack');
    a.classList.add('beat');
    clearTimeout(this._bt);
    this._bt = setTimeout(() => a.classList.remove('beat'), 90);
  }

  gradeFlash(grade, err) {
    const el = $('gradeflash');
    const col = { Perfect: '#ffd978', Great: '#82e3ec', Good: '#c9b6ef', Miss: '#8d8698' }[grade];
    const ms = Math.round(err);
    el.innerHTML = `<span style="color:${col}">${grade.toUpperCase()}</span><small>${Math.abs(ms) < 12 ? 'on the beat' : ms < 0 ? `early ${-ms}ms` : `late ${ms}ms`}</small>`;
    el.classList.add('show');
    clearTimeout(this._gf);
    this._gf = setTimeout(() => el.classList.remove('show'), 380);
  }

  /** Highway pulse when a Perfect lands — tint follows selected Encore / fashion. */
  beatSpark(color = null) {
    const ring = $('approach');
    if (!ring) return;
    const col = color || this.g.encoreSys?.accentColor?.() || '#ffd978';
    ring.style.borderColor = col;
    ring.style.opacity = '1';
    ring.animate?.(
      [{ transform: 'scale(1.05)', borderWidth: '3px' }, { transform: 'scale(1.55)', borderWidth: '1px' }],
      { duration: 220, easing: 'ease-out' },
    );
  }

  dynamicsUp(d) {
    const el = $('dynmark');
    el.animate([{ transform: 'scale(2)' }, { transform: 'scale(1)' }], { duration: 400, easing: 'ease-out' });
    if (d.mark === 'ff') this.toast('ff — Fortissimo! Crit and speed peak', 'gold');
  }

  toast(text, kind = '', color = null) {
    const box = $('toasts');
    const el = document.createElement('div');
    el.className = 'toast ' + kind;
    if (color) el.style.color = color, el.style.borderColor = color;
    el.textContent = text;
    box.appendChild(el);
    while (box.children.length > 4) box.removeChild(box.firstChild);
    setTimeout(() => el.remove(), 2800);
  }

  banner(title, sub = '') {
    $('bannerTitle').textContent = title;
    $('bannerSub').textContent = sub;
    const b = $('banner');
    b.classList.add('show');
    clearTimeout(this._bn);
    this._bn = setTimeout(() => b.classList.remove('show'), 2800);
  }

  /** Full-screen Recital ceremony flash: goal | bank | inherit | miss */
  ceremonyFlash(kind = 'goal') {
    const el = $('ceremonyflash');
    if (el) {
      el.className = `on ${kind}`;
      el.classList.remove('hidden');
      clearTimeout(this._cf);
      this._cf = setTimeout(() => {
        el.classList.add('hidden');
        el.className = 'hidden';
      }, 520);
    }
    // Ground nodal bloom (same plate modes as the floor shader).
    const pos = this.g?.player?.pos;
    const samples = this.g?.world?.ceremonyFigure?.(kind, pos?.x, pos?.z);
    if (samples?.nodal?.length && this.g?.particles) {
      const col = kind === 'miss' ? '#6a5a88' : kind === 'inherit' ? '#c690ff' : kind === 'bank' ? '#7fd0e4' : '#ffe7a8';
      const c = new THREE.Color(col);
      for (const s of samples.nodal.slice(0, 28)) {
        this.g.particles.emit(s.x, (pos?.y ?? 0) + 0.5, s.z, c, { speed: 2.4, life: 0.7, gravity: 0.45, kind: 3, size: 0.75 });
      }
    }
  }

  hint(text) {
    const h = $('hint');
    if (!text) { h.classList.add('hidden'); return; }
    h.textContent = text;
    h.classList.remove('hidden');
  }

  update(dt) {
    const g = this.g, P = g.player, S = P.stats, pr = g.profile, R = g.rhythm;
    // Bars
    $('hpfill').style.width = (clamp(P.hp / S.maxHp, 0, 1) * 100).toFixed(1) + '%';
    $('shieldfill').style.width = (clamp(P.shield / S.maxHp, 0, 1) * 100).toFixed(1) + '%';
    $('hptext').textContent = `${Math.ceil(P.hp)} / ${S.maxHp}` + (P.shield > 0 ? ` (+${Math.ceil(P.shield)})` : '');
    if (this.spN !== S.spMax) { this.spN = S.spMax; $('sp').innerHTML = '<i></i>'.repeat(S.spMax); }
    const pips = $('sp').children;
    for (let i = 0; i < pips.length; i++) pips[i].classList.toggle('on', i < P.sp);
    $('xpfill').style.width = ((pr.xp / xpToNext(pr.level)) * 100).toFixed(1) + '%';
    $('lvl').textContent = pr.level;
    // Combo + dynamics
    $('dynmark').textContent = R.dyn.mark;
    $('cresfill').style.width = R.crescendo + '%';
    const encLive = g.encoreSys?.active ? (g.encoreSys.variant?.short || 'ENCORE') : R.encoreActive ? 'ENCORE' : null;
    $('combo').innerHTML = R.combo >= 3 ? `${R.combo}<small>${encLive || ('COMBO ×' + R.multiplier('Good').toFixed(2))}</small>` : '';
    // Approach ring: closes exactly as the next beat becomes audible.
    const spb = g.audio.spb;
    const toNext = clamp(1 - g.beatPhase, 0, 1);
    const ring = $('approach');
    ring.style.transform = `scale(${1 + toNext * 0.9})`;
    ring.style.opacity = (0.35 + (1 - toNext) * 0.65).toFixed(2);
    const encCol = g.encoreSys?.accentColor?.() || '#ffd978';
    ring.style.borderColor = toNext < 0.12 || toNext > 0.9 ? encCol : '#82d2db';
    // Skills
    for (let i = 0; i < 4; i++) {
      const b = document.querySelector(`.skill[data-i="${i}"]`);
      const id = pr.loadout[i];
      const sk = SKILL_BY_ID[id];
      if (this.skillIds[i] !== id) {
        this.skillIds[i] = id;
        b.querySelector('b').textContent = sk ? ELEMENT_STYLE[sk.element].glyph : '·';
        b.querySelector('b').style.color = sk ? ELEMENT_STYLE[sk.element].color : '#fff';
        b.style.borderColor = sk ? ELEMENT_STYLE[sk.element].color + '99' : '';
        b.querySelector('small').textContent = sk ? sk.name.split(' ')[0] : '';
      }
      if (!sk) continue;
      const cost = g.skillCost(sk);
      b.querySelector('em').textContent = '◆'.repeat(cost);
      const left = Math.max(0, g.cooldowns[i] - g.time);
      b.querySelector('.cd').style.setProperty('--cd', left > 0 ? (left / g.cdTotal[i]).toFixed(3) : 0);
      b.classList.toggle('nosp', P.sp < cost);
    }
    const dl = Math.max(0, g.dodgeReadyAt - g.time);
    $('btnDodge').querySelector('.cd').style.setProperty('--cd', dl > 0 ? (dl / g.dodgeCd).toFixed(3) : 0);
    $('encfill').style.height = (R.encore / R.encoreMax) * 100 + '%';
    const encBtn = $('btnEncore');
    encBtn.classList.toggle('ready', R.encore >= R.encoreMax);
    const ev = g.encoreSys?.variant;
    if (ev) {
      const label = encBtn.querySelector('span');
      if (label && label.dataset.id !== ev.id) {
        label.dataset.id = ev.id;
        label.textContent = ev.short;
        label.title = `${ev.name} — ${ev.blurb} (hold / Alt+T to cycle)`;
        encBtn.style.borderColor = ev.color;
      }
      if (g.encoreSys.active) encBtn.classList.add('ready');
    }
    // Interact
    const it = g.nearestInteract();
    const ib = $('btnInteract');
    if (it && !P.dead) { ib.textContent = it.label; ib.classList.remove('hidden'); } else ib.classList.add('hidden');
    // Boss bar
    const boss = g.enemies.find((e) => e.boss && !e.dead && e.aggro);
    $('bossbar').classList.toggle('hidden', !boss);
    if (boss) {
      $('bossname').textContent = `${boss.name} · Lv ${boss.level}` + (boss.broken ? ' · BROKEN' : '');
      $('bossfill').style.width = (clamp(boss.hp / boss.maxHp, 0, 1) * 100).toFixed(1) + '%';
      $('bosstough').style.width = (boss.maxTough ? clamp(boss.tough / boss.maxTough, 0, 1) * 100 : 0).toFixed(1) + '%';
    }
    const rift = g.activities.rift;
    $('riftbar').classList.toggle('hidden', !rift || !!boss);
    if (rift) {
      $('riftlabel').textContent = `Rift Tier ${rift.tier} · ${Math.floor(rift.progress)}%`;
      const left = Math.max(0, rift.limit - rift.time);
      $('rifttime').textContent = rift.done ? 'Cleared' : `${Math.floor(left / 60)}:${String(Math.floor(left % 60)).padStart(2, '0')}`;
      $('rifttime').style.color = left < 30 ? '#ff8a9a' : '';
      $('riftfill').style.width = rift.progress + '%';
    }
    const rg = $('recgoals');
    if (rg) {
      if (rift?.goals?.length && !rift.done) {
        rg.classList.remove('hidden');
        const bless = rift.blessing
          ? `<div class="bless">✦ ${esc(rift.blessing.name)} · ${esc(rift.blessing.desc)}</div>`
          : '';
        const echo = rift.inherit?.passed
          ? `<div class="echo-on">Echo Motifs active</div>`
          : '';
        rg.innerHTML = `<b>Recital goals</b>${bless}${echo}` + rift.goals.map((x) => {
          const pct = Math.min(100, (x.prog / x.n) * 100);
          return `<div class="g ${x.done ? 'done' : ''}">${x.done ? '✓ ' : ''}${esc(x.text)} <i><em style="width:${pct}%"></em></i></div>`;
        }).join('');
      } else rg.classList.add('hidden');
    }
    this._t += dt;
    if (this._t > 0.4) {
      this._t = 0;
      $('gold').textContent = fmt(pr.gold);
      $('shards').textContent = fmt(pr.shards);
      $('notes').textContent = fmt(pr.notes);
      $('gs').textContent = 'GS ' + g.loot.gearScore();
      $('zone').textContent = g.zoneName();
      this.tracker();
      this.obj = g.activities.rift ? null : g.progress.objective();
      $('objective').innerHTML = this.obj ? `<b>${esc(this.obj.title)}</b>${esc(this.obj.text)}` : '';
      $('newdot').classList.toggle('on', pr.inventory.some((i) => i.isNew));
      $('bountydot').classList.toggle('on', pr.bounties.some((b) => b.done));
    }
    this._mm += dt;
    if (this._mm > 0.1) { this._mm = 0; this.minimap(); }
    this.compass();
  }

  // Edge arrow toward the current Movement objective when it is off-screen.
  compass() {
    const el = $('compass'), g = this.g, t = this.obj && this.obj.target;
    if (!t || g.player.dead) { el.classList.add('hidden'); return; }
    const P = g.player.pos;
    const d = Math.hypot(t.x - P.x, t.z - P.z);
    const p = g.overlay.project(t.x, (t.y || 0) + 2, t.z);
    const w = innerWidth, h = innerHeight;
    if (d < 12 || (p && p.x > 40 && p.x < w - 40 && p.y > 90 && p.y < h - 60)) { el.classList.add('hidden'); return; }
    const c = g.overlay.project(P.x, P.y + 1, P.z) || { x: w / 2, y: h / 2 };
    const ang = Math.atan2(t.z - P.z, t.x - P.x);
    const r = Math.min(w, h) * 0.36;
    el.style.left = clamp(c.x + Math.cos(ang) * r * 1.3, 50, w - 50) + 'px';
    el.style.top = clamp(c.y + Math.sin(ang) * r, 150, h - 70) + 'px';
    el.querySelector('i').style.transform = `rotate(${ang}rad)`;
    el.querySelector('span').textContent = Math.round(d) + 'm';
    el.classList.remove('hidden');
  }

  tracker() {
    const pr = this.g.profile;
    $('tracker').innerHTML = pr.bounties.map((b) => `<div class="trk ${b.done ? 'done' : ''}">${b.done ? '✓ ' : ''}${esc(b.text)}<div class="p"><i style="width:${(b.prog / b.n) * 100}%"></i></div></div>`).join('');
  }

  // ================================================================ minimap
  minimap() {
    const g = this.g, cv = $('minimap'), c = cv.getContext('2d'), P = g.player;
    const W = cv.width, H = cv.height;
    c.fillStyle = '#171225';
    c.fillRect(0, 0, W, H);
    const range = 110;
    const toMap = (x, z) => [W / 2 + ((x - P.pos.x) / range) * (W / 2), H / 2 + ((z - P.pos.z) / range) * (H / 2)];
    if (g.world.inRift) {
      c.strokeStyle = '#8f6bff'; c.lineWidth = 3;
      c.beginPath(); c.arc(...toMap(0, 0), (34 / range) * (W / 2), 0, Math.PI * 2); c.stroke();
    } else if (g.overview) {
      const ov = g.overview, ext = ov.extent, sz = ov.canvas.width;
      const sx = ((P.pos.x - range + ext) / (ext * 2)) * sz, sy = ((P.pos.z - range + ext) / (ext * 2)) * sz, sw = ((range * 2) / (ext * 2)) * sz;
      c.imageSmoothingEnabled = true;
      c.drawImage(ov.canvas, sx, sy, sw, sw, 0, 0, W, H);
      for (const p of g.activities.pois) {
        if (Math.abs(p.x - P.pos.x) > range || Math.abs(p.z - P.pos.z) > range) continue;
        this.poiIcon(c, p, ...toMap(p.x, p.z), 1);
      }
      const ev = g.activities.event;
      if (ev) {
        const [x, y] = toMap(clamp(ev.x, P.pos.x - range * 0.95, P.pos.x + range * 0.95), clamp(ev.z, P.pos.z - range * 0.95, P.pos.z + range * 0.95));
        c.fillStyle = '#ffd978'; c.font = 'bold 26px sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('★', x, y);
      }
    }
    const ob = this.obj && this.obj.target;
    if (ob && !g.world.inRift) {
      const [x, y] = toMap(clamp(ob.x, P.pos.x - range * 0.92, P.pos.x + range * 0.92), clamp(ob.z, P.pos.z - range * 0.92, P.pos.z + range * 0.92));
      c.strokeStyle = '#ffd978'; c.lineWidth = 4; c.beginPath(); c.arc(x, y, 11, 0, Math.PI * 2); c.stroke();
    }
    for (const e of g.enemies) {
      if (e.dead) continue;
      const [x, y] = toMap(e.pos.x, e.pos.z);
      c.fillStyle = e.boss ? '#ff4d6d' : e.elite ? '#ff9a4a' : '#ff6b81';
      c.beginPath(); c.arc(x, y, e.boss ? 9 : e.elite ? 6 : 4, 0, Math.PI * 2); c.fill();
    }
    c.save();
    c.translate(W / 2, H / 2);
    c.rotate(-P.facing + Math.PI);
    c.fillStyle = '#fff'; c.strokeStyle = '#171225'; c.lineWidth = 3;
    c.beginPath(); c.moveTo(0, -14); c.lineTo(9, 10); c.lineTo(0, 5); c.lineTo(-9, 10); c.closePath(); c.stroke(); c.fill();
    c.restore();
  }

  poiIcon(c, p, x, y, s) {
    const g = this.g, pr = g.profile;
    c.textAlign = 'center'; c.textBaseline = 'middle';
    const glyph = (t, col, size) => { c.font = `bold ${size * s}px sans-serif`; c.lineWidth = 4; c.strokeStyle = 'rgba(23,18,37,.85)'; c.strokeText(t, x, y); c.fillStyle = col; c.fillText(t, x, y); };
    switch (p.type) {
      case 'camp': if (g.time - p.clearedAt > 150) { c.fillStyle = '#ff6b81'; c.beginPath(); c.arc(x, y, 5 * s, 0, Math.PI * 2); c.fill(); } break;
      case 'chest': if (g.time - p.openedAt > 600) glyph('▣', '#ffd978', 18); break;
      case 'shrine': glyph('𝄞', pr.shrines.includes(p.id) ? '#ffd978' : '#82d2db', 24); break;
      case 'sheet': if (!pr.sheets.includes(p.id) && Math.hypot(p.x - g.player.pos.x, p.z - g.player.pos.z) < 70) glyph('♪', '#fff6e0', 22); break;
      case 'pylon': glyph('◆', pr.pylons.includes(p.id) ? '#62c8ff' : '#8a8a9a', 20); break;
      case 'rift': glyph('◎', '#b89cff', 22); break;
      case 'boss': glyph('♛', g.time > p.cdUntil ? '#ff5470' : '#8a6a70', 22); break;
      case 'forge': glyph('⚒', '#ffcf7a', 18); break;
      case 'board': glyph('📜', '#fff', 16); break;
      case 'font': glyph('✧', '#8fe0ff', 18); break;
      case 'overlook': glyph('⌂', (pr.vistas || []).includes(p.id) ? '#ffd978' : '#f6f0f8', 18); break;
      case 'photo': glyph('▭', '#c8b6ef', 16); break;
      case 'chime': glyph('♫', '#9fe6ff', 16); break;
      case 'musicgate': glyph('═', p.open ? '#62c8ff' : '#9fe6ff', 16); break;
      case 'cleanse': glyph('◎', p.cleared ? '#8fd8ff' : '#c690ff', 16); break;
      case 'ariagate': glyph('◈', p.open ? '#ffd978' : '#e8dff8', 16); break;
      case 'destination': glyph('◇', (pr.dews || []).includes(p.id) ? '#ffd978' : '#9fe6ff', 18); break;
    }
  }

  // ================================================================ panels
  open(name) {
    const g = this.g;
    if (g.player.dead || g.activities.shrine) return;
    this.panel = name;
    g.setPaused(true);
    $('panel').classList.remove('hidden');
    g.audio.ui();
    this.render();
  }

  close() {
    this.panel = null;
    $('panel').classList.add('hidden');
    this.g.setPaused(false);
    this.g.save();
  }

  render() {
    const base = ['wardrobe', 'skills', 'map', 'bounties', 'settings'];
    const ctx = ['forge', 'blessings', 'rift'].includes(this.panel) ? [this.panel] : [];
    const names = { wardrobe: '👗 Wardrobe', skills: '♫ Skills', map: '🗺 Map', bounties: '📜 Bounties', settings: '⚙ Settings', forge: '⟡ Synthesis', blessings: '✧ Blessings', rift: '◎ Rift' };
    $('tabs').innerHTML = [...ctx, ...base].map((t) => `<button data-t="${t}" class="${t === this.panel ? 'on' : ''}">${names[t]}</button>`).join('');
    $('tabs').querySelectorAll('button').forEach((b) => b.addEventListener('click', () => { this.panel = b.dataset.t; this.render(); }));
    const body = $('panelbody');
    body.scrollTop = 0;
    this['render_' + this.panel](body);
  }

  iconSrc(key) {
    if (!key) return null;
    return `assets/icons/${key}.svg`;
  }

  itemIconHtml(it) {
    const key = it.icon || this.g.loot.iconKey(it);
    const src = this.iconSrc(key);
    const fb = SLOT_BY_ID[it.slot]?.icon || '♪';
    if (!src) return `<span class="ico-fallback">${fb}</span>`;
    return `<img class="ico" src="${src}" alt="" onerror="this.replaceWith(Object.assign(document.createElement('span'),{className:'ico-fallback',textContent:'${fb}'}))" />`;
  }

  itemBox(it, attrs = '') {
    const R = RARITIES[it.rarity];
    const eq = this.g.profile.equipment[it.slot];
    const better = !Object.values(this.g.profile.equipment).includes(it) && this.g.loot.score(it) > this.g.loot.score(eq);
    return `<div class="slotbox ${this.sel === it ? 'sel' : ''}" style="border-color:${R.color};box-shadow:inset 0 0 12px ${R.color}33" ${attrs}>
      ${this.itemIconHtml(it)}<span class="lv">${it.ilvl}</span>${it.up ? `<span class="up">+${it.up}</span>` : ''}${it.quality ? `<span class="up" style="left:4px;right:auto;color:#9fe4ff">Q${it.quality}</span>` : ''}
      ${better ? '<span class="better">▲</span>' : ''}${it.isNew ? '<span class="newb"></span>' : ''}${it.locked ? '<span class="lock">🔒</span>' : ''}</div>`;
  }

  itemDetail(it) {
    const g = this.g, L = g.loot, R = RARITIES[it.rarity];
    const eq = g.profile.equipment[it.slot];
    const equipped = eq === it;
    const sv = L.salvageValue(it);
    let cmp = '';
    if (!equipped) {
      const d = L.score(it) - L.score(eq);
      cmp = `<div class="cmp">vs equipped: <span class="${d >= 0 ? 'pos' : 'neg'}">${d >= 0 ? '▲ +' : '▼ '}${d} power</span>${eq ? ` (${esc(eq.name)})` : ' (empty slot)'}</div>`;
    }
    return `<div class="item-name" style="color:${R.color}">${esc(it.name)}${it.up ? ' +' + it.up : ''}</div>
      <div class="item-sub">${R.name} ${SLOT_BY_ID[it.slot].name} · iLvl ${it.ilvl}${equipped ? ' · Equipped' : ''}</div>
      <div class="item-lines">${L.lines(it).map((l) => `<div>${esc(l)}</div>`).join('')}</div>
      ${it.aria ? `<div class="item-aria">Aria — ${esc(ARIA_BY_ID[it.aria].name)}: ${esc(ARIA_BY_ID[it.aria].desc)}
        <span class="oshi-pin ${g.profile.oshiAria === it.aria ? 'on' : ''}" data-a="oshi" title="Pin as oshi Aria">${g.profile.oshiAria === it.aria ? '★ oshi' : '☆ pin oshi'}</span></div>` : ''}
      ${cmp}
      <div class="btns">
        ${equipped ? '' : '<button class="btn gold" data-a="equip">Equip</button>'}
        ${equipped ? '' : `<button class="btn" data-a="salvage" ${it.locked ? 'disabled' : ''}>Salvage → Motifs (+${sv.gold}● +${sv.shards}◆)</button>`}
        <button class="btn" data-a="lock">${it.locked ? 'Unlock' : 'Lock'}</button>
      </div>`;
  }

  motifChip(m, opts = {}) {
    const src = this.iconSrc(`motif_${m.element.toLowerCase()}`);
    const cls = ['motifchip', opts.on ? 'on' : '', opts.dim ? 'dim' : ''].filter(Boolean).join(' ');
    const attrs = opts.attrs || '';
    return `<span class="${cls}" ${attrs}><img src="${src}" alt=""/>${esc(m.name)} ×${m.n}</span>`;
  }

  render_wardrobe(body) {
    const g = this.g, pr = g.profile, S = g.player.stats, L = g.loot;
    const eqHtml = SLOTS.map((s) => {
      const it = pr.equipment[s.id];
      return it ? this.itemBox(it, `data-eq="${s.id}"`) : `<div class="slotbox empty"><img class="ico" src="assets/icons/slot_${s.id}.svg" alt="" onerror="this.replaceWith(Object.assign(document.createElement('span'),{className:'ico-fallback',textContent:'${s.icon}'}))"/></div>`;
    }).join('');
    const W = g.rhythm.windows();
    const inv = pr.inventory.slice().sort((a, b) => b.rarity - a.rarity || b.ilvl - a.ilvl);
    const motifs = L.motifInventory();
    const echo = pr.echoLineage?.phrase;
    // Nikki Ability Outfit catalogue — ethereal biome traversal identities.
    const unlocked = new Set(pr.abilityOutfits || []);
    const outfits = Object.values(ABILITY_OUTFITS);
    const abilityHtml = `<div class="pedigree" style="margin-top:8px"><div class="title">Ability Outfits</div>
      ${outfits.map((ab) => {
        const on = unlocked.has(ab.id);
        const wearing = !!pr.equipment?.[ab.slot];
        const state = on ? (wearing ? 'ready' : 'unlocked') : 'locked';
        const tip = on
          ? (wearing ? `${ab.name} equipped — space opens` : `Unlocked · equip ${ab.slotLabel} to use`)
          : `Locked · ${ab.slotLabel} opens ${ab.name}`;
        return `<div style="opacity:${on ? 1 : 0.55};margin:4px 0"><span style="color:${ab.color}">✦</span> ${esc(ab.name)} · ${esc(ab.slotLabel)} <span class="muted">(${state})</span><div class="muted" style="font-size:12px">${esc(tip)}</div></div>`;
      }).join('')}
    </div>`;
    body.innerHTML = `<div class="cols">
      <div>
        <div class="card"><h3>Wardrobe · GS ${L.gearScore()}</h3><div class="equip">${eqHtml}</div>
          <div class="stats" style="margin-top:8px">
            <span>Attack</span><span>${S.attack}</span><span>Max HP</span><span>${S.maxHp}</span>
            <span>Poise</span><span>${S.armor}</span><span>Crit</span><span>${Math.round(S.crit * 100)}% · ×${S.critDmg.toFixed(2)}</span>
            <span>Perfect window</span><span>±${Math.round(W.perfect)}ms</span><span>Damage</span><span>+${Math.round(S.dmg * 100)}%</span>
            <span>Basic attack</span><span>${S.family === 'melee' ? 'Melee' : 'Ranged'} · ${S.basicElement}</span><span>Arias</span><span>${[...S.arias].map((a) => ARIA_BY_ID[a].name).join(', ') || '—'}</span>
          </div>
          ${abilityHtml}
          ${echo ? `<div class="pedigree"><div class="title">Echo Pedigree</div>${esc(g.echo.pedigreeHtml())}<div style="margin-top:4px;opacity:.85">Next pass ${Math.round(g.echo.passChance() * 100)}%${pr.oshiAria ? ` · oshi ${esc(ARIA_BY_ID[pr.oshiAria]?.name || pr.oshiAria)}` : ''}</div></div>` : ''}
        </div>
        <div class="card" id="detail" style="margin-top:10px">${this.sel ? this.itemDetail(this.sel) : '<div class="muted">Tap an item to inspect it. ▲ marks an upgrade. Salvage yields Motifs for Harmonic Synthesis. Opus items carry an Aria.</div>'}</div>
      </div>
      <div>
        <div class="card"><h3>Bag ${pr.inventory.length}/${L.INV_MAX}</h3>
          <div class="btns" style="margin:0 0 8px">
            <button class="btn gold" data-a="best">Equip best</button>
            <button class="btn" data-a="s0">Salvage Common → Motifs</button>
            <button class="btn" data-a="s1">Salvage ≤ Tuned</button>
            <button class="btn" data-a="auto">Auto-salvage: ${pr.settings.autoSalvage ? 'On' : 'Off'}</button>
          </div>
          <div class="grid">${inv.map((it) => this.itemBox(it, `data-uid="${it.uid}"`)).join('') || '<div class="muted">Empty. Defeat slimes, open chests and clear rifts.</div>'}</div>
        </div>
        <div class="card" style="margin-top:10px"><h3>Motifs</h3>
          <div class="muted">Atelier-style materials from salvage. Spend them at the Forge (Harmonic Synthesis).</div>
          <div class="motifbag">${motifs.map((m) => this.motifChip(m)).join('') || '<div class="muted">No Motifs yet — salvage spare gear.</div>'}</div>
        </div>
      </div></div>`;
    body.querySelectorAll('[data-uid]').forEach((el) => el.addEventListener('click', () => {
      const it = pr.inventory.find((i) => i.uid === +el.dataset.uid);
      if (it) { it.isNew = false; this.sel = it; this.render(); }
    }));
    body.querySelectorAll('[data-eq]').forEach((el) => el.addEventListener('click', () => { this.sel = pr.equipment[el.dataset.eq]; this.render(); }));
    body.querySelectorAll('[data-a]').forEach((el) => el.addEventListener('click', () => {
      const a = el.dataset.a;
      if (a === 'equip' && this.sel) { L.equip(this.sel); g.audio.ui(); }
      else if (a === 'salvage' && this.sel) { L.salvage(this.sel); this.sel = null; }
      else if (a === 'lock' && this.sel) this.sel.locked = !this.sel.locked;
      else if (a === 'best') { const n = L.equipBest(); this.toast(n ? `Equipped ${n} upgrade${n > 1 ? 's' : ''}` : 'Already wearing your best'); }
      else if (a === 's0' || a === 's1') {
        const r = L.salvageWhere((it) => it.rarity <= (a === 's0' ? 0 : 1) && L.score(it) <= L.score(pr.equipment[it.slot]));
        const bits = Object.entries(r.motifs || {}).map(([id, n]) => `${MOTIF_BY_ID[id]?.name || id}×${n}`);
        this.toast(`Salvaged ${r.n}: +${r.gold}● +${r.shards}◆` + (bits.length ? ` · ${bits.join(', ')}` : ''));
      }
      else if (a === 'auto') pr.settings.autoSalvage = !pr.settings.autoSalvage;
      else if (a === 'oshi' && this.sel?.aria) {
        pr.oshiAria = pr.oshiAria === this.sel.aria ? null : this.sel.aria;
        this.toast(pr.oshiAria ? `Oshi Aria: ${ARIA_BY_ID[pr.oshiAria].name}` : 'Oshi Aria cleared', 'gold');
        g.save();
      }
      this.render();
    }));
  }

  render_skills(body) {
    const g = this.g, pr = g.profile;
    const slot = (i) => {
      const s = SKILL_BY_ID[pr.loadout[i]];
      const col = s ? ELEMENT_STYLE[s.element].color : '#fff';
      return `<div class="slotbox ${this.loadSel === i ? 'sel' : ''}" data-ls="${i}" style="border-color:${col}"><span style="color:${col}">${s ? ELEMENT_STYLE[s.element].glyph : '·'}</span><span class="lv">${i + 1}</span></div>`;
    };
    const rows = SKILLS.map((s) => {
      const un = g.progress.isUnlocked(s);
      const st = ELEMENT_STYLE[s.element];
      const inL = pr.loadout.indexOf(s.id);
      return `<div class="skillrow ${un ? '' : 'locked'}" data-sk="${s.id}">
        <div class="ic" style="border-color:${st.color};color:${st.color}">${st.glyph}</div>
        <div class="tx"><b>${esc(s.name)}</b>${inL >= 0 ? ` <span style="color:var(--gold-hi)">· slot ${inL + 1}</span>` : ''}
          <div class="meta">${s.element} · ${s.sp} Harmony · ${Math.round(s.cd)} beats · power ×${s.power} · ${s.kind}${s.niche ? ' · ' + s.niche : ''}</div>
          <div>${esc(s.desc)}</div>
          ${un ? '' : `<div class="meta">🔒 Unlocks at Lv ${s.unlockLevel} — or find Lost Sheet Music</div>`}
        </div></div>`;
    }).join('');
    body.innerHTML = `<div class="card"><h3>Loadout — tap a slot, then a skill</h3><div class="loadout">${[0, 1, 2, 3].map(slot).join('')}</div>
      <div class="muted">${SKILLS.filter((s) => g.progress.isUnlocked(s)).length}/${SKILLS.length} skills learned. Every skill is a chart from DT_MelodySlime_Skills: its notes play when you cast. Cooldowns are in beats, so faster biomes cycle skills faster.</div></div>
      <div style="margin-top:10px">${rows}</div>`;
    body.querySelectorAll('[data-ls]').forEach((el) => el.addEventListener('click', () => { this.loadSel = +el.dataset.ls; this.render(); }));
    body.querySelectorAll('[data-sk]').forEach((el) => el.addEventListener('click', () => {
      const id = el.dataset.sk;
      if (!g.progress.isUnlocked(SKILL_BY_ID[id])) return;
      const cur = pr.loadout.indexOf(id);
      if (cur >= 0) pr.loadout[cur] = pr.loadout[this.loadSel];
      pr.loadout[this.loadSel] = id;
      g.cooldowns[this.loadSel] = 0;
      g.audio.ui();
      this.loadSel = (this.loadSel + 1) % 4;
      this.render();
    }));
  }

  render_bounties(body) {
    const g = this.g, pr = g.profile;
    const daily = g.progress.ensureDaily();
    const dailyDone = daily.tasks.filter((t) => t.done).length;
    const phraseN = Object.keys(pr.phrasebook || {}).length;
    const concertN = (pr.concertSkins || []).length;
    body.innerHTML = `<div class="card"><h3>Daily Recital · ${daily.day}</h3>
      <div class="muted">Three tasks each UTC day. Clear all for Golden Notes + Daily Overture Trail (fashion-only).</div>
      <div style="margin-top:8px">${daily.tasks.map((t) => `<div class="bounty ${t.done ? 'done' : ''}"><b>${esc(t.text)}</b>
        <div class="p"><i style="width:${(t.prog / t.n) * 100}%"></i></div>
        <div class="muted">${t.prog}/${t.n}</div></div>`).join('')}</div>
      <div style="margin-top:8px;display:flex;justify-content:space-between;align-items:center">
        <span class="muted">${dailyDone}/3 · ${daily.claimed ? 'claimed today' : 'claim when complete'}</span>
        <button class="btn gold" data-daily="1" ${daily.claimed || dailyDone < 3 ? 'disabled' : ''}>Claim Recital</button>
      </div></div>
      <div class="card" style="margin-top:10px"><h3>Bounties · Chorus Cache ${pr.bountySet}/3</h3><div class="muted">Claim three bounties for a Chorus Cache (Virtuoso item + 25 Golden Notes). New bounties roll in as you claim.</div></div>
      <div style="margin-top:10px">${pr.bounties.map((b, i) => `<div class="bounty ${b.done ? 'done' : ''}"><b>${esc(b.text)}</b>
        <div class="p"><i style="width:${(b.prog / b.n) * 100}%"></i></div>
        <div style="display:flex;justify-content:space-between;align-items:center"><span class="muted">${b.prog}/${b.n} · reward: gold, XP, Resonant+ item, 6 Golden Notes</span>
        <button class="btn gold" data-c="${i}" ${b.done ? '' : 'disabled'}>Claim</button></div></div>`).join('')}</div>
      <div class="card"><h3>Journal</h3><div class="stats">
        <span>Slimes defeated</span><span>${fmt(pr.stats.kills)}</span><span>Perfect hits</span><span>${fmt(pr.stats.perfects)}</span>
        <span>Best combo</span><span>${pr.stats.bestCombo}</span><span>Maestros defeated</span><span>${pr.stats.bosses}</span>
        <span>Rifts cleared</span><span>${pr.stats.rifts} (best tier ${pr.riftTier})</span><span>Shrines attuned</span><span>${pr.shrines.length}/15</span>
        <span>Sheet music</span><span>${pr.sheets.length}/25</span><span>Explored</span><span>${g.progress.percent()}%</span>
        <span>Phrasebook biomes</span><span>${phraseN}/8</span><span>Concert trails</span><span>${concertN}</span>
        <span>Fashion gold frames</span><span>${(pr.fashionGold || []).length}</span><span>Encore exams</span><span>${(pr.maestroExams || []).length}</span>
        <span>Regions 100%</span><span>${(pr.regionsDone || []).length}/8</span><span>Resonance Dew</span><span>${(pr.dews || []).filter((id) => !String(id).endsWith('_open')).length}/16</span>
      </div></div>`;
    body.querySelectorAll('[data-c]').forEach((el) => el.addEventListener('click', () => { g.progress.claim(+el.dataset.c); this.render(); }));
    body.querySelectorAll('[data-daily]').forEach((el) => el.addEventListener('click', () => { g.progress.claimDaily(); this.render(); }));
  }

  render_map(body) {
    const g = this.g;
    const regions = g.progress.regionBoard?.() || [];
    const regionRow = regions.length
      ? `<div class="card" style="margin-top:8px"><h3>Region completion</h3>
          <div class="muted">Dew + fashion frames + Reveal overlook per biome. No new world authority.</div>
          <div class="stats" style="margin-top:6px">${regions.map((r) => `<span>${esc(r.label)}</span><span>${r.complete ? '✓ 100%' : `${r.pct}% · Dew ${r.dew}/${r.dewTotal}`}</span>`).join('')}</div>
          <button class="btn gold" data-ping-dew="1" style="margin-top:8px">✧ Ping nearest Dew</button></div>`
      : '';
    body.innerHTML = `<canvas id="bigmap" width="720" height="720"></canvas>
      <div class="legend"><span>◆ Pylon (tap to travel)</span><span>◇ Dew</span><span>𝄞 Shrine</span><span>♛ Maestro</span><span>◎ Rift</span><span>Explored ${g.progress.percent()}%</span></div>
      ${regionRow}
      <div class="muted" style="text-align:center">${BIOMES.map((b) => `${b.name.split('—')[0].trim()} Lv ${b.levels[0]}–${b.levels[1]} · ${b.bpm} BPM ${b.meter}/4`).join(' · ')}</div>`;
    body.querySelectorAll('[data-ping-dew]').forEach((el) => el.addEventListener('click', () => {
      const ping = g.progress.pingRegion();
      if (!ping) { this.toast('All regions complete — no Dew left'); return; }
      this.toast(`Ping · ${ping.target.name || 'Resonance Dew'}`);
      g.audio.ui();
      this.close();
    }));
    const cv = $('bigmap');
    this.drawBigMap(cv);
    cv.addEventListener('click', (e) => {
      const r = cv.getBoundingClientRect();
      const mx = ((e.clientX - r.left) / r.width) * cv.width, my = ((e.clientY - r.top) / r.height) * cv.height;
      const ext = g.overview.extent;
      let best = null, bd = 40;
      for (const p of g.activities.pois) {
        if (p.type !== 'pylon' || !g.profile.pylons.includes(p.id)) continue;
        const px = ((p.x + ext) / (ext * 2)) * cv.width, py = ((p.z + ext) / (ext * 2)) * cv.height;
        const d = Math.hypot(px - mx, py - my);
        if (d < bd) { bd = d; best = p; }
      }
      if (best) {
        if (g.activities.rift) { this.toast('Leave the rift first'); return; }
        if (g.inCombat) { this.toast('Cannot travel while enemies are singing at you'); return; }
        g.travelTo(best);
        this.close();
      }
    });
  }

  drawBigMap(cv) {
    const g = this.g, c = cv.getContext('2d'), ov = g.overview, W = cv.width;
    c.imageSmoothingEnabled = true;
    c.drawImage(ov.canvas, 0, 0, W, W);
    const N = g.progress.GRID, cell = W / N;
    const fog = document.createElement('canvas');
    fog.width = fog.height = N;
    const fc = fog.getContext('2d'), img = fc.createImageData(N, N);
    for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
      const k = (j * N + i) * 4;
      img.data[k] = 23; img.data[k + 1] = 18; img.data[k + 2] = 37; img.data[k + 3] = g.progress.explored(i, j) ? 0 : 205;
    }
    fc.putImageData(img, 0, 0);
    c.drawImage(fog, 0, 0, W, W);
    const ext = ov.extent;
    const to = (x, z) => [((x + ext) / (ext * 2)) * W, ((z + ext) / (ext * 2)) * W];
    c.font = 'italic bold 20px Georgia, serif'; c.textAlign = 'center';
    for (const b of BIOMES) {
      const [x, y] = to(b.cx * 1.05, b.cz * 1.05);
      c.lineWidth = 4; c.strokeStyle = 'rgba(23,18,37,.8)';
      const label = b.name.split('—')[0].trim();
      c.strokeText(label, x, y - 30); c.fillStyle = '#fff'; c.fillText(label, x, y - 30);
    }
    for (const p of g.activities.pois) {
      const [x, y] = to(p.x, p.z);
      const i = Math.floor(x / cell), j = Math.floor(y / cell);
      if (p.type !== 'pylon' && !g.progress.explored(clamp(i, 0, N - 1), clamp(j, 0, N - 1))) continue;
      if (p.type === 'camp' || p.type === 'sheet') continue;
      this.poiIcon(c, p, x, y, 1.1);
      // Momo-style pulse on remaining Resonance Dew.
      if (p.type === 'destination' && p.id && !(g.profile.dews || []).includes(p.id)) {
        const pulse = 10 + Math.sin(performance.now() / 280) * 3;
        c.strokeStyle = 'rgba(159,230,255,.85)';
        c.lineWidth = 2;
        c.beginPath(); c.arc(x, y, pulse, 0, Math.PI * 2); c.stroke();
      }
    }
    for (const b of BIOMES) {
      const bi = BIOMES.indexOf(b);
      const st = g.progress.regionStatus?.(bi);
      if (!st) continue;
      const [x, y] = to(b.cx * 1.05, b.cz * 1.05);
      c.font = 'bold 14px sans-serif';
      c.fillStyle = st.complete ? '#ffd978' : '#9fe6ff';
      c.strokeStyle = 'rgba(23,18,37,.85)'; c.lineWidth = 3;
      const tag = st.complete ? '100%' : `${st.pct}%`;
      c.strokeText(tag, x, y - 8); c.fillText(tag, x, y - 8);
    }
    const [px, py] = to(g.player.pos.x, g.player.pos.z);
    c.fillStyle = '#fff'; c.strokeStyle = '#171225'; c.lineWidth = 3;
    c.beginPath(); c.arc(px, py, 8, 0, Math.PI * 2); c.fill(); c.stroke();
  }

  render_forge(body) {
    const g = this.g, pr = g.profile, L = g.loot;
    const list = [...SLOTS.map((s) => pr.equipment[s.id]).filter(Boolean), ...pr.inventory.slice().sort((a, b) => L.score(b) - L.score(a)).slice(0, 12)];
    if (!this.forgeSel || !list.includes(this.forgeSel)) {
      this.forgeSel = list[0] || null;
      this.synthSlots = [];
    }
    const it = this.forgeSel;
    const motifs = L.motifInventory();
    if (!Array.isArray(this.synthSlots)) this.synthSlots = [];

    const preview = it ? L.synthPreview(it, this.synthSlots) : null;
    const ringClass = (i) => {
      if (!preview) return '';
      const need = preview.loops[i]?.fillNeed || 1;
      const f = preview.fills[i] || 0;
      if (f >= need) return 'filled';
      if (f > 0) return 'partial';
      return '';
    };

    let rings = '';
    if (it) {
      rings = `<div class="cymatic">
        <div class="ring r0 ${ringClass(0)}"></div>
        <div class="ring r1 ${ringClass(1)}"></div>
        <div class="ring r2 ${ringClass(2)}"></div>
        <div class="ring r3 ${ringClass(3)}"></div>
        <div class="hub"></div>
      </div>
      <div class="loop-row">${(preview?.loops || []).map((lp, i) => {
        const f = preview.fills[i] || 0;
        const dots = '●'.repeat(Math.min(f, lp.fillNeed)) + '○'.repeat(Math.max(0, lp.fillNeed - f));
        return `<span class="motifchip">${esc(lp.name)} ${dots}</span>`;
      }).join('')}</div>
      <div class="muted" style="text-align:center;margin-top:6px">Quality ${preview.quality} · Trait slots ${preview.traitSlots}/3 · Rebuilds ${it.synthCount || 0}/5</div>`;
    }

    const assigned = this.synthSlots.filter(Boolean);
    let detail = '<div class="muted">Select gear, tap Motifs to fill cymatic loops, then Synthesize. Temper (hone) after for +levels.</div>';
    if (it) {
      const c = L.honeCost(it);
      const chance = Math.min(1, honeChance(it.up || 0) + (it.pity || 0));
      const maxed = (it.up || 0) >= HONE_MAX;
      const canSynth = preview.filledLoops >= 1 && pr.gold >= preview.cost.gold && pr.shards >= preview.cost.shards && (it.synthCount || 0) < 5;
      detail = `<div class="item-name" style="color:${RARITIES[it.rarity].color}">${esc(it.name)}${it.up ? ' +' + it.up : ''}</div>
        <div class="item-sub">${RARITIES[it.rarity].name} · iLvl ${it.ilvl}${it.quality ? ` · Q${it.quality}` : ''}</div>
        <div class="item-lines">${L.lines(it).map((l) => `<div>${esc(l)}</div>`).join('')}</div>
        ${it.aria ? `<div class="item-aria">Aria — ${esc(ARIA_BY_ID[it.aria].name)}</div>` : ''}
        <div class="stats" style="margin-top:8px">
          <span>Synth cost</span><span>${fmt(preview.cost.gold)}● ${preview.cost.shards}◆ + Motifs</span>
          <span>You have</span><span>${fmt(pr.gold)}● ${pr.shards}◆</span>
          <span>Temper</span><span>+${it.up || 0} → +${Math.min(HONE_MAX, (it.up || 0) + 1)} · ${Math.round(chance * 100)}%</span>
          <span>Temper cost</span><span>${fmt(c.gold)}● ${c.shards}◆</span>
        </div>
        <div class="btns">
          <button class="btn gold" id="synthesize" ${canSynth ? '' : 'disabled'}>Harmonic Synthesis</button>
          <button class="btn" id="hone" ${maxed || pr.gold < c.gold || pr.shards < c.shards ? 'disabled' : ''}>${maxed ? 'Max +' + HONE_MAX : 'Temper ⚒'}</button>
          <button class="btn" id="clearsynth" ${assigned.length ? '' : 'disabled'}>Clear Motifs</button>
        </div>
        <div class="forgeresult" id="honeres"></div>
        <div class="muted" style="margin-top:6px">Fill 2+ rings to transfer Motifs as traits. Opus Aria ring = Super Trait.</div>`;
    }

    body.innerHTML = `<div class="synth-wrap">
      <div class="card"><h3>Choose gear</h3>
        <div class="grid">${list.map((x) => this.itemBox(x, `data-fu="${x.uid}"`).replace('slotbox', 'slotbox' + (x === it ? ' sel' : ''))).join('') || '<div class="muted">No gear yet.</div>'}</div>
      </div>
      <div class="card"><h3>Cymatic loops</h3>${rings || '<div class="muted">Select a piece of gear.</div>'}
        <h3 style="margin-top:12px">Motif bag</h3>
        <div class="motifbag">${motifs.map((m) => {
          const used = this.synthSlots.filter((id) => id === m.id).length;
          const left = m.n - used;
          return this.motifChip({ ...m, n: left }, { on: used > 0, dim: left <= 0, attrs: `data-mid="${m.id}"` });
        }).join('') || '<div class="muted">Salvage gear in the Wardrobe to earn Motifs.</div>'}</div>
      </div>
      <div class="card"><h3>Synthesize</h3>${detail}</div>
    </div>`;

    body.querySelectorAll('[data-fu]').forEach((el) => el.addEventListener('click', () => {
      this.forgeSel = list.find((x) => x.uid === +el.dataset.fu);
      this.synthSlots = [];
      this.render();
    }));
    // Beat-sync pulse rings when panel is open
    const prev = this._prevFills || [];
    body.querySelectorAll('.cymatic .ring').forEach((el, i) => {
      if (preview && (preview.fills[i] || 0) >= (preview.loops[i]?.fillNeed || 1) && (prev[i] || 0) < (preview.loops[i]?.fillNeed || 1)) {
        el.classList.add('justfilled');
        const mid = this.synthSlots[this.synthSlots.length - 1];
        const Mel = mid && MOTIF_BY_ID[mid];
        if (Mel) g.audio.motifChord(Mel.element);
      }
      el.classList.add('beatpulse');
      setTimeout(() => el.classList.remove('beatpulse'), 280);
    });
    this._prevFills = preview ? preview.fills.slice() : [];

    body.querySelectorAll('[data-mid]').forEach((el) => el.addEventListener('click', () => {
      const id = el.dataset.mid;
      const have = L.motifCount(id);
      const used = this.synthSlots.filter((x) => x === id).length;
      if (used >= have) return;
      if (this.synthSlots.length >= 8) { this.toast('Loop board full'); return; }
      this.synthSlots.push(id);
      const Mel = MOTIF_BY_ID[id];
      if (Mel) g.audio.motifChord(Mel.element);
      this.render();
    }));
    const cs = body.querySelector('#clearsynth');
    if (cs) cs.addEventListener('click', () => { this.synthSlots = []; this.render(); });
    const syn = body.querySelector('#synthesize');
    if (syn) syn.addEventListener('click', () => {
      const r = L.synthesize(it, this.synthSlots.slice());
      if (!r.ok) {
        this.toast(r.reason === 'cost' ? 'Not enough gold/shards' : r.reason === 'motifs' ? 'Missing Motifs' : r.reason === 'rebuild_max' ? 'Rebuild limit reached' : 'Fill at least one loop');
        return;
      }
      this.synthSlots = [];
      g.audio.synthResolve(it.quality || 50);
      this.render();
      const res = $('honeres');
      if (res) {
        res.textContent = `✦ Synthesized · Q${it.quality}` + (r.transferred?.length ? ` · ${r.transferred.join(', ')}` : '');
        res.style.color = '#ffd978';
      }
      g.audio.levelUp();
      g.save();
    });
    const hb = body.querySelector('#hone');
    if (hb) hb.addEventListener('click', () => {
      const r = L.hone(it);
      if (!r.ok) return;
      this.render();
      const res = $('honeres');
      if (r.success) { res.textContent = `✦ Tempered! +${it.up}`; res.style.color = '#ffd978'; g.audio.levelUp(); }
      else { res.textContent = 'The metal rings false… (pity banked)'; res.style.color = '#ff8a9a'; g.audio.fail(); }
      g.save();
    });
  }

  render_blessings(body) {
    const g = this.g, pr = g.profile;
    body.innerHTML = `<div class="card"><h3>Blessing Font · ${pr.notes} Golden Notes</h3><div class="muted">Permanent blessings from DT_Blessings. Earn Golden Notes from Maestros, rifts, shrines and bounty caches.</div></div>
      <div style="margin-top:10px">${BLESSINGS.map((b) => {
        const own = pr.blessings.includes(b.blessing_id);
        return `<div class="skillrow ${own ? '' : ''}"><div class="ic" style="border-color:var(--rose);color:var(--rose)">✧</div>
          <div class="tx"><b>${esc(b.display_name)}</b><div>${esc(b.description)}</div><div class="meta">${b.token_cost} Golden Notes</div></div>
          <button class="btn ${own ? '' : 'gold'}" data-b="${b.blessing_id}" ${own || pr.notes < b.token_cost ? 'disabled' : ''}>${own ? 'Owned' : 'Receive'}</button></div>`;
      }).join('')}</div>`;
    body.querySelectorAll('[data-b]').forEach((el) => el.addEventListener('click', () => {
      const b = BLESSINGS.find((x) => x.blessing_id === el.dataset.b);
      if (!b || pr.notes < b.token_cost || pr.blessings.includes(b.blessing_id)) return;
      pr.notes -= b.token_cost;
      pr.blessings.push(b.blessing_id);
      g.player.recalc();
      g.audio.levelUp();
      this.toast(`Blessing received: ${b.display_name}`, 'gold');
      g.save();
      this.render();
    }));
  }

  render_rift(body) {
    const g = this.g, pr = g.profile;
    const max = pr.riftTier + 1;
    if (!this.riftTier || this.riftTier > max) this.riftTier = max;
    const T = this.riftTier;
    const chance = g.echo.passChance(T);
    const phrase = pr.echoLineage?.phrase;
    const pity = pr.echoLineage?.pity || 0;
    body.innerHTML = `<div class="card" style="text-align:center"><h3>Resonance Rift</h3>
      <div class="muted">Silence waves of dissonance to fill the bar, then defeat the Rift Guardian. Clear within 4:00 to unlock the next tier. Tier 3+ adds a Burden from DT_Burdens for extra rarity.</div>
      <div class="tiers"><button id="tminus">−</button><span>Tier ${T}</span><button id="tplus">+</button></div>
      <div class="stats" style="max-width:320px;margin:0 auto"><span>Enemy level</span><span>${pr.level + Math.max(0, T - 1) * 2}</span><span>Tempo</span><span>${124 + Math.min(24, T * 2)} BPM</span>
      <span>Rewards</span><span>${3 + Math.floor(T / 3)} items (Resonant+) · ${10 + T * 2}♪</span><span>Best cleared</span><span>${pr.riftTier}</span></div>
      <div class="echo-banner" style="max-width:420px;margin:12px auto 0">
        <img src="assets/icons/echo_phrase.svg" width="20" height="20" alt="" style="vertical-align:middle;margin-right:6px"/>
        ${phrase
          ? `Echo Lineage pass <b>${Math.round(chance * 100)}%</b>${pity ? ` · pity +${Math.round(pity * 100)}%` : ''} · Phrase T${phrase.tier} Q${phrase.quality}`
          : 'No Echo Phrase yet — clear a Rift to bank one (Uma-style inheritance).'}
      </div>
      <button class="primary" id="enterrift" style="margin-top:14px">Enter the Recital ◎</button></div>`;
    $('tminus').addEventListener('click', () => { this.riftTier = Math.max(1, T - 1); this.render(); });
    $('tplus').addEventListener('click', () => { this.riftTier = Math.min(max, T + 1); this.render(); });
    $('enterrift').addEventListener('click', () => { const p = this.riftPortal; this.close(); g.activities.enterRift(T, p); });
  }

  render_settings(body) {
    const g = this.g, pr = g.profile, st = pr.settings;
    const seg = (key, opts) => `<div class="seg" data-seg="${key}">${opts.map(([v, l]) => `<button data-v="${v}" class="${st[key] === v ? 'on' : ''}">${l}</button>`).join('')}</div>`;
    const W = g.rhythm.windows();
    body.innerHTML = `<div class="card">
      <div class="row"><span>Music</span><input type="range" min="0" max="1" step="0.05" value="${st.music}" data-r="music"></div>
      <div class="row"><span>Effects</span><input type="range" min="0" max="1" step="0.05" value="${st.sfx}" data-r="sfx"></div>
      <div class="row"><span>Rhythm difficulty<br><small class="muted">Perfect ±${Math.round(W.perfect)} · Great ±${Math.round(W.great)} · Good ±${Math.round(W.good)} ms</small></span>${seg('difficulty', Object.entries(DIFFICULTY).map(([k, d]) => [k, d.name]))}</div>
      <div class="row"><span>Audio latency offset<br><small class="muted">${st.offsetMs} ms · Bluetooth headphones usually need +150–250</small></span>
        <div class="seg"><button data-o="-10">−10</button><button data-o="10">+10</button><button id="calib" class="on">Calibrate</button></div></div>
      <div class="row"><span>Graphics</span>${seg('quality', [['auto', 'Auto'], ['low', 'Low'], ['high', 'High']])}</div>
      <div class="row"><span>Screen shake</span>${seg('shake', [[true, 'On'], [false, 'Off']])}</div>
      <div class="row"><span>Controls</span><span class="muted">Touch: left thumb moves, right cluster fights. Keys: WASD · Space/J attack (hold = auto) · Q E R F or 1–4 skills · Shift dodge · T Encore · X interact · I K M B menus.</span></div>
      <div class="row"><span>Save</span><button class="btn" id="wipe">Reset progress</button></div>
      <div class="muted" style="margin-top:8px">Rhythm windows, grade multipliers, Harmony (SP), Crescendo, Encore, toughness and the element wheel come from Plugins/MelodiaCore/Rules/melodia_rules.json (v${RULES.version ?? 3} rules). Skills and enemies come from DT_MelodySlime_Skills / DT_MelodySlime_Enemies; biomes from the Gaea world-gen setups.</div>
    </div>`;
    body.querySelectorAll('[data-r]').forEach((el) => el.addEventListener('input', () => { st[el.dataset.r] = +el.value; g.audio.setVolumes(st.music, st.sfx); }));
    body.querySelectorAll('[data-seg]').forEach((segEl) => segEl.querySelectorAll('button').forEach((b) => b.addEventListener('click', () => {
      const key = segEl.dataset.seg;
      let v = b.dataset.v;
      if (v === 'true') v = true; else if (v === 'false') v = false;
      st[key] = v;
      if (key === 'quality') g.applyQuality();
      this.render();
    })));
    body.querySelectorAll('[data-o]').forEach((b) => b.addEventListener('click', () => { st.offsetMs += +b.dataset.o; this.render(); }));
    $('calib').addEventListener('click', () => { this.close(); g.startCalibration(); });
    $('wipe').addEventListener('click', () => {
      if (b2 !== 1) { b2 = 1; $('wipe').textContent = 'Tap again to erase everything'; return; }
      g.wipe();
    });
    let b2 = 0;
  }

  motifMorph({ fromIcon, motifIds = [], rarity = 0, label = '', kind = 'salvage' }) {
    const box = $('motifmorph');
    if (!box) { this.toast(label); return; }
    const colors = ['#ddd7e6', '#7fe69a', '#6fb8ff', '#c690ff', '#ffae45'];
    const col = colors[Math.min(4, rarity)] || '#ffd978';
    const from = $('mmFrom');
    const to = $('mmTo');
    const flash = $('mmFlash');
    const lab = $('mmLabel');
    from.src = this.iconSrc(fromIcon) || 'assets/icons/echo_phrase.svg';
    from.parentElement.classList.remove('flip');
    to.classList.remove('show');
    to.innerHTML = (motifIds.length ? motifIds : ['motif_arcane']).slice(0, 3).map((id) => {
      const M = MOTIF_BY_ID[id];
      const el = (M?.element || 'Arcane').toLowerCase();
      return `<img src="assets/icons/motif_${el}.svg" alt=""/>`;
    }).join('');
    flash.style.color = col;
    flash.classList.remove('on');
    lab.textContent = label || '';
    box.classList.remove('hidden');
    requestAnimationFrame(() => {
      from.parentElement.classList.add('flip');
      flash.classList.add('on');
      setTimeout(() => to.classList.add('show'), 180);
    });
    if (kind === 'salvage') this.g.audio.loot(rarity);
    clearTimeout(this._morphT);
    this._morphT = setTimeout(() => {
      box.classList.add('hidden');
      if (label) this.toast(label, kind === 'synth' ? 'gold' : '');
    }, 900);
  }

  // ================================================================ rift reward reveal
  showRiftReward(payload) {
    const box = $('riftreward');
    if (!box) return;
    const { tier, inTime, notes, gold, items, phrase, passChance, pity, blessing, motifPack } = payload;
    $('rrKicker').textContent = inTime ? `RIFT TIER ${tier} CLEARED` : `RIFT TIER ${tier} CLEARED (OVER TIME)`;
    $('rrTitle').textContent = 'Resonance Remains';
    $('rrSub').textContent = blessing
      ? `Blessing: ${blessing.name} · Echo Lineage banks for the next Recital`
      : 'Staged rewards · Echo Lineage banks for the next Recital';
    const cards = [];
    (items || []).forEach((it, i) => {
      const R = RARITIES[it.rarity];
      cards.push(`<div class="rewardcard" style="animation-delay:${i * 0.12}s;border-color:${R.color}">
        ${this.itemBox(it)}
        <b style="color:${R.color}">${esc(it.name)}</b>
        <div class="meta">${R.name} · iLvl ${it.ilvl}</div>
      </div>`);
    });
    cards.push(`<div class="rewardcard" style="animation-delay:${(items?.length || 0) * 0.12}s;border-color:var(--rose)">
      <div class="slotbox" style="border-color:var(--rose)">♪</div>
      <b>+${notes} Golden Notes</b>
      <div class="meta">+${gold} gold on the ground</div>
    </div>`);
    if (motifPack) {
      const delay = ((items?.length || 0) + 0.5) * 0.12;
      const bits = Object.entries(motifPack.motifs || {}).map(([id, n]) => `${MOTIF_BY_ID[id]?.name || id}×${n}`).join(', ');
      cards.push(`<div class="rewardcard" style="animation-delay:${delay}s;border-color:var(--lavender)">
        <div class="slotbox" style="border-color:var(--lavender)">✦</div>
        <b>Motif Pack ×${motifPack.n}</b>
        <div class="meta">${esc(bits)}</div>
      </div>`);
    }
    if (phrase) {
      const delay = ((items?.length || 0) + 1) * 0.12;
      cards.push(`<div class="rewardcard" style="animation-delay:${delay}s;border-color:var(--aqua)">
        <div class="slotbox" style="border-color:var(--aqua)"><img class="ico" src="assets/icons/echo_phrase.svg" alt=""/></div>
        <b>Echo Phrase T${phrase.tier}</b>
        <div class="meta">Q${phrase.quality} · ${(phrase.motifs || []).map((m) => m.key).join(', ')}</div>
      </div>`);
      const pd = phrase.pedigree;
      if (pd) {
        cards.push(`<div class="rewardcard pedigree-card" style="animation-delay:${delay + 0.12}s;border-color:var(--aqua)">
          <div class="pedigree"><div class="title">Phrase Pedigree</div>
          ${esc(this.g.echo.pedigreeHtml())}
          ${(pd.goals || []).length ? `<div style="margin-top:4px">Goals: ${esc(pd.goals.join(' · '))}</div>` : ''}
          </div>
        </div>`);
      }
    }
    const goals = payload.goals || [];
    if (goals.length) {
      const delay = ((items?.length || 0) + 3) * 0.12;
      cards.push(`<div class="rewardcard" style="animation-delay:${delay}s;border-color:var(--gold)">
        <b>Recital Goals</b>
        <div class="meta">${goals.map((x) => (x.done ? '✓ ' : '· ') + esc(x.text)).join('<br>')}</div>
      </div>`);
    }
    $('rrRow').innerHTML = cards.join('');
    $('rrLineage').innerHTML = `<img src="assets/icons/echo_phrase.svg" alt=""/>Echo Lineage next pass ${Math.round((passChance || 0) * 100)}%${pity ? ` · pity +${Math.round(pity * 100)}%` : ''}`;
    box.classList.remove('hidden');
    this.ceremonyFlash('bank');
    const btn = $('rrContinue');
    const done = () => {
      box.classList.add('hidden');
      this.toast('Echo Phrase banked — enter another Rift to inherit', 'gold');
    };
    btn.onclick = done;
  }

  // ================================================================ shrine
  openShrine(s) {
    $('shrine').classList.remove('hidden');
    const mk = (id) => { $(id).innerHTML = Array.from({ length: s.slots }, (_, i) => `<i class="${s.call.some((c) => c.slot === i) ? 'note' : ''}" data-s="${i}"></i>`).join(''); };
    mk('shrinecall'); mk('shrineresp');
  }

  shrineFrame(s, now) {
    const ph = $('shrinephase');
    const step = s.spb / 2;
    if (now < s.callStart) ph.textContent = 'Count-in… listen to the shrine';
    else if (now < s.respStart) ph.textContent = 'Listen…';
    else ph.textContent = 'Answer! Tap the same rhythm';
    const callKids = $('shrinecall').children, respKids = $('shrineresp').children;
    const ci = Math.floor((now - s.callStart) / step), ri = Math.floor((now - s.respStart) / step);
    for (let i = 0; i < callKids.length; i++) {
      callKids[i].classList.toggle('lit', ci >= i && callKids[i].classList.contains('note') && now < s.respStart + s.spb);
      callKids[i].classList.toggle('now', ci === i);
      respKids[i].classList.toggle('now', ri === i);
    }
  }

  shrineGrade(r) {
    const el = $('shrineresp').querySelector(`[data-s="${r.slot}"]`);
    if (el) { el.classList.add(r.grade); el.textContent = r.grade[0]; }
  }

  closeShrine() { $('shrine').classList.add('hidden'); }

  tutorialTick(dt) {
    const g = this.g, pr = g.profile;
    if (pr.tutorial >= TUTORIAL.length) { this.hint(null); return; }
    this._tut = (this._tut || 0) + dt;
    this.hint(`${TUTORIAL[pr.tutorial]}  (${pr.tutorial + 1}/${TUTORIAL.length})`);
    if (this._tut > 8) { this._tut = 0; pr.tutorial++; }
  }
}
