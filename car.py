import math

class Zhigul:
    MAX_SPEED = 24.0
    MAX_REVERSE = 8.0
    ACCEL = 16.0
    TURN_RATE = 110.0
    HALF_L = 2.15
    HALF_W = 0.95

    def __init__(self, x, y, z, yaw=0.0):
        self.x, self.y, self.z = x, y, z
        self.yaw = yaw
        self.speed = 0.0
        self.vy = 0.0

    def forward(self):
        th = math.radians(self.yaw)
        return -math.sin(th), -math.cos(th)

    def update(self, dt, gas, reverse, left, right, brake, world):
        if gas:
            self.speed = min(self.MAX_SPEED, self.speed + self.ACCEL * dt)
        elif reverse:
            if self.speed > 0.1:
                self.speed = max(0.0, self.speed - self.ACCEL * 2.5 * dt)
            else:
                self.speed = max(-self.MAX_REVERSE, self.speed - self.ACCEL * 0.7 * dt)
        else:
            self.speed *= math.exp(-1.2 * dt)
        if brake:
            self.speed *= math.exp(-4.0 * dt)
        if abs(self.speed) < 0.05:
            self.speed = 0.0

        steer = (1.0 if left else 0.0) - (1.0 if right else 0.0)
        if steer and abs(self.speed) > 0.3:
            sign = 1.0 if self.speed >= 0.0 else -1.0
            factor = min(1.0, abs(self.speed) / 6.0)
            self.yaw = (self.yaw + self.TURN_RATE * dt * steer * sign * factor) % 360.0

        step = self.speed * dt
        if step:
            fx, fz = self.forward()
            nx = self.x + fx * step
            nz = self.z + fz * step
            if not self._blocked(world, nx, nz):
                self.x, self.z = nx, nz
            else:
                self.speed = 0.0

        gh = world.ground_height(self.x, self.z, min(world.WORLD_HEIGHT - 1,
                                                     int(math.floor(self.y)) + 2))
        if self.y < gh - 1e-3:
            self.y = gh
            self.vy = 0.0
        else:
            self.vy -= 25.0 * dt
            self.y += self.vy * dt
            if self.y < gh:
                self.y = gh
                self.vy = 0.0

    def _blocked(self, world, x, z):
        th = math.radians(self.yaw)
        c, s = math.cos(th), math.sin(th)
        for lx, lz in ((-self.HALF_W, -self.HALF_L), (self.HALF_W, -self.HALF_L),
                       (-self.HALF_W, self.HALF_L), (self.HALF_W, self.HALF_L),
                       (0.0, -self.HALF_L), (0.0, self.HALF_L),
                       (-self.HALF_W, 0.0), (self.HALF_W, 0.0)):
            wx = x + lx * c + lz * s
            wz = z - lx * s + lz * c
            ix, iz = int(math.floor(wx)), int(math.floor(wz))
            for iy in (int(math.floor(self.y + 1.05)), int(math.floor(self.y + 1.7))):
                if world.solid(ix, iy, iz):
                    return True
        return False

    def intersects_block(self, cx, cy, cz):
        return (abs(cx + 0.5 - self.x) < self.HALF_L + 0.5 and
                abs(cz + 0.5 - self.z) < self.HALF_L + 0.5 and
                cy < self.y + 2.0 and cy + 1 > self.y)

    def distance_to(self, x, z):
        return math.hypot(x - self.x, z - self.z)
