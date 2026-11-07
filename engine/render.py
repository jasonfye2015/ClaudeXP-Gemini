"""Drawing a Game: the level's mesh, its props (instanced plants), the figures (skinned on the card), the bolts, sparks,
torch flames and rune circles (glowing billboards), the sky outdoors, and the wand in Claude's hand. Lighting is per
pixel: an ambient, the sun outdoors, Claude's own light, the torches and every bolt in the air."""
import ctypes
import math
import time
from pathlib import Path

import numpy as np
from OpenGL import GL
from PIL import Image

from ..game import data as D

from . import dressmesh
from . import gl
from .itempics import drop_picture
from . import weatherfx
from . import levelmesh
from .figures import Pack, Plants

TEXTURES = Path(__file__).resolve().parents[1] / "assets" / "textures"
ART = Path(__file__).resolve().parents[1] / "assets" / "cm"
ITEMS = Path(__file__).resolve().parents[1] / "assets" / "items"
MAX_LIGHTS = 24
CHUNK = 24
MAX_JOINTS = 64

LIGHTING = """
uniform vec3 uEye;
uniform vec3 uAmbient;
uniform vec3 uFogColour;
uniform float uFogDensity;
uniform vec3 uSunDir;
uniform vec3 uSunCol;
uniform int uLightCount;
uniform vec4 uLightPos[24];
uniform vec4 uLightCol[24];
uniform sampler2D uAmbMap; uniform vec2 uAmbN;     // (a floor of the Deep: r the ambient by square, g its floor, b wet, a stained)
vec3 lit(vec3 p, vec3 n, vec3 base) {
    float ak = uAmbN.x > 0.0 ? texture(uAmbMap, p.xz / uAmbN).r : 1.0;
    vec3 c = uAmbient * ak + uSunCol * max(dot(n, -uSunDir), 0.0);
    for (int i = 0; i < uLightCount; i++) {
        vec3 d = uLightPos[i].xyz - p;
        float dist = length(d);
        float att = clamp(1.0 - dist / uLightPos[i].w, 0.0, 1.0);
        att *= att;
        float ndl = max(dot(n, d / max(dist, 1e-3)), 0.0) * 0.8 + 0.2;
        c += uLightCol[i].rgb * att * ndl;
    }
    vec3 col = base * c;
    float f = 1.0 - exp(-pow(uFogDensity * length(p - uEye), 1.4));
    return mix(col, uFogColour, clamp(f, 0.0, 1.0));
}
vec4 outColour(vec3 c, float a) { return vec4(pow(max(c, vec3(0.0)), vec3(1.0 / 2.2)), a); }
"""

WORLD_VS = """#version 330 core
layout(location=0) in vec3 aPos; layout(location=1) in vec3 aNrm; layout(location=2) in vec2 aUV;
layout(location=3) in float aLayer; layout(location=4) in float aShade;
uniform mat4 uProj; uniform mat4 uView; uniform float uLift;
out vec3 vPos; out vec3 vNrm; out vec2 vUV; flat out float vLayer; out float vShade;
void main() { vec3 p = aPos + vec3(0.0, uLift, 0.0); vPos = p; vNrm = aNrm; vUV = aUV; vLayer = aLayer; vShade = aShade;
              gl_Position = uProj * uView * vec4(p, 1.0); }"""
WORLD_FS = """#version 330 core
in vec3 vPos; in vec3 vNrm; in vec2 vUV; flat in float vLayer; in float vShade;
uniform sampler2DArray uTex; uniform vec3 uTint; uniform float uSnow; uniform float uWet;
uniform sampler2D uMap; uniform vec2 uMapN; uniform float uGBlend; uniform float uGrassL; uniform float uDirtL;
uniform float uTime; uniform float uDapple; uniform float uMud; uniform float uAutumn;
out vec4 frag;
""" + LIGHTING + """
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y); }
vec4 cellAt(vec2 c) { return texture(uMap, (c + 0.5) / uMapN); }
float kindAt(vec2 c) { return floor(cellAt(c).b * 255.0 + 0.5); }
// the ground, blended as Claude and Magic's is (its uGBlend): the neighbour's ground fading in at a square's edge along a
// line the noise breaks; big soft patches so the tiling doesn't show; the grass worn to earth where the feet go; dark mud
// at the water's banks; the sun dappled under the trees; autumn's leaves drifted at the walls; the earth muddied by rain
vec3 ground(vec3 t) {
    vec2 cw = vPos.xz, cell = floor(cw), f = cw - cell;
    vec4 here = cellAt(cell);
    float me = floor(here.b * 255.0 + 0.5);
    if (me < 0.5 || here.g > 0.5) return t;
    if (abs(me - 1.0 - vLayer) > 0.5) t = texture(uTex, vec3(vUV, me - 1.0)).rgb * uTint;   // (the forest floor: drawn as the map says)
    float n = (vnoise(cw * 2.3) - 0.5) * 0.55 + (vnoise(cw * 7.0) - 0.5) * 0.25;
    float bestW = 0.0, bestL = -1.0;
    for (int k = 0; k < 8; k++) {
        vec2 off = k == 0 ? vec2(-1.0, 0.0) : k == 1 ? vec2(1.0, 0.0) : k == 2 ? vec2(0.0, -1.0) : k == 3 ? vec2(0.0, 1.0) :
                   k == 4 ? vec2(-1.0, -1.0) : k == 5 ? vec2(1.0, -1.0) : k == 6 ? vec2(-1.0, 1.0) : vec2(1.0, 1.0);
        float other = kindAt(cell + off);
        if (other < 0.5 || other == me) continue;
        vec2 e = vec2(off.x > 0.0 ? 1.0 - f.x : f.x, off.y > 0.0 ? 1.0 - f.y : f.y);
        float dist = off.x != 0.0 && off.y != 0.0 ? length(e) : off.x != 0.0 ? e.x : e.y;
        float w = (1.0 - smoothstep(0.0, 0.34, dist + n * 0.8 - 0.06)) * 0.5;   // (each side gives half: half and half at the line)
        if (w > bestW) { bestW = w; bestL = other - 1.0; }
    }
    if (bestL >= 0.0) t = mix(t, texture(uTex, vec3(vUV, bestL)).rgb * uTint, bestW * 0.95);
    float big = vnoise(cw * 0.13) * 0.65 + vnoise(cw * 0.37 + 7.0) * 0.35, hue = vnoise(cw * 0.21 + 3.0);
    t *= 0.84 + 0.32 * big;
    bool grass = abs(me - 1.0 - uGrassL) < 0.5, earth = abs(me - 1.0 - uDirtL) < 0.5;
    if (grass) t = mix(t, t * vec3(1.08, 1.05, 0.82), smoothstep(0.55, 0.85, hue) * 0.6);
    float worn = here.a;
    if (worn > 0.02 && grass && uDirtL >= 0.0) {
        float wn = vnoise(cw * 3.7) * 0.6 + vnoise(cw * 11.0) * 0.4;
        float k = smoothstep(0.5, 0.85, worn * 1.1 - wn * 0.6 + 0.1);
        t = mix(t, texture(uTex, vec3(vUV, uDirtL)).rgb * uTint * (0.84 + 0.32 * big), k * 0.85);
    }
    vec2 wq = cw / uMapN;
    {   // the banks: wet mud from the water's edge, fading into the grass in a ragged line
        vec2 o = 0.55 / uMapN;
        float wn = max(max(texture(uMap, wq + vec2(o.x, 0.0)).g, texture(uMap, wq - vec2(o.x, 0.0)).g),
                       max(texture(uMap, wq + vec2(0.0, o.y)).g, texture(uMap, wq - vec2(0.0, o.y)).g));
        wn = max(wn, 0.8 * max(max(texture(uMap, wq + o).g, texture(uMap, wq - o).g),
                               max(texture(uMap, wq + vec2(o.x, -o.y)).g, texture(uMap, wq + vec2(-o.x, o.y)).g)));
        float bank = smoothstep(0.2, 0.48, wn + (vnoise(cw * 4.5) - 0.5) * 0.2);
        if (bank > 0.0) t = mix(t, mix(vec3(0.2, 0.16, 0.11), vec3(0.33, 0.27, 0.19), vnoise(cw * 11.0)), bank * 0.88);
    }
    vec2 o4 = 0.4 / uMapN;
    float edge = step(0.7, texture(uMap, wq + vec2(o4.x, 0.0)).r) + step(0.7, texture(uMap, wq - vec2(o4.x, 0.0)).r) +
                 step(0.7, texture(uMap, wq + vec2(0.0, o4.y)).r) + step(0.7, texture(uMap, wq - vec2(0.0, o4.y)).r);
    if (uAutumn > 0.0) {   // leaves drifted against the walls and the trunks: scattered, turned, leaf-shaped
        float lf = smoothstep(0.45, 0.8, min(edge, 1.0) * 0.8 + vnoise(cw * 4.0) * 0.5 - 0.1) * uAutumn
                   + smoothstep(0.78, 0.95, vnoise(cw * 0.9 + 3.0)) * 0.5 * uAutumn;   // (and a few blown into drifts)
        vec2 lq = cw * 16.0 + vec2(vnoise(cw * 5.0), vnoise(cw * 5.0 + 9.0)) * 1.6, lc = floor(lq);
        float lh = hash(lc), la = hash(lc + 3.3) * 6.28;
        vec2 lp = fract(lq) - 0.5 - (vec2(hash(lc + 1.1), hash(lc + 2.2)) - 0.5) * 0.4;
        lp = mat2(cos(la), sin(la), -sin(la), cos(la)) * lp;
        float ld = length(lp * vec2(1.0, 1.9)) + step(hash(lc + 4.4), 0.45);
        vec3 lcol = lh < 0.33 ? vec3(0.62, 0.28, 0.08) : lh < 0.66 ? vec3(0.78, 0.52, 0.12) : vec3(0.45, 0.2, 0.08);
        t = mix(t, lcol * (0.75 + 0.3 * hash(lc + 5.5)), min(lf, 1.0) * (1.0 - smoothstep(0.28, 0.34, ld)) * 0.85);
    }
    if (uMud > 0.0 && (earth || grass)) {   // after rain: the earth and the worn grass muddied, in patches
        float md = earth ? 0.55 + 0.45 * vnoise(cw * 4.6) : smoothstep(0.4, 0.75, vnoise(cw * 1.7) + worn * 0.4);
        t = mix(t, t * vec3(0.55, 0.5, 0.45), md * uMud * 0.75);
    }
    if (uDapple > 0.0) {   // the sun broken by the leaves into soft patches that drift in the breeze, under and beside the trees
        vec2 o = 1.3 / uMapN, j = (vec2(vnoise(cw * 1.1), vnoise(cw * 1.1 + 5.0)) - 0.5) * 1.2 / uMapN;
        float cover = 0.0;
        for (int k = 0; k < 8; k++) { float a = float(k) * 0.785; cover += min(1.0, texture(uMap, wq + j + vec2(cos(a), sin(a)) * o).r * 2.0); }
        cover = cover / 8.0 + (vnoise(cw * 0.45) - 0.5) * 0.5;
        float tm = uTime * 0.05, sp = vnoise(cw * 3.4 + vec2(tm, tm * 0.6)) * 0.55 + vnoise(cw * 8.5 - vec2(tm * 1.7, tm)) * 0.45;
        t *= mix(1.0, mix(0.8, 1.3, smoothstep(0.46, 0.62, sp)), uDapple * smoothstep(0.0, 0.6, cover));
    }
    return t;
}
vec4 dcell(vec2 c) { return texture(uAmbMap, (c + 0.5) / uAmbN); }
vec3 deep(vec3 t, out float wetK) {
    wetK = 0.0;
    vec3 n = normalize(vNrm);
    vec2 cw = vPos.xz;
    if (n.y > 0.9) {
        vec4 d = dcell(floor(cw));
        if (abs(vPos.y - d.g) > 0.03) return t;                                  // (a box's top, not the floor)
        vec4 here = texture(uAmbMap, cw / uAmbN);
        float st = clamp(here.a, 0.0, 1.0);
        float s = smoothstep(0.52, 0.86, vnoise(cw * 1.3) * 0.6 + vnoise(cw * 4.3 + 3.0) * 0.4) * (0.35 + 0.65 * st);
        t = mix(t, t * vec3(0.5, 0.45, 0.38), s * 0.8);                          // stains in blotches
        t *= 0.88 + 0.24 * vnoise(cw * 0.35 + 5.0);                              // (and the tiling broken)
        float w = max(here.b, 0.0);
        float pz = smoothstep(0.44, 0.52, vnoise(cw * 1.7 + 11.0) * 0.7 + vnoise(cw * 5.1) * 0.3 + w * 0.6 - 0.5) * step(0.04, w);
        wetK = pz;
        t = mix(t, t * vec3(0.38, 0.42, 0.48), pz * 0.85);                       // a puddle: dark, and cold
    } else if (abs(n.y) < 0.2) {
        vec4 d = dcell(floor(cw + n.xz * 0.5));
        float h = vPos.y - d.g, st = clamp(d.a, 0.0, 1.0);
        float u = dot(cw, vec2(-n.z, n.x));
        float streak = smoothstep(0.58, 0.9, vnoise(vec2(u * 5.5, vPos.y * 0.45)) * 0.75 + vnoise(vec2(u * 17.0, 1.0)) * 0.25);
        t = mix(t, t * vec3(0.55, 0.55, 0.5), streak * (0.25 + 0.5 * st));    // water's long stains down the stone
        float g = 1.0 - smoothstep(0.0, 0.6, h + (vnoise(vec2(u * 3.0, 2.0)) - 0.5) * 0.35);
        t = mix(t, t * vec3(0.42, 0.4, 0.33), g * (0.45 + 0.35 * st));         // the grime at its foot
    }
    return t;
}
vec3 sheen(vec3 p) {                                                       // the lights caught in a puddle
    vec3 v = normalize(uEye - p), s = vec3(0.0);
    for (int i = 0; i < uLightCount; i++) {
        vec3 d = uLightPos[i].xyz - p; float dist = length(d);
        float att = clamp(1.0 - dist / (uLightPos[i].w * 1.6), 0.0, 1.0);
        vec3 hv = normalize(d / max(dist, 1e-3) + v);
        s += uLightCol[i].rgb * pow(max(hv.y, 0.0), 90.0) * att * 2.5;
    }
    return s + uAmbient * 0.12 * pow(1.0 - max(v.y, 0.0), 3.0);
}
void main() { vec3 base = texture(uTex, vec3(vUV, vLayer)).rgb * uTint;
              if (uGBlend > 0.0 && uMapN.x > 0.0 && vNrm.y > 0.9 && vPos.y < 0.6) base = mix(base, ground(base), uGBlend);
              float wetK = 0.0;
              if (uAmbN.x > 0.0) base = deep(base, wetK);
              base *= vShade;
              float up = smoothstep(0.5, 0.9, vNrm.y);
              base = mix(base, vec3(0.86, 0.89, 0.95) * vShade, uSnow * up * (0.75 + 0.25 * texture(uTex, vec3(vUV * 3.0, vLayer)).g));
              base *= 1.0 - uWet * 0.3 * up;
              vec3 col = lit(vPos, normalize(vNrm), base);
              if (wetK > 0.0) col += sheen(vPos) * wetK * exp(-pow(uFogDensity * length(vPos - uEye), 1.4));
              frag = outColour(col, 1.0); }"""

# Claude and Magic's painted things: on the walls, the floors, hanging, standing - cut out by their alpha, lit like
# the walls, and glowing (shade above 1) when they're braziers, glowcaps, crystals
ART_FS = """#version 330 core
in vec3 vPos; in vec3 vNrm; in vec2 vUV; flat in float vLayer; in float vShade;
uniform sampler2DArray uArt; uniform vec3 uTint; uniform float uAlphaCut; uniform float uWaterAlpha; uniform float uTime;
out vec4 frag;
""" + LIGHTING + """
void main() {
    vec2 uv = vUV;
    if (uWaterAlpha > 0.0) uv += vec2(sin(uTime * 0.3 + vPos.z) * 0.03, uTime * 0.04);
    vec4 t = texture(uArt, vec3(uv, vLayer));
    if (uWaterAlpha <= 0.0 && t.a < uAlphaCut) discard;
    vec3 base = t.rgb * uTint * min(vShade, 1.0);
    vec3 c = lit(vPos, normalize(vNrm), base) + base * max(vShade - 1.0, 0.0);
    frag = outColour(c, uWaterAlpha > 0.0 ? uWaterAlpha : 1.0); }"""

FIG_VS = """#version 330 core
layout(location=0) in vec3 aPos; layout(location=1) in vec2 aUV; layout(location=2) in vec3 aCol;
layout(location=3) in vec4 aJoints; layout(location=4) in vec4 aWeights;
uniform mat4 uProj; uniform mat4 uView; uniform mat4 uModel; uniform mat4 uJoints[64];
out vec3 vPos; out vec2 vUV; out vec3 vCol;
void main() {
    mat4 sk = aWeights.x * uJoints[int(aJoints.x)] + aWeights.y * uJoints[int(aJoints.y)]
            + aWeights.z * uJoints[int(aJoints.z)] + aWeights.w * uJoints[int(aJoints.w)];
    vec4 wp = uModel * sk * vec4(aPos, 1.0);
    vPos = wp.xyz; vUV = aUV; vCol = aCol;
    gl_Position = uProj * uView * wp; }"""
FIG_FS = """#version 330 core
in vec3 vPos; in vec2 vUV; in vec3 vCol;
uniform sampler2D uTex; uniform int uTextured; uniform vec3 uTint; uniform float uTintMix; uniform float uFlash;
uniform float uAlpha; uniform vec3 uGlow;
out vec4 frag;
""" + LIGHTING + """
void main() {
    vec3 n = normalize(cross(dFdx(vPos), dFdy(vPos)));
    vec3 base = uTextured == 1 ? texture(uTex, vUV).rgb : pow(vCol, vec3(2.2));
    float l = dot(base, vec3(0.3, 0.55, 0.15));
    base = mix(base, l * uTint * 2.2, uTintMix);
    vec3 v = normalize(uEye - vPos);
    float rim = pow(1.0 - abs(dot(n, v)), 2.0);
    vec3 c = lit(vPos, n, base) + base * (uAmbient * 0.8 + vec3(0.10, 0.09, 0.08) * rim * 2.0) + uGlow;
    c = mix(c, vec3(1.0, 0.95, 0.9), uFlash);
    frag = outColour(c, uAlpha); }"""

PLANT_VS = """#version 330 core
layout(location=0) in vec3 aPos; layout(location=1) in vec3 aCol;
layout(location=2) in vec4 aInst; layout(location=3) in vec2 aInst2;
uniform mat4 uProj; uniform mat4 uView;
out vec3 vPos; out vec3 vCol;
void main() { float c = cos(aInst.w), s = sin(aInst.w), k = aInst2.x;
    vec3 p = vec3(c * aPos.x + s * aPos.z, aPos.y, -s * aPos.x + c * aPos.z) * k + aInst.xyz;
    vPos = p; vCol = aCol * aInst2.y; gl_Position = uProj * uView * vec4(p, 1.0); }"""
# things already placed in the world (the chests, posed on the card each frame): position and colour
SOLID_VS = """#version 330 core
layout(location=0) in vec3 aPos; layout(location=1) in vec3 aCol;
uniform mat4 uProj; uniform mat4 uView;
out vec3 vPos; out vec3 vCol;
void main() { vPos = aPos; vCol = aCol; gl_Position = uProj * uView * vec4(aPos, 1.0); }"""
PLANT_FS = """#version 330 core
in vec3 vPos; in vec3 vCol;
uniform vec3 uTint; uniform float uSnow;
out vec4 frag;
""" + LIGHTING + """
void main() { vec3 n = normalize(cross(dFdx(vPos), dFdy(vPos)));
    vec3 base = pow(vCol, vec3(2.2)) * uTint;
    base = mix(base, vec3(0.8, 0.83, 0.9), uSnow * smoothstep(0.35, 0.8, abs(n.y)));
    frag = outColour(lit(vPos, n, base), 1.0); }"""

# billboards: glows (0), rune circles flat on the floor (1), the Deep's mouth (2), torch flames (3), bars of light (4)
GLOW_VS = """#version 330 core
layout(location=0) in vec3 aPos; layout(location=1) in vec2 aUV; layout(location=2) in vec4 aCol;
layout(location=3) in float aMode;
uniform mat4 uProj; uniform mat4 uView;
out vec2 vUV; out vec4 vCol; flat out float vMode; out vec3 vPos;
void main() { vUV = aUV; vCol = aCol; vMode = aMode; vPos = aPos; gl_Position = uProj * uView * vec4(aPos, 1.0); }"""
GLOW_FS = """#version 330 core
in vec2 vUV; in vec4 vCol; flat in float vMode; in vec3 vPos;
uniform float uTime;
out vec4 frag;
void main() {
    vec2 p = vUV * 2.0 - 1.0; float r = length(p); float a = 0.0;
    if (vMode < 0.5) { a = pow(max(0.0, 1.0 - r), 2.2); a += pow(max(0.0, 1.0 - r * 2.5), 3.0) * 2.0; }
    else if (vMode < 1.5) { float ang = atan(p.y, p.x);
        float ring = smoothstep(0.06, 0.0, abs(r - 0.82)) + smoothstep(0.05, 0.0, abs(r - 0.62)) * 0.8;
        float spokes = smoothstep(0.92, 1.0, cos(ang * 6.0 + uTime * 0.8)) * step(0.62, r) * step(r, 0.82);
        float glyph = smoothstep(0.85, 1.0, sin(ang * 18.0 - uTime * 1.3)) * step(0.66, r) * step(r, 0.78) * 0.6;
        a = (ring + spokes + glyph) * (0.75 + 0.25 * sin(uTime * 2.0)) + pow(max(0.0, 1.0 - r), 3.0) * 0.5; }
    else if (vMode < 2.5) { float ang = atan(p.y, p.x);
        float sw = sin(ang * 3.0 + r * 9.0 - uTime * 2.5) * 0.5 + 0.5;
        a = pow(max(0.0, 1.0 - r), 1.5) * (0.35 + 0.65 * sw); }
    else if (vMode < 3.5) { float fl = sin(uTime * 13.0 + vPos.x * 7.0) * 0.08 + sin(uTime * 7.3 + vPos.z * 5.0) * 0.06;
        vec2 q = vec2(p.x * (1.4 + fl * 3.0), (p.y + 0.3) * 0.8);
        a = pow(max(0.0, 1.0 - length(q)), 1.6) * smoothstep(-1.0, -0.2, p.y); }
    else if (vMode < 4.5) { a = (1.0 - abs(p.y)) * pow(max(0.0, 1.0 - abs(p.x)), 0.5); }
    else if (vMode > 6.5) { float y = vUV.y;                                   // (0 the floor .. 1 the grate)
        a = pow(max(0.0, 1.0 - abs(p.x)), 1.6) * smoothstep(0.0, 0.25, y) * (0.45 + 0.55 * y) * smoothstep(1.0, 0.93, y);
        a *= 0.85 + 0.15 * sin(uTime * 0.7 + vPos.x * 3.0 + y * 4.0); }
    else { if (vMode < 5.5) a = smoothstep(1.0, 0.2, length(p)); else a = (1.0 - abs(p.x)) * smoothstep(1.0, 0.6, abs(p.y));
           if (a < 0.01) discard; frag = vec4(vCol.rgb, a * vCol.a); return; }
    if (a < 0.003) discard;
    frag = vec4(vCol.rgb * a * vCol.a, 1.0); }"""

SKY_VS = """#version 330 core
layout(location=0) in vec2 aPos; out vec2 vP;
void main() { vP = aPos; gl_Position = vec4(aPos, 0.9999, 1.0); }"""
SKY_FS = """#version 330 core
in vec2 vP; uniform mat4 uInvPV; uniform vec3 uTop; uniform vec3 uHorizon; uniform vec3 uSunDir;
uniform vec3 uMoonV; uniform float uPhase; uniform float uSunDisc; uniform float uMoonDisc; uniform float uStars;
uniform float uCloud; uniform vec2 uWind; uniform float uTime; uniform float uAurora; uniform float uRainbow;
uniform float uFlash; uniform float uStorm;
out vec4 frag;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p) { float a = 0.5, s = 0.0; for (int i = 0; i < 5; i++) { s += a * noise(p); p *= 2.03; a *= 0.5; } return s; }
void main() { vec4 w = uInvPV * vec4(vP, 1.0, 1.0); vec3 d = normalize(w.xyz / w.w);
    float h = clamp(d.y, -0.2, 1.0);
    vec3 top = pow(uTop, vec3(2.2)), hor = pow(uHorizon, vec3(2.2));
    vec3 c = mix(hor, top, pow(max(h, 0.0), 0.55));
    // the stars, and the moon in its phase
    if (uStars > 0.01 && d.y > 0.0) { vec2 g = floor(d.xz / (d.y + 0.25) * 220.0); float s = hash(g);
        if (s > 0.996) c += vec3(0.9, 0.92, 1.0) * uStars * (0.55 + 0.45 * sin(uTime * 2.0 + s * 90.0)) * smoothstep(0.0, 0.25, d.y); }
    vec3 mv = normalize(uMoonV); float md = dot(d, mv);
    if (uMoonDisc > 0.01 && md > 0.9985) { vec3 r = normalize(cross(mv, vec3(0, 1, 0))); float x = dot(d - mv * md, r) / 0.055;
        float lit = uPhase <= 4.0 ? step(cos(uPhase * 0.785398), x) : step(x, cos((uPhase - 4.0) * 0.785398));
        if (uPhase == 0.0) lit = 0.04;
        c = mix(c, vec3(0.92, 0.92, 0.85) * (0.25 + 0.75 * lit), uMoonDisc * smoothstep(0.9985, 0.9992, md)); }
    c += vec3(0.6, 0.65, 0.8) * pow(max(md, 0.0), 60.0) * 0.08 * uMoonDisc;
    // the sun
    float sun = max(dot(d, -uSunDir), 0.0);
    c += vec3(1.0, 0.85, 0.6) * (pow(sun, 420.0) * 3.0 * uSunDisc + pow(sun, 10.0) * 0.22 * uSunDisc);
    // the aurora, hanging in the north
    if (uAurora > 0.0 && d.y > 0.02) { float band = fbm(vec2(d.x * 3.0 + uTime * 0.03, uTime * 0.05)) ;
        float curtain = smoothstep(0.05, 0.25, d.y) * smoothstep(0.7, 0.3, d.y) * smoothstep(0.1, -0.5, d.z);
        c += vec3(0.15, 0.9, 0.5) * curtain * band * uAurora * 0.9 + vec3(0.5, 0.2, 0.8) * curtain * pow(band, 3.0) * uAurora * 0.6; }
    // a rainbow, opposite the sun
    if (uRainbow > 0.0) { float a = degrees(acos(clamp(dot(d, uSunDir), -1.0, 1.0)));
        float t = (a - 40.5) / 2.2; if (t > 0.0 && t < 1.0 && d.y > 0.0) {
        vec3 rb = clamp(abs(fract(t + vec3(0.0, 0.33, 0.67)) * 6.0 - 3.0) - 1.0, 0.0, 1.0);
        c = mix(c, c + rb * 0.35, uRainbow * sin(t * 3.14159)); } }
    // the clouds, drifting with the wind
    if (d.y > 0.0) { vec2 uv = d.xz / (d.y + 0.15) * 1.4 + uWind * uTime * 0.02;
        float n = fbm(uv); float cov = smoothstep(1.0 - uCloud * 1.15, 1.0 - uCloud * 1.15 + 0.35, n);
        vec3 cc = mix(hor * 1.15 + vec3(0.04), top * 0.7 + hor * 0.5, 0.4) * (1.0 - 0.45 * uStorm) + vec3(1.0, 0.85, 0.7) * pow(sun, 6.0) * 0.25 * uSunDisc;
        c = mix(c, cc, cov * smoothstep(0.0, 0.12, d.y) * 0.95); }
    c += vec3(0.75, 0.78, 0.9) * uFlash;
    frag = vec4(pow(max(c, vec3(0.0)), vec3(1.0 / 2.2)), 1.0); }"""


def face_yaw(dx, dz):
    return math.atan2(-dx, dz)


class GpuFigure:
    def __init__(self, model):
        self.model = model
        assert model.n_joints <= MAX_JOINTS, (model.name, model.n_joints)
        n = len(model.positions)
        col = model.colours if model.texture is None else np.ones((n, 3), np.float32)
        data = np.concatenate([model.positions, model.uv, col, model.joints.astype(np.float32), model.weights], 1)
        self.mesh = gl.Mesh([(0, 3), (1, 2), (2, 3), (3, 4), (4, 4)], data, model.indices)
        self.tex = gl.texture_2d(model.texture, repeat=False) if model.texture else None
        lo, hi = model.measure()
        self.lo, self.hi = lo, hi
        self.centre = ((lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2)


class Renderer:
    def __init__(self):
        self.world = gl.Program(WORLD_VS, WORLD_FS)
        self.art = gl.Program(WORLD_VS, ART_FS)
        self.fig = gl.Program(FIG_VS, FIG_FS)
        self.plant = gl.Program(PLANT_VS, PLANT_FS)
        self.solid = gl.Program(SOLID_VS, PLANT_FS)
        try:
            self.chest = np.load(Path(__file__).resolve().parents[1] / "assets" / "figures" / "chest.npz")
        except OSError:
            self.chest = None
        self.chest_mesh = None
        self.glow = gl.Program(GLOW_VS, GLOW_FS)
        self.sky = gl.Program(SKY_VS, SKY_FS)
        self.pack = Pack.load()
        self.plants = Plants.load()
        self.figs = {}
        self.plant_meshes = {}
        names = sorted(p.stem for p in TEXTURES.glob("*.jpg"))
        self.layers = {n: i for i, n in enumerate(names)}
        self.tex_array = gl.texture_array([Image.open(TEXTURES / f"{n}.jpg") for n in names], 512)
        self.level_mesh = gl.Mesh([(0, 3), (1, 3), (2, 2), (3, 1), (4, 1)])
        art_names = sorted(p.stem for p in ART.glob("*.png"))
        pics = [Image.open(ART / f"{n}.png") for n in art_names]
        for f in sorted(ITEMS.glob("*.png")):                      # (the item sprites: pixel art, enlarged crisply)
            im = Image.open(f).convert("RGBA")
            if im.width != im.height:                              # (a tall crop: stood on a square, its feet down)
                side = max(im.size)
                sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
                sq.paste(im, ((side - im.width) // 2, side - im.height))
                im = sq
            pics.append(im.resize((256, 256), Image.NEAREST))
            art_names.append("item:" + f.name)
        self.art_layers = {n: i for i, n in enumerate(art_names)}
        self.art_array = gl.texture_array(pics, 256) if art_names else None
        self.dress_mesh = gl.Mesh([(0, 3), (1, 3), (2, 2), (3, 1), (4, 1)])
        self.water_mesh = gl.Mesh([(0, 3), (1, 3), (2, 2), (3, 1), (4, 1)])
        self.bill_mesh = gl.Mesh([(0, 3), (1, 3), (2, 2), (3, 1), (4, 1)], dynamic=True)
        self.flood_mesh = gl.Mesh([(0, 3), (1, 3), (2, 2), (3, 1), (4, 1)])
        self.wx_mesh = gl.Mesh([(0, 3), (1, 2), (2, 4), (3, 1)], dynamic=True)
        self.flash = 0.0
        self.atm = None
        self.glow_mesh = gl.Mesh([(0, 3), (1, 2), (2, 4), (3, 1)], dynamic=True)
        self.sky_mesh = gl.Mesh([(0, 2)], np.array([[-1, -1], [1, -1], [1, 1], [-1, -1], [1, 1], [-1, 1]], np.float32))
        self.inst = {}                                       # plant name -> (instance buffer, count)
        self.level = None
        self.t0 = time.perf_counter()
        self.recoil = 0.0
        self.bob = 0.0
        self.anim_now = 0.0
        self.arcs = []
        self._version = 0
        self.proj_view = np.identity(4, np.float32)
        self.map_tex, self.map_n = None, (0.0, 0.0)
        self.amb_tex, self.amb_n = None, (0.0, 0.0)
        self.ground_blend = True                             # (the ground's blending: Options, on/off)

    # ---- the level ---------------------------------------------------------------------------------------------
    def set_level(self, L):
        self.level = L
        layer_of = lambda i: self.layers.get(L.textures[int(i)], 0) if int(i) < len(L.textures) else 0   # noqa: E731
        self.level_mesh.upload(levelmesh.build(L, layer_of))
        if getattr(self, "map_tex", None):
            GL.glDeleteTextures(1, [self.map_tex])
            self.map_tex = None
        if getattr(self, "amb_tex", None):
            GL.glDeleteTextures(1, [self.amb_tex])
            self.amb_tex = None
        self.amb_n = (0.0, 0.0)
        if getattr(L, "amb", None) is not None and not L.outdoor:
            from . import groundmap
            self.amb_tex = _float_texture(groundmap.deep(L))
            self.amb_n = (float(L.w), float(L.h))
        self.map_n = (0.0, 0.0)
        if L.outdoor:                                      # (the ground's map, for it to blend: engine/groundmap.py)
            from . import groundmap
            M = groundmap.build(L, layer_of)
            self.map_tex = gl.texture_2d(Image.fromarray(M, "RGBA"), srgb=False, repeat=False, mip=False)
            self.map_n = (float(L.w), float(L.h))
        self.dress_mesh.upload(dressmesh.static(L, self.art_layers.get))
        from ..game import dress as _dress
        theme = _dress.CM_THEME_OF_BAND[min(9, max(0, (L.depth - 1) // 10))]
        self.water_mesh.upload(dressmesh.water(L, self.art_layers.get(f"t{theme}.water0", 0)))
        # (the floodwater a storm above can bring into the first floors' sunken rooms)
        sunk = {(x, y) for (x, y) in L.open_squares() if L.floor[y, x] < -0.1} if 1 <= L.depth <= 3 else set()
        fl = type("F", (), {"water": sunk, "floor": L.floor * 0 + 0.0})()
        self.flood_mesh.upload(dressmesh.water(fl, self.art_layers.get(f"t{theme}.water0", 0)) if sunk else np.zeros((0, 10), np.float32))
        self.cells = weatherfx.ceiling_cells(L) if not L.outdoor else None
        self._props(L)

    def _props(self, L):
        for vao, buf, _n, _mesh in self.inst.values():
            GL.glDeleteBuffers(1, [buf])
            GL.glDeleteVertexArrays(1, [vao])
        self.inst = {}
        groups = {}
        for p in L.props:                               # (by model and by a chunk of 16 squares: far chunks aren't drawn)
            groups.setdefault((p["model"], int(p["x"]) // CHUNK, int(p["z"]) // CHUNK), []).append(p)
        for key, ps in groups.items():
            name = key[0]
            if not self.plants.has(name):
                continue
            mesh = self._plant_mesh(name)
            arr = np.array([[p["x"], p.get("y", 0.0), p["z"], p["yaw"], p["scale"], p.get("bright", 1.0)] for p in ps],
                           np.float32)
            # (a vertex array of its own: the model's vertices and indices, and this chunk's instances)
            vao = GL.glGenVertexArrays(1)
            GL.glBindVertexArray(vao)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, mesh.vbo)
            GL.glEnableVertexAttribArray(0)
            GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 24, ctypes.c_void_p(0))
            GL.glEnableVertexAttribArray(1)
            GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, 24, ctypes.c_void_p(12))
            GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, mesh.ebo)
            buf = GL.glGenBuffers(1)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, buf)
            GL.glBufferData(GL.GL_ARRAY_BUFFER, arr.nbytes, arr, GL.GL_STATIC_DRAW)
            GL.glEnableVertexAttribArray(2)
            GL.glVertexAttribPointer(2, 4, GL.GL_FLOAT, GL.GL_FALSE, 24, ctypes.c_void_p(0))
            GL.glVertexAttribDivisor(2, 1)
            GL.glEnableVertexAttribArray(3)
            GL.glVertexAttribPointer(3, 2, GL.GL_FLOAT, GL.GL_FALSE, 24, ctypes.c_void_p(16))
            GL.glVertexAttribDivisor(3, 1)
            GL.glBindVertexArray(0)
            self.inst[key] = (vao, buf, len(ps), mesh)

    def _plant_mesh(self, name):
        if name not in self.plant_meshes:
            pos, col, idx = self.plants.mesh(name)
            self.plant_meshes[name] = gl.Mesh([(0, 3), (1, 3)], np.concatenate([pos, col], 1), idx)
        return self.plant_meshes[name]

    def gpu_figure(self, name):
        if name not in self.figs:
            self.figs[name] = GpuFigure(self.pack.model(name))
        return self.figs[name]

    # ---- the frame ---------------------------------------------------------------------------------------------
    def draw(self, g, w, h, dt):
        L = g.level
        if L is not self.level:
            self.set_level(L)
        elif getattr(L, "version", 0) != self._version:            # (something broke: the props again)
            self._props(L)
        self._version = getattr(L, "version", 0)
        now = time.perf_counter() - self.t0
        self.anim_now += dt
        GL.glViewport(0, 0, w, h)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDepthFunc(GL.GL_LEQUAL)
        GL.glDisable(GL.GL_CULL_FACE)
        GL.glDisable(GL.GL_BLEND)
        fogc, fogd = L.fog
        atm = None
        if L.outdoor and getattr(g, "sky", None) is not None:
            from .atmosphere import look
            atm = look(g.sky, True, L.fog[1])
            fogc, fogd = atm["fog"]
        self.flash = max(0.0, getattr(self, "flash", 0.0) - dt * 4)
        GL.glClearColor(*fogc, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        proj = gl.perspective(72.0, w / max(1, h), 0.05, 120.0)
        self._proj_cache = proj
        eye = g.eye
        moving = abs(getattr(g, "_speed_seen", 0)) > 0.1
        self.bob += dt * ((13.0 if getattr(g, "running", False) else 9.0) if moving else 0.0)
        bob_y = math.sin(self.bob) * 0.025 if moving else 0.0
        view = gl.view_matrix((eye[0], eye[1] + bob_y, eye[2]), g.yaw, g.pitch)
        self.proj_view = proj @ view
        lights = self._lights(g, now)
        outdoor = L.outdoor
        if atm:
            sv = np.array(atm["sun_v"], np.float32)
            sun_dir = -sv / np.linalg.norm(sv)
            amb = atm["ambient"] + self.flash * 0.8
            sun_col = atm["sun_col"]
        else:
            sun_dir = np.array([-0.35, -0.8, -0.45], np.float32)
            sun_dir /= np.linalg.norm(sun_dir)
            amb = L.ambient + self.flash * 0.25
            sun_col = (0, 0, 0)
        common = {"uEye": eye, "uAmbient": (amb * 0.9, amb * 0.92, amb), "uFogColour": [c ** 2.2 for c in fogc],
                  "uFogDensity": fogd, "uSunDir": sun_dir, "uSunCol": sun_col}
        self.atm = atm
        if outdoor:
            self._sky(proj, view, sun_dir, fogc, atm, now)
        progs = (self.world, self.fig, self.plant, self.art, self.solid)
        GL.glActiveTexture(GL.GL_TEXTURE5)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.amb_tex or 0)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        for p in progs:
            p.use()
            p.int("uAmbMap", 5)
            p.vec("uAmbN", self.amb_n if self.amb_tex else (0.0, 0.0))
            p.mat4("uProj", proj)
            p.mat4("uView", view)
            for k, v in common.items():
                if k == "uFogDensity":
                    p.float(k, v)
                else:
                    p.vec(k, v)
            p.int("uLightCount", len(lights))
            if lights:
                p.vec4s("uLightPos", [l[0] for l in lights])
                p.vec4s("uLightCol", [l[1] for l in lights])
        # the level
        self.world.use()
        self.world.vec("uTint", L.tint)
        self.world.float("uSnow", min(1.0, (atm["snow"] * 0.9 + atm["frost"] * 0.35)) if atm else 0.0)
        self.world.float("uWet", min(1.0, atm["rain"] + 0.0) if atm else 0.0)
        blend = 1.0 if outdoor and self.map_tex and self.ground_blend else 0.0
        self.world.float("uGBlend", blend)
        self.world.vec("uMapN", self.map_n if blend else (0.0, 0.0))
        self.world.float("uGrassL", float(self.layers.get("ground.grass", -1)))
        self.world.float("uDirtL", float(self.layers.get("ground.dirt", -1)))
        self.world.float("uTime", now)
        self.world.float("uDapple", min(1.0, atm["sun_disc"]) * 0.9 if atm and blend else 0.0)
        self.world.float("uMud", atm.get("mud", 0.0) if atm and blend else 0.0)
        self.world.float("uAutumn", atm.get("autumn", 0.0) if atm and blend else 0.0)
        GL.glActiveTexture(GL.GL_TEXTURE3)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.map_tex or 0)
        self.world.int("uMap", 3)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D_ARRAY, self.tex_array)
        self.world.int("uTex", 0)
        self.level_mesh.draw()
        # the props
        self.plant.use()
        self.plant.vec("uTint", (1, 1, 1) if outdoor else tuple(min(1.0, t) * 0.9 for t in L.tint))
        self.plant.float("uSnow", atm["snow"] * 0.7 if atm else 0.0)
        fx, fz = math.sin(g.yaw), -math.cos(g.yaw)
        reach = 70.0 if outdoor else 40.0
        for (name, chx, chz), (vao, _buf, n, mesh) in self.inst.items():
            dx, dz = (chx + 0.5) * CHUNK - g.x, (chz + 0.5) * CHUNK - g.z
            d = math.hypot(dx, dz)
            if d > reach + CHUNK or (d > CHUNK * 1.2 and (dx * fx + dz * fz) / d < -0.45):
                continue                                                # (too far, or well behind him)
            GL.glBindVertexArray(vao)
            GL.glDrawElementsInstanced(GL.GL_TRIANGLES, mesh.count, GL.GL_UNSIGNED_INT, None, n)
        GL.glBindVertexArray(0)
        # the chests, in the round
        self._chests(g, L, outdoor, atm)
        # Claude and Magic's things: on the walls and floors, hanging, standing
        if self.art_array is not None:
            self._dressing(g, L, now)
        # the figures
        self.fig.use()
        self.fig.int("uTex", 0)
        for n in L.npcs:
            v = D.VENDORS[n["vendor"]]
            self._figure(v["figure"], {"tint": v.get("tint"), "scale": 1.0}, n["x"], n.get("y", L.floor_at(n["x"], n["z"])),
                         n["z"], n["yaw"], 1.0, n.setdefault("anim", {}), "idle", 0, False, 1.0, (0, 0, 0))
        fx, fz = math.sin(g.yaw), -math.cos(g.yaw)
        for m in g.monsters:
            dx, dz = m.x - g.x, m.z - g.z
            d2 = dx * dx + dz * dz
            if d2 > 32 * 32 or (d2 > 4 and dx * fx + dz * fz < -0.2 * math.sqrt(d2)):
                continue                                                # (behind him, or lost in the dark)
            self._monster(g, m)
        # the water's surface
        if self.art_array is not None and (self.water_mesh.count or self.flood_mesh.count):
            self.art.use()
            GL.glActiveTexture(GL.GL_TEXTURE1)
            GL.glBindTexture(GL.GL_TEXTURE_2D_ARRAY, self.art_array)
            self.art.int("uArt", 1)
            self.art.float("uWaterAlpha", 0.72)
            self.art.float("uTime", now)
            GL.glEnable(GL.GL_BLEND)
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
            GL.glDepthMask(GL.GL_FALSE)
            self.water_mesh.draw()
            fd = g.wx.get("flood", 0.0) if getattr(g, "wx", None) else 0.0
            if fd > 0 and self.flood_mesh.count:                      # (the floodwater, rising and draining)
                self.art.float("uLift", -0.28 - (1 - fd) * 0.5)
                self.flood_mesh.draw()
                self.art.float("uLift", 0.0)
            GL.glDepthMask(GL.GL_TRUE)
            GL.glDisable(GL.GL_BLEND)
            self.art.float("uWaterAlpha", 0.0)
            GL.glActiveTexture(GL.GL_TEXTURE0)
        # glows: bolts, sparks, torches, the stairs' rune circle, the Deep's mouth
        self._glows(g, view, now)
        # the weather: rain, snow, leaves, a twister; below, the drips and the grates' water
        self._weather(g, L, view, now)
        # the wand in his hand
        if getattr(g, "hand", True):
            self._wand(g, proj, view, now, dt, lights, common)

    def _dressing(self, g, L, now):
        self.art.use()
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D_ARRAY, self.art_array)
        self.art.int("uArt", 1)
        self.art.vec("uTint", tuple(min(1.0, t) for t in L.tint))
        self.art.float("uAlphaCut", 0.45)
        self.art.float("uWaterAlpha", 0.0)
        self.art.float("uTime", now)
        self.dress_mesh.draw()
        things = []
        get = self.art_layers.get
        for s in L.sprites:
            lay = get(s["name"])
            if lay is not None:
                things.append((s["x"], s["y"], s["z"], s["w"], s["h"], lay, 1.5 if s.get("glow") else 1.0))
        pile = get("item:dc_gold_gold_pile_10.png") or get("sp.coins")
        pics = {"health": get("item:s7_P_Red01.png"), "mana": get("item:s7_P_Blue01.png"), "scroll": get("item:s7_I_Scroll.png")}
        for pk in L.pickups:                                            # (things lying about, in their own pictures)
            if pk["kind"] == "gold" and pile is not None:
                things.append((pk["x"], pk["y"], pk["z"], 0.42, 0.42, pile, 1.25))
            elif pics.get(pk["kind"]) is not None:
                bob = 0.05 * math.sin(now * 2.5 + pk["phase"])
                things.append((pk["x"], pk["y"] + 0.04 + bob, pk["z"], 0.34, 0.34, pics[pk["kind"]], 1.35))
        for d in getattr(g, "drops", ()):                               # (what was had, flying to him)
            if g.time < d["t"]:
                continue
            lay = get("item:" + (drop_picture(d["what"]) or ""))
            if lay is None:
                continue
            s = (0.34 if d["what"] != "gold" else 0.4) * (1 - 0.6 * d.get("fly", 0.0))
            things.append((d["x"], d["y"] - s * 0.5, d["z"], s, s, lay, 1.4))
        farm = getattr(g, "farm", None)
        if farm is not None and L.kind == "town":                      # (the crops in the farm's plots)
            from .itempics import crop_picture
            for i, p in enumerate(farm.plots):
                if p and i < len(L.farm_cells):
                    lay = get("item:" + (crop_picture(p["crop"], farm.stage(i)) or ""))
                    if lay is not None:
                        x, y = L.farm_cells[i]
                        h = 1.05 if farm.stage(i) else 0.8
                        things.append((x + 0.5, L.floor[y, x] - 0.02, y + 0.5, h, h, lay, 1.0))
        wood = get("fu.table")
        for f in g.fx:                                                  # (splinters of what broke)
            if f.get("kind") == "debris":
                lay = get(f.get("pic") or "")
                lay = lay if lay is not None and f.get("pic", "").startswith(("fu.", "sp.", "fungus")) else wood
                if lay is not None:
                    things.append((f["x"], f["y"], f["z"], f["size"] * 2, f["size"] * 2, lay, 0.9))
        data = dressmesh.billboards(things, g.eye, g.yaw)
        if len(data):
            self.bill_mesh.upload(data)
            self.bill_mesh.draw()
        GL.glActiveTexture(GL.GL_TEXTURE0)

    def _weather(self, g, L, view, now):
        sky = getattr(g, "sky", None)
        if sky is None:
            return
        right = view[0, :3]
        if L.outdoor and self.atm:
            data = weatherfx.surface(self.atm, g.eye, right, now, sky.twister(L.w), 0.0)
        elif 1 <= L.depth <= 10 and self.cells is not None:
            data = weatherfx.below(L, sky.now(), max(0.0, 1 - (L.depth - 1) / 10), g.eye, right, now, self.cells)
        else:
            return
        if not len(data):
            return
        self.wx_mesh.upload(data)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glDepthMask(GL.GL_FALSE)
        self.glow.use()
        self.glow.mat4("uProj", self._proj_cache)
        self.glow.mat4("uView", view)
        self.glow.float("uTime", now)
        self.wx_mesh.draw()
        GL.glDepthMask(GL.GL_TRUE)
        GL.glDisable(GL.GL_BLEND)

    def lightning(self, strength=1.0):
        self.flash = max(self.flash, strength)

    CHEST_SCALE = 0.5
    CHEST_OPEN = 1.95                      # (radians: the lid thrown back)

    def _chests(self, g, L, outdoor, atm):
        """Kenney's chest (assets/figures/chest.npz): the body, and the lid swinging back on its hinge when opened."""
        if self.chest is None or not L.chests:
            return
        C = self.chest
        bp, bc, bi = C["body_pos"], C["body_col"], C["body_idx"]
        lp, lc, li, hinge = C["lid_pos"], C["lid_col"], C["lid_idx"], C["hinge"]
        pos, col, idx = [], [], []
        n = 0
        for c in L.chests:
            if c.get("broken") or (c["x"] - g.x) ** 2 + (c["z"] - g.z) ** 2 > 40 * 40:
                continue
            M = gl.model_matrix(c["x"], c["y"], c["z"], c.get("yaw", 0.0), self.CHEST_SCALE)
            if c["opened"]:
                k = min(1.0, (g.time - c.get("opened_at", -99)) / 0.5)
                a = -self.CHEST_OPEN * (1 - (1 - k) ** 3)
            else:
                a = 0.0
            T = np.identity(4, np.float32)
            T[:3, 3] = hinge
            Ml = M @ T @ _rot_x(a)
            for P, Cc, Ii, Mm in ((bp, bc, bi, M), (lp, lc, li, Ml)):
                w = (np.concatenate([P, np.ones((len(P), 1), np.float32)], 1) @ Mm.T)[:, :3]
                pos.append(w)
                col.append(Cc)
                idx.append(Ii + n)
                n += len(P)
        if not pos:
            return
        if self.chest_mesh is None:
            self.chest_mesh = gl.Mesh([(0, 3), (1, 3)], np.zeros((0, 6), np.float32), np.zeros(0, np.uint32), dynamic=True)
        self.chest_mesh.upload(np.concatenate([np.concatenate(pos), np.concatenate(col)], 1).astype(np.float32),
                               np.concatenate(idx).astype(np.uint32))
        self.solid.use()
        self.solid.vec("uTint", (1, 1, 1) if outdoor else tuple(min(1.0, t) for t in L.tint))
        self.solid.float("uSnow", 0.0)
        self.chest_mesh.draw()

    def _sky(self, proj, view, sun_dir, fogc, atm, now):
        GL.glDepthMask(GL.GL_FALSE)
        self.sky.use()
        inv = np.linalg.inv(proj @ np.block([[view[:3, :3], np.zeros((3, 1))], [np.zeros((1, 3)), np.ones((1, 1))]]))
        self.sky.mat4("uInvPV", inv)
        A = atm or {"sky_top": (0.16, 0.30, 0.55), "sky_horizon": fogc, "moon_v": (0, -1, 0), "phase": 0, "sun_disc": 1.0,
                    "moon_disc": 0.0, "stars": 0.0, "cloud": 0.12, "wind": (0.2, (1, 0)), "aurora": 0.0, "rainbow": 0.0,
                    "storm": 0.0}
        self.sky.vec("uTop", A["sky_top"])
        self.sky.vec("uHorizon", A["sky_horizon"])
        self.sky.vec("uSunDir", sun_dir)
        self.sky.vec("uMoonV", A["moon_v"])
        self.sky.float("uPhase", A["phase"])
        self.sky.float("uSunDisc", A["sun_disc"])
        self.sky.float("uMoonDisc", A["moon_disc"])
        self.sky.float("uStars", A["stars"])
        self.sky.float("uCloud", A["cloud"])
        sp, (wx, wz) = A["wind"]
        self.sky.vec("uWind", (wx * (0.3 + sp), wz * (0.3 + sp)))
        self.sky.float("uTime", now)
        self.sky.float("uAurora", A["aurora"])
        self.sky.float("uRainbow", A["rainbow"])
        self.sky.float("uFlash", self.flash * 0.6)
        self.sky.float("uStorm", A["storm"])
        self.sky_mesh.draw()
        GL.glDepthMask(GL.GL_TRUE)

    def _lights(self, g, now):
        L = g.level
        ex, ey, ez = g.eye
        out = []
        if not L.outdoor:                                               # Claude's own light: the wand's glow
            amb = getattr(L, "amb", None)                               # (dimmer down a dark corridor)
            k = 0.5 + 0.5 * float(amb[min(L.h - 1, max(0, int(ez))), min(L.w - 1, max(0, int(ex)))]) if amb is not None else 1.0
            out.append(((ex, ey + 0.1, ez, 6.5), (0.5 * k, 0.46 * k, 0.38 * k, 1)))
        for b in g.bolts[:10]:
            c = D.ELEMENT_COLOUR[b.element]
            out.append(((b.x, b.y, b.z, 3.2 if not b.foe else 2.6), (c[0] * 0.9, c[1] * 0.9, c[2] * 0.9, 1)))
        for f in [f for f in g.fx if f.get("kind") != "debris"][-4:]:
            k = max(0.0, 1 - (g.time - f["t"]) / f.get("life", 0.5))
            c = f["c"]
            out.append(((f["x"], f["y"], f["z"], 2.5), (c[0] * k * 1.4, c[1] * k * 1.4, c[2] * k * 1.4, 1)))
        above = self._above(g)
        shafts = [(x, f + 1.0, z, above[0] * 0.9, above[1] * 0.9, above[2] * 0.9, 4.8, "shaft")
                  for x, z, f, _c in getattr(L, "shafts", ())] if above[3] > 0.05 else []
        torches = sorted(list(L.lights) + shafts, key=lambda t: (t[0] - ex) ** 2 + (t[2] - ez) ** 2)
        for t in torches[:MAX_LIGHTS - len(out)]:
            if len(t) > 7:                                          # (the light through a grate: steady)
                out.append(((t[0], t[1], t[2], t[6]), (t[3], t[4], t[5], 1)))
                continue
            fl = 0.85 + 0.15 * math.sin(now * 11 + t[0] * 3) * math.sin(now * 7.3 + t[2])
            torch = t[3] > 0.9 and t[4] < 0.7 and t[6] > 5
            k = 2.1 if torch and not L.outdoor else 1.3                 # (a torch below burns bright, and reaches)
            out.append(((t[0], t[1], t[2], t[6] * (1.3 if torch and not L.outdoor else 1.0)), (t[3] * fl * k, t[4] * fl * k, t[5] * fl * k, 1)))
        if L.stairs and not L.outdoor:
            out.append(((L.stairs[0], L.floor_at(*L.stairs) + 0.4, L.stairs[1], 4.0), (0.35, 0.5, 1.0, 1)))
        return out[:MAX_LIGHTS]

    def _above(self, g):
        """The light coming down through a grate: the day's (warm, pale) or the moon's (cold, faint), dulled by cloud
        -> (r, g, b, strength)."""
        sky = getattr(g, "sky", None)
        if sky is None:
            return (0.0, 0.0, 0.0, 0.0)
        kind = sky.now()["kind"]
        dull = 0.55 if kind in ("rain", "storm", "snow", "mist") else 0.8 if kind == "cloud" else 1.0
        if sky.night:
            k = 0.35 * dull
            return (0.55 * k, 0.65 * k, 0.95 * k, k)
        return (1.0 * dull, 0.93 * dull, 0.75 * dull, dull)

    # ---- figures -----------------------------------------------------------------------------------------------
    def _monster(self, g, m):
        fig = self.pack.figure("monster:" + (m.d.get("figure") or m.name))
        if not fig:
            return
        alpha = 1.0
        if m.dead:
            gone = g.time - m.dead_time
            if gone > 5.0:
                return
            alpha = 1.0 if gone < 3.5 else max(0.0, 1 - (gone - 3.5) / 1.5)
        if m.dead:
            cue = "die"
        elif m.strike >= 0:
            cue = "cast" if m.kind == "ranged" else "attack"
        elif m.hit_flash > 0.08:
            cue = "hit"
        else:
            cue = "walk" if m.moving else "idle"
        glow = (0, 0, 0)
        if "burn" in m.status:
            glow = (0.25, 0.08, 0.0)
        elif "chill" in m.status:
            glow = (0.0, 0.08, 0.2)
        elif m.status.get("venom"):
            glow = (0.03, 0.15, 0.0)
        flip = min(1.0, (g.time - m.dead_time) / FLIP_TIME) if m.dead else 0.0
        self._figure(fig["model"], fig, m.x, m.y + (m.lift * (1 - flip)), m.z, m.yaw, m.size, m.anim, cue, m.hit_flash,
                     m.dead, alpha, glow, flip=flip,
                     speed=1.0 if "chill" not in m.status else 0.55)

    def _figure(self, model_name, fig, x, y, z, yaw, size, st, cue, flash, dead, alpha, glow, speed=1.0, flip=0.0):
        try:
            G = self.gpu_figure(model_name)
        except KeyError:
            return
        M = G.model
        H = 0.8 * (fig.get("scale") or 1.0) * size
        s = min(H / max(1e-3, M.height()), H * 1.1 / max(1e-3, M.width()))
        # the clip: once for a strike, a hit and a death (held at its end), looped for walking and idling
        once = cue in ("attack", "cast", "hit", "die")
        clip = cue if M.has(cue) else ("attack" if cue == "cast" and M.has("attack") else ("idle" if M.has("idle") else None))
        if clip and cue in ("walk",) and not M.has("walk"):
            clip = "idle"
        if st.get("clip") != clip or (once and st.get("cue") != cue):
            if not (st.get("once") and st.get("clip") == clip and not dead):
                st["clip"], st["since"], st["once"], st["cue"] = clip, self.anim_now, once, cue
        t = (self.anim_now - st.get("since", 0)) * (1.0 if once else speed)
        if st.get("once") and clip and t > M.clips[clip].length and not dead:
            st["clip"] = None                                   # (done: back to walking or idling next frame)
        if dead:                                       # (the dead go stiff: they keep their standing pose, and flip)
            J = M.skin_matrices("idle" if M.has("idle") else None, 0.0)
        else:
            J = M.skin_matrices(clip, t, once=bool(st.get("once")))
        model = gl.model_matrix(x, y, z, yaw, s)
        offset = np.identity(4, np.float32)
        offset[:3, 3] = (-G.centre[0], -float(G.lo[1]), -G.centre[1])
        if flip > 0:
            model = model @ _flip_matrix(G, flip)
        self.fig.mat4("uModel", model @ offset)
        self.fig.mat4("uJoints", J, len(J))
        tint = fig.get("tint")
        if tint:
            self.fig.vec("uTint", [(c / 255) ** 2.2 for c in tint])
            self.fig.float("uTintMix", 0.55)
        else:
            self.fig.vec("uTint", (1, 1, 1))
            self.fig.float("uTintMix", 0.0)
        self.fig.float("uFlash", min(1.0, flash * 5))
        self.fig.float("uAlpha", alpha)
        self.fig.vec("uGlow", glow)
        if G.tex:
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, G.tex)
            self.fig.int("uTextured", 1)
        else:
            self.fig.int("uTextured", 0)
        if alpha < 1:
            GL.glEnable(GL.GL_BLEND)
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        G.mesh.draw()
        if alpha < 1:
            GL.glDisable(GL.GL_BLEND)

    # ---- glows -------------------------------------------------------------------------------------------------
    def _glows(self, g, view, now):
        L = g.level
        right = view[0, :3]
        up = view[1, :3]
        verts = []

        def bill(x, y, z, size, c, a=1.0, mode=0.0, stretch=1.0):
            r = right * size
            u = up * size * stretch
            p = np.array([x, y, z], np.float32)
            corners = (p - r - u, p + r - u, p + r + u, p - r + u)
            uvs = ((0, 0), (1, 0), (1, 1), (0, 1))
            for i in (0, 1, 2, 0, 2, 3):
                verts.append((*corners[i], *uvs[i], *c, a, mode))

        def flat(x, y, z, size, c, a, mode):
            corners = ((x - size, y, z - size), (x + size, y, z - size), (x + size, y, z + size), (x - size, y, z + size))
            uvs = ((0, 0), (1, 0), (1, 1), (0, 1))
            for i in (0, 1, 2, 0, 2, 3):
                verts.append((*corners[i], *uvs[i], *c, a, mode))

        for b in g.bolts:
            c = D.ELEMENT_COLOUR[b.element]
            bill(b.x, b.y, b.z, 0.16 if not b.foe else 0.22, c, 1.6)
            for k in (1, 2, 3):                                               # its tail
                t = k * 0.025
                bill(b.x - b.vx * t, b.y - b.vy * t, b.z - b.vz * t, 0.12 - k * 0.025, c, 0.7 - k * 0.15)
        for d in getattr(g, "drops", ()):                                # (a glint about what was had: in its rarity's colour)
            if g.time >= d["t"]:
                rk = d.get("rarity", -1)
                c = D.RARITIES[rk][2] if rk >= 1 else (0.9, 0.85, 0.7)
                bill(d["x"], d["y"], d["z"], 0.14 + 0.04 * max(0, rk), c, 0.3 + 0.12 * max(0, rk))
                if rk >= 2:                                                # (Rare and up: a pillar of its light)
                    fy = d.get("floor", d["y"] - 0.5)
                    bill(d["x"], fy + 0.9, d["z"], 0.12 + 0.03 * rk, c, 0.25 + 0.1 * rk, 4.0, 9.0)
                if rk >= 4:                                                # (Legendary: and a ring on the ground)
                    flat(d["x"], d.get("floor", d["y"] - 0.5) + 0.03, d["z"], 0.6, c, 1.0, 1.0)
        for f in g.fx:
            if f.get("kind") == "debris":
                continue
            k = (g.time - f["t"]) / f.get("life", 0.5)
            if k < 1:
                bill(f["x"], f["y"], f["z"], 0.15 + k * 0.45, f["c"], (1 - k) * 1.4)
        ex, ez = g.x, g.z
        for t in L.lights:
            if (t[0] - ex) ** 2 + (t[2] - ez) ** 2 > 900:
                continue
            if t[3] > 0.9 and t[4] < 0.7 and t[6] > 5:                     # (a torch: its flame, and the glow about it)
                big = not L.outdoor
                bill(t[0], t[1] + 0.05, t[2], 0.17 if big else 0.13, (1.0, 0.6, 0.25), 1.8 if big else 1.6, 3.0, 1.6)
                if big:
                    bill(t[0], t[1], t[2], 0.6, (1.0, 0.55, 0.22), 0.28)
            else:                                                       # (a glowing thing: its halo)
                bill(t[0], t[1], t[2], 0.35, (t[3], t[4], t[5]), 0.35)
        for k, (dx, dtop, dz, dfloor) in enumerate(getattr(L, "drips", ())):
            if (dx - ex) ** 2 + (dz - ez) ** 2 > 225:
                continue
            ph = (now * 0.75 + k * 0.618) % 1.0                         # (a drop falls, then a splash)
            if ph < 0.8:
                t = ph / 0.8
                bill(dx, dtop - (dtop - dfloor) * t * t, dz, 0.035, (0.55, 0.7, 0.9), 1.4, 0.0, 1.8)
            else:
                k2 = (ph - 0.8) / 0.2
                bill(dx, dfloor + 0.02, dz, 0.05 + k2 * 0.12, (0.5, 0.65, 0.85), (1 - k2) * 0.9)
        for pk in getattr(L, "pickups", ()):                         # (potions, scrolls and finds, glowing)
            if pk["kind"] == "gold" or (pk["x"] - ex) ** 2 + (pk["z"] - ez) ** 2 > 600:
                continue
            if pk["kind"] != "item":                                    # (a potion or scroll: a faint glow under it)
                c = {"health": (1.0, 0.25, 0.2), "mana": (0.3, 0.45, 1.0), "scroll": (0.9, 0.8, 0.5)}[pk["kind"]]
                bill(pk["x"], pk["y"] + 0.2, pk["z"], 0.25, c, 0.3)
                continue
            c = {"health": (1.0, 0.25, 0.2), "mana": (0.3, 0.45, 1.0), "scroll": (0.9, 0.8, 0.5), "item": (1.0, 0.85, 0.4)}[pk["kind"]]
            bobh = pk["y"] + 0.25 + 0.06 * math.sin(now * 2.5 + pk["phase"])
            bill(pk["x"], bobh, pk["z"], 0.14, c, 1.4)
            if pk["kind"] == "item":
                bill(pk["x"], bobh, pk["z"], 0.3 + 0.05 * math.sin(now * 5 + pk["phase"]), c, 0.35)
        above = self._above(g)
        if above[3] > 0.05:                                             # (light through the grates, and dust in it)
            cam_r = np.array([view[0, 0], 0.0, view[0, 2]], np.float32)
            cam_r /= max(1e-4, float(np.linalg.norm(cam_r)))
            col = tuple(c * 0.8 for c in above[:3])
            for k, (x, z, f, c) in enumerate(getattr(L, "shafts", ())):
                if (x - ex) ** 2 + (z - ez) ** 2 > 700:
                    continue
                bot, top = cam_r * 0.62, cam_r * 0.36
                quad = [(x - bot[0], f, z - bot[2], 0, 0), (x + bot[0], f, z + bot[2], 1, 0),
                        (x + top[0], c, z + top[2], 1, 1), (x - top[0], c, z - top[2], 0, 1)]
                for i in (0, 1, 2, 0, 2, 3):
                    q = quad[i]
                    verts.append((q[0], q[1], q[2], q[3], q[4], *col, 1.25, 7.0))
                flat(x, f + 0.015, z, 0.7, above[:3], 0.95 * above[3], 0.0)
                for m in range(7):                                     # (motes, turning slowly as they sink)
                    ph = (now * 0.05 + m * 0.143 + k * 0.37) % 1.0
                    a = m * 2.4 + now * 0.3
                    bill(x + math.cos(a) * 0.2, c - (c - f) * ph, z + math.sin(a) * 0.2, 0.025, above[:3], 0.9 * math.sin(ph * math.pi))
        if L.stairs and not L.outdoor:
            sx, sz = L.stairs
            sealed = L.guardian and not g.guardian_down
            c = (1.0, 0.35, 0.25) if sealed else (0.45, 0.65, 1.0)
            flat(sx, L.floor_at(sx, sz) + 0.02, sz, 0.95, c, 1.2, 1.0)
            bill(sx, L.floor_at(sx, sz) + 0.6, sz, 0.55, c, 0.35, 0.0, 1.6)
        if L.outdoor and L.portal:
            px, pz = L.portal
            fy = L.floor_at(px, pz)
            flat(px, fy + 0.03, pz, 2.1, (0.45, 0.35, 1.0), 1.3, 2.0)
            flat(px, fy + 0.05, pz, 2.3, (0.6, 0.5, 1.0), 0.8, 1.0)
            bill(px, fy + 0.9, pz, 0.9, (0.5, 0.4, 1.0), 0.3, 0.0, 1.5)
        self.arcs = [a for a in self.arcs if now - a[2] < 0.25]
        for a in self.arcs:
            (x0, y0, z0), (x1, y1, z1), born = a
            k = 1 - (now - born) / 0.25
            if k <= 0:
                continue
            for i in range(9):
                t = i / 8
                jit = 0.0 if i in (0, 8) else 0.12
                bill(x0 + (x1 - x0) * t + np.random.uniform(-jit, jit), y0 + (y1 - y0) * t + np.random.uniform(-jit, jit),
                     z0 + (z1 - z0) * t + np.random.uniform(-jit, jit), 0.1, (0.95, 0.95, 0.6), k * 1.3)
        if not verts:
            return
        self.glow_mesh.upload(np.array(verts, np.float32))
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_ONE, GL.GL_ONE)
        GL.glDepthMask(GL.GL_FALSE)
        self.glow.use()
        self.glow.mat4("uProj", self._proj_cache)
        self.glow.mat4("uView", view)
        self.glow.float("uTime", now)
        self.glow_mesh.draw()
        GL.glDepthMask(GL.GL_TRUE)
        GL.glDisable(GL.GL_BLEND)

    # ---- the wand ----------------------------------------------------------------------------------------------
    def _wand(self, g, proj, view, now, dt, lights, common):
        w = g.player.wand()
        if w is None:
            return
        try:
            G = self.gpu_figure("gear:wand")
        except KeyError:
            return
        self.recoil = max(0.0, self.recoil - dt * 6)
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
        M = G.model
        J = M.skin_matrices(None, 0)
        if not hasattr(G, "grip"):                     # (the wand lies along -z at rest, its gem at the -z end)
            v = M.skinned(J)
            G.grip = np.array([v[:, 0].mean(), v[:, 1].mean(), v[:, 2].max() - 0.15], np.float32)
            G.tip = np.array([v[:, 0].mean(), v[:, 1].mean(), v[:, 2].min()], np.float32)
            G.length = float(v[:, 2].max() - v[:, 2].min())
        s = 0.34 / max(1e-3, G.length)
        sway = math.sin(self.bob * 0.5) * 0.008
        # in view space: low and to the right, pointing ahead and a little up and in
        cam_inv = np.linalg.inv(view)
        hold = np.identity(4, np.float32)
        hold[:3, 3] = (0.16 + sway, -0.21 + abs(math.sin(self.bob)) * 0.008 - self.recoil * 0.015, -0.30 + self.recoil * 0.05)
        tilt = _rot_y(math.radians(9)) @ _rot_x(math.radians(13 + self.recoil * 10))
        centre = np.identity(4, np.float32)
        centre[:3, 3] = -G.grip
        scale = np.diag([s, s, s, 1]).astype(np.float32)
        model = cam_inv @ hold @ tilt @ scale @ centre
        self.fig.use()
        self.fig.mat4("uModel", model)
        self.fig.mat4("uJoints", J, len(J))
        self.fig.vec("uTint", (1, 1, 1))
        self.fig.float("uTintMix", 0.0)
        self.fig.float("uFlash", 0.0)
        self.fig.float("uAlpha", 1.0)
        el = g.player.wand_stats()["element"]
        c = D.ELEMENT_COLOUR[el]
        self.fig.vec("uGlow", (c[0] * 0.05, c[1] * 0.05, c[2] * 0.05))
        if G.tex:
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, G.tex)
            self.fig.int("uTextured", 1)
        G.mesh.draw()
        # the gem's glow at the tip
        tip = model @ np.array([*G.tip, 1.0], np.float32)
        self._tip = tip[:3]
        verts = []
        right, up = view[0, :3], view[1, :3]
        size = 0.035 + 0.02 * math.sin(now * 6) ** 2 + self.recoil * 0.05
        p = tip[:3]
        corners = (p - right * size - up * size, p + right * size - up * size, p + right * size + up * size, p - right * size + up * size)
        uvs = ((0, 0), (1, 0), (1, 1), (0, 1))
        for i in (0, 1, 2, 0, 2, 3):
            verts.append((*corners[i], *uvs[i], *c, 1.5, 0.0))
        self.glow_mesh.upload(np.array(verts, np.float32))
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_ONE, GL.GL_ONE)
        GL.glDepthMask(GL.GL_FALSE)
        self.glow.use()
        self.glow.mat4("uProj", proj)
        self.glow.mat4("uView", view)
        self.glow_mesh.draw()
        GL.glDepthMask(GL.GL_TRUE)
        GL.glDisable(GL.GL_BLEND)

    def kick(self):
        self.recoil = 1.0

    def arc(self, a, b):
        self.arcs.append((a, b, time.perf_counter() - self.t0))


def _float_texture(A):
    """A float RGBA texture (h, w, 4), filtered, held at its edges."""
    h, w = A.shape[:2]
    tex = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA16F, w, h, 0, GL.GL_RGBA, GL.GL_FLOAT, np.ascontiguousarray(A, np.float32))
    for k, v in ((GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE), (GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE),
                 (GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR), (GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)):
        GL.glTexParameteri(GL.GL_TEXTURE_2D, k, v)
    return tex


def _rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]], np.float32)


FLIP_TIME = 0.45


def _flip_matrix(G, k):
    """A dead figure flipping over, k from 0 to 1, in its own units (feet at 0, centred): one that stands tall falls
    flat on its back; one that's long or round (a rat, a wolf, a blob) rolls over belly-up - with a little hop."""
    lo, hi = G.lo, G.hi
    h = float(hi[1] - lo[1])
    depth = float(hi[2] - lo[2])
    e = 1 - (1 - k) ** 3                                  # (quick, then settling)
    hop = math.sin(min(1.0, k) * math.pi) * h * 0.25
    if h > depth * 1.15:                                  # a biped: onto its back
        a = -math.pi / 2 * e
        R = _rot_x(a)
        T = np.identity(4, np.float32)
        T[1, 3] = depth / 2 * e + hop
        return T @ R
    a = math.pi * e                                       # four legs or none: belly-up, rolled about its length
    pivot = np.identity(4, np.float32)
    pivot[1, 3] = h / 2
    back = np.identity(4, np.float32)
    back[1, 3] = -h / 2
    T = np.identity(4, np.float32)
    T[1, 3] = hop
    return T @ pivot @ _rot_z(a) @ back


def _rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]], np.float32)


def _rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)


def project(proj_view, p, w, h):
    """A world point to window pixels (None when behind the eye)."""
    v = proj_view @ np.array([p[0], p[1], p[2], 1.0], np.float32)
    if v[3] <= 0.05:
        return None
    x, y = v[0] / v[3], v[1] / v[3]
    return ((x * 0.5 + 0.5) * w, (1 - (y * 0.5 + 0.5)) * h)

