import pygame
from OpenGL.GL import GL_COMPILE, GL_NEAREST, GL_QUADS, GL_RGBA, GL_TEXTURE_2D, \
    GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER, GL_UNSIGNED_BYTE, glBegin, glBindTexture, \
    glColor3f, glEnd, glEndList, glGenLists, glGenTextures, glNewList, glPopMatrix, \
    glPushMatrix, glRotatef, glTexCoord2f, glTexImage2D, glTexParameteri, glTranslatef, \
    glVertex3f
from tex import tile_uv

def upload_atlas(surf):
    data = pygame.image.tostring(surf, "RGBA", True)
    tid = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tid)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surf.get_width(), surf.get_height(),
                 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    return tid



def build_display_list(world):
    dl = glGenLists(1)
    glNewList(dl, GL_COMPILE)
    glBegin(GL_QUADS)
    for (x, y, z), b in world.blocks.items():
        _emit_block(world, x, y, z, b)
    glEnd()
    glEndList()
    return dl


def _emit_block(world, x, y, z, b):
    from world import BLOCK_TILES, FACES
    top, side, bottom = BLOCK_TILES[b]
    for (nx, ny, nz), shade, verts in FACES:
        if world.solid(x + nx, y + ny, z + nz):
            continue
        tile = top if ny == 1 else bottom if ny == -1 else side
        u0, v0, u1, v1 = tile_uv(tile)
        uvs = (u0, u1), (v0, v1)
        glColor3f(shade, shade, shade)
        for rx, ry, rz, u_sel, v_sel in verts:
            glTexCoord2f(uvs[0][u_sel], uvs[1][v_sel])
            glVertex3f(x + rx, y + ry, z + rz)


BODY = (0.52, 0.07, 0.11)
GLASS = (0.30, 0.42, 0.52)
TIRE = (0.07, 0.07, 0.08)
METAL = (0.72, 0.72, 0.74)
HEADLIGHT = (1.00, 0.95, 0.55)
TAILLIGHT = (0.85, 0.08, 0.05)
SEAT = (0.35, 0.12, 0.10)


def _shade(rgb, k):
    return (rgb[0] * k, rgb[1] * k, rgb[2] * k)


def _box(cx, cy, cz, sx, sy, sz, rgb):
    x0, x1 = cx - sx / 2.0, cx + sx / 2.0
    y0, y1 = cy - sy / 2.0, cy + sy / 2.0
    z0, z1 = cz - sz / 2.0, cz + sz / 2.0
    faces = [
        (1.0, [(x0, y1, z1), (x0, y1, z0), (x1, y1, z0), (x1, y1, z1)]),
        (0.5, [(x0, y0, z0), (x0, y0, z1), (x1, y0, z1), (x1, y0, z0)]),
        (0.70, [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)]),
        (0.70, [(x0, y0, z1), (x0, y0, z0), (x0, y1, z0), (x0, y1, z1)]),
        (0.85, [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]),
        (0.85, [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)]),
    ]
    glBegin(GL_QUADS)
    for k, verts in faces:
        glColor3f(*_shade(rgb, k))
        for vx, vy, vz in verts:
            glVertex3f(vx, vy, vz)
    glEnd()



def draw_zhigul(car):
    glPushMatrix()
    glTranslatef(car.x, car.y, car.z)
    glRotatef(car.yaw, 0.0, 1.0, 0.0)

    for wx in (-0.85, 0.85):
        for wz in (-1.35, 1.35):
            _box(wx, 0.34, wz, 0.26, 0.68, 0.7, TIRE)

    _box(0.0, 0.78, 0.0, 1.72, 0.85, 4.25, BODY)

    _box(0.0, 1.45, -0.15, 1.58, 0.6, 2.0, GLASS)
    _box(-0.78, 1.45, -0.15, 0.14, 0.6, 2.0, BODY)
    _box(0.78, 1.45, -0.15, 0.14, 0.6, 2.0, BODY)
    _box(0.0, 1.45, 0.85, 1.58, 0.6, 0.16, BODY)
    _box(0.0, 1.78, -0.15, 1.60, 0.14, 2.1, BODY)

    _box(-0.40, 1.25, 0.15, 0.6, 0.2, 0.7, SEAT)
    _box(0.40, 1.25, 0.15, 0.6, 0.2, 0.7, SEAT)

    _box(0.0, 0.5, -2.22, 1.85, 0.22, 0.2, METAL)
    _box(0.0, 0.5, 2.22, 1.85, 0.22, 0.2, METAL)

    _box(-0.55, 0.88, -2.14, 0.34, 0.22, 0.12, HEADLIGHT)
    _box(0.55, 0.88, -2.14, 0.34, 0.22, 0.12, HEADLIGHT)
    _box(-0.55, 0.88, 2.14, 0.34, 0.22, 0.12, TAILLIGHT)
    _box(0.55, 0.88, 2.14, 0.34, 0.22, 0.12, TAILLIGHT)

    glPopMatrix()
