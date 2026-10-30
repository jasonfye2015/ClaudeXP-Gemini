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

// aFx: a hit's red flash, the alpha (a foe fading), and glow - how much of the texture's own colour shows unlit
const FRAG = `#version 300 es
precision highp float; precision highp sampler2DArray;
in vec3 vWorld; in vec3 vUV; in float vShade; in vec3 vFx;
uniform sampler2DArray uTex; uniform vec3 uEye; uniform vec3 uTorch; uniform vec3 uFog;
uniform float uReach; uniform float uFlicker; uniform float uAmbient;
out vec4 fragColor;
void main() {
  vec4 t = texture(uTex, vUV);
  if (t.a < 0.5) discard;
  float d = distance(vWorld, uEye);
  float r2 = uReach * uReach;
  float light = uAmbient + uFlicker * r2 / (r2 + 2.2 * d * d + 0.4 * d);
  vec3 col = t.rgb * vShade * uTorch * light;
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
    for (const n of ["uViewProj", "uTex", "uEye", "uTorch", "uFog", "uReach", "uFlicker", "uAmbient"]) this.loc[n] = gl.getUniformLocation(this.program, n);
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
  setTextures(art) {
    const gl = this.gl;
    if (this.texture) gl.deleteTexture(this.texture);
    this.texture = gl.createTexture();
    this.index = art.index;
    gl.bindTexture(gl.TEXTURE_2D_ARRAY, this.texture);
    gl.texImage3D(gl.TEXTURE_2D_ARRAY, 0, gl.RGBA8, art.size, art.size, art.layers.length, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    art.layers.forEach((layer, i) => gl.texSubImage3D(gl.TEXTURE_2D_ARRAY, 0, 0, 0, i, art.size, art.size, 1, gl.RGBA, gl.UNSIGNED_BYTE, layer));
    gl.generateMipmap(gl.TEXTURE_2D_ARRAY);
    this.crisp = Boolean(art.crisp);                                     // pixel tiles stay pixels when they come close
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_MAG_FILTER, art.crisp ? gl.NEAREST : gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    const aniso = gl.getExtension("EXT_texture_filter_anisotropic");
    if (aniso) gl.texParameterf(gl.TEXTURE_2D_ARRAY, aniso.TEXTURE_MAX_ANISOTROPY_EXT, Math.min(8, gl.getParameter(aniso.MAX_TEXTURE_MAX_ANISOTROPY_EXT)));
  }

  // ---- the floor's mesh ----
  setFloor(floor, theme) {
    this.theme = theme;
    const grid = floor.grid, size = grid.length, out = [], features = floor.features || {};
    const quad = (a, b, c, d, layer, shade) => {           // four corners, counter-clockwise from the bottom left as seen
      const uv = [[0, 1], [1, 1], [1, 0], [0, 0]];
      for (const i of [0, 1, 2, 0, 2, 3]) out.push(...[a, b, c, d][i], uv[i][0], uv[i][1], layer, shade, 0, 1, 0);
    };
    const pickWall = (x, y, d, wx, wy) => {
      const f = features[`${wx},${wy}`];
      if (f && f.type === "secret" && !f.found) return this.index.wallsecret;    // (a hairline, for the sharp-eyed)
      const h = (x * 73856093) ^ (y * 19349663) ^ (d * 83492791);
      const r = ((h >>> 0) % 1000) / 1000;
      return r < this.theme.bones * 0.5 ? this.index.wallbones : r < 0.6 ? this.index.wall : this.index.wall2;
    };
    for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
      if (grid[y][x] !== 0) continue;
      quad([x, 0, y + 1], [x + 1, 0, y + 1], [x + 1, 0, y], [x, 0, y], this.index.floor, 0.9);
      quad([x, 1, y], [x + 1, 1, y], [x + 1, 1, y + 1], [x, 1, y + 1], this.index.ceiling, 0.7);
      const solid = (nx, ny) => ny < 0 || ny >= size || nx < 0 || nx >= size || grid[ny][nx] !== 0;
      if (solid(x, y - 1)) quad([x, 0, y], [x + 1, 0, y], [x + 1, 1, y], [x, 1, y], pickWall(x, y, 0, x, y - 1), 1.0);                 // north wall, facing south
      if (solid(x, y + 1)) quad([x + 1, 0, y + 1], [x, 0, y + 1], [x, 1, y + 1], [x + 1, 1, y + 1], pickWall(x, y, 2, x, y + 1), 1.0);   // south wall, facing north
      if (solid(x + 1, y)) quad([x + 1, 0, y], [x + 1, 0, y + 1], [x + 1, 1, y + 1], [x + 1, 1, y], pickWall(x, y, 1, x + 1, y), 0.84);   // east wall, facing west
      if (solid(x - 1, y)) quad([x, 0, y + 1], [x, 0, y], [x, 1, y], [x, 1, y + 1], pickWall(x, y, 3, x - 1, y), 0.84);                 // west wall, facing east
    }
    const gl = this.gl;
    gl.bindBuffer(gl.ARRAY_BUFFER, this.staticBuf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(out), gl.STATIC_DRAW);
    this.staticCount = out.length / STRIDE;
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
      const layer = this.index[s.layer];
      if (layer === undefined) continue;
      const cx = s.x + 0.5 + (s.dx || 0), cz = s.y + 0.5 + (s.dz || 0), w = s.w || 0.7, h = s.h || 0.7;
      const flash = s.flash || 0, alpha = s.alpha === undefined ? 1 : s.alpha, shade = s.shade || 1, glow = s.glow || 0;
      const uv = [[0, 1], [1, 1], [1, 0], [0, 0]];
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
    const proj = mat4Perspective(Math.PI / 3 * (this.zoomNow || 1), aspect, 0.05, 80);
    this.viewProj = mat4Mul(proj, view);
    const t = this.theme;
    gl.clearColor(t.fog[0], t.fog[1], t.fog[2], 1);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.useProgram(this.program);
    gl.uniformMatrix4fv(this.loc.uViewProj, false, this.viewProj);
    gl.uniform3fv(this.loc.uEye, eye);
    gl.uniform3fv(this.loc.uTorch, t.torch);
    gl.uniform3fv(this.loc.uFog, t.fog);
    gl.uniform1f(this.loc.uReach, t.reach * this.lightNow);
    gl.uniform1f(this.loc.uFlicker, this.flicker);
    gl.uniform1f(this.loc.uAmbient, 0.06 * Math.min(1, this.lightNow * 2));
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D_ARRAY, this.texture);
    gl.uniform1i(this.loc.uTex, 0);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.staticBuf);
    this._attributes();
    gl.drawArrays(gl.TRIANGLES, 0, this.staticCount);
    const dyn = this._spriteMesh();
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
