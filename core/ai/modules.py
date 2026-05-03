import math

class AIModule:
    def __init__(self, unit, engine):
        self.unit = unit
        self.engine = engine

    def update(self, dt):
        pass


class DashModule(AIModule):
    def __init__(self, unit, engine, dash_distance=160, dash_cd=3.0):
        super().__init__(unit, engine)
        self.dash_distance = dash_distance
        self.dash_cd = dash_cd
        self.dash_cooldown = 0.0
        self._dash_target_x = 0.0
        self._dash_target_y = 0.0
        self.dash_speed = unit.speed * self.dash_distance * 5

    def update(self, dt):
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt

        if not self.unit.has_status("dashing"):
            return

        dx = self._dash_target_x - self.unit.x
        dy = self._dash_target_y - self.unit.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 5:
            speed = self.dash_speed * dt
            self.unit.x += (dx / dist) * speed
            self.unit.y += (dy / dist) * speed
        else:
            self.unit.remove_status("dashing")

    def try_dash(self, target):
        if self.dash_cooldown > 0:
            return False
        if self.unit.has_status("attacking") or self.unit.has_status("dashing"):
            return False

        dist = self.engine.get_distance(self.unit, target)
        if dist >= self.unit.attack_range:
            return False

        self.unit.add_status("dashing")
        self.unit.set_status_with_timer("dashing", 0.3)
        self.dash_cooldown = self.dash_cd

        dx = self.unit.x - target.x
        dy = self.unit.y - target.y
        d = math.sqrt(dx * dx + dy * dy)
        if d > 0:
            self._dash_target_x = self.unit.x + (dx / d) * self.dash_distance
            self._dash_target_y = self.unit.y + (dy / d) * self.dash_distance

        return True