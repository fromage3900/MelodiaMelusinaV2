// Supplemental meso detail only: never changes source Gaea UVs.
// Quintic-interpolated value noise, two octaves, world units in centimeters.
// This is a coverage refinement, not a signed distance field or snow simulation.
struct SnowNoise
{
    float hash(float2 p)
    {
        float3 q=frac(float3(p.xyx)*0.1031);
        q+=dot(q,q.yzx+33.33);
        return frac((q.x+q.y)*q.z);
    }
    float value(float2 p)
    {
        float2 i=floor(p), f=frac(p);
        float2 u=f*f*f*(f*(f*6.0-15.0)+10.0);
        return lerp(lerp(hash(i),hash(i+float2(1,0)),u.x),
                    lerp(hash(i+float2(0,1)),hash(i+float2(1,1)),u.x),u.y)*2.0-1.0;
    }
};
SnowNoise noise;
float2 p=WorldPosition.xy/max(WorldSizeCM,1.0);
float footprint=max(length(ddx(p)),length(ddy(p)));
float a=1.0-smoothstep(0.25,0.75,footprint);
float b=1.0-smoothstep(0.25,0.75,footprint*2.03);
float F=(noise.value(p)*a+0.5*noise.value(p*2.03+float2(17.3,-9.1))*b)/1.5;
float C=saturate(Coverage);
float edge=4.0*C*(1.0-C);
// Preserve original zero-strength values, including legacy additive coverage.
return Coverage + (saturate(C+edge*saturate(Strength)*F)-C);
