"use strict";
// The first-person view, in WebGL 2: the floor's walls, floor and ceiling as one mesh built when the floor is
// entered; chests, hatches and monsters as billboards rebuilt each frame; a torch that falls off with distance and
// flickers, and fog the colour of the depth. The camera steps and turns smoothly (or snaps, if that's the setting).
const VERT = `#version 300 es
precision highp float;
in vec3 aPos; in vec3 aUV; in float aShade; in vec3 aFx;
uniform mat4 uViewProj;
out vec3 vWorld; out vec3 vUV; out float vShade; out vec3 vFx;
void main() { vWorld = aPos; vUV = aUV; vShade = aShade; vFx = aFx; gl_Position = uViewProj * vec4(aPos, 1.0); }`;

// aFx: a hit's red flash, the alpha (a foe fading), and glow - how much of the texture's own colour shows unlit;
// a glow of 2 is the sky's own things (the sun, the moon: the picture as it is, no light, no fog), 3 the sky dome
// (the picture's red is how high: the horizon's colour to the zenith's)
const FRAG = `#version 300 es
precision highp float; precision highp sampler2DArray;
in vec3 vWorld; in vec3 vUV; in float vShade; in vec3 vFx;
uniform sampler2DArray uTex; uniform sampler2DArray uShared; uniform vec3 uEye; uniform vec3 uTorch; uniform vec3 uFog;
uniform float uReach; uniform float uFlicker; uniform float uAmbient;
uniform vec3 uZenith; uniform vec3 uHorizon;
uniform int uLights; uniform vec4 uLightPos[12]; uniform vec3 uLightCol[12];   // the lights about the party: xyz, reach in w; colour
uniform vec3 uSun; uniform float uSunK; uniform vec3 uGrade;                    // the sun's (or the moon's) direction and strength on the surface; the band's grade
out vec4 fragColor;
void main() {
  bool shared = vUV.z > 999.5;                                            // a layer of 1000 and up is the shared texture's (what never changes between bands)
  vec4 ts = texture(uShared, vec3(vUV.xy, max(vUV.z - 1000.0, 0.0))), tt = texture(uTex, vec3(vUV.xy, min(vUV.z, 999.0)));
  vec4 t = shared ? ts : tt;
  if (vFx.z > 2.5) { fragColor = vec4(mix(uHorizon, uZenith, t.r), 1.0); return; }
  if (t.a < 0.5) discard;
  if (vFx.z > 1.5) { fragColor = vec4(t.rgb, t.a * vFx.y); return; }
  float d = distance(vWorld, uEye);
  float r2 = uReach * uReach;
  float light = uAmbient + uFlicker * r2 / (r2 + 2.2 * d * d + 0.4 * d);
  vec3 n = normalize(cross(dFdx(vWorld), dFdy(vWorld)));                      // the surface's facing, from the triangle itself
  if (dot(n, uEye - vWorld) < 0.0) n = -n;
  if (uSunK > 0.0) light *= mix(1.0, 0.62 + 0.55 * max(dot(n, uSun), 0.0), uSunK * step(abs(n.y), 0.7));   // walls facing the sun lit, the others in shade
  vec3 extra = vec3(0.0);
  for (int i = 0; i < 12; i++) {
    if (i >= uLights) break;
    vec3 L = uLightPos[i].xyz - vWorld; float ld = length(L), reach = uLightPos[i].w;
    float fall = max(0.0, 1.0 - ld / reach); fall *= fall;
    float face = 0.35 + 0.65 * max(dot(n, L / max(ld, 0.001)), 0.0);
    extra += uLightCol[i] * fall * face;
  }
  vec3 col = t.rgb * vShade * (uTorch * light + extra) * uGrade;
  float fog = smoothstep(uReach * 0.55, uReach * 1.7, d);
  col = mix(col, uFog, fog);
  col = mix(col, t.rgb, vFx.z * (1.0 - fog * 0.7));
  col = mix(col, vec3(1.0, 0.3, 0.2), vFx.x);
  fragColor = vec4(col, t.a * vFx.y);
}`;

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
    for (const n of ["uViewProj", "uTex", "uShared", "uEye", "uTorch", "uFog", "uReach", "uFlicker", "uAmbient", "uZenith", "uHorizon", "uLights", "uLightPos", "uLightCol", "uSun", "uSunK", "uGrade"]) this.loc[n] = gl.getUniformLocation(this.program, n);
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
    this.lights = [];                  // [{x, y, z, reach, colour [r, g, b], flicker}]: what lights the walls about the party this frame (12 at most)
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
  _upload(tex, layers, size, crisp) {
    const gl = this.gl;
    gl.bindTexture(gl.TEXTURE_2D_ARRAY, tex);
    gl.texImage3D(gl.TEXTURE_2D_ARRAY, 0, gl.RGBA8, size, size, Math.max(1, layers.length), 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    let scratch = null;
    layers.forEach((layer, i) => {
      let src = layer;
      if (layer.width !== size) { scratch = scratch || Object.assign(document.createElement("canvas"), { width: size, height: size }); const p = scratch.getContext("2d"); p.clearRect(0, 0, size, size); p.imageSmoothingEnabled = !crisp; p.drawImage(layer, 0, 0, size, size); src = scratch; }
      gl.texSubImage3D(gl.TEXTURE_2D_ARRAY, 0, 0, 0, i, size, size, 1, gl.RGBA, gl.UNSIGNED_BYTE, src);
    });
    gl.generateMipmap(gl.TEXTURE_2D_ARRAY);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_MAG_FILTER, crisp ? gl.NEAREST : gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    const aniso = gl.getExtension("EXT_texture_filter_anisotropic");
    if (aniso) gl.texParameterf(gl.TEXTURE_2D_ARRAY, aniso.TEXTURE_MAX_ANISOTROPY_EXT, Math.min(8, gl.getParameter(aniso.MAX_TEXTURE_MAX_ANISOTROPY_EXT)));
  }

  setTextures(art) {
    const gl = this.gl, names = Object.keys(art.index), own = [], rest = [];
    for (const name of names) { if (CM.art.isThemeLayer(name, art.theme)) own.push(name); else if (!CM.art.isSurfaceLayer(name)) rest.push(name); }   // (the outdoors below ground: not needed, not uploaded - so the shared set is the same for every band)
    const index = {};
    own.forEach((name, i) => { index[name] = i; });
    rest.forEach((name, i) => { index[name] = 1000 + i; });
    const sharedKey = `${art.sharedKey || ""}:${rest.join("|").length}:${rest.length}`;
    if (!this.shared || this.sharedKey !== sharedKey) {
      if (this.shared) gl.deleteTexture(this.shared);
      this.shared = gl.createTexture(); this.sharedKey = sharedKey;
      this._upload(this.shared, rest.map((name) => art.layers[art.index[name]]), CM.SHARED_SIZE, Boolean(art.crisp));
      this.uploads = (this.uploads || 0) + rest.length;
    }
    if (this.texture) gl.deleteTexture(this.texture);
    this.texture = gl.createTexture();
    this._upload(this.texture, own.map((name) => art.layers[art.index[name]]), art.size, Boolean(art.crisp));
    this.uploads = (this.uploads || 0) + own.length;
    this.index = index;
    this.sub = art.sub || {};
    this.crisp = Boolean(art.crisp);                                     // pixel tiles stay pixels when they come close
  }

  // ---- the floor's mesh (worked out in 26-surface.js: the walls by their kinds, the ground, trees, canopy; no ceiling under a sky) ----
  setFloor(floor, theme) {
    this.theme = theme;
    const props = CM.scatter(floor, this.seed, this.density, { season: this.season }).concat(CM.traceProps(floor));   // (and what the party left)
    this.standing = props.filter((p) => p.how === "stand");
    const mesh = CM.floorMesh(floor, theme, this.index, { props, sub: this.sub });
    this.mesh = { ceilings: mesh.ceilings, walls: mesh.walls, roofs: mesh.roofs, trees: mesh.trees, props: mesh.props, standing: this.standing.length };
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
  punch() { if (CM.reducedMotion) return; this.punchT = 1; }                                                            // the party leans into a blow

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
  // on that wall of the cell) - plus dx/dz (an offset in the cell), lift, flash, alpha, glow, shade.
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
      if (s.flat) {
        corners = [[cx - w / 2, 0.003, cz + w / 2], [cx + w / 2, 0.003, cz + w / 2], [cx + w / 2, 0.003, cz - w / 2], [cx - w / 2, 0.003, cz - w / 2]];
      } else if (s.axis) {
        corners = s.axis === "ns"                                        // a door across a corridor running north-south
          ? [[cx - 0.5, 0, cz], [cx + 0.5, 0, cz], [cx + 0.5, 1, cz], [cx - 0.5, 1, cz]]
          : [[cx, 0, cz + 0.5], [cx, 0, cz - 0.5], [cx, 1, cz - 0.5], [cx, 1, cz + 0.5]];
      } else if (s.face !== undefined) {
        const [dx, dz] = CM.DIRS[s.face], inset = 0.012;                // flush with that wall, a hair into the room
        const px = s.x + 0.5 + dx * (0.5 - inset), pz = s.y + 0.5 + dz * (0.5 - inset);
        const ax = -dz, az = dx;                                         // along the wall
        const y0 = 0.5 - h / 2 + lift, y1 = 0.5 + h / 2 + lift;
        corners = [[px - ax * w / 2, y0, pz - az * w / 2], [px + ax * w / 2, y0, pz + az * w / 2], [px + ax * w / 2, y1, pz + az * w / 2], [px - ax * w / 2, y1, pz - az * w / 2]];
      } else {
        corners = [[cx - right[0] * w / 2, lift, cz - right[2] * w / 2], [cx + right[0] * w / 2, lift, cz + right[2] * w / 2],
          [cx + right[0] * w / 2, lift + h, cz + right[2] * w / 2], [cx - right[0] * w / 2, lift + h, cz - right[2] * w / 2]];
      }
      for (const i of [0, 1, 2, 0, 2, 3]) out.push(...corners[i], uv[i][0], uv[i][1], layer, shade, flash, alpha, glow);
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
    const jx = Math.sin(this.time * 61) * this.shakeT * 0.06, jy = Math.sin(this.time * 47 + 1) * this.shakeT * 0.045, pk = Math.sin(this.punchT * Math.PI) * 0.1;
    const eye = [this.eye[0] + right[0] * jx + fwd[0] * pk, this.eye[1] + this.bob + jy, this.eye[2] + right[2] * jx + fwd[2] * pk];
    if (this.zoomAnim) { const z = this.zoomAnim; z.t += dt * 1000 / z.ms; const k = CM.ease(Math.min(1, z.t)); this.zoomNow = z.back ? CM.lerp(z.from, z.to, Math.sin(k * Math.PI)) : CM.lerp(z.from, z.to, k); if (z.t >= 1) { this.zoomNow = z.back ? z.from : z.to; this.zoomAnim = null; } }
    if (this.rollAnim) { const r = this.rollAnim; r.t += dt * 1000 / r.ms; this.rollNow = CM.lerp(r.from, r.to, CM.ease(Math.min(1, r.t))); if (r.t >= 1) this.rollAnim = null; }
    const roll = this.rollNow || 0, up = [Math.sin(roll) * right[0], Math.cos(roll), Math.sin(roll) * right[2]];
    const view = mat4LookAt(eye, [eye[0] + fwd[0], eye[1], eye[2] + fwd[2]], up);
    const proj = mat4Perspective(Math.PI / 3 * (this.zoomNow || 1), aspect, 0.05, 260);
    this.viewProj = mat4Mul(proj, view);
    const t = this.theme, sky = t.sky ? this.sky || CM.sky(null) : null;
    const clear = sky ? sky.zenith : t.fog, fogc = sky ? sky.horizon : t.fog;
    gl.clearColor(clear[0], clear[1], clear[2], 1);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.useProgram(this.program);
    gl.uniformMatrix4fv(this.loc.uViewProj, false, this.viewProj);
    gl.uniform3fv(this.loc.uEye, eye);
    // under a sky: daylight is flat and reaches to the horizon; at night the torch and the moon do what they can
    gl.uniform3fv(this.loc.uTorch, sky ? [t.torch[0] + (1 - t.torch[0]) * sky.light, t.torch[1] + (1 - t.torch[1]) * sky.light, t.torch[2] + (1 - t.torch[2]) * sky.light] : t.torch);
    gl.uniform3fv(this.loc.uFog, fogc);
    gl.uniform1f(this.loc.uReach, sky ? (6 + 54 * sky.light) * (sky.night ? Math.max(0.5, this.lightNow) : 1) : t.reach * this.lightNow);
    gl.uniform1f(this.loc.uFlicker, sky ? this.flicker * (1 - sky.light) : this.flicker);
    gl.uniform1f(this.loc.uAmbient, sky ? 0.04 + 0.98 * sky.light : 0.06 * Math.min(1, this.lightNow * 2));
    gl.uniform3fv(this.loc.uZenith, clear);
    gl.uniform3fv(this.loc.uHorizon, fogc);
    const lights = this.lights.slice(0, 12), pos = new Float32Array(48), col = new Float32Array(36);
    lights.forEach((l, i) => { const f = l.flicker ? 0.85 + 0.15 * Math.sin(this.time * (6 + i) + i * 1.7) : 1; pos.set([l.x, l.y, l.z, l.reach], i * 4); col.set(l.colour.map((c) => c * f), i * 3); });
    gl.uniform1i(this.loc.uLights, lights.length); gl.uniform4fv(this.loc.uLightPos, pos); gl.uniform3fv(this.loc.uLightCol, col);
    if (sky && (sky.sun !== null || sky.moon !== null)) {                // the light's direction: where the sun is on its arc (or, at night, the moon)
      const t = sky.sun !== null && sky.light > 0.15 ? sky.sun : sky.moon !== null ? sky.moon : 0.5, a = Math.PI * t, el = Math.sin(a) * 0.5;
      const v = [Math.cos(a) * Math.cos(el), Math.sin(el), Math.sin(a) * Math.cos(el)], m = Math.hypot(...v);
      gl.uniform3fv(this.loc.uSun, v.map((c) => c / m)); gl.uniform1f(this.loc.uSunK, sky.sun !== null && sky.light > 0.15 ? 0.9 : 0.4);
    } else { gl.uniform3fv(this.loc.uSun, [0, 1, 0]); gl.uniform1f(this.loc.uSunK, 0); }
    gl.uniform3fv(this.loc.uGrade, t.grade || [1, 1, 1]);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D_ARRAY, this.texture);
    gl.uniform1i(this.loc.uTex, 0);
    gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D_ARRAY, this.shared || this.texture); gl.uniform1i(this.loc.uShared, 1); gl.activeTexture(gl.TEXTURE0);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.staticBuf);
    this._attributes();
    gl.drawArrays(gl.TRIANGLES, 0, this.staticCount);
    const dyn = sky ? this._skyMesh(eye).concat(this._spriteMesh()) : this._spriteMesh();
    if (dyn.length) {
      gl.bindBuffer(gl.ARRAY_BUFFER, this.dynBuf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(dyn), gl.DYNAMIC_DRAW);
      this._attributes();
      gl.drawArrays(gl.TRIANGLES, 0, dyn.length / STRIDE);
    }
  }

  // the colour of one pixel, for the tests: is anything being drawn?
  pixel(x, y) {
    const gl = this.gl, px = new Uint8Array(4);
    gl.readPixels(x, this.canvas.height - 1 - y, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
    return Array.from(px);
  }
};
