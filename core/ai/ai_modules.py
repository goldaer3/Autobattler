import math

class AIModule:
    def __init__(self, unit, engine):
        self.unit = unit
        self.engine = engine

    def update(self, dt):
        pass


class RollModule(AIModule):
    def __init__(self, unit, engine, roll_distance=100, roll_cd=2.0):
        super().__init__(unit, engine)
        self.roll_distance = roll_distance
        self.roll_cd = roll_cd
        self.roll_cooldown = 0.0
        self._roll_target_x = 0.0
        self._roll_target_y = 0.0
        self.roll_speed = unit.speed * roll_distance * 5

    def update(self, dt):
        if self.roll_cooldown > 0:
            self.roll_cooldown -= dt

        if not self.unit.has_status("rolling"):
            return

        dx = self._roll_target_x - self.unit.x
        dy = self._roll_target_y - self.unit.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 5:
            speed = self.roll_speed * dt
            self.unit.x += (dx / dist) * speed
            self.unit.y += (dy / dist) * speed
            self.unit._last_move_dx = dx  # Сохраняем направление движения
        else:
            self.unit.remove_status("rolling")

    def try_roll(self, enemy_x, enemy_y):
        if self.roll_cooldown > 0:
            return False
        if self.unit.has_status("rolling") or self.unit.has_status("attacking"):
            return False
        if not self.unit.alive:
            return False

        dx = enemy_x - self.unit.x
        dy = enemy_y - self.unit.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            self._roll_target_x = self.unit.x - (dx / dist) * self.roll_distance
            self._roll_target_y = self.unit.y - (dy / dist) * self.roll_distance

        self.unit.add_status("rolling")
        self.unit.set_status_with_timer("rolling", 0.3)
        self.roll_cooldown = self.roll_cd
        return True

    def check_and_roll(self, threats):
        if not threats:
            return False
        for threat in threats:
            dist = self.engine.get_distance(self.unit, threat)
            if dist < 80:
                self.try_roll(threat.x, threat.y)
                return True
        return False


class PowerAttackModule(AIModule):
    def __init__(self, unit, engine, damage_multiplier=2.0, cd=3.0):
        super().__init__(unit, engine)
        self.damage_multiplier = damage_multiplier
        self.cd = cd
        self.cooldown = 0.0

    def update(self, dt):
        if self.cooldown > 0:
            self.cooldown -= dt

    def can_power_attack(self):
        return self.cooldown <= 0

    def trigger_power_attack(self, target, engine):
        if not self.can_power_attack():
            return None

        dmg = target.take_damage(self.unit.atk * self.damage_multiplier)
        target.set_status_with_timer("stun", 1.0)
        engine.logs.append(f"{self.unit.name} -> {target.name}: -{dmg:.0f} HP (POWER ATTACK + STUN!)")
        self.cooldown = self.cd

        return dmg


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
            self.unit._last_move_dx = dx  # Сохраняем направление движения
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


class Spell1Module(AIModule):
    def __init__(self, unit, engine, spell_cd=8.0):
        super().__init__(unit, engine)
        self.spell_cd = spell_cd
        self.spell_cooldown = 0.0

    def update(self, dt):
        if self.spell_cooldown > 0:
            self.spell_cooldown -= dt

    def try_spell(self):
        if self.spell_cooldown > 0:
            return False

        enemies = []
        for u in self.engine.all_units:
            if u.team != self.unit.team and u.alive:
                enemies.append(u)

        if not enemies:
            return False

        target = min(enemies, key=lambda e: self.engine.get_distance(self.unit, e))

        # Телепортируем врага сразу
        far_x = self.engine.arena_w - 50 if self.unit.x < self.engine.arena_w / 2 else 50
        far_y = self.engine.arena_h - 50 if self.unit.y < self.engine.arena_h / 2 else 50

        target.x = far_x
        target.y = far_y
        self.engine.logs.append(f"{self.unit.name} teleported {target.name} to the void!")

        self.spell_cooldown = self.spell_cd
        return True


