"""Drawing the Hollow Oak: the wood (textured, normal-mapped, lit by the lantern, the fungus and a little moon), the
fungus glowing, the moonbeams and the dust in them, the sky through the broken crown, fog pooled low, her silk
(glinting where a light catches it, lost in the dark where none does; shivering when walked on, dipping under him),
her small ones about the den, and - now and then, high in the dark - a cluster of eyes.

    r = Renderer()            (inside a current OpenGL 3.3 context)
    r.draw(night, w, h, now)
"""
import math

from pathlib import Path

import numpy as np
from OpenGL import GL
from PIL import Image

from . import fogfx, gl, held, silkmesh, treemesh
from ..game import tree as T
from ..game import web as W

TEXTURES = Path(__file__).resolve().parents[1] / "assets" / "textures"
LAYERS = ("Bark007", "Ground103", "ScatteredLeaves001")
# each layer's colour, to turn the textures into the inside of an old oak: dark, red-brown, damp
LAYER_TINT = ((0.30, 0.205, 0.15), (0.40, 0.30, 0.235), (0.36, 0.25, 0.18))
MAX_LIGHTS = 16
FOG = (0.018, 0.022, 0.03)

LIGHTING = """
uniform vec3 uEye; uniform vec3 uAmbient; uniform vec3 uMoonDir; uniform vec3 uMoonCol;
uniform int uLightCount; uniform vec4 uLightPos[16]; uniform vec4 uLightCol[16];
uniform vec3 uFog; uniform float uFogDensity;
float moonReach(float y) { return smoothstep(%(TOP)s * 0.35, %(TOP)s + 2.0, y); }
vec3 lit(vec3 p, vec3 n, vec3 base, float shade) {
    vec3 c = uAmbient * shade + uMoonCol * max(dot(n, -uMoonDir), 0.0) * moonReach(p.y) * shade;
    for (int i = 0; i < uLightCount; i++) {
        vec3 d = uLightPos[i].xyz - p; float dist = length(d);
        float att = clamp(1.0 - dist / uLightPos[i].w, 0.0, 1.0); att *= att;
        float ndl = max(dot(n, d / max(dist, 1e-3)), 0.0) * 0.85 + 0.15;
        c += uLightCol[i].rgb * att * ndl;
    }
    return base * c;
}
vec3 fogged(vec3 p, vec3 col) {
    float dist = length(p - uEye);
    float low = 0.22 * exp(-max(p.y, 0.0) / 1.6);                       // (fog pooled at the foot of the hollow)
    float f = 1.0 - exp(-pow((uFogDensity + low) * dist, 1.25));
    return mix(col, uFog, clamp(f, 0.0, 1.0));
}
vec4 outColour(vec3 c) { return vec4(pow(max(c, vec3(0.0)), vec3(1.0 / 2.2)), 1.0); }
""" % {"TOP": f"{T.TOP:.1f}"}

WORLD_VS = """#version 330 core
layout(location=0) in vec3 aPos; layout(location=1) in vec3 aNrm; layout(location=2) in vec2 aUV;
layout(location=3) in float aLayer; layout(location=4) in float aShade;
uniform mat4 uPV;
out vec3 vPos; out vec3 vNrm; out vec2 vUV; flat out float vLayer; out float vShade;
void main() { vPos = aPos; vNrm = aNrm; vUV = aUV; vLayer = aLayer; vShade = aShade; gl_Position = uPV * vec4(aPos, 1.0); }"""

WORLD_FS = """#version 330 core
in vec3 vPos; in vec3 vNrm; in vec2 vUV; flat in float vLayer; in float vShade;
uniform sampler2DArray uTex; uniform sampler2DArray uNrmTex; uniform vec3 uTint[3];
uniform int uDripCount; uniform vec3 uDrips[24];         // (x, z, the floor's height where each drip lands)
out vec4 frag;
""" + LIGHTING + """
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p) { float v = 0.0, a = 0.5; for (int i = 0; i < 4; i++) { v += a * vnoise(p); p = p * 2.07 + 13.3; a *= 0.5; } return v; }
vec3 sheen(vec3 p, vec3 n, float power) {               // (the lights caught in a wet surface)
    vec3 v = normalize(uEye - p), s = vec3(0.0);
    for (int i = 0; i < uLightCount; i++) {
        vec3 d = uLightPos[i].xyz - p; float dist = length(d);
        float att = clamp(1.0 - dist / (uLightPos[i].w * 1.8), 0.0, 1.0);
        s += uLightCol[i].rgb * pow(max(dot(n, normalize(d / max(dist, 1e-3) + v)), 0.0), power) * att;
    }
    return s + uMoonCol * pow(max(dot(n, normalize(-uMoonDir + v)), 0.0), power) * moonReach(p.y) * 2.0;
}
mat3 frame(vec3 N, vec3 p, vec2 uv) {          // (the surface's own axes, from how its position and uv change)
    vec3 dp1 = dFdx(p), dp2 = dFdy(p); vec2 du1 = dFdx(uv), du2 = dFdy(uv);
    vec3 a = cross(dp2, N), b = cross(N, dp1);
    vec3 t = a * du1.x + b * du2.x, bt = a * du1.y + b * du2.y;
    float k = inversesqrt(max(max(dot(t, t), dot(bt, bt)), 1e-12));
    return mat3(t * k, bt * k, N);
}
void main() {
    int L = int(vLayer + 0.5);
    vec3 base = texture(uTex, vec3(vUV, vLayer)).rgb * uTint[L];
    vec3 N = normalize(vNrm);
    if (dot(N, uEye - vPos) < 0.0) N = -N;                              // (lit from the side he sees)
    vec3 m = texture(uNrmTex, vec3(vUV, vLayer)).xyz * 2.0 - 1.0;
    vec3 n = normalize(frame(N, vPos, vUV) * vec3(m.xy * 1.05, m.z));
    float grain = 0.85 + 0.3 * fract(sin(dot(floor(vPos.xz * 3.0 + vPos.y), vec2(12.9898, 78.233))) * 43758.5453);
    base *= mix(1.0, grain, 0.25);
    float wet = 0.0, puddle = 0.0;
    if (N.y > 0.8 && L != 0) {                          // (the floor and the ledge: damp in patches, puddled under the drips)
        float m = fbm(vPos.xz * 0.42 + 3.0);
        wet = smoothstep(0.48, 0.72, m);
        for (int i = 0; i < uDripCount; i++) {
            if (abs(vPos.y - uDrips[i].z) < 0.3) {
                float d = distance(vPos.xz, uDrips[i].xy) + (fbm(vPos.xz * 2.1) - 0.5) * 0.55;
                wet = max(wet, 1.0 - smoothstep(0.35, 1.35, d));
            }
        }
        puddle = smoothstep(0.8, 0.9, wet + (fbm(vPos.xz * 1.3 + 7.0) - 0.5) * 0.25);
        if (vPos.y < 0.2) puddle = max(puddle, smoothstep(0.72, 0.8, fbm(vPos.xz * 0.3 + 11.0)) * 0.9);   // (pools in the bowl)
        base *= mix(1.0, 0.5, wet);
        base = mix(base, base * 0.22 + vec3(0.004, 0.005, 0.007), puddle);
        n = normalize(mix(n, N, puddle));               // (water lies flat over the earth's grain)
    } else if (abs(N.y) < 0.5 && vPos.y < 1.4) {       // (the wall damp at its foot, darker the lower)
        wet = (1.0 - smoothstep(0.0, 1.4, vPos.y)) * smoothstep(0.35, 0.6, fbm(vec2(atan(vPos.z, vPos.x) * 9.0, vPos.y * 1.5)));
        base *= mix(1.0, 0.6, wet);
    }
    vec3 col = lit(vPos, n, base, vShade);
    col += sheen(vPos, n, 30.0) * wet * 0.12 + sheen(vPos, N, 160.0) * puddle * 0.9;
    frag = outColour(fogged(vPos, col));
}"""

DRESS_VS = """#version 330 core
layout(location=0) in vec3 aPos; layout(location=1) in vec3 aNrm; layout(location=2) in vec3 aCol;
uniform mat4 uPV; out vec3 vPos; out vec3 vNrm; out vec3 vCol;
void main() { vPos = aPos; vNrm = aNrm; vCol = aCol; gl_Position = uPV * vec4(aPos, 1.0); }"""

DRESS_FS = """#version 330 core
in vec3 vPos; in vec3 vNrm; in vec3 vCol;
out vec4 frag;
""" + LIGHTING + """
void main() {
    vec3 N = normalize(vNrm);
    if (dot(N, uEye - vPos) < 0.0) N = -N;
    frag = outColour(fogged(vPos, lit(vPos, N, vCol, 0.9)));
}"""

GLOWY_VS = """#version 330 core
layout(location=0) in vec3 aPos; layout(location=1) in vec3 aCol;
uniform mat4 uPV; out vec3 vPos; out vec3 vCol;
void main() { vPos = aPos; vCol = aCol; gl_Position = uPV * vec4(aPos, 1.0); }"""

FUNGUS_VS = """#version 330 core
layout(location=0) in vec3 aPos; layout(location=1) in vec3 aCol; layout(location=2) in vec2 aBreath;
uniform mat4 uPV; out vec3 vPos; out vec3 vCol; flat out vec2 vBreath;
void main() { vPos = aPos; vCol = aCol; vBreath = aBreath; gl_Position = uPV * vec4(aPos, 1.0); }"""

FUNGUS_FS = """#version 330 core
in vec3 vPos; in vec3 vCol; flat in vec2 vBreath; uniform float uTime;
out vec4 frag;
""" + LIGHTING + """
void main() {
    float s = 0.5 + 0.5 * sin(uTime * 6.2831853 / vBreath.x + vBreath.y);
    float pulse = 0.18 + 0.82 * s * s * (3.0 - 2.0 * s);              // (each patch fading almost out, and growing back)
    frag = outColour(fogged(vPos, vCol * pulse * 0.95));
}"""

GLOW_VS = """#version 330 core
layout(location=0) in vec3 aPos; layout(location=1) in vec2 aUV; layout(location=2) in vec4 aCol; layout(location=3) in float aMode;
uniform mat4 uPV; out vec2 vUV; out vec4 vCol; flat out float vMode; out vec3 vPos;
void main() { vUV = aUV; vCol = aCol; vMode = aMode; vPos = aPos; gl_Position = uPV * vec4(aPos, 1.0); }"""

GLOW_FS = """#version 330 core
in vec2 vUV; in vec4 vCol; flat in float vMode; in vec3 vPos; uniform float uTime;
out vec4 frag;
void main() {
    vec2 p = vUV * 2.0 - 1.0; float a;
    if (vMode < 0.5) { float r = length(p); a = pow(max(0.0, 1.0 - r), 2.0) + pow(max(0.0, 1.0 - r * 3.0), 3.0) * 1.5; }
    else if (vMode > 1.5) { float r = length(p); a = smoothstep(0.12, 0.0, abs(r - 0.78)) * smoothstep(1.0, 0.9, r); }
    else { a = pow(max(0.0, 1.0 - abs(p.x)), 1.8) * smoothstep(0.0, 0.3, vUV.y) * smoothstep(1.0, 0.8, vUV.y)
               * (0.8 + 0.2 * sin(uTime * 0.5 + vUV.y * 5.0 + vPos.x)); }
    if (a < 0.003) discard;
    frag = vec4(vCol.rgb * a * vCol.a, 1.0);
}"""

FOG_VS = """#version 330 core
layout(location=0) in vec3 aPos; layout(location=1) in vec2 aUV; layout(location=2) in float aAlpha;
layout(location=3) in float aSeed; layout(location=4) in float aKind;
uniform mat4 uPV; out vec3 vPos; out vec2 vUV; out float vAlpha; out float vSeed; flat out float vKind;
void main() { vPos = aPos; vUV = aUV; vAlpha = aAlpha; vSeed = aSeed; vKind = aKind; gl_Position = uPV * vec4(aPos, 1.0); }"""

FOG_FS = """#version 330 core
in vec3 vPos; in vec2 vUV; in float vAlpha; in float vSeed; flat in float vKind;
uniform float uTime; uniform vec3 uEye; uniform vec4 uLantern; uniform vec3 uLanternCol; uniform float uWallR;
out vec4 frag;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p) { float v = 0.0, a = 0.5; for (int i = 0; i < 4; i++) { v += a * vnoise(p); p = p * 2.03 + 17.1; a *= 0.5; } return v; }
void main() {
    float t = uTime, a;
    if (vKind < 0.5) {                                      // (a layer of ground fog: drifting, thinning at the wall)
        vec2 q = vPos.xz * 0.32 + vec2(t * 0.045, t * 0.028) + vSeed * 9.0;
        float n = fbm(q + vec2(fbm(q * 0.7 + t * 0.02), 0.0) * 1.6);
        a = smoothstep(0.32, 0.8, n) * vAlpha;
        float r = length(vPos.xz);
        a *= 1.0 - smoothstep(uWallR - 2.4, uWallR - 0.4, r);
        float graze = abs(normalize(vPos - uEye).y);         // (seen edge-on, the layers would stack into a wall: thinned)
        a *= mix(0.25, 1.0, smoothstep(0.02, 0.3, graze));
    } else {                                                // (a wisp: a soft patch of mist, its edge torn by the noise)
        vec2 p = vUV * 2.0 - 1.0;
        float n = fbm(vUV * 2.2 + vSeed * 13.0 + vec2(t * 0.03, -t * 0.02));
        a = (1.0 - smoothstep(0.25, 1.0, length(p) + (n - 0.5) * 0.55)) * smoothstep(0.25, 0.75, n) * vAlpha;
    }
    float d = distance(vPos, uEye);
    a *= smoothstep(0.35, 2.2, d) * exp(-d * 0.028);        // (never a flat sheet across his face; lost in the far dark)
    if (a < 0.004) discard;
    float l = clamp(1.0 - distance(vPos, uLantern.xyz) / uLantern.w, 0.0, 1.0);
    vec3 col = vec3(0.07, 0.08, 0.095) + uLanternCol * l * l * 0.42 + vec3(0.06, 0.07, 0.11) * smoothstep(12.0, 30.0, vPos.y);
    frag = vec4(pow(col, vec3(1.0 / 2.2)), a);
}"""

SILK_VS = """#version 330 core
layout(location=0) in vec3 aPos; layout(location=1) in vec3 aTan; layout(location=2) in float aSide;
layout(location=3) in float aWidth; layout(location=4) in float aGroup; layout(location=5) in float aFree;
layout(location=6) in float aPhase;
uniform mat4 uPV; uniform vec3 uEye; uniform float uTime; uniform float uAmp[8]; uniform vec4 uDip; uniform float uDipGroup;
uniform float uPixel;
out vec3 vPos; out vec3 vTan; out float vCover;
void main() {
    int g = int(aGroup + 0.5);
    vec3 p = aPos;
    float shiver = sin(uTime * (11.0 + aPhase) + aPhase * 7.0 + aPos.x * 1.3 + aPos.z * 1.1);
    p.y += aFree * (uAmp[g] * shiver * 0.05 + 0.01 * sin(uTime * 0.7 + aPhase * 5.0));     // (shaking; and breathing)
    if (g >= 5) p.xz += aFree * 0.05 * vec2(sin(uTime * 0.5 + aPhase), cos(uTime * 0.43 + aPhase * 1.7));   // (drifting)
    if (abs(aGroup - uDipGroup) < 0.5) {                                 // (his weight, where he stands)
        float d = distance(p.xz, uDip.xz);
        p.y -= uDip.w * aFree * exp(-d * d / 1.4);
    }
    vec3 v = normalize(p - uEye);
    vec3 s = normalize(cross(aTan, v) + vec3(1e-5));
    float w = max(aWidth, uPixel * length(p - uEye) * 1.1);               // (never thinner than a pixel: fainter instead)
    vCover = aWidth / w;
    p += s * aSide * w * 0.5;
    vPos = p; vTan = aTan;
    gl_Position = uPV * vec4(p, 1.0);
}"""

SILK_FS = """#version 330 core
in vec3 vPos; in vec3 vTan; in float vCover;
uniform vec3 uEye; uniform vec3 uAmbient; uniform vec3 uMoonDir; uniform vec3 uMoonCol;
uniform int uLightCount; uniform vec4 uLightPos[16]; uniform vec4 uLightCol[16]; uniform float uFogDensity;
uniform float uWhite;
out vec4 frag;
float strand(vec3 T, vec3 L, vec3 V, float power) {          // (a thread's light: along its length, never flat)
    vec3 H = normalize(L + V); float th = dot(T, H);
    return pow(sqrt(max(0.0, 1.0 - th * th)), power);
}
void main() {
    vec3 T = normalize(vTan), V = normalize(uEye - vPos);
    vec3 c = uAmbient * 0.7;
    for (int i = 0; i < uLightCount; i++) {
        vec3 d = uLightPos[i].xyz - vPos; float dist = length(d);
        float att = clamp(1.0 - dist / uLightPos[i].w, 0.0, 1.0); att *= att * att;
        vec3 L = d / max(dist, 1e-3);
        float diff = sqrt(max(0.0, 1.0 - pow(dot(T, L), 2.0)));
        c += uLightCol[i].rgb * att * (diff * 0.16 + strand(T, L, V, 400.0) * 0.9);
    }
    float moon = smoothstep(%(TOP)s * 0.35, %(TOP)s + 2.0, vPos.y);
    c += uMoonCol * moon * moon * (0.45 + strand(T, -uMoonDir, V, 160.0) * 2.8);     // (silver, under the moon)
    float dist = length(vPos - uEye);
    float low = 0.22 * exp(-max(vPos.y, 0.0) / 1.6);
    c *= exp(-pow((uFogDensity + low) * dist, 1.25));                    // (lost in the fog, far off)
    c += vec3(0.5, 0.52, 0.56) * uWhite;                                  // (fresh silk, close: white)
    c *= vec3(0.86, 0.9, 1.0) * vCover;
    frag = vec4(max(c, vec3(0.0)) * 1.6, 1.0);         // (added as it is: faint threads stay faint, glints stand out)
}""" % {"TOP": f"{T.TOP:.1f}"}

SPIDER_VS = """#version 330 core
layout(location=0) in vec3 aPos; layout(location=1) in vec3 aNrm; layout(location=2) in vec3 aCol;
uniform mat4 uPV; uniform mat4 uModel; out vec3 vPos; out vec3 vNrm; out vec3 vCol;
void main() { vec4 p = uModel * vec4(aPos, 1.0); vPos = p.xyz; vNrm = normalize(mat3(uModel) * aNrm); vCol = aCol;
              gl_Position = uPV * p; }"""

SPIDER_FS = """#version 330 core
in vec3 vPos; in vec3 vNrm; in vec3 vCol;
uniform float uRim;
out vec4 frag;
""" + LIGHTING + """
void main() {
    vec3 N = normalize(vNrm);
    if (dot(N, uEye - vPos) < 0.0) N = -N;
    vec3 col = lit(vPos, N, vCol * 2.2, 1.0);
    col += vec3(0.3, 0.34, 0.44) * pow(1.0 - abs(dot(N, normalize(uEye - vPos))), 2.0) * uRim;   // (an edge of the den's light)
    vec3 V = normalize(uEye - vPos);
    for (int i = 0; i < uLightCount; i++) {                    // (a hard shine on the chitin)
        vec3 d = uLightPos[i].xyz - vPos; float dist = length(d);
        float att = clamp(1.0 - dist / uLightPos[i].w, 0.0, 1.0);
        col += uLightCol[i].rgb * att * att * pow(max(dot(N, normalize(d / max(dist, 1e-3) + V)), 0.0), 30.0) * 1.1;
    }
    if (vCol.r > 0.15 && vCol.g < 0.06) {                      // (the eyes: they catch any light there is)
        float shine = 0.0;
        for (int i = 0; i < uLightCount; i++) shine += clamp(1.0 - distance(uLightPos[i].xyz, vPos) / uLightPos[i].w, 0.0, 1.0);
        col += vec3(0.9, 0.12, 0.05) * (0.03 + shine * 1.2 + uRim * 0.6);
    }
    frag = outColour(fogged(vPos, col));
}"""

CRAWLER_FS = """#version 330 core
in vec3 vPos; in vec3 vNrm; in vec3 vCol;
uniform float uLamp;
out vec4 frag;
void main() {                                                   // (on his eyes: lit from behind him by the lantern)
    vec3 N = normalize(vNrm);
    if (N.z < 0.0) N = -N;
    vec3 L = normalize(vec3(0.35, -0.45, 0.8));
    float d = max(dot(N, L), 0.0);
    float spec = pow(max(dot(N, normalize(L + vec3(0.0, 0.0, 1.0))), 0.0), 24.0);
    vec3 warm = vec3(1.0, 0.72, 0.45);
    vec3 c = vCol * (0.25 + 2.2 * d * uLamp) * warm + warm * spec * (0.06 + 0.5 * uLamp);
    if (vCol.r > 0.15 && vCol.g < 0.06) c = vec3(0.9, 0.12, 0.05) * (0.25 + 0.9 * uLamp);
    frag = vec4(pow(max(c, vec3(0.0)), vec3(1.0 / 2.2)), 1.0);
}"""

SKY_VS = """#version 330 core
layout(location=0) in vec2 aP; out vec2 vP; void main() { vP = aP; gl_Position = vec4(aP, 0.9999, 1.0); }"""
SKY_FS = """#version 330 core
in vec2 vP; uniform mat4 uInvPV; uniform vec3 uMoon; uniform float uTime; out vec4 frag;
float hash(vec3 p) { return fract(sin(dot(p, vec3(12.9898, 78.233, 45.164))) * 43758.5453); }
vec3 aurora(vec3 d, float t) {
    // curtains of light strung across the sky: each a wavering line on the sky's plane, drawn as several layers one
    // above another (green low, violet high) so it has height; rays shimmering along it; slow, faint, breathing
    if (d.y < 0.08) return vec3(0.0);
    vec3 c = vec3(0.0);
    for (int k = 0; k < 2; k++) {
        float off = float(k) * 1.15 - 0.35;
        for (int i = 0; i < 6; i++) {
            float f = float(i);
            vec2 uv = d.xz / d.y / (1.0 + f * 0.1);                        // (a plane higher for each layer)
            float x = uv.x;
            float line = off + 0.55 * sin(x * 0.32 + t * 0.028 + float(k) * 2.0) + 0.22 * sin(x * 0.85 - t * 0.045)
                       + 0.06 * sin(x * 2.3 + t * 0.09);
            float dist = abs(uv.y - line);
            float band = exp(-pow(dist / (0.05 + f * 0.012), 2.0));
            float rays = 0.45 + 0.55 * pow(0.5 + 0.5 * sin(x * 26.0 + sin(x * 2.7 + t * 0.17) * 2.5 + t * 0.23), 2.0);
            float breathe = 0.6 + 0.4 * sin(t * 0.08 + x * 0.4 + float(k) * 2.4);
            vec3 tint = mix(vec3(0.12, 0.95, 0.5), vec3(0.6, 0.22, 0.85), smoothstep(0.0, 5.0, f));
            c += tint * band * rays * breathe * 0.021 * (1.0 - f * 0.11);
        }
    }
    return c * smoothstep(0.08, 0.35, d.y) * exp(-length(d.xz / d.y) * 0.12);
}
void main() {
    vec4 a = uInvPV * vec4(vP, -1.0, 1.0), b = uInvPV * vec4(vP, 1.0, 1.0);
    vec3 d = normalize(b.xyz / b.w - a.xyz / a.w);
    vec3 col = mix(vec3(0.0015, 0.002, 0.004), vec3(0.003, 0.0045, 0.01), smoothstep(0.0, 1.0, d.y));
    vec3 q = floor(d * 380.0); float s = hash(q);
    col += vec3(0.55, 0.6, 0.75) * step(0.9975, s) * smoothstep(0.1, 0.5, d.y) * (0.4 + 0.6 * hash(q + 3.0))
         * (0.75 + 0.25 * sin(uTime * (1.0 + 3.0 * hash(q + 7.0)) + hash(q) * 30.0));      // (the stars, twinkling)
    col += aurora(d, uTime);
    float m = dot(d, normalize(uMoon));
    col += vec3(0.75, 0.78, 0.9) * smoothstep(0.9994, 0.9997, m) + vec3(0.08, 0.09, 0.14) * pow(max(m, 0.0), 260.0);
    frag = vec4(pow(col, vec3(1.0 / 2.2)), 1.0);
}"""


class Renderer:
    def __init__(self):
        self.tree = T.Tree()
        self.world = gl.Program(WORLD_VS, WORLD_FS)
        self.fung = gl.Program(FUNGUS_VS, FUNGUS_FS)
        self.glow = gl.Program(GLOW_VS, GLOW_FS)
        self.sky = gl.Program(SKY_VS, SKY_FS)
        self.fog = gl.Program(FOG_VS, FOG_FS)
        self.fog_mesh = gl.Mesh([(0, 3), (1, 2), (2, 1), (3, 1), (4, 1)], dynamic=True)
        self.wisps = fogfx.wisps(self.tree)
        self.fog_on = True
        colours = [Image.open(TEXTURES / f"{n}.color.jpg") for n in LAYERS]
        normals = [Image.open(TEXTURES / f"{n}.normal.jpg") for n in LAYERS]
        self.tex = gl.texture_array(colours, 512)
        self.ntex = gl.texture_array(normals, 512, srgb=False)
        from ..game.den import Den
        self.den = Den(self.tree)
        self.mesh = gl.Mesh([(0, 3), (1, 3), (2, 2), (3, 1), (4, 1)], treemesh.world(self.tree, self.den))
        self.dress_prog = gl.Program(DRESS_VS, DRESS_FS)
        self.dress = gl.Mesh([(0, 3), (1, 3), (2, 3)], treemesh.dress(self.den))
        self.held_parts = held.parts()
        self.wand_parts, _tip = held.wand_parts()
        self.wand_mesh = gl.Mesh([(0, 3), (1, 3), (2, 3)], dynamic=True)
        self.held_mesh = gl.Mesh([(0, 3), (1, 3), (2, 3)], dynamic=True)
        self._held_at = (0.0, None)
        drips = self.den.drips[:24]
        self.drip_uniform = np.array([(x, z, b) for x, _t, z, b in drips], np.float32)
        fv, self.fungus_lights = treemesh.fungus(self.tree)
        self.fungus = gl.Mesh([(0, 3), (1, 3), (2, 2)], fv)
        self.beams = treemesh.shafts(self.tree)
        self.glow_mesh = gl.Mesh([(0, 3), (1, 2), (2, 4), (3, 1)], dynamic=True)
        self.sky_mesh = gl.Mesh([(0, 2)], np.array([[-1, -1], [1, -1], [1, 1], [-1, -1], [1, 1], [-1, 1]], np.float32))
        self.web = W.Web(self.tree)
        self.silk_prog = gl.Program(SILK_VS, SILK_FS)
        self.silk = gl.Mesh([(0, 3), (1, 3), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1)], silkmesh.silk(self.web))
        self.amp = np.zeros(W.GROUPS, np.float32)
        self.spider_prog = gl.Program(SPIDER_VS, SPIDER_FS)
        sv, self.spider_clips, self.spider_n = silkmesh.spider_frames()
        self.spiders = gl.Mesh([(0, 3), (1, 3), (2, 3)], sv)
        self.crawler_prog = gl.Program(SPIDER_VS, CRAWLER_FS)
        self.loose = gl.Mesh([(0, 3), (1, 3), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1)], dynamic=True)
        _w, self.wand_tip = held.wand_parts()
        self.hand_parts = held.arm_parts() + held.hand_parts()
        self.hand_mesh = gl.Mesh([(0, 3), (1, 3), (2, 3)], dynamic=True)
        self.moon = np.array((0.35, 1.0, -0.25), np.float32)
        self.moon /= np.linalg.norm(self.moon)

    # ---- a frame ---------------------------------------------------------------------------------------------
    def draw(self, night, w, h, now):
        GL.glViewport(0, 0, w, h)
        GL.glClearColor(*FOG, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glEnable(GL.GL_DEPTH_TEST)                         # (what the painter over the view may have left: undone)
        GL.glDepthFunc(GL.GL_LESS)
        GL.glDepthMask(GL.GL_TRUE)
        GL.glDisable(GL.GL_BLEND)
        GL.glDisable(GL.GL_SCISSOR_TEST)
        GL.glDisable(GL.GL_STENCIL_TEST)
        GL.glColorMask(GL.GL_TRUE, GL.GL_TRUE, GL.GL_TRUE, GL.GL_TRUE)
        GL.glDisable(GL.GL_CULL_FACE)
        eye = night.eye
        proj = gl.perspective(70.0, w / max(1, h), 0.05, 160.0)
        view = gl.view_matrix(eye, night.yaw, night.pitch)
        roll = getattr(night, "sway", 0.0) * 0.2                # (his lean, on a strand)
        if roll:
            c, s = math.cos(roll), math.sin(roll)
            view = np.array(((c, s, 0, 0), (-s, c, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)), np.float32) @ view
        pv = proj @ view
        self.pv = pv
        self._view = view
        self.now = now
        self._held_at = (now, held.hold(night, now))
        # the sky, behind everything (seen only up through the crown)
        GL.glDepthMask(GL.GL_FALSE)
        self.sky.use()
        self.sky.mat4("uInvPV", np.linalg.inv(pv))
        self.sky.vec("uMoon", self.moon)
        self.sky.float("uTime", now)
        self.sky_mesh.draw()
        GL.glDepthMask(GL.GL_TRUE)
        lights = self._lights(night, now)
        for prog in (self.world, self.fung, self.dress_prog, self.spider_prog, self.silk_prog):
            prog.use()
            prog.mat4("uPV", pv)
            prog.vec("uEye", eye)
            dim = 0.3 + 0.7 * min(1.0, night.lamp.level) if night.lantern else 1.0     # (the lamp's own bounce)
            prog.vec("uAmbient", (0.022 * dim, 0.02 * dim, 0.026 * dim))
            prog.vec("uMoonDir", -self.moon)
            prog.vec("uMoonCol", (0.11, 0.13, 0.2))
            prog.vec("uFog", [c ** 2.2 for c in FOG])
            prog.float("uFogDensity", 0.045)
            prog.int("uLightCount", len(lights))
            if lights:
                prog.vec4s("uLightPos", [l[0] for l in lights])
                prog.vec4s("uLightCol", [l[1] for l in lights])
        self.world.use()
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D_ARRAY, self.tex)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D_ARRAY, self.ntex)
        self.world.int("uTex", 0)
        self.world.int("uNrmTex", 1)
        GL.glUniform3fv(self.world.loc("uTint"), 3, np.array(LAYER_TINT, np.float32))
        self.world.int("uDripCount", len(self.drip_uniform))
        GL.glUniform3fv(self.world.loc("uDrips"), len(self.drip_uniform), self.drip_uniform)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        self.mesh.draw()
        self.dress_prog.use()
        self.dress.draw()
        self.fung.use()
        self.fung.float("uTime", now)
        self.fungus.draw()
        self._spiders(night)
        self._silk(night, now, proj, h)
        self._glows(night, view, now)
        if self.fog_on:
            self._fog(night, view, now, lights)
        if night is not None and getattr(night, "show_lantern", True):
            self._lantern(night, now)
        self._crawlers(night, w, h)
        self._hand(night)

    def _hand(self, night):
        """His left hand, swiping them off his face: over everything, them too."""
        crawlers = getattr(night, "crawlers", None)
        s = crawlers.swipe_phase() if crawlers is not None and getattr(night, "show_lantern", True) else None
        if s is None:
            return
        wrist, axes = held.swipe(night, s)
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
        self.hand_mesh.upload(held.place(self.hand_parts, wrist, axes))
        self.dress_prog.use()
        self.hand_mesh.draw()

    def _crawlers(self, night, w, h):
        """The small ones running across his eyes: drawn flat on the view, over everything, seen from above."""
        crawlers = getattr(night, "crawlers", None)
        runs = crawlers.active() if crawlers is not None and getattr(night, "show_lantern", True) else []
        if not runs:
            return
        aspect = w / max(1, h)
        ortho = np.array(((1 / aspect, 0, 0, 0), (0, 1, 0, 0), (0, 0, -0.5, 0), (0, 0, 0, 1)), np.float32)
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
        self.crawler_prog.use()
        self.crawler_prog.mat4("uPV", ortho)
        self.crawler_prog.float("uLamp", min(1.0, night.lamp.level) if night.lantern else 0.0)
        first, frames, fps = self.spider_clips["walk"]
        for u, v, du, dv, size, t in runs:
            x, y = (u * 2 - 1) * aspect, v * 2 - 1
            fx, fy = du * 2 * aspect, dv * 2
            n = math.hypot(fx, fy) or 1.0
            fx, fy = fx / n, fy / n
            s = size * 2                                       # (a share of the screen's height: in view units)
            m = np.identity(4, np.float32)
            m[:3, 0] = (-fy * s, fx * s, 0)                     # (its right)
            m[:3, 1] = (0, 0, s)                                # (its back, toward him)
            m[:3, 2] = (fx * s, fy * s, 0)                      # (the way it runs)
            m[:3, 3] = (x, y, 0)
            self.crawler_prog.mat4("uModel", m)
            self.spiders.draw_range((first + int(t * fps) % frames) * self.spider_n, self.spider_n)

    def _spiders(self, night):
        """Her small ones, each in its own place and pose, a frame of its walk or its stillness."""
        brood = getattr(night, "brood", None)
        if brood is None:
            return
        self.spider_prog.use()
        self.spider_prog.float("uRim", 0.0)
        eye = np.array(night.eye)
        look = np.array((math.sin(night.yaw), 0.0, -math.cos(night.yaw)))
        for pos, fwd, up, size, clip, t in brood.near(night.eye):
            p = np.array(pos)
            to = p - eye
            if float(np.dot(to, look)) < -0.5 and float(np.linalg.norm(to)) > 1.0:
                continue
            self._spider(p, fwd, up, size, clip, t)
        self.spider_prog.float("uRim", 0.3)
        for x, y, z, top, size, ph in night.danglers.active():  # (hanging before him: its back to him, turning a little)
            to = eye - np.array((x, y, z))
            ang = math.atan2(to[2], to[0]) + 0.5 * math.sin(self.now * 0.7 + ph)
            self._spider(self._dangle(x, y, z, ph), (0.0, -1.0, 0.0), (math.cos(ang), 0.0, math.sin(ang)), size, "idle",
                         self.now + ph)

    def _dangle(self, x, y, z, ph):
        """Where a dangler is this moment: bobbing on its thread, swinging a little."""
        t = self.now
        return np.array((x + 0.02 * math.sin(t * 0.9 + ph), y + 0.025 * math.sin(t * 1.7 + ph * 2),
                         z + 0.02 * math.cos(t * 0.8 + ph)))

    def _spider(self, p, fwd, up, size, clip, t):
        up = np.asarray(up, np.float64)
        up = up / (float(np.linalg.norm(up)) or 1.0)
        f = np.asarray(fwd, np.float64) - up * float(np.dot(fwd, up))
        f /= float(np.linalg.norm(f)) or 1.0
        right = np.cross(up, f)
        m = np.identity(4, np.float32)
        m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = right * size, up * size, f * size, p
        first, frames, fps = self.spider_clips[clip]
        k = first + int(t * fps) % frames
        self.spider_prog.mat4("uModel", m)
        self.spiders.draw_range(k * self.spider_n, self.spider_n)

    def _silk(self, night, now, proj, h):
        """Every thread: added over what's behind it, as light caught in it."""
        web_on = getattr(night, "on", None)
        tremor = getattr(night, "tremor", 0.0)
        target = np.full(W.GROUPS, 0.04, np.float32)
        if web_on is not None:
            target[web_on.group] = min(2.5, 0.25 + tremor * 0.6)
            for b in range(5):                                  # (all her silk is one thing: the rest feel it too)
                if b != web_on.group:
                    target[b] = max(target[b], min(1.0, tremor * 0.12))
        self.amp += (target - self.amp) * 0.15
        self.silk_prog.use()
        self.silk_prog.float("uTime", now)
        self.silk_prog.float("uWhite", 0.0)
        GL.glUniform1fv(self.silk_prog.loc("uAmp"), W.GROUPS, self.amp)
        if web_on is not None:
            self.silk_prog.vec4s("uDip", [(night.x, night.y, night.z, W.DIP)])
            self.silk_prog.float("uDipGroup", float(web_on.group))
        else:
            self.silk_prog.float("uDipGroup", -1.0)
        self.silk_prog.float("uPixel", 2.0 / (max(1, h) * float(proj[1, 1])))
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_ONE, GL.GL_ONE)
        GL.glDepthMask(GL.GL_FALSE)
        self.silk.draw()
        threads = []
        for x, y, z, top, size, ph in night.danglers.active():
            p = self._dangle(x, y, z, ph)
            threads.append(([(x, top, z), (p[0], p[1] + size * 0.25, p[2])], 0.003, 7, [0.0, 0.0], 0.0))
        if threads:
            self.silk_prog.float("uWhite", 0.14)
            self.loose.upload(silkmesh.ribbons(threads))
            self.loose.draw()
        GL.glDepthMask(GL.GL_TRUE)
        GL.glDisable(GL.GL_BLEND)

    def flame_at(self, night):
        now = getattr(self, "now", 0.0)
        if self._held_at[0] != now or self._held_at[1] is None:
            self._held_at = (now, held.hold(night, now))
        return tuple(held.flame(*self._held_at[1][1]))

    def _lantern(self, night, now):
        """The lantern in his hand, drawn over everything (it's never inside a wall), and its flame."""
        if not night.lantern:
            return
        (grip, waxes), (origin, axes) = self._held_at[1] if self._held_at[1] is not None else held.hold(night, now)
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
        self.wand_mesh.upload(held.place(self.wand_parts, grip, waxes))
        self.held_mesh.upload(held.place(self.held_parts, origin, axes))
        self.dress_prog.use()
        self.wand_mesh.draw()
        self.held_mesh.draw()
        self._swarm(night, (grip, waxes), (origin, axes), now)
        lvl = night.lamp.level
        f = held.flame(origin, axes)
        verts = []
        right, up = self._view[0, :3], self._view[1, :3]
        for size, col, a in ((0.012 + 0.008 * lvl, (1.0, 0.92, 0.7), 1.6 * lvl), (0.03, (1.0, 0.6, 0.25), 1.1 * lvl),
                             (0.1, (1.0, 0.5, 0.2), 0.35 * lvl), (0.006, (1.0, 0.25, 0.08), 0.9)):
            r, u = right * size, up * size * (1.4 if size < 0.04 else 1.0)
            corners = (f - r - u, f + r - u, f + r + u, f - r + u)
            for i, uv in zip((0, 1, 2, 0, 2, 3), ((0, 0), (1, 0), (1, 1), (0, 0), (1, 1), (0, 1))):
                verts.append((*corners[i], *uv, *col, a, 0.0))
        self.glow_mesh.upload(np.array(verts, np.float32))
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_ONE, GL.GL_ONE)
        GL.glDepthMask(GL.GL_FALSE)
        self.glow.use()
        self.glow.mat4("uPV", self.pv)
        self.glow.float("uTime", now)
        self.glow_mesh.draw()
        GL.glDepthMask(GL.GL_TRUE)
        GL.glDisable(GL.GL_BLEND)

    def _swarm(self, night, wand, lantern, now):
        """The babies on his wand and his lantern; and those letting go, each on a thread of white silk."""
        swarm = getattr(night, "swarm", None)
        if swarm is None or not swarm.babies:
            return
        (grip, wx), (ring, la) = wand, lantern
        W = np.stack(wx, axis=1)
        tip = W @ np.asarray(self.wand_tip, np.float64)
        along = tip / (float(np.linalg.norm(tip)) or 1.0)

        def on_wand(s):
            return grip + tip * (0.3 + 0.7 * s) + wx[0] * 0.012

        def on_lantern(phi, hh):
            return ring + la[0] * math.cos(phi) * 0.05 + la[1] * hh + la[2] * math.sin(phi) * 0.05
        self.spider_prog.use()
        self.spider_prog.float("uRim", 0.4)
        threads = []
        for b in swarm.babies:
            size = b["size"]
            if b["state"] == "wand":
                self._spider(on_wand(b["s"]), along, wx[0], size, "walk", b["anim"])
                continue
            if b["state"] == "lantern":
                phi = b["phi"]
                out = la[0] * math.cos(phi) + la[2] * math.sin(phi)
                tangent = -la[0] * math.sin(phi) + la[2] * math.cos(phi)
                f = tangent * math.cos(b["head"]) + la[1] * math.sin(b["head"])
                self._spider(on_lantern(phi, b["h"]), f, out, size, "idle" if b["rest"] > 0 else "walk", b["anim"])
                continue
            if b["state"] == "hang":
                anchor = on_wand(b["h"]) if b["phi"] is None else on_lantern(b["phi"], b["h"])
                sw = 0.4 * math.sin(now * 2.6 + b["seed"] * 6.0) * (1.0 if b["len"] >= b["reach"] else b["len"] / b["reach"])
                body = anchor + la[0] * math.sin(sw) * b["len"] - np.array((0.0, 1.0, 0.0)) * math.cos(sw) * b["len"]
                b["drop_from"] = (anchor, body)
            else:
                a0, b0 = b.get("drop_from", (ring, ring))
                drop = np.array((0.0, b["fall"], 0.0))
                anchor, body = a0 - drop, b0 - drop
            to = np.asarray(night.eye) - body
            self._spider(body, (0.0, -1.0, 0.0), (to[0], 0.0, to[2]), size, "idle", b["anim"])
            threads.append(([tuple(anchor), tuple(body + np.array((0.0, size * 0.25, 0.0)))], 0.0012, 7, [0.0, 0.0], 0.0))
        if threads:
            self.silk_prog.use()
            self.silk_prog.float("uWhite", 0.3)
            GL.glEnable(GL.GL_BLEND)
            GL.glBlendFunc(GL.GL_ONE, GL.GL_ONE)
            GL.glDepthMask(GL.GL_FALSE)
            self.loose.upload(silkmesh.ribbons(threads))
            self.loose.draw()
            GL.glDepthMask(GL.GL_TRUE)
            GL.glDisable(GL.GL_BLEND)

    def _lights(self, night, now):
        ex, ey, ez = night.eye
        out = []
        if night.lantern:                                     # (his lantern: from its flame, as bright as the lamp allows)
            reach, k = night.lantern_reach()
            fx, fy, fz = self.flame_at(night)
            out.append(((fx, fy, fz, max(0.6, reach)), (0.6 * k, 0.39 * k, 0.22 * k, 1)))
        near = sorted(self.fungus_lights, key=lambda l: (l[0] - ex) ** 2 + (l[1] - ey) ** 2 + (l[2] - ez) ** 2)
        for l in near[:MAX_LIGHTS - len(out) - 3]:
            k = treemesh.glow_level(now, l[7], l[8]) * 0.8
            out.append(((l[0], l[1], l[2], l[6]), (l[3] * k, l[4] * k, l[5] * k, 1)))
        for start, end, width in sorted(self.beams, key=lambda b: float(np.sum((b[1] - np.array(night.eye)) ** 2)))[:3]:
            out.append(((*end, 4.5), (0.1, 0.12, 0.18, 1)))   # (where a moonbeam falls, a little light)
        return out[:MAX_LIGHTS]

    def _fog(self, night, view, now, lights):
        """The ground fog's layers and the wisps of mist, drawn last, farthest first, over what's behind them."""
        eye = np.array(night.eye, np.float32)
        verts = []
        R = T.R0 + 1.2
        for k, (y, thick) in enumerate(fogfx.LAYERS):           # (the layers: a square over the hollow's floor)
            corners = ((-R, y, -R), (R, y, -R), (R, y, R), (-R, y, R))
            _fog_quad(verts, corners, thick, k * 0.37, 0.0)
        right, up = view[0, :3], view[1, :3]
        placed = []
        for w in self.wisps:
            p = np.array(fogfx.wisp_at(w, now), np.float32)
            placed.append((float(np.sum((p - eye) ** 2)), p, w))
        placed.sort(key=lambda x: -x[0])
        for _d, p, w in placed:
            r, u = right * w["size"], up * w["size"] * 0.55
            _fog_quad(verts, (p - r - u, p + r - u, p + r + u, p - r + u), w["alpha"], w["seed"], 1.0)
        self.fog_mesh.upload(np.array(verts, np.float32))
        lan = lights[0] if night.lantern and lights else ((0, -99, 0, 1), (0, 0, 0, 1))
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glDepthMask(GL.GL_FALSE)
        self.fog.use()
        self.fog.mat4("uPV", self.pv)
        self.fog.float("uTime", now)
        self.fog.vec("uEye", eye)
        self.fog.vec("uLantern", lan[0])
        self.fog.vec("uLanternCol", lan[1][:3])
        self.fog.float("uWallR", T.R0 * 0.97)
        self.fog_mesh.draw()
        GL.glDepthMask(GL.GL_TRUE)
        GL.glDisable(GL.GL_BLEND)

    def _glows(self, night, view, now):
        verts = []
        right, up = view[0, :3], view[1, :3]

        def bill(p, size, c, a):
            r, u = right * size, up * size
            p = np.asarray(p, np.float32)
            corners = (p - r - u, p + r - u, p + r + u, p - r + u)
            for i, uv in zip((0, 1, 2, 0, 2, 3), ((0, 0), (1, 0), (1, 1), (0, 0), (1, 1), (0, 1))):
                verts.append((*corners[i], *uv, *c, a, 0.0))
        eye = np.array(night.eye, np.float32)
        # the moonbeams: soft columns turned to face him
        for start, end, width in self.beams:
            axis = end - start
            side = np.cross(axis, start - eye)
            n = float(np.linalg.norm(side)) or 1.0
            side = side / n * width
            quad = (end - side * 1.6, end + side * 1.6, start + side * 0.6, start - side * 0.6)
            for i, uv in zip((0, 1, 2, 0, 2, 3), ((0, 0), (1, 0), (1, 1), (0, 0), (1, 1), (0, 1))):
                verts.append((*quad[i], *uv, 0.5, 0.58, 0.8, 0.55, 1.0))
            for m in range(6):                                # (dust turning in the beam)
                ph = (now * 0.04 + m * 0.17 + float(start[1]) * 0.1) % 1.0
                p = start + axis * ph + side * 0.6 * math.sin(now * 0.3 + m * 2.0)
                bill(p, 0.025, (0.75, 0.8, 1.0), 0.8 * math.sin(ph * math.pi))
        # the fungus: a soft halo about each cluster
        for l in self.fungus_lights:
            bill((l[0], l[1], l[2]), 1.3, treemesh.GLOW, 0.42 * treemesh.glow_level(now, l[7], l[8]))
        # water, dripping: a drop falls, then a ring spreads where it lands
        for k, (x, top, z, bottom) in enumerate(self.den.drips):
            if (x - eye[0]) ** 2 + (z - eye[2]) ** 2 > 400:
                continue
            period = 1.6 + (k * 0.37) % 1.4
            ph = (now / period + k * 0.618) % 1.0
            if ph < 0.75:
                f = ph / 0.75
                bill((x, top - (top - bottom) * f * f, z), 0.022, (0.55, 0.65, 0.8), 0.9)
            else:
                f = (ph - 0.75) / 0.25
                size = 0.08 + f * 0.32
                corners = ((x - size, bottom + 0.012, z - size), (x + size, bottom + 0.012, z - size),
                           (x + size, bottom + 0.012, z + size), (x - size, bottom + 0.012, z + size))
                for i, uv in zip((0, 1, 2, 0, 2, 3), ((0, 0), (1, 0), (1, 1), (0, 0), (1, 1), (0, 1))):
                    verts.append((*corners[i], *uv, 0.45, 0.55, 0.7, 0.8 * (1 - f), 2.0))
        # the small ones' eyes, low in the dark: a few red points, close together, that blink
        for pos, alpha, count, seed in night.lurking():
            for k in range(count):
                row = k // 2
                ox = ((k % 2) - 0.5) * 0.085 + (seed - 0.5) * 0.03 * row
                oy = -row * 0.05
                p = np.array(pos, np.float32) + right * ox + up * oy
                bill(p, 0.045 if row == 0 else 0.033, (1.0, 0.25, 0.12), alpha * (1.4 if row == 0 else 0.9))
            bill(np.array(pos, np.float32), 0.22, (0.5, 0.08, 0.04), alpha * 0.18)      # (a faint red haze about them)
        # the way out, behind him: night air through the roots
        tx, tz = self.tree.tunnel_point(T.TUNNEL_LEN - 0.05, 0.0)
        bill((tx, self.tree.tunnel_floor(T.TUNNEL_LEN) + 0.8, tz), 0.9, (0.35, 0.45, 0.7), 0.5)
        # her eyes, high in the dark: eight small lights that watch, and are gone when he comes close
        for e in night.eyes():
            for k in range(8):
                ox = (k % 4 - 1.5) * 0.09 + (0.03 if k >= 4 else 0)
                oy = (0.06 if k < 4 else -0.04) - abs(k % 4 - 1.5) * 0.02
                p = np.array(e["pos"], np.float32) + right * ox + up * oy
                bill(p, 0.05 if k in (1, 2) else 0.035, (1.0, 0.35, 0.18), e["alpha"] * (0.9 if k in (1, 2) else 0.6))
        if not verts:
            return
        self.glow_mesh.upload(np.array(verts, np.float32))
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_ONE, GL.GL_ONE)
        GL.glDepthMask(GL.GL_FALSE)
        self.glow.use()
        self.glow.mat4("uPV", self.pv)
        self.glow.float("uTime", now)
        self.glow_mesh.draw()
        GL.glDepthMask(GL.GL_TRUE)
        GL.glDisable(GL.GL_BLEND)


def _fog_quad(verts, corners, alpha, seed, kind):
    for i, uv in zip((0, 1, 2, 0, 2, 3), ((0, 0), (1, 0), (1, 1), (0, 0), (1, 1), (0, 1))):
        verts.append((*corners[i], *uv, alpha, seed, kind))


def project(pv, p, w, h):
    v = pv @ np.array((*p, 1.0), np.float32)
    if v[3] <= 0.01:
        return None
    return ((v[0] / v[3] * 0.5 + 0.5) * w, (1 - (v[1] / v[3] * 0.5 + 0.5)) * h)



