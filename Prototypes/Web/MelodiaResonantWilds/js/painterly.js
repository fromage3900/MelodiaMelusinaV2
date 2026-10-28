// Resonant Wilds — directional anisotropic Kuwahara image abstraction.
// New GLSL implementation inspired by Kyprianidis, Kang & Döllner (2009).
// Structure tensor eigenvectors align elliptical sampling along local edges.
// Four low-variance sectors are softly blended, then mixed with the original.
// No external GPU framework; no persistent CPU image copies or readbacks.
import * as THREE from 'three';
import { legacyRender } from './cel.js';

const params = new URLSearchParams(window.location.search);
export const painterlyEnabled = !legacyRender && params.get('kuwahara') === '1';

const vertex = `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position.xy, 0.0, 1.0);
}`;

const fragment = `
precision highp float;
uniform sampler2D tScene;
uniform vec2 uTexel;
uniform float uStrength;
uniform float uRadius;
varying vec2 vUv;

vec3 at(vec2 px) {
  return texture2D(tScene, clamp(vUv + px * uTexel, vec2(0.0), vec2(1.0))).rgb;
}

void main() {
  vec3 original = at(vec2(0.0));
  // Estimate the 2x2 image structure tensor from local RGB derivatives.
  vec3 dx = (at(vec2(1.0, 0.0)) - at(vec2(-1.0, 0.0))) * 0.5;
  vec3 dy = (at(vec2(0.0, 1.0)) - at(vec2(0.0, -1.0))) * 0.5;
  float a = dot(dx, dx) + 0.000001;
  float b = dot(dx, dy);
  float c = dot(dy, dy) + 0.000001;
  float disc = sqrt((a-c)*(a-c) + 4.0*b*b);
  float coherence = clamp(disc / (a + c), 0.0, 1.0);
  float phi = 0.5 * atan(2.0*b, a-c);
  // The minor eigenvector follows the edge tangent; enlarge that axis.
  vec2 tangent = vec2(-sin(phi), cos(phi));
  vec2 normal = vec2(-tangent.y, tangent.x);
  float stretch = mix(1.0, 2.2, coherence);
  vec3 s0 = vec3(0.0), s1 = vec3(0.0), s2 = vec3(0.0), s3 = vec3(0.0);
  vec3 q0 = vec3(0.0), q1 = vec3(0.0), q2 = vec3(0.0), q3 = vec3(0.0);
  float w0 = 0.0, w1 = 0.0, w2 = 0.0, w3 = 0.0;
  // Bounded radius <= 3: 49 taps max + tensor, evaluated on a half-resolution target.
  for (int j = -3; j <= 3; ++j) {
    for (int i = -3; i <= 3; ++i) {
      if (abs(float(i)) > uRadius || abs(float(j)) > uRadius) continue;
      float x = float(i), y = float(j);
      vec2 ellipseOffset = tangent*x*stretch + normal*y/max(stretch, 0.001);
      vec3 v = at(ellipseOffset);
      float w = exp(-0.12*(x*x + y*y));
      if (i <= 0 && j <= 0) { s0 += w*v; q0 += w*v*v; w0 += w; }
      if (i >= 0 && j <= 0) { s1 += w*v; q1 += w*v*v; w1 += w; }
      if (i <= 0 && j >= 0) { s2 += w*v; q2 += w*v*v; w2 += w; }
      if (i >= 0 && j >= 0) { s3 += w*v; q3 += w*v*v; w3 += w; }
    }
  }
  vec3 m0 = s0/max(w0,0.0001), m1 = s1/max(w1,0.0001);
  vec3 m2 = s2/max(w2,0.0001), m3 = s3/max(w3,0.0001);
  vec3 v0 = max(q0/max(w0,0.0001)-m0*m0, vec3(0.0));
  vec3 v1 = max(q1/max(w1,0.0001)-m1*m1, vec3(0.0));
  vec3 v2 = max(q2/max(w2,0.0001)-m2*m2, vec3(0.0));
  vec3 v3 = max(q3/max(w3,0.0001)-m3*m3, vec3(0.0));
  vec3 lum = vec3(0.2126, 0.7152, 0.0722);
  float p0 = 1.0/pow(dot(v0,lum)+0.0005, 2.0);
  float p1 = 1.0/pow(dot(v1,lum)+0.0005, 2.0);
  float p2 = 1.0/pow(dot(v2,lum)+0.0005, 2.0);
  float p3 = 1.0/pow(dot(v3,lum)+0.0005, 2.0);
  vec3 painted = (p0*m0+p1*m1+p2*m2+p3*m3)/max(p0+p1+p2+p3,0.0001);
  gl_FragColor = vec4(mix(original, painted, clamp(uStrength,0.0,1.0)), 1.0);
  #include <colorspace_fragment>
}`;

export class PainterlyFilter {
  constructor() {
    const coarse = matchMedia('(pointer: coarse)').matches;
    this.scale = coarse ? 0.35 : 0.5;
    this.target = new THREE.WebGLRenderTarget(1, 1, {
      depthBuffer: true, stencilBuffer: false,
      minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter,
    });
    this.target.texture.name = 'Melodia_Kuwahara_P0';
    this.material = new THREE.ShaderMaterial({
      uniforms: {
        tScene: { value: this.target.texture },
        uTexel: { value: new THREE.Vector2(1, 1) },
        uStrength: { value: coarse ? 0.45 : 0.65 },
        uRadius: { value: coarse ? 2 : 3 },
      },
      vertexShader: vertex,
      fragmentShader: fragment,
      depthTest: false,
      depthWrite: false,
    });
    this.scene = new THREE.Scene();
    this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    this.quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.material);
    this.quad.frustumCulled = false;
    this.scene.add(this.quad);
    this.size = [0, 0];
  }

  resize(renderer) {
    const canvas = renderer.domElement;
    const w = Math.max(1, Math.round(canvas.width * this.scale));
    const h = Math.max(1, Math.round(canvas.height * this.scale));
    if (w === this.size[0] && h === this.size[1]) return;
    this.target.setSize(w, h);
    this.material.uniforms.uTexel.value.set(1/w, 1/h);
    this.size = [w, h];
  }

  render(renderer, scene, camera) {
    this.resize(renderer);
    const prev = renderer.getRenderTarget();
    try {
      renderer.setRenderTarget(this.target);
      renderer.clear(true, true, true);
      renderer.render(scene, camera);
      renderer.setRenderTarget(prev);
      renderer.render(this.scene, this.camera);
    } finally {
      renderer.setRenderTarget(prev);
    }
  }

  dispose() {
    this.quad.geometry.dispose();
    this.material.dispose();
    this.target.dispose();
  }
}
