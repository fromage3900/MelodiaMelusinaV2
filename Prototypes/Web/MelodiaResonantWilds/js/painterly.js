// Floraison crisp painterly — opt-in anisotropic Kuwahara image abstraction.
// Based on the archived my-site d2c3379 preview, now composited AFTER the
// canonical hard RGB cel bands, OutlinePass, bloom and OutputPass.
// Crucially this samples the COMPOSER'S FULL-RESOLUTION final image. The old
// half-resolution blur/upscale target is deliberately NOT restored.
// ?kuwahara=1 (or =crisp) enables; ?paint=0 is a true A/B bypass.
// No gameplay, world, save, camera or material ownership is changed.
import * as THREE from 'three';
import { ShaderPass } from '../vendor/postprocessing/ShaderPass.js';
import { legacyRender, nprV2 } from './cel.js';

const query = new URLSearchParams(typeof window === 'undefined' ? '' : window.location.search);
export const painterlyEnabled = !legacyRender && nprV2 &&
  (query.get('kuwahara') === '1' || query.get('kuwahara') === 'crisp');

const vertexShader = `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position.xy, 0.0, 1.0);
}`;

const fragmentShader = `
precision highp float;
uniform sampler2D tDiffuse;
uniform vec2 uTexel;
uniform float uStrength;
uniform float uRadius;
uniform float uAnisotropy;
uniform float uEdgeProtect;
uniform float uEdgeLock;
varying vec2 vUv;

vec3 at(vec2 px) {
  return texture2D(tDiffuse, clamp(vUv + px * uTexel, vec2(0.0), vec2(1.0))).rgb;
}

void main() {
  vec3 original = at(vec2(0.0));
  // Tensor-aligned local stroke direction, evaluated in output pixel space.
  vec3 dx = 0.5 * (at(vec2(1.0, 0.0)) - at(vec2(-1.0, 0.0)));
  vec3 dy = 0.5 * (at(vec2(0.0, 1.0)) - at(vec2(0.0, -1.0)));
  float a = dot(dx, dx) + 0.000001;
  float b = dot(dx, dy);
  float c = dot(dy, dy) + 0.000001;
  float disc = sqrt((a-c)*(a-c) + 4.0*b*b);
  float coherence = clamp(disc / (a+c), 0.0, 1.0);
  float phi = 0.5 * atan(2.0*b, a-c);
  vec2 tangent = vec2(-sin(phi), cos(phi));
  vec2 normal = vec2(-tangent.y, tangent.x);
  float stretch = mix(1.0, uAnisotropy, coherence);

  vec3 s0=vec3(0.0), s1=vec3(0.0), s2=vec3(0.0), s3=vec3(0.0);
  vec3 q0=vec3(0.0), q1=vec3(0.0), q2=vec3(0.0), q3=vec3(0.0);
  float w0=0.0, w1=0.0, w2=0.0, w3=0.0;
  // A bounded 49-tap kernel, just as in the historic preview, but WITHOUT
  // the half-size scene render that lost small geometry/shadow silhouettes.
  for (int j = -3; j <= 3; ++j) {
    for (int i = -3; i <= 3; ++i) {
      if (abs(float(i)) > uRadius || abs(float(j)) > uRadius) continue;
      float x=float(i), y=float(j);
      vec2 offset = tangent*x*stretch + normal*y/max(stretch,0.001);
      vec3 v=at(offset);
      float w=exp(-0.12*(x*x + y*y));
      if (i<=0 && j<=0) { s0+=w*v; q0+=w*v*v; w0+=w; }
      if (i>=0 && j<=0) { s1+=w*v; q1+=w*v*v; w1+=w; }
      if (i<=0 && j>=0) { s2+=w*v; q2+=w*v*v; w2+=w; }
      if (i>=0 && j>=0) { s3+=w*v; q3+=w*v*v; w3+=w; }
    }
  }
  vec3 m0=s0/max(w0,0.0001), m1=s1/max(w1,0.0001);
  vec3 m2=s2/max(w2,0.0001), m3=s3/max(w3,0.0001);
  vec3 v0=max(q0/max(w0,0.0001)-m0*m0,vec3(0.0));
  vec3 v1=max(q1/max(w1,0.0001)-m1*m1,vec3(0.0));
  vec3 v2=max(q2/max(w2,0.0001)-m2*m2,vec3(0.0));
  vec3 v3=max(q3/max(w3,0.0001)-m3*m3,vec3(0.0));
  vec3 lum=vec3(0.2126,0.7152,0.0722);
  float p0=1.0/pow(dot(v0,lum)+0.0005,uEdgeProtect);
  float p1=1.0/pow(dot(v1,lum)+0.0005,uEdgeProtect);
  float p2=1.0/pow(dot(v2,lum)+0.0005,uEdgeProtect);
  float p3=1.0/pow(dot(v3,lum)+0.0005,uEdgeProtect);
  vec3 painted=(p0*m0+p1*m1+p2*m2+p3*m3)/max(p0+p1+p2+p3,0.0001);

  // Restore source pixels at crisp cel boundaries, silhouettes and ink.
  // Difference protection prevents large colour-band jumps from blending away.
  float edge = max(length(dx), length(dy));
  float edgeMask = smoothstep(0.035,0.16,edge);
  float bandChange = smoothstep(0.055,0.24,abs(dot(painted-original,lum)));
  float protect = clamp(uEdgeLock * max(edgeMask,bandChange*0.7),0.0,1.0);
  float weight = clamp(uStrength,0.0,1.0) * (1.0-protect);
  gl_FragColor = vec4(mix(original,painted,weight),1.0);
}`;

export class PainterlyFilter {
  constructor() {
    this.coarse = typeof matchMedia === 'function' && matchMedia('(pointer: coarse)').matches;
    this.settings = {
      strength: this.coarse ? 0.62 : 0.85,
      radius: this.coarse ? 2 : 3,
      anisotropy: 1.5,
      edgeProtect: 3.7,
      edgeLock: 0.94,
    };
    this.pass = new ShaderPass({
      uniforms: {
        tDiffuse: { value: null },
        uTexel: { value: new THREE.Vector2(1,1) },
        uStrength: { value: this.settings.strength },
        uRadius: { value: this.settings.radius },
        uAnisotropy: { value: this.settings.anisotropy },
        uEdgeProtect: { value: this.settings.edgeProtect },
        uEdgeLock: { value: this.settings.edgeLock },
      },
      vertexShader, fragmentShader,
    });
    this.pass.material.depthTest = false;
    this.pass.material.depthWrite = false;
    this.applySettings({
      strength: query.get('paint') ?? this.settings.strength,
      radius: query.get('rad') ?? this.settings.radius,
      anisotropy: query.get('anis') ?? this.settings.anisotropy,
      edgeProtect: query.get('edge') ?? this.settings.edgeProtect,
      edgeLock: query.get('sharp') ?? this.settings.edgeLock,
    });
  }
  applySettings(changes = {}) {
    const bounds = {
      strength: [0,1], radius: [1,this.coarse ? 2 : 3], anisotropy: [1,3.2],
      edgeProtect: [1,4.5], edgeLock: [0,1],
    };
    for (const [key,range] of Object.entries(bounds)) {
      if (!(key in changes)) continue;
      const n = Number(changes[key]);
      if (!Number.isFinite(n)) continue;
      this.settings[key] = Math.min(range[1],Math.max(range[0],
        key==='radius' ? Math.round(n) : n));
    }
    for (const [key,uniform] of [
      ['strength','uStrength'],['radius','uRadius'],
      ['anisotropy','uAnisotropy'],['edgeProtect','uEdgeProtect'],
      ['edgeLock','uEdgeLock'],
    ]) this.pass.uniforms[uniform].value = this.settings[key];
    this.pass.enabled = this.settings.strength > 0.001;
    return { ...this.settings };
  }
  resize(widthPixels,heightPixels) {
    // Composer pixel ratio is already applied by its caller.
    this.pass.uniforms.uTexel.value.set(1/Math.max(1,widthPixels),1/Math.max(1,heightPixels));
  }
  dispose() { this.pass.dispose(); }
}
