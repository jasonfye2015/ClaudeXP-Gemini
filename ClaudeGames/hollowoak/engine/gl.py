"""The thin layer over OpenGL 3.3 core (PyOpenGL): programs, meshes, textures. Everything else draws through this.
(The same small layer the Timeline's other first-person games use, kept here so this game stands on its own.)"""
import ctypes
import io

import numpy as np
import OpenGL

OpenGL.ERROR_CHECKING = False            # (PyOpenGL checks every call by default: far too slow for a frame's draws)
OpenGL.ERROR_LOGGING = False
from OpenGL import GL  # noqa: E402

from PIL import Image


class Program:
    def __init__(self, vs, fs):
        self.id = GL.glCreateProgram()
        shaders = []
        for kind, src in ((GL.GL_VERTEX_SHADER, vs), (GL.GL_FRAGMENT_SHADER, fs)):
            s = GL.glCreateShader(kind)
            GL.glShaderSource(s, src)
            GL.glCompileShader(s)
            if not GL.glGetShaderiv(s, GL.GL_COMPILE_STATUS):
                raise RuntimeError(GL.glGetShaderInfoLog(s).decode(errors="replace") + "\n" + src[:400])
            GL.glAttachShader(self.id, s)
            shaders.append(s)
        GL.glLinkProgram(self.id)
        if not GL.glGetProgramiv(self.id, GL.GL_LINK_STATUS):
            raise RuntimeError(GL.glGetProgramInfoLog(self.id).decode(errors="replace"))
        for s in shaders:
            GL.glDeleteShader(s)
        self._loc = {}

    def loc(self, name):
        if name not in self._loc:
            self._loc[name] = GL.glGetUniformLocation(self.id, name)
        return self._loc[name]

    def use(self):
        GL.glUseProgram(self.id)
        return self

    def mat4(self, name, m, count=1):
        GL.glUniformMatrix4fv(self.loc(name), count, GL.GL_TRUE, np.ascontiguousarray(m, np.float32))   # (row-major in)

    def vec(self, name, v):
        v = np.asarray(v, np.float32).ravel()
        {1: GL.glUniform1fv, 2: GL.glUniform2fv, 3: GL.glUniform3fv, 4: GL.glUniform4fv}[len(v)](self.loc(name), 1, v)

    def vec3s(self, name, arr):
        a = np.ascontiguousarray(arr, np.float32)
        if len(a):
            GL.glUniform3fv(self.loc(name), len(a), a)

    def vec4s(self, name, arr):
        a = np.ascontiguousarray(arr, np.float32)
        if len(a):
            GL.glUniform4fv(self.loc(name), len(a), a)

    def int(self, name, v):
        GL.glUniform1i(self.loc(name), int(v))

    def float(self, name, v):
        GL.glUniform1f(self.loc(name), float(v))


class Mesh:
    """One vertex array: interleaved float32 attributes (+ optional uint32 indices)."""

    def __init__(self, layout, data=None, indices=None, dynamic=False):
        self.layout = layout                       # [(location, components), ...] all float32
        self.stride = sum(c for _, c in layout) * 4
        self.vao = GL.glGenVertexArrays(1)
        self.vbo = GL.glGenBuffers(1)
        self.ebo = None
        self.count = 0
        self.dynamic = dynamic
        GL.glBindVertexArray(self.vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        off = 0
        for loc, comps in layout:
            GL.glEnableVertexAttribArray(loc)
            GL.glVertexAttribPointer(loc, comps, GL.GL_FLOAT, GL.GL_FALSE, self.stride, ctypes.c_void_p(off))
            off += comps * 4
        if indices is not None:
            self.ebo = GL.glGenBuffers(1)
        GL.glBindVertexArray(0)
        if data is not None:
            self.upload(data, indices)

    def upload(self, data, indices=None):
        data = np.ascontiguousarray(data, np.float32)
        GL.glBindVertexArray(self.vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, data.nbytes, data if data.size else None,
                        GL.GL_DYNAMIC_DRAW if self.dynamic else GL.GL_STATIC_DRAW)
        if indices is not None:
            indices = np.ascontiguousarray(indices, np.uint32)
            GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.ebo)
            GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL.GL_STATIC_DRAW)
            self.count = len(indices)
        else:
            self.count = data.size * 4 // self.stride
        GL.glBindVertexArray(0)

    def draw(self, mode=GL.GL_TRIANGLES):
        if not self.count:
            return
        GL.glBindVertexArray(self.vao)
        if self.ebo is not None:
            GL.glDrawElements(mode, self.count, GL.GL_UNSIGNED_INT, None)
        else:
            GL.glDrawArrays(mode, 0, self.count)
        GL.glBindVertexArray(0)

    def draw_range(self, first, count, mode=GL.GL_TRIANGLES):
        """A run of the vertices (no indices): one frame of many kept one after another."""
        GL.glBindVertexArray(self.vao)
        GL.glDrawArrays(mode, first, count)
        GL.glBindVertexArray(0)

    def delete(self):
        GL.glDeleteBuffers(1, [self.vbo])
        if self.ebo is not None:
            GL.glDeleteBuffers(1, [self.ebo])
        GL.glDeleteVertexArrays(1, [self.vao])


def _mip(target):
    GL.glGenerateMipmap(target)
    GL.glTexParameteri(target, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR)
    GL.glTexParameteri(target, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    try:
        GL.glTexParameterf(target, 0x84FE, 8.0)           # (anisotropic filtering, where the card has it)
    except Exception:
        pass


def texture_array(images, size=512, srgb=True):
    """A 2D texture array from PIL images (each resized to size x size, RGBA); srgb False for data (normal maps)."""
    tex = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D_ARRAY, tex)
    GL.glTexImage3D(GL.GL_TEXTURE_2D_ARRAY, 0, GL.GL_SRGB8_ALPHA8 if srgb else GL.GL_RGBA8, size, size, len(images), 0, GL.GL_RGBA,
                    GL.GL_UNSIGNED_BYTE, None)
    for i, im in enumerate(images):
        im = im.convert("RGBA").resize((size, size), Image.LANCZOS)
        GL.glTexSubImage3D(GL.GL_TEXTURE_2D_ARRAY, 0, 0, 0, i, size, size, 1, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE,
                           im.tobytes())
    GL.glTexParameteri(GL.GL_TEXTURE_2D_ARRAY, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
    GL.glTexParameteri(GL.GL_TEXTURE_2D_ARRAY, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
    _mip(GL.GL_TEXTURE_2D_ARRAY)
    return tex


def texture_2d(image, srgb=True, repeat=True, mip=True):
    if isinstance(image, (bytes, bytearray)):
        image = Image.open(io.BytesIO(image))
    im = image.convert("RGBA")
    tex = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_SRGB8_ALPHA8 if srgb else GL.GL_RGBA8, im.width, im.height, 0,
                    GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, im.tobytes())
    wrap = GL.GL_REPEAT if repeat else GL.GL_CLAMP_TO_EDGE
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, wrap)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, wrap)
    if mip:
        _mip(GL.GL_TEXTURE_2D)
    else:
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    return tex


def perspective(fovy_deg, aspect, near, far):
    f = 1.0 / np.tan(np.radians(fovy_deg) / 2)
    m = np.zeros((4, 4), np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = 2 * far * near / (near - far)
    m[3, 2] = -1
    return m


def view_matrix(eye, yaw, pitch):
    """Looking along yaw (0 = -z, turning right as yaw grows) and pitch (up positive)."""
    cy, sy, cp, sp = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch)
    fwd = np.array([sy * cp, sp, -cy * cp], np.float32)
    right = np.array([cy, 0, sy], np.float32)
    up = np.cross(right, fwd)
    m = np.identity(4, np.float32)
    m[0, :3], m[1, :3], m[2, :3] = right, up, -fwd
    m[:3, 3] = -m[:3, :3] @ np.asarray(eye, np.float32)
    return m


def model_matrix(x, y, z, yaw, s):
    """Scaled, turned about y by yaw (facing yaw like the camera), stood at (x, y, z)."""
    c, sn = np.cos(yaw), np.sin(yaw)
    m = np.identity(4, np.float32)
    m[0, 0], m[0, 2] = c * s, -sn * s
    m[2, 0], m[2, 2] = sn * s, c * s
    m[1, 1] = s
    m[:3, 3] = (x, y, z)
    return m
