import math
import os
import random

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

from car import Zhigul
from player import Player
from renderer import build_display_list, draw_zhigul, upload_atlas
from tex import build_atlas_surface, tile_uv
from world import BLOCK_NAMES, BLOCK_TILES, BRICK, DIRT, GRASS, LEAVES, PLANK, STONE, \
    WOOD, World, raycast

WIDTH, HEIGHT = 1152, 648
FOV = 70.0
REACH = 5.0

HOTBAR = [GRASS, DIRT, STONE, WOOD, LEAVES, PLANK, BRICK]


def resize(w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOV, w / h, 0.1, 300.0)
    glMatrixMode(GL_MODELVIEW)


def apply_camera(x, y, z, yaw, pitch):
    glRotatef(pitch, 1.0, 0.0, 0.0)
    glRotatef(yaw, 0.0, 1.0, 0.0)
    glTranslatef(-x, -y, -z)


def draw_highlight(cell):
    x, y, z = cell
    a, b = 0.002, 0.998
    corners = [(x + i, y + j, z + k) for i in (a, b) for j in (a, b) for k in (a, b)]
    edges = [(0, 1), (0, 2), (1, 3), (2, 3), (4, 5), (4, 6), (5, 7), (6, 7),
             (0, 4), (1, 5), (2, 6), (3, 7)]
    glDisable(GL_TEXTURE_2D)
    glColor3f(0.05, 0.05, 0.05)
    glLineWidth(2.0)
    glBegin(GL_LINES)
    for i, j in edges:
        for c in (corners[i], corners[j]):
            glVertex3f(*c)
    glEnd()
    glEnable(GL_TEXTURE_2D)


def draw_hud(atlas, sel_index):
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIDTH, 0, HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    cx, cy = WIDTH / 2, HEIGHT / 2
    glDisable(GL_TEXTURE_2D)
    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_LINES)
    glVertex2f(cx - 9, cy)
    glVertex2f(cx + 9, cy)
    glVertex2f(cx, cy - 9)
    glVertex2f(cx, cy + 9)
    glEnd()

    slot = 48
    gap = 6
    total = len(HOTBAR) * (slot + gap) - gap
    bx = (WIDTH - total) / 2
    by = 12
    glBindTexture(GL_TEXTURE_2D, atlas)
    glEnable(GL_TEXTURE_2D)
    for i, b in enumerate(HOTBAR):
        x = bx + i * (slot + gap)
        tile = BLOCK_TILES[b][1]
        u0, v0, u1, v1 = tile_uv(tile)
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(u0, v0)
        glVertex2f(x + 6, by + 6)
        glTexCoord2f(u1, v0)
        glVertex2f(x + slot - 6, by + 6)
        glTexCoord2f(u1, v1)
        glVertex2f(x + slot - 6, by + slot - 6)
        glTexCoord2f(u0, v1)
        glVertex2f(x + 6, by + slot - 6)
        glEnd()
        if i == sel_index:
            glColor3f(1.0, 1.0, 1.0)
        else:
            glColor3f(0.35, 0.35, 0.35)
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x, by)
        glVertex2f(x + slot, by)
        glVertex2f(x + slot, by + slot)
        glVertex2f(x, by + slot)
        glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)


def find_spawn(world):
    cx = world.SIZE // 2
    for _ in range(600):
        x = cx + random.randint(-20, 20)
        z = cx + random.randint(-20, 20)
        gh = world.ground_height(x, z)
        if world.get(x, gh, z) == GRASS and world.get(x, gh + 1, z) == 0 \
                and world.get(x, gh + 2, z) == 0:
            return x + 0.5, gh, z + 0.5
    return cx + 0.5, world.ground_height(cx, cx) + 1.0, cx + 0.5


def init_gl():
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    glClearColor(0.53, 0.78, 0.92, 1.0)
    glEnable(GL_TEXTURE_2D)


def main():
    pygame.init()
    pygame.display.set_caption("Майнкрафт с ЖЫГУЛём (Python)")
    pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF | pygame.OPENGL)
    resize(WIDTH, HEIGHT)
    init_gl()

    seed = random.randrange(1, 99999)
    world = World(seed=seed)
    atlas = upload_atlas(build_atlas_surface(seed % 1000))

    sx, sy, sz = find_spawn(world)
    player = Player(sx, sy, sz)
    car = Zhigul(sx + 6.5, world.ground_height(sx + 6.5, sz + 4.5), sz + 4.5, yaw=45.0)

    in_car = False
    sel_index = 0
    show_cursor = False
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

    clock = pygame.time.Clock()
    frames = 0
    caption_timer = 0.0
    limit = int(os.environ.get("SMOKE_FRAMES", "0")) or None

    running = True
    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        frames += 1
        caption_timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    show_cursor = not show_cursor
                    pygame.event.set_grab(not show_cursor)
                    pygame.mouse.set_visible(show_cursor)
                elif event.key == pygame.K_e:
                    if in_car:
                        th = math.radians(car.yaw)
                        px = car.x + 1.9 * math.cos(th)
                        pz = car.z - 1.9 * math.sin(th)
                        py = world.ground_height(px, pz)
                        player.x, player.y, player.z = px, py, pz
                        player.vx = player.vy = player.vz = 0.0
                        in_car = False
                    elif car.distance_to(player.x, player.z) < 3.0:
                        in_car = True
                        player.vx = player.vy = player.vz = 0.0
                elif not in_car:
                    if event.key == pygame.K_f:
                        player.fly = not player.fly
                        player.vy = 0.0
                    elif pygame.K_1 <= event.key <= pygame.K_7:
                        sel_index = event.key - pygame.K_1
            elif event.type == pygame.MOUSEBUTTONDOWN and not show_cursor and not in_car:
                eye = player.eye_pos()
                dx, dy, dz = player.look_dir()
                hit = raycast(world, *eye, dx, dy, dz, REACH)
                if hit:
                    cell, adjacent = hit
                    if event.button == 1:
                        if cell[1] > 0:
                            world.set_block(*cell, 0)
                    elif event.button == 3 and adjacent and \
                            world.in_bounds(*adjacent) and world.get(*adjacent) == 0:
                        if not player.intersects_block(*adjacent) and \
                                not car.intersects_block(*adjacent):
                            world.set_block(*adjacent, HOTBAR[sel_index])
            elif event.type == pygame.MOUSEMOTION and not show_cursor:
                if in_car:
                    player.pitch = max(-60.0, min(60.0, player.pitch - event.rel[1] * 0.14))
                else:
                    player.rotate(event.rel[0], event.rel[1])

        keys = pygame.key.get_pressed()
        if not show_cursor:
            if in_car:
                car.update(dt, keys[pygame.K_w], keys[pygame.K_s],
                           keys[pygame.K_a], keys[pygame.K_d],
                           keys[pygame.K_SPACE], world)
                player.x, player.z = car.x, car.z
                player.y = car.y + 1.0
                player.yaw = car.yaw
            else:
                move_x = (1 if keys[pygame.K_w] else 0) - (1 if keys[pygame.K_s] else 0)
                move_z = (1 if keys[pygame.K_d] else 0) - (1 if keys[pygame.K_a] else 0)
                player.update(dt, move_x, move_z, keys[pygame.K_SPACE],
                              keys[pygame.K_LCTRL], keys[pygame.K_LSHIFT], world)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        if in_car:
            apply_camera(car.x, car.y + 2.1, car.z, car.yaw, player.pitch)
        else:
            ex, ey, ez = player.eye_pos()
            apply_camera(ex, ey, ez, player.yaw, player.pitch)

        if world.dirty:
            world.dl = build_display_list(world)
            world.dirty = False
        glBindTexture(GL_TEXTURE_2D, atlas)
        glEnable(GL_TEXTURE_2D)
        glColor3f(1.0, 1.0, 1.0)
        glCallList(world.dl)

        draw_zhigul(car)

        if not in_car and not show_cursor:
            eye = player.eye_pos()
            dx, dy, dz = player.look_dir()
            hit = raycast(world, *eye, dx, dy, dz, REACH)
            if hit:
                draw_highlight(hit[0])

        draw_hud(atlas, sel_index)

        pygame.display.flip()

        fps = 1.0 / dt if dt > 0 else 0.0
        if caption_timer >= 0.5:
            caption_timer = 0.0
            if in_car:
                kmh = abs(car.speed) * 3.6
                info = "ЖЫГУЛЬ: W/S газ, A/D поворот, Пробел — тормоз, E — выйти  |  %.0f км/ч" % kmh
            elif car.distance_to(player.x, player.z) < 3.0:
                info = "E — сесть в ЖЫГУЛЬ"
            else:
                info = ("%s  |  ЛКМ — копать, ПКМ — ставить, 1-7 — блоки, F — полёт"
                        % BLOCK_NAMES[HOTBAR[sel_index]])
            pygame.display.set_caption("Майнкрафт с ЖЫГУЛём  |  FPS %.0f  |  %s"
                                       % (fps, info))

        if limit and frames >= limit:
            running = False

    pygame.quit()


if __name__ == "__main__":
    main()
