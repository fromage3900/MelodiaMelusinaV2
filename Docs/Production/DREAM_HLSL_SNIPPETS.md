# Dream System — ready-to-paste HLSL Custom-node snippets

Zero-dependency HLSL for `MaterialExpressionCustom` nodes to extend the dream system.
All are self-contained (no view globals that break the Nanite permutation — pass UV from
a TextureCoordinate input pin, WorldPos from a WorldPosition node, Time from a Time node).
Output type noted per snippet. Splice at the emissive tail like the existing effects; gate
every one behind a `*Strength` scalar defaulting to 0.

Sources / lineage: Inigo Quilez cosine palette + value noise (iquilezles.org, MIT-spirit
public domain articles); standard curl-noise + caustics constructions. Safe to use.

---

## 1. Improved Curl-Noise Dream Mist  (float3)
Real curl of a value-noise potential → organic swirling advection (upgrade over the sine
version currently in `10h`). Inputs: `UV`(float2) `Time` `Scale` `Speed`.
```hlsl
float2 p = UV*Scale; float t = Time*Speed;
float2 e = float2(0.01, 0.0);
#define N(x) frac(sin(dot(floor(x),float2(127.1,311.7)))*43758.5)
float n1 = N(p+e.yx+t); float n2 = N(p-e.yx+t);
float n3 = N(p+e.xy+t); float n4 = N(p-e.xy+t);
float2 curl = float2((n1-n2), -(n3-n4))/(2.0*e.x);
float m = 0.5+0.5*sin(dot(p+curl, float2(1.7,1.3)) + t);
return float3(m,m,m);
```

## 2. Water Caustics  (float3)  — for M_Water_Master_Grand_v6
Cheap animated caustic bands (looks great under the dream shimmer). Inputs: `UV` `Time` `Scale`.
```hlsl
float2 p = UV*Scale; float t = Time*0.5;
float c = 0.0;
for (int i=0; i<3; i++){
  float2 q = p + float2(sin(t+p.y*3.0), cos(t+p.x*3.0))*0.3;
  c += 1.0 - abs(sin(q.x*6.28318)*sin(q.y*6.28318));
  p *= 1.7;
}
c = pow(saturate(c/3.0), 4.0);
return float3(c,c,c);
```

## 3. Star-Nest lite  (float3)  — dreamy volumetric sparkle field
A trimmed star-nest (Kali/Shadertoy family) for crystal/night surfaces. Inputs: `UV` `Time`.
```hlsl
float2 uv = UV-0.5; float t = Time*0.05;
float3 col=0; float2 p=uv*3.0;
for(int i=0;i<8;i++){
  p = abs(p)/dot(p,p) - 0.9;
  col += float3(0.6,0.7,1.0)*length(p)*0.06;
}
return saturate(col*(0.5+0.5*sin(t*6.28318)));
```

## 4. Chromatic Dispersion Rim  (float3)  — prismatic edge split
Splits the fresnel rim into RGB by a dispersion amount (glassy Nikki edge). Inputs:
`Rim`(float1 fresnel) `Disp`.
```hlsl
float r = saturate(Rim+Disp);
float g = saturate(Rim);
float b = saturate(Rim-Disp);
return float3(r*r, g*g, b*b);
```

## 5. Heart/Petal Sigil variant  (float1)  — for the Kaleidoscope Sigil (10f)
Swap into the sigil for a petal/heart motif instead of rings. Inputs: `UV` `Time` `Petals`.
```hlsl
float2 p = UV-0.5; float a = atan2(p.y,p.x); float r = length(p)*2.0;
float petal = 0.5+0.5*cos(a*Petals + Time);
float shape = smoothstep(0.02, 0.0, abs(r - petal*0.6));
return saturate(shape*(1.0-r));
```

---

## Native UE 5.8 Substrate Toon features to exploit (no plugin, biggest win)
The 5.8 Substrate Toon BSDF (already the master's shading model) exposes, per Epic's 5.8
notes, features worth wiring that need NO external code:
- **Self-shadow extinction with hatching patterns** — hand-drawn cross-hatch in shadow.
- **Ramp-based diffuse & specular with dithering** — cleaner toon banding control.
- **Anisotropic specular highlights** — the Tangent/Anisotropy BSDF inputs (currently
  unconnected on `SubstrateToonBSDF_4`) → silk/hair/water streak highlights.

These are the highest-ROI, lowest-risk "make it shine" additions and should be preferred
over installing any third-party toon plugin on render day.
