import math
from config import ARENA_W, BATTLE_ARENA_H

class AIBehavior:
    def __init__(self, unit, engine):
        self.unit = unit
        self.engine = engine
        self.modules = []

    def add_module(self, module):
        self.modules.append(module)

    def update(self, dt, target):
        for module in self.modules:
            module.update(dt)


class AI1(AIBehavior):
    def __init__(self, unit, engine):
        super().__init__(unit, engine)
        self._reload_timer = 0.0

    def update(self, dt, target):
        if not target or not target.alive:
            return

        if self.unit.has_status("attacking") or self.unit.has_status("dashing"):
            super().update(dt, target)
            return

        distance = self.engine.get_distance(self.unit, target)
        attack_range = self.unit.attack_range if self.unit.attack_range > 0 else 60

        if self._reload_timer > 0:
            self._reload_timer -= dt
            if self._reload_timer <= 0:
                self._reload_timer = 0.0
            self.unit.add_status("reloading")
        else:
            self.unit.remove_status("reloading")

        dx = target.x - self.unit.x
        dy = target.y - self.unit.y
        length = math.sqrt(dx * dx + dy * dy) or 1

        if distance <= attack_range and self._reload_timer <= 0:
            self.unit.add_status("attacking")
            self.unit.set_status_with_timer("attacking", 0.5)
            dmg = target.take_damage(self.unit.atk)
            self.engine.logs.append(f"{self.unit.name} -> {target.name}: -{dmg:.0f} HP")
            if not target.alive:
                self.engine.logs.append(f"{target.name} defeated!")
            self._reload_timer = self.unit.attack_cooldown
        elif distance > attack_range:
            speed = self.unit.speed * 100 * dt
            self.unit.x += (dx / length) * speed
            self.unit.y += (dy / length) * speed
            self.unit.add_status("moving")

        super().update(dt, target)


class AI2(AIBehavior):
    def __init__(self, unit, engine):
        super().__init__(unit, engine)
        self._reload_timer = 0.0

    def _get_ranged_teammates(self):
        teammates = []
        for u in self.engine.all_units:
            if u.team == self.unit.team and u.alive and u.id != self.unit.id:
                if hasattr(u, 'attack_range') and u.attack_range > 0:
                    teammates.append(u)
        return teammates

    def _is_nearest_to_enemy(self, target):
        my_dist = self.engine.get_distance(self.unit, target)
        teammates = self._get_ranged_teammates()
        for tm in teammates:
            dist = self.engine.get_distance(tm, target)
            if dist < my_dist:
                return False
        return True

    def _get_flee_offset_angle(self):
        teammates = self._get_ranged_teammates()
        unit_index = 0
        for i, tm in enumerate(teammates):
            if tm.id == self.unit.id:
                unit_index = i + 1
                break
        base_angle = 30
        offset = base_angle if (unit_index % 2 == 1) else -base_angle
        extra = (unit_index // 2) * 15
        return offset + extra if unit_index % 2 == 1 else offset - extra

    def _rotate_vector(self, dx, dy, angle_deg):
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        new_dx = dx * cos_a - dy * sin_a
        new_dy = dx * sin_a + dy * cos_a
        return new_dx, new_dy

    def _can_move_to(self, dx, dy, distance=40):
        new_x = self.unit.x + dx * distance
        new_y = self.unit.y + dy * distance
        margin = 40
        return margin < new_x < ARENA_W - margin and margin < new_y < BATTLE_ARENA_H - margin

    def _get_safe_flee_direction(self, base_dx, base_dy):
        if self._can_move_to(base_dx, base_dy):
            return base_dx, base_dy
        to_center_x = (ARENA_W / 2 - self.unit.x)
        to_center_y = (BATTLE_ARENA_H / 2 - self.unit.y)
        center_len = math.sqrt(to_center_x * to_center_x + to_center_y * to_center_y)
        if center_len > 0:
            to_center_x /= center_len
            to_center_y /= center_len
        if self._can_move_to(to_center_x, to_center_y):
            return to_center_x, to_center_y
        perp_x = -base_dy
        perp_y = base_dx
        if self._can_move_to(perp_x, perp_y):
            return perp_x, perp_y
        if self._can_move_to(-perp_x, -perp_y):
            return -perp_x, -perp_y
        return 0, 0

    def _is_cornered(self, target):
        dist = self.engine.get_distance(self.unit, target)
        if dist > 100:
            return False
        can_flee = self._can_move_to(-(target.x - self.unit.x), -(target.y - self.unit.y), 20)
        return not can_flee

    def _try_dash_escape(self, dx, dy, target):
        dash_module = None
        for module in self.modules:
            if hasattr(module, 'try_dash'):
                dash_module = module
                break
        if not dash_module:
            return False
        if dash_module.dash_cooldown > 0:
            return False
        if self._is_cornered(target) or not self._can_move_to(dx, dy, 30):
            dash_module.try_dash(target)
            return True
        return False

    def update(self, dt, target):
        if not target or not target.alive:
            return

        if self.unit.has_status("attacking") or self.unit.has_status("dashing"):
            super().update(dt, target)
            return

        distance = self.engine.get_distance(self.unit, target)
        attack_range = self.unit.attack_range
        retreat_range = attack_range * 0.7

        if self._reload_timer > 0:
            self._reload_timer -= dt
            if self._reload_timer <= 0:
                self._reload_timer = 0.0
            self.unit.add_status("reloading")
        else:
            self.unit.remove_status("reloading")

        dx = target.x - self.unit.x
        dy = target.y - self.unit.y
        length = math.sqrt(dx * dx + dy * dy) or 1

        should_flee = distance < retreat_range and self._is_nearest_to_enemy(target)

        if should_flee:
            flee_dx = -(dx / length)
            flee_dy = -(dy / length)
            angle_offset = self._get_flee_offset_angle()
            if angle_offset != 0:
                flee_dx, flee_dy = self._rotate_vector(flee_dx, flee_dy, angle_offset)
            flee_len = math.sqrt(flee_dx * flee_dx + flee_dy * flee_dy) or 1
            flee_dx /= flee_len
            flee_dy /= flee_len

            safe_dx, safe_dy = self._get_safe_flee_direction(flee_dx, flee_dy)
            if safe_dx != 0 or safe_dy != 0:
                self._try_dash_escape(safe_dx, safe_dy, target)
                if not self.unit.has_status("dashing"):
                    speed = self.unit.speed * 80 * dt
                    self.unit.x += safe_dx * speed
                    self.unit.y += safe_dy * speed
                    self.unit.add_status("moving")
            else:
                pass
            super().update(dt, target)
            return

        if distance <= attack_range and self._reload_timer <= 0:
            self.unit.add_status("attacking")
            self.unit.set_status_with_timer("attacking", self.unit.attack_duration)
            self.engine.create_projectile(self.unit, target)
            self._reload_timer = self.unit.attack_cooldown
        elif distance > attack_range:
            speed = self.unit.speed * 100 * dt
            self.unit.x += (dx / length) * speed
            self.unit.y += (dy / length) * speed
            self.unit.add_status("moving")

        super().update(dt, target)