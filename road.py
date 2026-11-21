"""Жигули: Бесконечная дорога — маленькая 2D-игра на pygame.

Сначала собираем Жигуль по деталям (колёса, двигатель, АКБ),
заправляем канистрой, а потом едем по бесконечной трассе:
заправки, дома у дороги, канистры на асфальте. Бензин конечен.

Запуск: python road.py
"""
import math
import random

import pygame

W, H = 800, 600
ROAD_W = 260
ROAD_X = W // 2
FPS = 60

INTRO, WALK, DRIVE, OVER = range(4)
PART_NAMES = ["колесо"] * 4 + ["двигатель", "аккумулятор"]

INTRO_TEXT = ("ЖИГУЛИ: БЕСКОНЕЧНАЯ ДОРОГА\n\n"
              "Часть 1: собери 6 деталей (колёса x4, двигатель, АКБ)\n"
              "Часть 2: найди канистру с бензином\n"
              "Часть 3: заправь машину и жми E рядом с ней\n\n"
              "Дорога бесконечна, бензина мало - заправляйся на АЗС\n"
              "и подбирай канистры. Финал - рекорд в километрах.\n\n"
              "WASD / стрелки - движение, E - действие\n\n"
              "Enter или Space - начать")


def rand(a, b):
    return a + random.random() * (b - a)


class Game:
    def __init__(self):
        self.font_big = pygame.font.Font(None, 30)
        self.font_mid = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 21)
        self.msg = ""
        self.msg_until = 0
        self.best = 0.0
        self.sprites = {"lada": self._build_lada(True),
                        "lada_dark": self._build_lada(False)}
        self.reset()

    # ---------------- состояние ----------------

    def reset(self):
        self.state = INTRO
        self.guy = {"x": float(ROAD_X), "y": 250.0, "speed": 190.0, "dir": 0.0}
        self.car = {"x": float(ROAD_X), "y": 380.0, "angle": 0.0, "speed": 0.0,
                    "max_speed": 330.0, "fuel": 0.0, "fuel_max": 100.0,
                    "parts": 0, "needed": 6, "has_canister": False, "ready": False}
        self.cam_y = 0.0
        self.km = 0.0
        self.hint = ""
        self.objects = []
        self.next_spawn_y = -400.0
        self.start_items = self._make_start_items()

    def _make_start_items(self):
        car = self.car
        spots = [(-170, 60), (170, -20), (-150, -160),
                 (200, -300), (-230, -420), (300, -560)]
        items = [{"type": "part", "name": PART_NAMES[i],
                  "x": car["x"] + spots[i][0], "y": car["y"] + spots[i][1],
                  "taken": False} for i in range(6)]
        items.append({"type": "canister", "x": car["x"] - 260, "y": car["y"] - 700,
                      "taken": False})
        return items

    def show_msg(self, text, sec):
        self.msg = text
        self.msg_until = pygame.time.get_ticks() + int(sec * 1000)

    # ---------------- генерация мира ----------------

    def ensure_world(self, top_y):
        while self.next_spawn_y > top_y:
            self.next_spawn_y -= rand(420, 760)
            y = self.next_spawn_y
            roll = random.random()
            if roll < 0.16 and y < -1200:
                side = -1 if random.random() < 0.5 else 1
                self.objects.append({"type": "station",
                                     "x": ROAD_X + side * (ROAD_W / 2 + 90),
                                     "y": y, "w": 150, "h": 110, "refuel": 0.0})
                self.objects.append({"type": "sign", "side": side,
                                     "x": ROAD_X + side * (ROAD_W / 2 + 30),
                                     "y": y - 40})
            elif roll < 0.34:
                side = -1 if random.random() < 0.5 else 1
                color = random.choice(["#b5443c", "#7a5230", "#5b6f8a", "#8a7a4a"])
                self.objects.append({"type": "house",
                                     "x": ROAD_X + side * (ROAD_W / 2 + 130),
                                     "y": y, "w": 90, "h": 80, "color": color})
                if random.random() < 0.55:
                    self.objects.append({"type": "canister",
                                         "x": ROAD_X + side * (ROAD_W / 2 + 55),
                                         "y": y + 40, "taken": False})
            elif roll < 0.55:
                self.objects.append({"type": "canister",
                                     "x": ROAD_X + rand(-ROAD_W / 2 + 40, ROAD_W / 2 - 40),
                                     "y": y, "taken": False})
            elif roll < 0.70:
                self.objects.append({"type": "pothole",
                                     "x": ROAD_X + rand(-ROAD_W / 2 + 50, ROAD_W / 2 - 50),
                                     "y": y, "r": 26})
            else:
                for _ in range(random.randint(2, 5)):
                    side = -1 if random.random() < 0.5 else 1
                    self.objects.append({"type": "tree",
                                         "x": ROAD_X + side * (ROAD_W / 2 + rand(35, W / 2 - 30)),
                                         "y": y + rand(-200, 200), "s": rand(0.8, 1.4)})

    # ---------------- логика ----------------

    def interact(self):
        car = self.car
        if car["ready"]:
            return
        d = math.hypot(self.guy["x"] - car["x"], self.guy["y"] - car["y"])
        if d < 70 and car["parts"] >= car["needed"] and car["has_canister"]:
            car["ready"] = True
            car["fuel"] = 42.0
            self.state = DRIVE
            self.hint = ""
            self.show_msg("Жигули на ходу! W - газ, S - тормоз,\n"
                          "A/D - руль. Собирай канистры,\n"
                          "заправляйся на АЗС, не брось без бензина!", 4)
        elif d < 70:
            missing = []
            if car["parts"] < car["needed"]:
                missing.append("ещё %d дет. (колёса, двигатель, АКБ)"
                               % (car["needed"] - car["parts"]))
            if not car["has_canister"]:
                missing.append("канистра с бензином")
            self.show_msg("Не хватает:\n- " + "\n- ".join(missing), 2.5)

    def update(self, dt, keys):
        car, guy = self.car, self.guy

        if self.state == WALK:
            dx = dy = 0.0
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                dy -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                dy += 1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                dx -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                dx += 1
            length = math.hypot(dx, dy) or 1.0
            guy["x"] += dx / length * guy["speed"] * dt
            guy["y"] += dy / length * guy["speed"] * dt
            if dx or dy:
                guy["dir"] = math.atan2(dy, dx)
            guy["x"] = max(20, min(W - 20, guy["x"]))

            for item in self.start_items:
                if item["taken"]:
                    continue
                if math.hypot(guy["x"] - item["x"], guy["y"] - item["y"]) < 34:
                    item["taken"] = True
                    if item["type"] == "part":
                        car["parts"] += 1
                    else:
                        car["has_canister"] = True

            near_car = math.hypot(guy["x"] - car["x"], guy["y"] - car["y"]) < 70
            if car["parts"] < car["needed"]:
                self.hint = "Собери детали Жигулей: %d / %d  (колёса x4, двигатель, АКБ)" % (
                    car["parts"], car["needed"])
            elif not car["has_canister"]:
                self.hint = "Теперь найди канистру с бензином (она левее)!"
            elif near_car:
                self.hint = "Нажми E - заправить и завестись!"
            else:
                self.hint = "Отлично! Возвращайся к машине и нажми E."

            self.ensure_world(guy["y"] - H / 2 - 600)

        elif self.state == DRIVE:
            offroad = abs(car["x"] - ROAD_X) > ROAD_W / 2 - 18

            acc = 0.0
            if car["fuel"] > 0:
                if keys[pygame.K_w] or keys[pygame.K_UP]:
                    acc = 240.0
                if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                    acc = -300.0
            car["speed"] += acc * dt
            car["speed"] -= car["speed"] * (1.6 if offroad else 0.5) * dt
            vmax = 130.0 if offroad else car["max_speed"]
            car["speed"] = max(-60.0, min(vmax, car["speed"]))
            car["y"] -= car["speed"] * dt

            steer = (-1 if keys[pygame.K_a] or keys[pygame.K_LEFT] else 0) + \
                    (1 if keys[pygame.K_d] or keys[pygame.K_RIGHT] else 0)
            if car["speed"] != 0:
                sign = 1 if car["speed"] >= 0 else -1
                car["x"] += steer * 160 * dt * min(1.0, abs(car["speed"]) / 120) * sign
                car["angle"] = steer * min(0.35, abs(car["speed"]) / 900) * sign
            car["x"] = max(30, min(W - 30, car["x"]))

            burn = (0.55 + abs(car["speed"]) / car["max_speed"] * 2.2) * (1.8 if offroad else 1.0)
            car["fuel"] = max(0.0, car["fuel"] - burn * dt)
            self.km = (380.0 - car["y"]) / 1000.0

            self.ensure_world(-car["y"] - H / 2 - 600)

            for obj in self.objects:
                if obj.get("taken"):
                    continue
                d = math.hypot(car["x"] - obj["x"], car["y"] - obj["y"])
                if obj["type"] == "canister" and d < 40:
                    obj["taken"] = True
                    car["fuel"] = min(car["fuel_max"], car["fuel"] + 25)
                elif obj["type"] == "station":
                    if abs(car["x"] - obj["x"]) < obj["w"] / 2 + 22 and \
                       abs(car["y"] - obj["y"]) < obj["h"] / 2 + 30:
                        car["fuel"] = min(car["fuel_max"], car["fuel"] + 45 * dt)
                        obj["refuel"] = 1.0
                elif obj["type"] == "pothole":
                    if abs(car["x"] - obj["x"]) < obj["r"] and \
                       abs(car["y"] - obj["y"]) < obj["r"] * 0.7 and abs(car["speed"]) > 40:
                        car["speed"] *= 0.55

            for obj in self.objects:
                if obj["type"] == "station" and obj["refuel"] > 0:
                    obj["refuel"] = max(0.0, obj["refuel"] - dt)

            if car["fuel"] <= 0 and abs(car["speed"]) < 8:
                self.best = max(self.best, self.km)
                self.state = OVER
                self.show_msg("Бензин кончился!\nПройдено: %.2f км\nРекорд: %.2f км\n\n"
                              "Enter - попробовать снова" % (self.km, self.best), 1e9)

        focus_y = guy["y"] if self.state in (WALK, INTRO) else car["y"]
        self.cam_y += (focus_y - H / 2 - self.cam_y) * min(1.0, dt * 6)

    # ---------------- отрисовка ----------------

    def draw(self, screen, now):
        cam_y = self.cam_y

        screen.fill((58, 125, 47))
        for y in range(int(-cam_y % 60) - 60, H, 60):
            pygame.draw.rect(screen, (51, 111, 42), (0, y, W, 30))

        pygame.draw.rect(screen, (85, 90, 96), (ROAD_X - ROAD_W // 2, 0, ROAD_W, H))
        pygame.draw.rect(screen, (138, 133, 119), (ROAD_X - ROAD_W // 2 - 14, 0, 14, H))
        pygame.draw.rect(screen, (138, 133, 119), (ROAD_X + ROAD_W // 2, 0, 14, H))
        for y in range(0, H, 74):
            pygame.draw.rect(screen, (232, 226, 176), (ROAD_X - 3, y, 6, 40))
        pygame.draw.rect(screen, (232, 226, 176), (ROAD_X - ROAD_W // 2 + 2, 0, 4, H))
        pygame.draw.rect(screen, (232, 226, 176), (ROAD_X + ROAD_W // 2 - 6, 0, 4, H))

        visible = [o for o in self.objects if -220 < o["y"] - cam_y < H + 220]
        if self.state in (WALK, INTRO):
            visible += [i for i in self.start_items if not i["taken"]]
        visible.sort(key=lambda o: o["y"])

        for obj in visible:
            sx, sy = int(obj["x"]), int(obj["y"] - cam_y)
            kind = obj["type"]
            if kind == "tree":
                self._draw_tree(screen, sx, sy, obj["s"])
            elif kind == "house":
                self._draw_house(screen, sx, sy, obj)
            elif kind == "station":
                self._draw_station(screen, sx, sy, obj)
            elif kind == "sign":
                self._draw_sign(screen, sx, sy)
            elif kind == "canister":
                self._draw_canister(screen, sx, sy, now)
            elif kind == "pothole":
                self._draw_pothole(screen, sx, sy, obj["r"])
            elif kind == "part":
                self._draw_part(screen, sx, sy, obj["name"], now)

        car = self.car
        cx, cy = int(car["x"]), int(car["y"] - cam_y)
        if self.state == DRIVE:
            sprite = pygame.transform.rotate(
                self.sprites["lada"] if car["ready"] else self.sprites["lada_dark"],
                -math.degrees(car["angle"]))
        else:
            sprite = self.sprites["lada_dark"]
        screen.blit(sprite, sprite.get_rect(center=(cx, cy)))

        if self.state == WALK:
            self._draw_guy(screen, int(self.guy["x"]), int(self.guy["y"] - cam_y))

        self._draw_hud(screen, now)
        if self.state == INTRO:
            self._draw_panel(screen, INTRO_TEXT, (255, 233, 125))
        elif self.msg and pygame.time.get_ticks() < self.msg_until:
            self._draw_panel(screen, self.msg, (255, 233, 125))

    def _draw_tree(self, screen, x, y, s):
        i = int(s)
        pygame.draw.circle(screen, (46, 107, 35), (x, y - 18 * i), 20 * i)
        pygame.draw.circle(screen, (60, 138, 46), (x - 6 * i, y - 24 * i), 13 * i)
        pygame.draw.rect(screen, (107, 74, 42), (x - 4 * i, y - 6 * i, 8 * i, 22 * i))

    def _draw_house(self, screen, x, y, o):
        w, h = o["w"], o["h"]
        pygame.draw.polygon(screen, (90, 58, 34),
                            [(x - w // 2 - 8, y - h // 2), (x, y - h // 2 - 26),
                             (x + w // 2 + 8, y - h // 2)])
        pygame.draw.rect(screen, pygame.Color(o["color"]), (x - w // 2, y - h // 2, w, h))
        pygame.draw.rect(screen, (255, 233, 125), (x - w // 2 + 12, y - 6, 20, 18))
        pygame.draw.rect(screen, (255, 233, 125), (x + w // 2 - 32, y - 6, 20, 18))
        pygame.draw.rect(screen, (74, 53, 36), (x - 9, y + h // 2 - 22, 18, 22))

    def _draw_station(self, screen, x, y, o):
        w, h = o["w"], o["h"]
        pygame.draw.rect(screen, (106, 106, 106), (x - w // 2 - 20, y - h // 2 - 10, w + 40, h + 20))
        pygame.draw.rect(screen, (227, 59, 59), (x - w // 2, y - h // 2, w, h))
        pygame.draw.rect(screen, (255, 255, 255), (x - w // 2 + 6, y - h // 2 + 6, w - 12, 26))
        label = self.font_small.render("АЗС", 1, (17, 17, 17))
        screen.blit(label, label.get_rect(center=(x, y - h // 2 + 19)))
        pygame.draw.rect(screen, (58, 58, 58), (x + w // 2 - 14, y + 6, 22, 30))
        pygame.draw.line(screen, (34, 34, 34), (x + w // 2 - 8, y + 20), (x + w // 2 + 22, y + 14), 3)
        if o["refuel"] > 0 and (pygame.time.get_ticks() // 100) % 2 == 0:
            pygame.draw.rect(screen, (89, 255, 110),
                             (x - w // 2 - 24, y - h // 2 - 14, w + 48, h + 28), 3)

    def _draw_sign(self, screen, x, y):
        pygame.draw.rect(screen, (51, 51, 51), (x - 3, y - 40, 6, 56))
        pygame.draw.rect(screen, (227, 59, 59), (x - 30, y - 64, 60, 30))
        label = self.font_small.render("ТОПЛИВО", 1, (255, 255, 255))
        screen.blit(label, label.get_rect(center=(x, y - 49)))

    def _draw_canister(self, screen, x, y, now):
        pygame.draw.rect(screen, (46, 125, 50), (x - 11, y - 14, 22, 28))
        pygame.draw.rect(screen, (27, 94, 32), (x - 11, y - 14, 22, 6))
        pygame.draw.rect(screen, (51, 51, 51), (x + 4, y - 18, 7, 6))
        label = self.font_mid.render("Б", 1, (255, 204, 0))
        screen.blit(label, (x - label.get_width() // 2 + 3, y - 6))
        if (now // 250) % 2 == 0:
            pygame.draw.rect(screen, (255, 216, 77), (x - 18, y - 30, 36, 38), 2)

    def _draw_pothole(self, screen, x, y, r):
        pygame.draw.ellipse(screen, (43, 43, 43), (x - r, y - r * 0.65, r * 2, r * 1.3))
        pygame.draw.ellipse(screen, (61, 61, 61), (x - r * 0.7 - 3, y - r * 0.45 - 3, r * 1.4, r * 0.9))

    def _draw_part(self, screen, x, y, name, now):
        if name == "колесо":
            pygame.draw.circle(screen, (24, 24, 24), (x, y), 14)
            pygame.draw.circle(screen, (154, 160, 166), (x, y), 6)
        elif name == "двигатель":
            pygame.draw.rect(screen, (122, 127, 133), (x - 15, y - 11, 30, 22))
            pygame.draw.rect(screen, (74, 79, 85), (x - 15, y - 11, 30, 7))
            pygame.draw.rect(screen, (192, 57, 43), (x + 6, y - 4, 6, 6))
        else:
            pygame.draw.rect(screen, (22, 22, 22), (x - 11, y - 14, 22, 28))
            pygame.draw.rect(screen, (255, 216, 77), (x - 7, y - 10, 14, 8))
            plus = self.font_mid.render("+", 1, (58, 160, 255))
            screen.blit(plus, (x - plus.get_width() // 2, y + 2))
        if (now // 250) % 2 == 0:
            pygame.draw.rect(screen, (142, 201, 255), (x - 18, y - 30, 36, 38), 2)

    def _draw_guy(self, screen, x, y):
        step = 1 if (pygame.time.get_ticks() // 150) % 2 == 0 else 0
        pygame.draw.rect(screen, (52, 87, 160), (x - 7, y + 2, 5, 10))
        pygame.draw.rect(screen, (52, 87, 160), (x + 2, y + 2 + step, 5, 10 - step))
        pygame.draw.rect(screen, (192, 57, 43), (x - 8, y - 10, 16, 14))
        pygame.draw.circle(screen, (232, 184, 138), (x, y - 16), 7)
        pygame.draw.rect(screen, (52, 87, 160), (x - 8, y - 23, 16, 5))

    def _build_lada(self, ready):
        surf = pygame.Surface((80, 112), pygame.SRCALPHA)
        body = pygame.Color("#d9d2a8")
        shadow = pygame.Surface((48, 100), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 60))
        surf.blit(shadow, (16, 6))
        for wx, wy in ((8, 14), (58, 14), (8, 76), (58, 76)):
            pygame.draw.rect(surf, (20, 20, 20), (wx, wy, 14, 26))
        pygame.draw.polygon(surf, body,
                            [(22, 10), (58, 10), (64, 26), (64, 94),
                             (57, 104), (23, 104), (16, 94), (16, 26)])
        pygame.draw.rect(surf, (185, 178, 135), (24, 40, 32, 30))
        glass = pygame.Color("#9fd4e8")
        pygame.draw.rect(surf, glass, (26, 26, 28, 10))
        pygame.draw.rect(surf, glass, (26, 74, 28, 8))
        head = (255, 247, 192) if ready else (136, 136, 136)
        pygame.draw.rect(surf, head, (22, 8, 10, 6))
        pygame.draw.rect(surf, head, (48, 8, 10, 6))
        if ready:
            light = pygame.Surface((48, 10), pygame.SRCALPHA)
            pygame.draw.polygon(light, (255, 247, 192, 26),
                                [(0, 10), (48, 10), (40, 0), (8, 0)])
            surf.blit(light, (16, 0))
        pygame.draw.rect(surf, (192, 57, 43), (21, 100, 10, 5))
        pygame.draw.rect(surf, (192, 57, 43), (49, 100, 10, 5))
        pygame.draw.rect(surf, (119, 119, 119), (30, 10, 20, 4))
        return surf

    def _draw_hud(self, screen, now):
        car = self.car
        if self.state in (DRIVE, OVER):
            pygame.draw.rect(screen, (0, 0, 0), (14, 14, 250, 34), border_radius=6)
            pygame.draw.rect(screen, (20, 20, 20), (22, 22, 234, 18), border_radius=4)
            f = car["fuel"] / car["fuel_max"]
            color = (89, 217, 94) if f > 0.5 else ((255, 216, 77) if f > 0.22 else (227, 59, 59))
            if f > 0:
                pygame.draw.rect(screen, color, (22, 22, int(234 * f), 18), border_radius=4)
            if 0 < car["fuel"] <= car["fuel_max"] * 0.22 and (now // 400) % 2 == 0:
                label = self.font_mid.render("МАЛО БЕНЗИНА!", 1, (255, 255, 255))
                screen.blit(label, (280, 22))
            label = self.font_big.render("%.2f км" % self.km, 1, (255, 255, 255))
            screen.blit(label, (14, 58))
            label = self.font_big.render("%d км/ч" % abs(round(car["speed"] / 3)), 1, (255, 255, 255))
            screen.blit(label, (14, 84))
            if self.state == DRIVE and self.km >= self.best > 0:
                label = self.font_mid.render("РЕКОРД!", 1, (255, 216, 77))
                screen.blit(label, (14, 110))
        if self.state == WALK and self.hint:
            pygame.draw.rect(screen, (0, 0, 0), (0, H - 44, W, 44))
            label = self.font_mid.render(self.hint, 1, (255, 233, 125))
            screen.blit(label, label.get_rect(center=(W // 2, H - 22)))

    def _draw_panel(self, screen, text, color):
        lines = text.split("\n")
        w = max(self.font_mid.size(line)[0] for line in lines) + 48
        h = len(lines) * (self.font_mid.get_height() + 6) + 32
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (W // 2, H // 2)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 190))
        screen.blit(surf, rect.topleft)
        pygame.draw.rect(screen, color, rect, 2, border_radius=8)
        for i, line in enumerate(lines):
            label = self.font_mid.render(line, 1, color)
            screen.blit(label, label.get_rect(centerx=W // 2,
                                              y=rect.y + 16 + i * (self.font_mid.get_height() + 6)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Жигули: Бесконечная дорога")
    clock = pygame.time.Clock()
    game = Game()

    running = True
    while running:
        dt = min(0.05, clock.tick(FPS) / 1000.0)
        now = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if game.state in (INTRO, OVER) and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    game.reset()
                    game.state = WALK
                elif game.state == WALK and event.key == pygame.K_e:
                    game.interact()
        game.update(dt, keys)
        game.draw(screen, now)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
