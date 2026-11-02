"use strict";
// The first-person view, in WebGL 2: the floor's walls, floor and ceiling as one mesh built when the floor is
// entered; chests, hatches and monsters as billboards rebuilt each frame; a torch that falls off with distance and
// flickers, and fog the colour of the depth. The camera steps and turns smoothly (or snaps, if that's the setting).
const VERT = `#version 300 es
precision highp float;
in vec3 aPos; in vec3 aUV; in float aShade; in vec3 aFx;
uniform mat4 uViewProj; uniform float uTime; uniform vec3 uWind;   // (v24.0) the wind: its way (x, z) and strength
out vec3 vWorld; out vec3 vUV; out float vShade; out vec3 vFx;
void main() { vec3 p = aPos; vec3 fx = aFx;
  if (aFx.x < 0.0) { float along = p.x * uWind.x + p.z * uWind.y, g = 0.5 + 0.5 * sin(uTime * 0.9 - along * 0.35);   // (a top that gives: the gust and its own flutter)
    float w = uWind.z * (0.3 + 0.7 * g * g + 0.22 * sin(uTime * 3.1 + p.x * 1.7 + p.z * 2.3)); p.xz += uWind.xy * (-aFx.x) * w; p.y -= abs(-aFx.x * w) * 0.25; fx.x = 0.0; }
  vWorld = p; vUV = aUV; vShade = aShade; vFx = fx; gl_Position = uViewProj * vec4(p, 1.0); }`;

// aFx: a hit's red flash, the alpha (a foe fading), and glow - how much of the texture's own colour shows unlit;
// a glow of 2 is the sky's own things (the sun, the moon: the picture as it is, no light, no fog), 3 the sky dome
// (the picture's red is how high: the horizon's colour to the zenith's)
const FRAG = `#version 300 es
precision highp float; precision highp sampler2DArray;
in vec3 vWorld; in vec3 vUV; in float vShade; in vec3 vFx;
uniform sampler2DArray uTex; uniform sampler2DArray uShared; uniform sampler2DArray uSurf;   // (v26.0: the outdoors' drawn pictures, 2000 and up)
 uniform vec3 uEye; uniform vec3 uTorch; uniform vec3 uFog;
uniform float uReach; uniform float uFlicker; uniform float uAmbient;
uniform vec3 uZenith; uniform vec3 uHorizon;
uniform int uLights; uniform vec4 uLightPos[24]; uniform vec3 uLightCol[24];   // the lights about the party: xyz, reach in w; colour (24 since v22.0)
uniform vec3 uTorchPos; uniform float uBump;   // (v22.0) where the party's torch is held, a little to the side and up; (v22.1) the relief's strength - 0 for all but walls, floors and the ground
uniform vec3 uSun; uniform float uSunK; uniform vec3 uGrade;                    // the sun's (or the moon's) direction and strength on the surface; the band's grade
uniform float uTime; uniform float uWet; uniform float uSnow; uniform float uMist; uniform float uHaze; uniform float uShaft; uniform vec3 uLift; uniform vec3 uLook;   // (v22.4: the band's lift in the shadows; contrast, saturation, frost)   // (v22.3: the air's body; the sunbeams)                                       // the time, for the water's ripples; the rain on the ground (0 dry .. 1 wet)
out vec4 fragColor;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y); }
vec3 shafts(vec3 vdir, float d) {                                          // (v22.3) looking toward the sun: bars of light standing in the air, the dust drifting in them
  if (uShaft <= 0.0 || uSunK <= 0.0) return vec3(0.0);
  vec3 sa = normalize(cross(uSun, vec3(0.0, 1.0, 0.001))), sb = cross(uSun, sa), q = uEye + vdir * min(d, 14.0) * 0.6;   // (the air part way along the look, not the surface)
  float bars = smoothstep(0.4, 0.8, vnoise(vec2(dot(q, sa) * 1.1, dot(q, sb) * 0.18 + uTime * 0.015))), toward = pow(max(dot(vdir, uSun), 0.0), 2.0);
  float dust = step(0.993, hash(floor(gl_FragCoord.xy * 0.5) + floor(uTime * 3.0))) * 0.5;
  return mix(uHorizon, vec3(1.0, 0.92, 0.72), 0.7) * uShaft * toward * bars * (0.55 + dust) * smoothstep(1.0, 7.0, d);
}
void main() {
  bool shared = vUV.z > 999.5;                                            // a layer of 1000 and up is the shared texture's (what never changes between bands)
  bool surf = vUV.z > 1999.5;
  vec4 ts = texture(uShared, vec3(vUV.xy, max(vUV.z - 1000.0, 0.0))), tt = texture(uTex, vec3(vUV.xy, min(vUV.z, 999.0))), tf = texture(uSurf, vec3(vUV.xy, max(vUV.z - 2000.0, 0.0)));
  vec4 t = surf ? tf : shared ? ts : tt;
  if (vFx.z > 2.5 && vFx.z < 3.5) { fragColor = vec4(mix(uHorizon, uZenith, t.r) + shafts(normalize(vWorld - uEye), 40.0) * 0.45, 1.0); return; }
  if (t.a < 0.5) discard;
  if (vFx.z > 1.5 && vFx.z < 3.5) { fragColor = vec4(t.rgb, t.a * vFx.y); return; }
  float d = distance(vWorld, uEye);
  if (vFx.z > 3.5) {                                                          // water (glow 4): it ripples, shows the sky (or the torch) by the angle, and glints
    vec2 p = vWorld.xz; float tm = uTime, flow = vFx.x;                  // (v24.1: vFx.x on water is its current - the river's; 0 still)
    if (flow > 0.0) p.y -= tm * 0.6 * flow;                                 // (the ripples carried downstream)
    float amp = flow > 0.0 ? 1.0 + 0.4 * flow : 0.3 + 0.7 * uWet;           // (still water lies calm and mirrors the sky; rain or a current stirs it)
    vec3 wn = normalize(vec3(amp * (0.14 * sin(p.x * 6.3 + tm * 1.7) + 0.08 * sin((p.x + p.y) * 11.0 - tm * 2.3)), 1.0, amp * (0.14 * cos(p.y * 5.7 - tm * 1.3) + 0.08 * cos((p.x - p.y) * 9.0 + tm * 1.9))));
    if (uWet > 0.0) { vec2 g = vWorld.xz * 2.5, id = floor(g), f = fract(g) - 0.5, c = (vec2(hash(id + 3.1), hash(id + 7.7)) - 0.5) * 0.6, q = f - c;   // (v24.1: the rain's rings, one a cell, each in its own time)
      float ph = fract(tm * 0.8 + hash(id)), rd = length(q), ring = exp(-pow((rd - ph * 0.45) * 28.0, 2.0)) * (1.0 - ph) * uWet;
      wn = normalize(wn + vec3(q.x, 0.0, q.y) / max(rd, 0.001) * ring * 0.7); }
    vec3 v = normalize(uEye - vWorld), r = reflect(-v, wn);
    float fr = 0.12 + 0.5 * pow(1.0 - max(dot(v, wn), 0.0), 3.0);
    float r2w = uReach * uReach, lw = uAmbient + uFlicker * r2w / (r2w + 2.2 * d * d + 0.4 * d);
    vec3 base = t.rgb * vec3(0.3, 0.46, 0.55) * vShade * uTorch * lw * uGrade;   // (deep water: dark, a little green)
    vec3 seen = uSunK > 0.0 ? mix(uHorizon, uZenith, clamp(r.y * 1.4, 0.0, 1.0)) * 0.75 * vec3(0.8, 0.92, 1.0) : uTorch * lw * 0.55;
    float glint = uSunK > 0.0 ? pow(max(dot(r, uSun), 0.0), 90.0) * 1.6 * uSunK : pow(max(dot(wn, v), 0.0), 160.0) * 0.9 * lw;
    vec3 wc = mix(base, seen, fr) + glint * vec3(1.0, 0.95, 0.82);
    wc = mix(wc, uFog, smoothstep(uReach * 0.55, uReach * 1.7, d));
    fragColor = vec4(wc, 0.86 * vFx.y); return;
  }
  float r2 = uReach * uReach;
  vec3 n = normalize(cross(dFdx(vWorld), dFdy(vWorld)));                      // the surface's facing, from the triangle itself
  if (dot(n, uEye - vWorld) < 0.0) n = -n;
  float spec = 0.0; vec3 n0 = n;
  if (uBump > 0.0 && vFx.z < 0.5) {                                        // (v22.1) relief: walls, floors and the ground take it from their own pictures
    vec2 px = 1.0 / vec2(surf ? textureSize(uSurf, 0).xy : shared ? textureSize(uShared, 0).xy : textureSize(uTex, 0).xy), uv = vUV.xy;
    float lz = surf ? max(vUV.z - 2000.0, 0.0) : shared ? max(vUV.z - 1000.0, 0.0) : min(vUV.z, 999.0);
    #define HT(o) dot((surf ? texture(uSurf, vec3(uv + (o), lz)) : shared ? texture(uShared, vec3(uv + (o), lz)) : texture(uTex, vec3(uv + (o), lz))).rgb, vec3(0.3, 0.59, 0.11))
    float hu = HT(vec2(px.x, 0.0)) - HT(vec2(-px.x, 0.0)), hv = HT(vec2(0.0, px.y)) - HT(vec2(0.0, -px.y));
    vec3 dpx = dFdx(vWorld), dpy = dFdy(vWorld); vec2 dux = dFdx(uv), duy = dFdy(uv);
    vec3 r1 = cross(dpy, n), r2 = cross(n, dpx); float det = dot(dpx, r1);
    vec3 grad = sign(det) * (hu * 0.5 / max(px.x, 1e-6) * (r1 * dux.x + r2 * duy.x) + hv * 0.5 / max(px.y, 1e-6) * (r1 * dux.y + r2 * duy.y));
    n = normalize(abs(det) * n - uBump * 0.02 * grad);
    vec3 v = normalize(uEye - vWorld), lt = normalize(uTorchPos - vWorld);
    spec = pow(max(dot(reflect(-lt, n), v), 0.0), 24.0) * (0.06 + 0.5 * uWet * step(0.7, n.y));   // (a little sheen on stone, more on wet ground)
  }
  vec3 tl = uTorchPos - vWorld, tdir = tl / max(length(tl), 0.001); float tface = 0.5 + 0.5 * max(dot(n0, tdir), 0.0);
  float relief = clamp(max(dot(n, tdir), 0.0) / max(dot(n0, tdir), 0.25), 0.35, 1.6);   // (v22.1: how much more or less a raised or sunk bit faces the torch than the flat wall does)
  tface *= mix(1.0, relief, min(1.0, uBump));   // (v22.0: the torch is held, not worn at the eye: what faces it, lit more)
  float light = uAmbient + uFlicker * r2 / (r2 + 2.2 * d * d + 0.4 * d) * tface;
  if (uSunK > 0.0) light *= mix(1.0, 0.62 + 0.55 * max(dot(n, uSun), 0.0), uSunK * step(abs(n0.y), 0.7));   // walls facing the sun lit, the others in shade
  vec3 extra = vec3(0.0), vdir = (vWorld - uEye) / max(d, 0.001), airGlow = vec3(0.0);
  for (int i = 0; i < 24; i++) {
    if (i >= uLights) break;
    vec3 L = uLightPos[i].xyz - vWorld; float ld = length(L), reach = uLightPos[i].w;
    float fall = max(0.0, 1.0 - ld / reach); fall *= fall;
    vec3 Ld = L / max(ld, 0.001); float face = (0.35 + 0.65 * max(dot(n0, Ld), 0.0)) * mix(1.0, clamp(max(dot(n, Ld), 0.0) / max(dot(n0, Ld), 0.25), 0.35, 1.6), min(1.0, uBump));
    extra += uLightCol[i] * fall * face;
    if (uHaze > 0.0) { vec3 EL = uLightPos[i].xyz - uEye; float tt = clamp(dot(EL, vdir), 0.0, d), md = length(EL - vdir * tt); airGlow += uLightCol[i] * exp(-md * md * 3.0) * smoothstep(0.0, 1.0, tt); }   // (v22.3: the lamp's glow in the air between)
  }
  vec3 col = t.rgb * vShade * (uTorch * light + extra) * uGrade;
  col += spec * uTorch * min(light, 1.2) * uGrade;
  float up = abs(n.y) > 0.97 ? 1.0 : n.y;                                 // (a level top takes snow seen from either side: the eye can stand at a hedge's height)
  if (uSnow > 0.0 && up > 0.55) { float cover = uSnow >= 0.99 ? 1.0 : smoothstep(-0.06, 0.06, uSnow - 0.85 * vnoise(vWorld.xz * 1.3) - 0.08);   // (v24.2: snow comes in patches as it builds, and goes the same way)
    col = mix(col, vec3(0.93, 0.95, 0.99) * (uTorch * light + extra) * uGrade, cover * smoothstep(0.55, 0.8, up) * 0.88); }   // snow lying on what faces up
  if (uWet > 0.0 && n.y > 0.7) {                                            // the rain on the ground: darker, and the sky in it at a low angle
    vec3 v = normalize(uEye - vWorld); float fw = pow(1.0 - max(v.y, 0.0), 4.0);
    col = col * (1.0 - 0.28 * uWet) + uWet * fw * mix(uHorizon, uZenith, 0.4) * 0.45;
  }
  float fog = smoothstep(uReach * 0.55, uReach * 1.7, d);
  fog = max(fog, uMist * (1.0 - smoothstep(0.0, 1.4, vWorld.y)) * smoothstep(0.8, 7.0, d) * 0.85);   // (mist: lying low on the land)
  if (uHaze > 0.0) {                                                        // (v22.3) the air has a body: it drifts, lies thicker low, and the lights glow in it
    float drift = 0.6 * vnoise(vWorld.xz * 0.35 + vec2(uTime * 0.06, uTime * 0.025)) + 0.4 * vnoise(vWorld.xz * 0.9 - vec2(uTime * 0.04, -uTime * 0.03));
    float body = uHaze * smoothstep(0.4, 5.0, d) * (1.0 - 0.6 * smoothstep(0.0, 1.2, vWorld.y)) * (0.5 + 0.9 * drift);
    fog = max(fog, min(0.8, body * 0.6));
    col += airGlow * uHaze * 0.22 * (1.0 - fog * 0.5) + uTorch * uFlicker * uHaze * 0.05 * (1.0 - exp(-d * 0.35)) * (1.0 - fog);
  }
  if (uLook.z > 0.0 && abs(n0.y) < 0.7) {                                   // (v22.4) a winter morning: frost on the walls, thickest low and in patches
    float fr = uLook.z * smoothstep(0.25, 0.65, vnoise(vec2(vWorld.x + vWorld.z, vWorld.y) * 5.0)) * (1.0 - smoothstep(0.2, 1.1, vWorld.y)) * 0.85;
    col = mix(col, vec3(0.82, 0.9, 1.0) * (uTorch * light + extra) * uGrade, fr);
  }
  col = mix(col, uFog, fog);
  col += shafts(vdir, d);
  { float lum = dot(col, vec3(0.3, 0.59, 0.11)); col = mix(vec3(lum), col, uLook.y); col = max((col - 0.18) * uLook.x + 0.18 + uLift * (1.0 - col), 0.0); }   // (v22.4: the grade - saturation, contrast about the dark's middle, the lift)
  col = mix(col, t.rgb, vFx.z * (1.0 - fog * 0.7));
  col = mix(col, vec3(1.0, 0.3, 0.2), vFx.x);
  fragColor = vec4(col, t.a * vFx.y);
}`;

// (v22.5) the glow: the frame is drawn off screen, what is bright in it taken out at a quarter size, blurred, and laid
// back over it - magic, portals, lamps, the sun softly haloed
const POST_VERT = `#version 300 es
in vec2 aP; out vec2 vT; void main() { vT = aP * 0.5 + 0.5; gl_Position = vec4(aP, 0.0, 1.0); }`;
const BRIGHT_FRAG = `#version 300 es
precision highp float; in vec2 vT; uniform sampler2D uSrc; uniform vec2 uPx; uniform float uThresh; out vec4 o;
void main() { vec3 c = vec3(0.0);
  for (int i = 0; i < 4; i++) { vec2 off = vec2(float(i % 2) - 0.5, float(i / 2) - 0.5) * uPx * 2.0; vec3 s = texture(uSrc, vT + off).rgb; float l = max(s.r, max(s.g, s.b)); c += s * smoothstep(uThresh, 1.0, l); }
  o = vec4(c * 0.25, 1.0); }`;
const BLUR_FRAG = `#version 300 es
precision highp float; in vec2 vT; uniform sampler2D uSrc; uniform vec2 uDir; out vec4 o;
void main() { vec3 c = texture(uSrc, vT).rgb * 0.227;
  c += (texture(uSrc, vT + uDir * 1.385).rgb + texture(uSrc, vT - uDir * 1.385).rgb) * 0.316;
  c += (texture(uSrc, vT + uDir * 3.231).rgb + texture(uSrc, vT - uDir * 3.231).rgb) * 0.070;
  o = vec4(c, 1.0); }`;
const COMPOSE_FRAG = `#version 300 es
precision highp float; in vec2 vT; uniform sampler2D uSrc; uniform sampler2D uGlow; uniform float uK; out vec4 o;
void main() { vec3 s = texture(uSrc, vT).rgb, g = texture(uGlow, vT).rgb; o = vec4(s + g * uK * (1.0 - s * 0.5), 1.0); }`;

const STRIDE = 10;                     // floats a vertex: pos 3, uv 3, shade 1, fx 3
const EYE_HEIGHT = 0.5;

function mat4Perspective(fovY, aspect, near, far) {
  const f = 1 / Math.tan(fovY / 2), nf = 1 / (near - far);
  return new Float32Array([f / aspect, 0, 0, 0, 0, f, 0, 0, 0, 0, (far + near) * nf, -1, 0, 0, 2 * far * near * nf, 0]);
}

function mat4LookAt(eye, target, up) {
  let zx = eye[0] - target[0], zy = eye[1] - target[1], zz = eye[2] - target[2];
  let len = Math.hypot(zx, zy, zz) || 1; zx /= len; zy /= len; zz /= len;
  let xx = up[1] * zz - up[2] * zy, xy = up[2] * zx - up[0] * zz, xz = up[0] * zy - up[1] * zx;
  len = Math.hypot(xx, xy, xz) || 1; xx /= len; xy /= len; xz /= len;
  const yx = zy * xz - zz * xy, yy = zz * xx - zx * xz, yz = zx * xy - zy * xx;
  return new Float32Array([xx, yx, zx, 0, xy, yy, zy, 0, xz, yz, zz, 0,
    -(xx * eye[0] + xy * eye[1] + xz * eye[2]), -(yx * eye[0] + yy * eye[1] + yz * eye[2]), -(zx * eye[0] + zy * eye[1] + zz * eye[2]), 1]);
}

function mat4Mul(a, b) {
  const out = new Float32Array(16);
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
    let s = 0;
    for (let k = 0; k < 4; k++) s += a[k * 4 + j] * b[i * 4 + k];
    out[i * 4 + j] = s;
  }
  return out;
}

CM.Renderer = class {
  constructor(canvas) {
    this.canvas = canvas;
    this.ok = false;
    this.error = "";
    const gl = canvas.getContext("webgl2", { antialias: true, alpha: false, depth: true, preserveDrawingBuffer: true });
    if (!gl) { this.error = "This needs WebGL 2, and the browser hasn't got it."; return; }
    this.gl = gl;
    this.program = this._program(VERT, FRAG);
    if (!this.program) return;
    this.loc = {};
    for (const n of ["uViewProj", "uTex", "uShared", "uSurf", "uEye", "uTorch", "uFog", "uReach", "uFlicker", "uAmbient", "uZenith", "uHorizon", "uLights", "uLightPos", "uLightCol", "uTorchPos", "uBump", "uSun", "uSunK", "uGrade", "uTime", "uWet", "uSnow", "uMist", "uHaze", "uShaft", "uLift", "uLook", "uWind"]) this.loc[n] = gl.getUniformLocation(this.program, n);
    this.staticBuf = gl.createBuffer(); this.staticCount = 0;
    this.dynBuf = gl.createBuffer(); this.dynCount = 0;
    this.texture = null; this.index = {};
    this.theme = CM.THEMES[0];
    this.eye = [1.5, EYE_HEIGHT, 1.5];
    this.yaw = 0;                      // radians; 0 looks north (-z), pi/2 east
    this.move = null;                  // {from, to, t, ms}
    this.turn = null;                  // {from, to, t, ms}
    this.sprites = [];
    this.time = 0;
    this.flicker = 1;
    this.viewProj = null;
    this.snap = false;
    this.bob = 0;
    this.light = 1;                    // how far the torch reaches, as a share of the depth's reach (1: a good torch)
    this.sky = null;                   // on the surface: CM.sky(game) this frame (the colours, the light, the sun and the moon); null below
    this.seed = ""; this.density = CM.DETAIL.medium; this.sub = {};   // the props: the run's seed and how many (the Detail setting), and where each sits in its layer
    this.standing = [];                // the floor's standing props, for the frame's billboards
    this.lights = [];                  // [{x, y, z, reach, colour [r, g, b], flicker}]: what lights the walls about the party this frame (24 at most since v22.0)
    this.season = "summer";           // the run's season, for what grows
    this.lightNow = 1;                 // (eased towards it)
    this.ok = true;
    gl.enable(gl.DEPTH_TEST);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    this.resize();
  }

  _program(vs, fs) {
    const gl = this.gl;
    const make = (kind, src) => {
      const s = gl.createShader(kind);
      gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) { this.error = "A shader didn't compile: " + gl.getShaderInfoLog(s); return null; }
      return s;
    };
    const v = make(gl.VERTEX_SHADER, vs), f = make(gl.FRAGMENT_SHADER, fs);
    if (!v || !f) return null;
    const p = gl.createProgram();
    gl.attachShader(p, v); gl.attachShader(p, f);
    gl.bindAttribLocation(p, 0, "aPos"); gl.bindAttribLocation(p, 1, "aUV"); gl.bindAttribLocation(p, 2, "aShade"); gl.bindAttribLocation(p, 3, "aFx");
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) { this.error = "The shaders didn't link: " + gl.getProgramInfoLog(p); return null; }
    return p;
  }

  resize() {
    const dpr = Math.min(2, window.devicePixelRatio || 1) * (this.scale || 1);   // (Settings > Render scale, or the automatic step-down when frames come late)
    const w = Math.max(1, Math.round(this.canvas.clientWidth * dpr)), h = Math.max(1, Math.round(this.canvas.clientHeight * dpr));
    if (this.canvas.width !== w || this.canvas.height !== h) { this.canvas.width = w; this.canvas.height = h; }
    this.gl.viewport(0, 0, w, h);
  }

  // ---- the textures ----
  // a set's pictures go two ways: the band's own (CM.art.isThemeLayer) into the band's texture at the set's size, and
  // the rest into the shared texture at CM.SHARED_SIZE - uploaded only when the shared ones are not already there
  // (art.sharedKey: the look). A layer of another size is scaled as it goes up.
  // (v21.4) gentle: behind the title card, the layers go up a slice a frame (the first read of a freshly painted canvas
  // is where the browser really paints it, a few milliseconds each), so the card stays smooth; the mipmaps when done
  _upload(tex, layers, size, crisp, gentle) {
    const gl = this.gl;
    gl.bindTexture(gl.TEXTURE_2D_ARRAY, tex);
    gl.texImage3D(gl.TEXTURE_2D_ARRAY, 0, gl.RGBA8, size, size, Math.max(1, layers.length), 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    if (gentle && typeof requestAnimationFrame !== "undefined") { let i = 0; const step = () => { if (!gl.isTexture(tex)) return; const until = performance.now() + 6; gl.bindTexture(gl.TEXTURE_2D_ARRAY, tex);
        while (i < layers.length && performance.now() < until) { this._layer(tex, layers[i], i, size, crisp); i++; }
        if (i < layers.length) requestAnimationFrame(step); else this._finish(tex, crisp); };
      gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_MAG_FILTER, crisp ? gl.NEAREST : gl.LINEAR); step(); return; }
    layers.forEach((layer, i) => this._layer(tex, layer, i, size, crisp));
    this._finish(tex, crisp);
  }
  _layer(tex, layer, i, size, crisp) {
    const gl = this.gl;
    let src = layer;
    if (layer.width !== size) {                                          // (a picture of another size: drawn to the set's size first)
      if (!this._scratch || this._scratch.width !== size) this._scratch = Object.assign(document.createElement("canvas"), { width: size, height: size });
      const p = this._scratch.getContext("2d"); p.clearRect(0, 0, size, size); p.imageSmoothingEnabled = !crisp; p.drawImage(layer, 0, 0, size, size); src = this._scratch;
    }
    if (src && src.getContext && src.width === size && src.height === size) { try { const p = src.getContext("2d"); if (p) src = p.getImageData(0, 0, size, size); } catch (e) { /* the canvas as it is */ } }   // (v21.4: a canvas's pixels read off it and handed over as pixels - several times quicker here than handing over the canvas)
    gl.texSubImage3D(gl.TEXTURE_2D_ARRAY, 0, 0, 0, i, size, size, 1, gl.RGBA, gl.UNSIGNED_BYTE, src);
  }
  _finish(tex, crisp) {
    const gl = this.gl; gl.bindTexture(gl.TEXTURE_2D_ARRAY, tex);
    gl.generateMipmap(gl.TEXTURE_2D_ARRAY);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_MAG_FILTER, crisp ? gl.NEAREST : gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    const aniso = gl.getExtension("EXT_texture_filter_anisotropic");
    if (aniso) gl.texParameterf(gl.TEXTURE_2D_ARRAY, aniso.TEXTURE_MAX_ANISOTROPY_EXT, Math.min(8, gl.getParameter(aniso.MAX_TEXTURE_MAX_ANISOTROPY_EXT)));
  }

  // (v21.4) a set made ready ahead of time: its pictures sent up a slice a frame into textures of its own, swapped in
  // at once when the set is asked for (the town's, while the title is up)
  prepare(art) {
    const gl = this.gl; if (!gl) return; if (this.prepared) { if (this.prepared.art === art) return; this._dropPrepared(); }
    const S = this._split(art), P = Object.assign({ art, texture: gl.createTexture(), shared: null, surfTex: null }, S);
    this._upload(P.texture, S.own.map(S.pic), S.sizes.own, Boolean(art.crisp), true);
    if (S.surf.length) { P.surfTex = gl.createTexture(); this._upload(P.surfTex, S.surf.map(S.pic), S.sizes.surf, Boolean(art.crisp), true); }
    if (this.sharedKey !== S.sharedKey) { P.shared = gl.createTexture(); this._upload(P.shared, S.rest.map(S.pic), S.sizes.shared, Boolean(art.crisp), true); }
    this.prepared = P;
  }
  _dropPrepared() { const P = this.prepared, gl = this.gl; if (!P) return; if (P.texture) gl.deleteTexture(P.texture); if (P.shared) gl.deleteTexture(P.shared); if (P.surfTex) gl.deleteTexture(P.surfTex); this.prepared = null; }
  // (v26.0) the split, right-sized: the band's own and the outdoors' photographs at the look's size (a Pixel set's at
  // 128 - its pictures are pixel art); the outdoors' drawn pictures into an array of their own at 256 (128 in Pixel);
  // the rest shared at 256 (128); and the small sprites - motes, sparks, signs, moons, keys - four to a layer
  _split(art) {
    if (art._split) return art._split;
    const look = String(art.sharedKey || "drawn:drawn").split(":")[1] || "drawn", Z = CM.art.LAYER_SIZES[look] || CM.art.LAYER_SIZES.drawn;
    const sizes = { own: Math.min(art.size || 256, Z.own), surf: Z.surf, shared: Z.shared }, own = [], surf = [], rest = [], packOwn = [], packSurf = [], packRest = [];
    for (const name of Object.keys(art.index)) {
      const theme = CM.art.isThemeLayer(name, art.theme), sfc = CM.art.isSurfaceLayer(name), small = CM.art.isPackable(name);
      if (theme && sfc && !CM.art.isPhotoLayer(name)) (small ? packSurf : surf).push(name);
      else if (theme) own.push(name);
      else if (!sfc) (small ? packRest : rest).push(name);
    }
    const sub = Object.assign({}, art.sub || {}), pics = {};
    const pack = (names, size, into, tag) => { for (let i = 0; i < names.length; i += 4) { const nm = `pack:${tag}${i / 4}`, c = document.createElement("canvas"); c.width = c.height = size; const p = c.getContext("2d"), h = size / 2, pad = art.crisp ? 0 : 2;
        p.imageSmoothingEnabled = !art.crisp; names.slice(i, i + 4).forEach((n, j) => { const x = (j % 2) * h, y = Math.floor(j / 2) * h; p.drawImage(art.layers[art.index[n]], x + pad, y + pad, h - 2 * pad, h - 2 * pad); sub[n] = [nm, (x + pad) / size, (y + pad) / size, (x + h - pad) / size, (y + h - pad) / size]; });
        pics[nm] = c; into.push(nm); } };
    pack(packSurf, sizes.surf, surf, "s"); pack(packRest, sizes.shared, rest, "r");
    const pic = (name) => pics[name] || art.layers[art.index[name]], packed = new Set([...packSurf, ...packRest]);
    return (art._split = { own, surf, rest, packed, sub, pic, sizes, sharedKey: `${art.sharedKey || ""}:${rest.join("|").length}:${rest.length}:${sizes.shared}` });
  }
  _indexOf(S) { const index = {}; S.own.forEach((n, i) => { index[n] = i; }); S.rest.forEach((n, i) => { index[n] = 1000 + i; }); S.surf.forEach((n, i) => { index[n] = 2000 + i; });
    for (const n of S.packed) index[n] = index[S.sub[n][0]];                     // (a packed one answers by its layer: the sprites read the corner from sub)
    return index; }
  setTextures(art, gentle) {
    if (this.prepared && this.prepared.art === art) { const P = this.prepared, gl = this.gl; this.prepared = null;   // (ready ahead: swapped in)
      if (P.shared) { if (this.shared) gl.deleteTexture(this.shared); this.shared = P.shared; this.sharedKey = P.sharedKey; }
      if (P.shared || this.sharedKey === P.sharedKey) { if (this.texture) gl.deleteTexture(this.texture); this.texture = P.texture; if (this.surfTex) gl.deleteTexture(this.surfTex); this.surfTex = P.surfTex;
        this.index = this._indexOf(P); this.sub = P.sub; this.crisp = Boolean(art.crisp); this.bumpK = /^stone/.test(art.sharedKey || "") ? 1.0 : art.crisp ? 0.45 : 0.7; return; }
      gl.deleteTexture(P.texture); if (P.surfTex) gl.deleteTexture(P.surfTex); }   // (the shared set moved on meanwhile: made the ordinary way)
    else if (this.prepared) this._dropPrepared();
    const gl = this.gl, S = this._split(art), { own, rest, surf, sharedKey } = S;   // (the outdoors below ground: not needed, not uploaded - so the shared set is the same for every band)
    if (!this.shared || this.sharedKey !== sharedKey) {
      if (this.shared) gl.deleteTexture(this.shared);
      this.shared = gl.createTexture(); this.sharedKey = sharedKey;
      this._upload(this.shared, rest.map(S.pic), S.sizes.shared, Boolean(art.crisp), gentle);
      this.uploads = (this.uploads || 0) + rest.length;
    }
    if (this.texture) gl.deleteTexture(this.texture);
    this.texture = gl.createTexture();
    this._upload(this.texture, own.map(S.pic), S.sizes.own, Boolean(art.crisp), gentle);
    if (this.surfTex) gl.deleteTexture(this.surfTex); this.surfTex = null;
    if (surf.length) { this.surfTex = gl.createTexture(); this._upload(this.surfTex, surf.map(S.pic), S.sizes.surf, Boolean(art.crisp), gentle); }
    this.uploads = (this.uploads || 0) + own.length + surf.length;
    this.index = this._indexOf(S);
    this.sub = S.sub;
    this.texBytes = Math.round((own.length * S.sizes.own ** 2 + surf.length * S.sizes.surf ** 2 + rest.length * S.sizes.shared ** 2) * 4 * 1.33);   // (v26.0: for the measure)
    this.crisp = Boolean(art.crisp);                                     // pixel tiles stay pixels when they come close
    this.bumpK = /^stone/.test(art.sharedKey || "") ? 1.0 : art.crisp ? 0.45 : 0.7;   // (v22.1: how deep the relief, by the look)
  }

  // ---- the floor's mesh (worked out in 26-surface.js: the walls by their kinds, the ground, trees, canopy; no ceiling under a sky) ----
  setFloor(floor, theme) {
    this.theme = theme; this.floorOn = floor; this.meshes = (this.meshes || 0) + 1;
    if (CM.seasonTurn && CM.game) { this.turnK = CM.seasonTurn(CM.game); this.leafK = CM.leafFall(CM.game); }   // (v24.2: how far the season has come in)
    const props = CM.scatter(floor, this.seed, this.density, { season: this.season, leafK: this.leafK || 0 }).concat(CM.traceProps(floor));   // (and what the party left)
    this.standing = props.filter((p) => p.how === "stand");
    const mesh = CM.floorMesh(floor, theme, this.index, { props, sub: this.sub, night: this.night || 0, turn: this.turnK === undefined ? 1 : this.turnK });   // (at night the town's windows are lit)
    this.mesh = { ceilings: mesh.ceilings, walls: mesh.walls, roofs: mesh.roofs, trees: mesh.trees, props: mesh.props, standing: this.standing.length };
    this.windowLights = mesh.windows || [];                              // (v22.0: the town's lit windows, each a little light on the street)
    const gl = this.gl;
    gl.bindBuffer(gl.ARRAY_BUFFER, this.staticBuf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(mesh.data), gl.STATIC_DRAW);
    this.staticCount = mesh.count;
  }
  // ---- the camera ----
  yawFor(facing) { return facing * Math.PI / 2; }

  setCamera(x, y, facing) {
    this.eye = [x + 0.5, EYE_HEIGHT, y + 0.5];
    this.yaw = this.yawFor(facing);
    this.move = this.turn = null;
  }

  moveTo(x, y, ms = 180) {
    const to = [x + 0.5, EYE_HEIGHT, y + 0.5];
    if (this.snap || ms <= 0) { this.eye = to; this.move = null; return; }
    this.move = { from: this.eye.slice(), to, t: 0, ms };
  }

  turnTo(facing, ms = 160) {
    let to = this.yawFor(facing), from = this.yaw;
    while (to - from > Math.PI) to -= Math.PI * 2;
    while (to - from < -Math.PI) to += Math.PI * 2;
    if (this.snap || ms <= 0) { this.yaw = to; this.turn = null; return; }
    this.turn = { from, to, t: 0, ms };
  }

  spinTo(facing, ms = 700) {                                           // a spinner: the whole way round, and then some
    let to = this.yawFor(facing);
    while (to < this.yaw) to += Math.PI * 2;
    this.turn = { from: this.yaw, to: to + Math.PI * 2, t: 0, ms };
  }

  get busy() { return this.move !== null || this.turn !== null; }
  // the camera's own moves: a push-in or a pull-back (zoom: the field of view's share, for ms), a tilt (roll, radians, for ms)
  zoomTo(k, ms = 500) { if (CM.reducedMotion) return; this.zoomAnim = { from: this.zoomNow || 1, to: k, t: 0, ms, back: true }; }
  rollTo(r, ms = 800) { if (CM.reducedMotion) return; this.rollAnim = { from: this.rollNow || 0, to: r, t: 0, ms }; }
  shake(strength) { if (CM.reducedMotion) return; this.shakeT = Math.max(this.shakeT || 0, Math.min(1, strength)); }   // the view judders, and settles
  punch() { if (CM.reducedMotion) return; this.punchT = 1; }
  nudge(side, k = 1) { if (CM.reducedMotion) return; this.nudgeT = 1; this.nudgeSide = side; this.nudgeK = k; }   // (v23.1) the view leans toward a heavy blow, and back                                                            // the party leans into a blow

  // where the camera is in grid terms (the cell it's heading for, while it steps)
  setSprites(list) { this.sprites = list; }

  // a world point on the canvas, in CSS pixels - or null when it's behind the camera
  project(x, y, z) {
    const m = this.viewProj;
    if (!m) return null;
    const cx = m[0] * x + m[4] * y + m[8] * z + m[12], cy = m[1] * x + m[5] * y + m[9] * z + m[13];
    const cw = m[3] * x + m[7] * y + m[11] * z + m[15];
    if (cw <= 0.01) return null;
    return [(cx / cw * 0.5 + 0.5) * this.canvas.clientWidth, (0.5 - cy / cw * 0.5) * this.canvas.clientHeight, cw];
  }

  _advance(dt) {
    if (this.move) {
      this.move.t = Math.min(1, this.move.t + dt * 1000 / this.move.ms);
      const k = CM.ease(this.move.t);
      this.eye = [CM.lerp(this.move.from[0], this.move.to[0], k), EYE_HEIGHT, CM.lerp(this.move.from[2], this.move.to[2], k)];
      this.bob = Math.sin(this.move.t * Math.PI) * 0.018;
      if (this.move.t >= 1) { this.move = null; this.bob = 0; }
    }
    if (this.turn) {
      this.turn.t = Math.min(1, this.turn.t + dt * 1000 / this.turn.ms);
      this.yaw = CM.lerp(this.turn.from, this.turn.to, CM.ease(this.turn.t));
      if (this.turn.t >= 1) { this.yaw = this.turn.to; this.turn = null; }
    }
  }

  // A sprite: {x, y (the cell), layer, w, h} and one of - nothing (a billboard facing the camera, standing on the
  // floor), flat (lying on the floor), axis "ns"/"ew" (standing across the cell's middle: a door), face 0-3 (a decal
  // on that wall of the cell) - plus dx/dz (an offset in the cell), lift, flash, alpha, glow, shade; and a billboard's
  // pose: tilt (radians, toppled about its foot), skew (its top swayed), scale, mirror (28-motion.js)
  _spriteMesh() {
    const out = [], right = [Math.cos(this.yaw), 0, Math.sin(this.yaw)];
    for (const s of this.sprites) {
      const sb = this.sub[s.layer], layer = sb ? this.index[sb[0]] : this.index[s.layer];   // (a prop: one corner of a shared layer)
      if (layer === undefined) continue;
      const cx = s.x + 0.5 + (s.dx || 0), cz = s.y + 0.5 + (s.dz || 0), w = s.w || 0.7, h = s.h || 0.7;
      const flash = s.flash || 0, alpha = s.alpha === undefined ? 1 : s.alpha, shade = s.shade || 1, glow = s.glow || 0;
      const uv = sb ? [[sb[1], sb[4]], [sb[3], sb[4]], [sb[3], sb[2]], [sb[1], sb[2]]] : [[0, 1], [1, 1], [1, 0], [0, 0]];
      let corners;
      const lift = s.lift || 0;
      if (s.flat && s.rot !== undefined) {                               // (v22.2) a shadow cast: turned toward where it falls and stretched by the light's angle
        const c = Math.cos(s.rot), sn = Math.sin(s.rot), hl = (w * (s.len || 1)) / 2, hw = w / 2, ox = c * hl * 0.85, oz = sn * hl * 0.85, y0 = 0.0035;
        const P = (a2, b2) => [cx + ox + c * a2 - sn * b2, y0, cz + oz + sn * a2 + c * b2];
        corners = [P(-hl, hw), P(hl, hw), P(hl, -hw), P(-hl, -hw)];
      } else if (s.flat) {
        corners = [[cx - w / 2, 0.003, cz + w / 2], [cx + w / 2, 0.003, cz + w / 2], [cx + w / 2, 0.003, cz - w / 2], [cx - w / 2, 0.003, cz - w / 2]];
      } else if (s.axis && s.swing) {                                    // a door swung on its hinge (28-motion.js): toward the side away from the party
        const L = 0.94, sd = s.swingSide || 1, sw = s.swing, top = 0.97;
        const [hx, hz, ex, ez] = s.axis === "ns" ? [cx - 0.47, cz, cx - 0.47 + Math.cos(sw) * L, cz + Math.sin(sw) * L * sd] : [cx, cz + 0.47, cx + Math.sin(sw) * L * sd, cz + 0.47 - Math.cos(sw) * L];
        corners = [[hx, 0, hz], [ex, 0, ez], [ex, top, ez], [hx, top, hz]];
      } else if (s.axis) {
        corners = s.axis === "ns"                                        // a door across a corridor running north-south (a portcullis lifted by `lift`)
          ? [[cx - 0.5, lift, cz], [cx + 0.5, lift, cz], [cx + 0.5, 1 + lift, cz], [cx - 0.5, 1 + lift, cz]]
          : [[cx, lift, cz + 0.5], [cx, lift, cz - 0.5], [cx, 1 + lift, cz - 0.5], [cx, 1 + lift, cz + 0.5]];
      } else if (s.face !== undefined) {
        const [dx, dz] = CM.DIRS[s.face], inset = 0.012;                // flush with that wall, a hair into the room
        const px = s.x + 0.5 + dx * (0.5 - inset), pz = s.y + 0.5 + dz * (0.5 - inset);
        const ax = -dz, az = dx;                                         // along the wall
        const y0 = 0.5 - h / 2 + lift, y1 = 0.5 + h / 2 + lift;
        corners = [[px - ax * w / 2, y0, pz - az * w / 2], [px + ax * w / 2, y0, pz + az * w / 2], [px + ax * w / 2, y1, pz + az * w / 2], [px - ax * w / 2, y1, pz - az * w / 2]];
      } else if (s.tilt || s.skew || s.scale) {                             // a monster's pose (28-motion.js): toppled about its foot, swaying, shrunk
        // toppled about the middle of its foot, then let down onto the floor: the picture's clear margin (a fifth of its
        // width a side) sinks under the floor, so what lies there lies on it
        const sc = s.scale || 1, W = w * sc, H = h * sc, sk = (s.skew || 0) * H, side = s.mirror ? 1 : -1, t = s.tilt || 0, c = Math.cos(t), sn = Math.sin(t) * side;
        const P = [[-W / 2, 0], [W / 2, 0], [W / 2 + sk, H], [-W / 2 + sk, H]].map(([u, v]) => (t ? [u * c + v * sn, -u * sn + v * c] : [u, v]));
        const drop = t ? -Math.min(...P.map((p) => p[1])) - 0.2 * W * Math.abs(Math.sin(t)) : 0, shift = t ? side * 0.15 * W * Math.abs(Math.sin(t)) : 0;
        corners = P.map(([uu, vv]) => [cx + right[0] * (uu + shift), lift + vv + drop, cz + right[2] * (uu + shift)]);
      } else {
        corners = [[cx - right[0] * w / 2, lift, cz - right[2] * w / 2], [cx + right[0] * w / 2, lift, cz + right[2] * w / 2],
          [cx + right[0] * w / 2, lift + h, cz + right[2] * w / 2], [cx - right[0] * w / 2, lift + h, cz - right[2] * w / 2]];
        if (s.sway && this.wind && CM.windAt && !CM.reducedMotion) { const k = s.sway * CM.windAt(cx, cz, this.time, this.wind); for (const j of [2, 3]) { corners[j][0] += this.wind.dir[0] * k; corners[j][2] += this.wind.dir[1] * k; } }   // (v24.0)
      }
      const uvs = s.mirror ? uv.map(([u, v], i) => [uv[i ^ 1][0], v]) : uv;   // (mirrored: it looks the other way)
      for (const i of [0, 1, 2, 0, 2, 3]) out.push(...corners[i], uvs[i][0], uvs[i][1], layer, shade, flash, alpha, s.water ? 4 : glow);   // (water: the shader's own)
    }
    return out;
  }

  _skyMesh(eye) {
    const layer = this.index.skygrad;
    if (layer === undefined) return [];
    const out = [], R = 150, lo = eye[1] - 12, hi = eye[1] + 110, [ex, , ez] = eye;   // (beyond the far ring, which stands forty squares past the map's edge)
    const quad = (a, b, c, d) => { const uv = [[0, 1], [1, 1], [1, 0], [0, 0]]; for (const i of [0, 1, 2, 0, 2, 3]) out.push(...[a, b, c, d][i], uv[i][0], uv[i][1], layer, 1, 0, 1, 3); };
    quad([ex - R, lo, ez - R], [ex + R, lo, ez - R], [ex + R, hi, ez - R], [ex - R, hi, ez - R]);
    quad([ex + R, lo, ez + R], [ex - R, lo, ez + R], [ex - R, hi, ez + R], [ex + R, hi, ez + R]);
    quad([ex + R, lo, ez - R], [ex + R, lo, ez + R], [ex + R, hi, ez + R], [ex + R, hi, ez - R]);
    quad([ex - R, lo, ez + R], [ex - R, lo, ez - R], [ex - R, hi, ez - R], [ex - R, hi, ez + R]);
    return out;
  }

  _attributes() {
    const gl = this.gl, bytes = STRIDE * 4;
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, bytes, 0);
    gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 3, gl.FLOAT, false, bytes, 12);
    gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 1, gl.FLOAT, false, bytes, 24);
    gl.enableVertexAttribArray(3); gl.vertexAttribPointer(3, 3, gl.FLOAT, false, bytes, 28);
  }

  // (v22.5) the glow's targets, made again when the canvas changes size: a multisampled frame, its resolved picture, and
  // two quarter-size pictures for the bright part and its blur
  _post() {
    const gl = this.gl, w = this.canvas.width, h = this.canvas.height, P = this.postT || (this.postT = {});
    if (!P.progs) { const mk = (fs) => { const p = this._program(POST_VERT, fs); return p ? { p, u: (n) => gl.getUniformLocation(p, n) } : null; };
      P.progs = { bright: mk(BRIGHT_FRAG), blur: mk(BLUR_FRAG), compose: mk(COMPOSE_FRAG) };
      if (!P.progs.bright || !P.progs.blur || !P.progs.compose) { P.broken = true; this.error = ""; return null; }
      P.vao = gl.createVertexArray(); gl.bindVertexArray(P.vao); const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW); gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0); gl.bindVertexArray(null); }
    if (P.w === w && P.h === h) return P;
    for (const k of ["msFb", "sceneFb", "aFb", "bFb"]) if (P[k]) gl.deleteFramebuffer(P[k]);
    for (const k of ["msCol", "msDep"]) if (P[k]) gl.deleteRenderbuffer(P[k]);
    for (const k of ["scene", "a", "b"]) if (P[k]) gl.deleteTexture(P[k]);
    const tex = (tw, th) => { const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, tw, th, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
      for (const [k, v] of [[gl.TEXTURE_MIN_FILTER, gl.LINEAR], [gl.TEXTURE_MAG_FILTER, gl.LINEAR], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, k, v); return t; };
    const fbFor = (t) => { const f = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, f); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0); return f; };
    const samples = Math.min(4, gl.getParameter(gl.MAX_SAMPLES) || 0);
    P.msFb = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, P.msFb);
    P.msCol = gl.createRenderbuffer(); gl.bindRenderbuffer(gl.RENDERBUFFER, P.msCol); gl.renderbufferStorageMultisample(gl.RENDERBUFFER, samples, gl.RGBA8, w, h); gl.framebufferRenderbuffer(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.RENDERBUFFER, P.msCol);
    P.msDep = gl.createRenderbuffer(); gl.bindRenderbuffer(gl.RENDERBUFFER, P.msDep); gl.renderbufferStorageMultisample(gl.RENDERBUFFER, samples, gl.DEPTH_COMPONENT24, w, h); gl.framebufferRenderbuffer(gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT, gl.RENDERBUFFER, P.msDep);
    const ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE;
    P.qw = Math.max(1, w >> 2); P.qh = Math.max(1, h >> 2);
    P.scene = tex(w, h); P.sceneFb = fbFor(P.scene); P.a = tex(P.qw, P.qh); P.aFb = fbFor(P.a); P.b = tex(P.qw, P.qh); P.bFb = fbFor(P.b);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.bindTexture(gl.TEXTURE_2D, null);
    if (!ok) { P.broken = true; return null; }
    P.w = w; P.h = h; return P;
  }

  _postEnd(P) {
    const gl = this.gl, w = P.w, h = P.h, pr = P.progs, sky = this.sky;
    gl.bindFramebuffer(gl.READ_FRAMEBUFFER, P.msFb); gl.bindFramebuffer(gl.DRAW_FRAMEBUFFER, P.sceneFb);
    gl.blitFramebuffer(0, 0, w, h, 0, 0, w, h, gl.COLOR_BUFFER_BIT, gl.NEAREST);
    gl.disable(gl.DEPTH_TEST); gl.disable(gl.BLEND); gl.bindVertexArray(P.vao); gl.activeTexture(gl.TEXTURE0);
    const pass = (prog, fb, vw, vh, src, set) => { gl.bindFramebuffer(gl.FRAMEBUFFER, fb); gl.viewport(0, 0, vw, vh); gl.useProgram(prog.p); gl.bindTexture(gl.TEXTURE_2D, src); gl.uniform1i(prog.u("uSrc"), 0); set(prog); gl.drawArrays(gl.TRIANGLES, 0, 3); };
    const day = sky ? Math.min(1, Math.max(0, (sky.light - 0.3) * 2)) : 0;   // (by day the whole sky is bright: only the brightest glows)
    pass(pr.bright, P.aFb, P.qw, P.qh, P.scene, (p) => { gl.uniform2f(p.u("uPx"), 1 / w, 1 / h); gl.uniform1f(p.u("uThresh"), 0.48 + 0.42 * day); });
    for (let i = 0; i < 2; i++) {
      pass(pr.blur, P.bFb, P.qw, P.qh, P.a, (p) => gl.uniform2f(p.u("uDir"), (1 + i) / P.qw, 0));
      pass(pr.blur, P.aFb, P.qw, P.qh, P.b, (p) => gl.uniform2f(p.u("uDir"), 0, (1 + i) / P.qh)); }
    gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.viewport(0, 0, w, h); gl.useProgram(pr.compose.p);
    gl.bindTexture(gl.TEXTURE_2D, P.scene); gl.uniform1i(pr.compose.u("uSrc"), 0);
    gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, P.a); gl.uniform1i(pr.compose.u("uGlow"), 1);
    gl.uniform1f(pr.compose.u("uK"), (this.bloom || 0) * (1 - 0.4 * day)); gl.drawArrays(gl.TRIANGLES, 0, 3);
    gl.bindTexture(gl.TEXTURE_2D, null); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, null);
    gl.bindVertexArray(null); gl.enable(gl.DEPTH_TEST); gl.enable(gl.BLEND);
  }

  frame(dt) {
    if (!this.ok || !this.texture) return;
    this.time += dt;
    this._advance(dt);
    this.lightNow += (this.light - this.lightNow) * Math.min(1, dt * 4);
    // a torch flame: a slow wander and a quick shiver - more of a shiver as it burns low
    const unsteady = this.light < 0.6 ? 2.2 : 1;
    this.flicker = 0.92 + unsteady * (0.06 * Math.sin(this.time * 7.3) + 0.03 * Math.sin(this.time * 17.1 + 1.0) + 0.02 * Math.sin(this.time * 31.7));
    const gl = this.gl, aspect = this.canvas.width / this.canvas.height;
    const fwd = [Math.sin(this.yaw), 0, -Math.cos(this.yaw)], right = [Math.cos(this.yaw), 0, Math.sin(this.yaw)];
    this.shakeT = (this.shakeT || 0) * Math.pow(0.0005, dt);              // a shake dies away in about a second
    if (this.shakeT < 0.01) this.shakeT = 0;
    this.punchT = Math.max(0, (this.punchT || 0) - dt / 0.22);
    this.nudgeT = Math.max(0, (this.nudgeT || 0) - dt / 0.32); const nz = Math.sin((this.nudgeT || 0) * Math.PI) * (this.nudgeK || 0) * 0.07, ns = this.nudgeSide || 0;
    const jx = Math.sin(this.time * 61) * this.shakeT * 0.06, jy = Math.sin(this.time * 47 + 1) * this.shakeT * 0.045, pk = Math.sin(this.punchT * Math.PI) * 0.1;
    const E = this.perch ? [this.perch.x + 0.5, this.perch.h + EYE_HEIGHT, this.perch.y + 0.5] : this.eye;   // (on a gate tower's top: 61c-tower.js)
    const eye = [E[0] + right[0] * (jx + nz * ns) + fwd[0] * (pk + nz), E[1] + this.bob + jy - nz * 0.15, E[2] + right[2] * (jx + nz * ns) + fwd[2] * (pk + nz)];
    if (this.zoomAnim) { const z = this.zoomAnim; z.t += dt * 1000 / z.ms; const k = CM.ease(Math.min(1, z.t)); this.zoomNow = z.back ? CM.lerp(z.from, z.to, Math.sin(k * Math.PI)) : CM.lerp(z.from, z.to, k); if (z.t >= 1) { this.zoomNow = z.back ? z.from : z.to; this.zoomAnim = null; } }
    if (this.rollAnim) { const r = this.rollAnim; r.t += dt * 1000 / r.ms; this.rollNow = CM.lerp(r.from, r.to, CM.ease(Math.min(1, r.t))); if (r.t >= 1) this.rollAnim = null; }
    const roll = this.rollNow || 0, up = [Math.sin(roll) * right[0], Math.cos(roll), Math.sin(roll) * right[2]];
    const view = this.inspect ? mat4LookAt(this.inspect.eye, this.inspect.at, [0, 1, 0]) : mat4LookAt(eye, [eye[0] + fwd[0], eye[1], eye[2] + fwd[2]], up);   // (inspect: a free camera for screenshots and the tests, never set in play)
    const proj = mat4Perspective(Math.PI / 3 * (this.zoomNow || 1), aspect, 0.05, 260);
    this.viewProj = mat4Mul(proj, view);
    const t = this.theme, sky = t.sky ? this.sky || CM.sky(null) : null;
    const clear = sky ? sky.zenith : t.fog, fogc = sky ? sky.horizon : t.fog;
    const post = this.bloom > 0 && !(this.postT && this.postT.broken) ? this._post() : null;   // (v22.5: the glow - drawn off screen first)
    if (post) { gl.bindFramebuffer(gl.FRAMEBUFFER, post.msFb); gl.viewport(0, 0, post.w, post.h); }
    gl.clearColor(clear[0], clear[1], clear[2], 1);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.useProgram(this.program);
    gl.uniformMatrix4fv(this.loc.uViewProj, false, this.viewProj);
    gl.uniform3fv(this.loc.uEye, this.inspect ? this.inspect.eye : eye);   // (the free camera sees from its own eye)
    // under a sky: daylight is flat and reaches to the horizon; at night the torch and the moon do what they can
    gl.uniform3fv(this.loc.uTorch, sky ? [t.torch[0] + (1 - t.torch[0]) * sky.light, t.torch[1] + (1 - t.torch[1]) * sky.light, t.torch[2] + (1 - t.torch[2]) * sky.light] : t.torch);
    gl.uniform3fv(this.loc.uFog, fogc);
    gl.uniform1f(this.loc.uReach, sky ? (6 + 54 * sky.light) * (sky.night ? Math.max(0.5, this.lightNow) : 1) : t.reach * this.lightNow);
    gl.uniform1f(this.loc.uFlicker, sky ? this.flicker * (1 - sky.light) : this.flicker);
    gl.uniform1f(this.loc.uAmbient, sky ? 0.04 + 0.98 * sky.light : 0.06 * Math.min(1, this.lightNow * 2));
    gl.uniform3fv(this.loc.uZenith, clear);
    gl.uniform3fv(this.loc.uHorizon, fogc);
    const lights = this.lights.slice(0, 24), pos = new Float32Array(96), col = new Float32Array(72);
    lights.forEach((l, i) => { const f = l.flicker ? 0.85 + 0.15 * Math.sin(this.time * (6 + i) + i * 1.7) : 1; pos.set([l.x, l.y, l.z, l.reach], i * 4); col.set(l.colour.map((c) => c * f), i * 3); });
    gl.uniform1i(this.loc.uLights, lights.length); gl.uniform4fv(this.loc.uLightPos, pos); gl.uniform3fv(this.loc.uLightCol, col);
    { const E2 = this.inspect ? this.inspect.eye : eye; gl.uniform3fv(this.loc.uTorchPos, [E2[0] + right[0] * 0.28 + fwd[0] * 0.15, E2[1] + 0.12, E2[2] + right[2] * 0.28 + fwd[2] * 0.15]); }   // (v22.0: held in the right hand, a little up)
    if (sky && (sky.sun !== null || sky.moon !== null)) {                // the light's direction: where the sun is on its arc (or, at night, the moon)
      const t = sky.sun !== null && sky.light > 0.15 ? sky.sun : sky.moon !== null ? sky.moon : 0.5, a = Math.PI * t, el = Math.sin(a) * 0.5;
      const v = [Math.cos(a) * Math.cos(el), Math.sin(el), Math.sin(a) * Math.cos(el)], m = Math.hypot(...v);
      gl.uniform3fv(this.loc.uSun, v.map((c) => c / m)); gl.uniform1f(this.loc.uSunK, sky.sun !== null && sky.light > 0.15 ? 0.9 : 0.4);
    } else { gl.uniform3fv(this.loc.uSun, [0, 1, 0]); gl.uniform1f(this.loc.uSunK, 0); }
    { const G = this.grading, g0 = t.grade || [1, 1, 1];                    // (v22.4: the band's grade and, above, the hour's: 76zzzx-grade.js)
      gl.uniform3fv(this.loc.uGrade, G ? g0.map((v, i) => v * G.mul[i]) : g0); gl.uniform3fv(this.loc.uLift, G ? G.lift : [0, 0, 0]); gl.uniform3fv(this.loc.uLook, G ? [G.con, G.sat, G.frost] : [1, 1, 0]); }
    gl.uniform1f(this.loc.uTime, CM.reducedMotion ? 0 : this.time || 0); gl.uniform1f(this.loc.uWet, sky ? this.wet || 0 : 0); gl.uniform1f(this.loc.uSnow, sky ? this.snow || 0 : 0); gl.uniform1f(this.loc.uMist, sky ? this.mist || 0 : 0);
    { const W = CM.reducedMotion ? null : this.wind; gl.uniform3fv(this.loc.uWind, W ? [W.dir[0], W.dir[1], W.k] : [1, 0, 0]); }   // (v24.0: 76zzzzc-wind.js)
    gl.uniform1f(this.loc.uHaze, this.air ? this.air.haze : 0); gl.uniform1f(this.loc.uShaft, this.air ? this.air.shaft : 0);   // (v22.3: 76zzzw-air.js)
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D_ARRAY, this.texture);
    gl.uniform1i(this.loc.uTex, 0);
    gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D_ARRAY, this.shared || this.texture); gl.uniform1i(this.loc.uShared, 1);
    gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D_ARRAY, this.surfTex || this.texture); gl.uniform1i(this.loc.uSurf, 2); gl.activeTexture(gl.TEXTURE0);
    gl.uniform1f(this.loc.uBump, CM.reliefOff ? 0 : (this.bumpK || 0.7) * (CM.reliefScale || 1));   // (v22.1: the relief on the floor's own mesh only)
    gl.bindBuffer(gl.ARRAY_BUFFER, this.staticBuf);
    this._attributes();
    gl.drawArrays(gl.TRIANGLES, 0, this.staticCount);
    gl.uniform1f(this.loc.uBump, 0);
    const dyn = sky ? this._skyMesh(eye).concat(this._spriteMesh()) : this._spriteMesh();
    if (dyn.length) {
      gl.bindBuffer(gl.ARRAY_BUFFER, this.dynBuf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(dyn), gl.DYNAMIC_DRAW);
      this._attributes();
      gl.drawArrays(gl.TRIANGLES, 0, dyn.length / STRIDE);
    }
    if (post) this._postEnd(post);
  }

  // the colour of one pixel, for the tests: is anything being drawn?
  pixel(x, y) {
    const gl = this.gl, px = new Uint8Array(4);
    gl.readPixels(x, this.canvas.height - 1 - y, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
    return Array.from(px);
  }
};
