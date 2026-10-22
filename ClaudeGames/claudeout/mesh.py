"""Mesh helpers shared by the vault and the surface: quads and boxes in the engine's vertex format
(x y z, u v, shade - six floats a vertex), and a cell grid for finding the boxes near a point."""
from . import art


def quad_uv(buf, pts, uvs, shade):
    """Two triangles for the quad pts[0..3] (counter-clockwise seen from the front), with a uv per corner."""
    for i in (0, 1, 2, 0, 2, 3):
        buf.extend(pts[i])
        buf.extend(uvs[i])
        buf.append(shade)


def quad(buf, a, b, c, d, tex, shade, reps=(1, 1)):
    """A quad a-b-c-d textured with one tile (reps > 1 stretches the tile across it that many times - only for
    tiles that tile, since the atlas clamps)."""
    u0, v0, u1, v1 = art.uv(tex)
    ru, rv = reps
    uvs = ((u0, v1), (u0 + (u1 - u0) * ru, v1), (u0 + (u1 - u0) * ru, v0 + (v1 - v0) * (1 - rv)), (u0, v0 + (v1 - v0) * (1 - rv)))
    quad_uv(buf, (a, b, c, d), uvs, shade)


def box(buf, x0, y0, z0, x1, y1, z1, top, side, bottom=False, front=None):
    """A box with its top and four sides (front: the -z face's own texture)."""
    quad(buf, (x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0), top, 1.0)
    quad(buf, (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), side, 0.8)           # +z
    quad(buf, (x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0), front or side, 0.8)  # -z
    quad(buf, (x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1), side, 0.65)          # +x
    quad(buf, (x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0), side, 0.65)          # -x
    if bottom:
        quad(buf, (x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), side, 0.5)


def cross(buf, x, y, z, w, h, tex, shade=0.9):
    """Two quads crossed at right angles: a tree or a bush that looks the same from every side."""
    quad(buf, (x - w / 2, y, z), (x + w / 2, y, z), (x + w / 2, y + h, z), (x - w / 2, y + h, z), tex, shade)
    quad(buf, (x, y, z - w / 2), (x, y, z + w / 2), (x, y + h, z + w / 2), (x, y + h, z - w / 2), tex, shade)


def box_grid(boxes, cell=4):
    """{(cx, cz): [(x0, z0, x1, z1), ...]} - which boxes touch each cell-sized patch of ground."""
    grid = {}
    for b in boxes:
        x0, z0, x1, z1 = b[0], b[1], b[2], b[3]
        for cx in range(int(x0 // cell), int(x1 // cell) + 1):
            for cz in range(int(z0 // cell), int(z1 // cell) + 1):
                grid.setdefault((cx, cz), []).append((x0, z0, x1, z1))
    return grid


def boxes_near(grid, x, z, cell=4):
    cx, cz = int(x // cell), int(z // cell)
    out = []
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            out.extend(grid.get((cx + dx, cz + dz), ()))
    return out
