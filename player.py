import math

GRAVITY = 28.0
JUMP_SPEED = 8.6
WALK_SPEED = 6.0
SPRINT_SPEED = 10.0
FLY_SPEED = 16.0


class Player:
    HALF = 0.3
    HEIGHT = 1.8
    EYE = 1.62

    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z
        self.vx = self.vy = self.vz = 0.0
        self.yaw = 0.0
        self.pitch = 0.0
        self.on_ground = False
        self.fly = False

    def eye_pos(self):
        return self.x, self.y + self.EYE, self.z

    def look_dir(self):
        th = math.radians(self.yaw)
        ph = math.radians(self.pitch)
        return (-math.sin(th) * math.cos(ph), math.sin(ph), -math.cos(th) * math.cos(ph))

    def rotate(self, dx, dy):
        self.yaw = (self.yaw - dx * 0.14) % 360.0
        self.pitch = max(-89.0, min(89.0, self.pitch - dy * 0.14))

    def update(self, dt, move_x, move_z, jump, down, sprint, world):
        th = math.radians(self.yaw)
        fwd = (-math.sin(th), -math.cos(th))
        right = (math.cos(th), -math.sin(th))
        mx = fwd[0] * move_x + right[0] * move_z
        mz = fwd[1] * move_x + right[1] * move_z
        norm = math.hypot(mx, mz)
        if norm > 1e-6:
            mx /= norm
            mz /= norm
        speed = SPRINT_SPEED if sprint else WALK_SPEED
        accel = 12.0 if (self.on_ground or self.fly) else 4.0
        f = min(1.0, accel * dt)
        self.vx += (mx * speed - self.vx) * f
        self.vz += (mz * speed - self.vz) * f

        if self.fly:
            vy = 0.0
            if jump:
                vy += FLY_SPEED
            if down:
                vy -= FLY_SPEED
            self.vy += (vy - self.vy) * min(1.0, 12.0 * dt)
        else:
            self.vy -= GRAVITY * dt
            if jump and self.on_ground:
                self.vy = JUMP_SPEED

        self.on_ground = False
        self._move_axis("x", self.vx * dt, world)
        self._move_axis("y", self.vy * dt, world)
        self._move_axis("z", self.vz * dt, world)

        if self.y < -40.0:
            self.y = world.ground_height(self.x, self.z) + 1.0
            self.vy = 0.0

    def _move_axis(self, axis, d, world):
        if d == 0.0:
            return
        x, y, z = self.x, self.y, self.z
        if axis == "x":
            x += d
        elif axis == "y":
            y += d
        else:
            z += d
        if self._collides(world, x, y, z):
            if axis == "y":
                if d < 0:
                    self.on_ground = True
                self.vy = 0.0
            else:
                setattr(self, "v" + axis, 0.0)
            return
        self.x, self.y, self.z = x, y, z

    def _collides(self, world, x, y, z):
        h = self.HALF
        x0 = int(math.floor(x - h))
        x1 = int(math.floor(x + h))
        y0 = int(math.floor(y))
        y1 = int(math.floor(y + self.HEIGHT))
        z0 = int(math.floor(z - h))
        z1 = int(math.floor(z + h))
        for ix in range(x0, x1 + 1):
            for iy in range(y0, y1 + 1):
                for iz in range(z0, z1 + 1):
                    if world.solid(ix, iy, iz):
                        return True
        return False

    def intersects_block(self, cx, cy, cz):
        h = self.HALF
        return (cx < self.x + h and cx + 1 > self.x - h and
                cy < self.y + self.HEIGHT and cy + 1 > self.y and
                cz < self.z + h and cz + 1 > self.z - h)
