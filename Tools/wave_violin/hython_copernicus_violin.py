# -*- coding: utf-8 -*-
# ME_WaveViolin Copernicus pass — hython-safe, harp-proven pattern.
# Night Reel belly cymatics: (1,2)x(2,1) Chladni interference = violin nodal cross.
# 9 maps x 1024. No fract/dot (need @ElementPixelSpace) — grain from sin-hash.
import hou, os, json

OUT = 'C:/EnvironmentPortfolio/BS_GodFile/Saved/Portfolio/wave_violin/copernicus'
os.makedirs(OUT + '/textures', exist_ok=True)

geo = hou.node('/obj').createNode('geo', 'ME_WaveViolin_Copernicus')
cop = geo.createNode('copnet', 'COPERNICUS_NightReel')
src = cop.createNode('constant', 'Canvas_RGB'); src.parm('signature').set('rgb')

BODY = '''@dst.set({expr});'''

def bake(label, expr):
    n = cop.createNode('opencl', 'NR_' + label); n.setInput(0, src)
    k = '''#bind layer !&dst
@KERNEL {
 float2 uv=(convert_float2(@ixy)+0.5f)/convert_float2(@res);
 float x=uv.x*2.f-1.f, y=uv.y*2.f-1.f;
 float r=sqrt(x*x+y*y);
 float px=x*.92f, py=y*.92f;
 float p1=sin(3.14159f*px)*sin(6.28319f*py);
 float p2=sin(6.28319f*px)*sin(3.14159f*py);
 float fa=p1+p2, fb=p1-p2;
 float nodal=clamp(exp(-fabs(fa)*34.f)+exp(-fabs(fb)*34.f),0.f,1.f);
 float edge=smoothstep(.94f,.78f,r);
 float bow=exp(-pow((r-.62f)*11.f,2.f))*.35f;
 float mask=clamp(nodal*edge+bow*edge,0.f,1.f);
 float grain=.5f+.5f*sin(37.1f*uv.x+19.7f*uv.y)*sin(11.3f*uv.x-29.1f*uv.y);
 OUTPUT
}'''.replace('OUTPUT', BODY.replace('{expr}', expr))
    n.parm('kernelcode').set(k)
    rop = cop.createNode('rop_image', 'BAKE_' + label); rop.setInput(0, n)
    path = OUT + f'/textures/T_ME_WaveViolin_{label}.png'
    rop.parm('copoutput').set(path); rop.parm('setres').set(1)
    rop.parmTuple('res').set((1024, 1024)); rop.parm('colorconversion').set('raw')
    try:
        rop.parm('execute').pressButton()
        ok = os.path.isfile(path)
        return {'map': label, 'bytes': os.path.getsize(path) if ok else 0, 'errors': list(n.errors())}
    except Exception as e:
        return {'map': label, 'failure': str(e)}

report = []
report.append(bake('BaseColor', 'mix(mix((float4)(.34f,.16f,.10f,1.f),(float4)(.55f,.30f,.15f,1.f),grain),(float4)(1.f,.78f,.42f,1.f),mask*.85f)'))
report.append(bake('Height', '(float4)(mask,mask,mask,1.f)'))
report.append(bake('Roughness', '(float4)(mix(.62f,.18f,mask),mix(.62f,.18f,mask),mix(.62f,.18f,mask),1.f)'))
report.append(bake('Metallic', '(float4)(mask*.9f,mask*.9f,mask*.9f,1.f)'))
report.append(bake('AO', '(float4)(1.f-mask*.55f,1.f-mask*.55f,1.f-mask*.55f,1.f)'))
report.append(bake('Emissive', '(float4)(mask*.95f,mask*.52f,mask*.16f,1.f)'))
report.append(bake('Iridescence', 'mix((float4)(.8f,.55f,.3f,1.f),(float4)(.45f,.3f,.85f,1.f),mask)'))
report.append(bake('Opacity', '(float4)(1.f-mask*.28f,1.f,1.f,1.f)'))
report.append(bake('ORM', '(float4)(1.f-mask*.55f,mix(.62f,.18f,mask),mask*.9f,1.f)'))

# Normal from Height via slope filter (no binding headaches: analytic derivative)
n = cop.createNode('opencl', 'NR_Normal'); n.setInput(0, src)
k = '''#bind layer !&dst
@KERNEL {
 float2 uv=(convert_float2(@ixy)+0.5f)/convert_float2(@res);
 float s=2.f/1024.f;
 float2 u;
 float fx_p, fx_m, fy_p, fy_m;
 // +X
 u=uv+(float2)(s,0.f); {float x=u.x*2.f-1.f,y=u.y*2.f-1.f;float r=sqrt(x*x+y*y);
  float px=x*.92f,py=y*.92f;float p1=sin(3.14159f*px)*sin(6.28319f*py),p2=sin(6.28319f*px)*sin(3.14159f*py);
  fx_p=clamp(exp(-fabs(p1+p2)*34.f)+exp(-fabs(p1-p2)*34.f),0.f,1.f)*smoothstep(.94f,.78f,r);}
 // -X
 u=uv-(float2)(s,0.f); {float x=u.x*2.f-1.f,y=u.y*2.f-1.f;float r=sqrt(x*x+y*y);
  float px=x*.92f,py=y*.92f;float p1=sin(3.14159f*px)*sin(6.28319f*py),p2=sin(6.28319f*px)*sin(3.14159f*py);
  fx_m=clamp(exp(-fabs(p1+p2)*34.f)+exp(-fabs(p1-p2)*34.f),0.f,1.f)*smoothstep(.94f,.78f,r);}
 // +Y
 u=uv+(float2)(0.f,s); {float x=u.x*2.f-1.f,y=u.y*2.f-1.f;float r=sqrt(x*x+y*y);
  float px=x*.92f,py=y*.92f;float p1=sin(3.14159f*px)*sin(6.28319f*py),p2=sin(6.28319f*px)*sin(3.14159f*py);
  fy_p=clamp(exp(-fabs(p1+p2)*34.f)+exp(-fabs(p1-p2)*34.f),0.f,1.f)*smoothstep(.94f,.78f,r);}
 // -Y
 u=uv-(float2)(0.f,s); {float x=u.x*2.f-1.f,y=u.y*2.f-1.f;float r=sqrt(x*x+y*y);
  float px=x*.92f,py=y*.92f;float p1=sin(3.14159f*px)*sin(6.28319f*py),p2=sin(6.28319f*px)*sin(3.14159f*py);
  fy_m=clamp(exp(-fabs(p1+p2)*34.f)+exp(-fabs(p1-p2)*34.f),0.f,1.f)*smoothstep(.94f,.78f,r);}
 float dx=fx_p-fx_m, dy=fy_p-fy_m;
 float3 nn=normalize((float3)(-dx*14.f,-dy*14.f,1.f));
 @dst.set((float4)(nn*.5f+.5f,1.f));
}'''
n.parm('kernelcode').set(k)
rop = cop.createNode('rop_image', 'BAKE_Normal'); rop.setInput(0, n)
path = OUT + '/textures/T_ME_WaveViolin_Normal.png'
rop.parm('copoutput').set(path); rop.parm('setres').set(1)
rop.parmTuple('res').set((1024, 1024)); rop.parm('colorconversion').set('raw')
try:
    rop.parm('execute').pressButton()
    report.append({'map': 'Normal', 'bytes': os.path.getsize(path) if os.path.isfile(path) else 0, 'errors': list(n.errors())})
except Exception as e:
    report.append({'map': 'Normal', 'failure': str(e)})

cop.layoutChildren(); geo.layoutChildren()
hou.hipFile.save(OUT + '/ME_WaveViolin_Copernicus.hip')
with open(OUT + '/copernicus_violin_audit.json', 'w') as f:
    json.dump(report, f, indent=2)
ok = sum(1 for r_ in report if r_.get('bytes', 0) > 1000 and not r_.get('errors'))
print(f'COPERNICUS_VIOLIN {"PASS" if ok >= 9 else "PARTIAL"} {ok}/9', json.dumps(report)[-600:], flush=True)
