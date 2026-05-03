import math
from config import ARENA_W, BATTLE_ARENA_H
from core.ai.ai_modules import RollModule, PowerAttackModule, DashModule, Spell1Module

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
        self._special_attack_timer = 0.0

    def _get_module(self, module_class):
        for mod in self.modules:
            if isinstance(mod, module_class):
                return mod
        return None

    def update(self, dt, target):
        if not target or not target.alive:
            return

        if self.unit.has_status("stun"):
            super().update(dt, target)
            return

        if self.unit.has_status("fear") and self.unit.fear_source and self.unit.fear_source.alive:
            self._update_flee_from_fear(dt)
            super().update(dt, target)
            return

        if self.unit.has_status("attacking") or self.unit.has_status("dashing") or self.unit.has_status("rolling"):
            super().update(dt, target)
            return

        roll_mod = self._get_module(RollModule)
        if roll_mod:
            projectiles = []
            for proj in getattr(self.engine, 'projectiles', []):
                if proj.team != self.unit.team:
                    projectiles.append(proj)
            roll_mod.check_and_roll(projectiles)

        power_attack_mod = self._get_module(PowerAttackModule)
        if power_attack_mod:
            if power_attack_mod.cooldown > 0:
                power_attack_mod.cooldown -= dt

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
            can_power = power_attack_mod and power_attack_mod.can_power_attack()
            
            if can_power:
                self.unit.add_status("attacking_special")
                special_duration = getattr(self.unit, '_special_attack_duration', 0.33)
                self.unit.set_status_with_timer("attacking_special", special_duration)
                power_attack_mod.trigger_power_attack(target, self.engine)
            else:
                self.unit.add_status("attacking")
                duration = getattr(self.unit, 'attack_duration', 0.5)
                self.unit.set_status_with_timer("attacking", duration)
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

    def _update_flee_from_fear(self, dt):
        fear_source = self.unit.fear_source
        if not fear_source or not fear_source.alive:
            self.unit.remove_status("fear")
            self.unit.fear_source = None
            return

        dx = self.unit.x - fear_source.x
        dy = self.unit.y - fear_source.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist == 0:
            dist = 1

        if hasattr(self.unit, '_facing_right'):
            self.unit._facing_right = fear_source.x < self.unit.x

        flee_speed = self.unit.speed * 120 * dt
        margin = 40
        new_x = self.unit.x + (dx / dist) * flee_speed
        new_y = self.unit.y + (dy / dist) * flee_speed

        if margin < new_x < ARENA_W - margin and margin < new_y < BATTLE_ARENA_H - margin:
            self.unit.x = new_x
            self.unit.y = new_y
        else:
            angle = math.atan2(dy, dx)
            angle += math.pi / 2
            self.unit.x += math.cos(angle) * flee_speed * 0.5
            self.unit.y += math.sin(angle) * flee_speed * 0.5

        self.unit.add_status("moving")


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

        if self.unit.has_status("stun"):
            super().update(dt, target)
            return

        if self.unit.has_status("fear") and self.unit.fear_source and self.unit.fear_source.alive:
            self._update_flee_from_fear(dt)
            super().update(dt, target)
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


class AI3(AIBehavior):
    def __init__(self, unit, engine):
        super().__init__(unit, engine)
        self._reload_timer = 0.0
        self._attack_timer = 0.0

    def _get_module(self, module_class):
        for mod in self.modules:
            if isinstance(mod, module_class):
                return mod
        return None

    def update(self, dt, target):
        print(f"[AI3] {self.unit.name}: status={self.unit.status}, reload={self._reload_timer:.2f}, attack_timer={self._attack_timer:.2f}, attack_type={getattr(self.unit, '_attack_type', 'basic')}")
        
        if not target or not target.alive:
            print(f"[AI3] no target")
            return

        if self.unit.has_status("stun"):
            super().update(dt, target)
            return

        if self.unit.has_status("fear") and self.unit.fear_source and self.unit.fear_source.alive:
            self._update_flee_from_fear(dt)
            super().update(dt, target)
            return

        if self.unit.has_status("attacking") or self.unit.has_status("dashing"):
            print(f"[AI3] busy, running modules")
            for module in self.modules:
                module.update(dt)
            super().update(dt, target)
            return

        for module in self.modules:
            module.update(dt)

        if self._reload_timer > 0:
            self._reload_timer -= dt
            if self._reload_timer <= 0:
                self._reload_timer = 0.0
                self.unit._attack_type = "basic"

        if self._attack_timer > 0:
            self._attack_timer -= dt
            if self._attack_timer <= 0:
                self._attack_timer = 0.0
                print(f"[AI3] attack timer ended, firing projectile!")
                if hasattr(self.unit, '_fire_projectile'):
                    self.unit._fire_projectile(self.engine)
                self.unit._attack_type = "basic"

        spell_mod = None
        for module in self.modules:
            if isinstance(module, Spell1Module):
                spell_mod = module
                break

        distance = self.engine.get_distance(self.unit, target)
        attack_range = self.unit.attack_range
        
        print(f"[AI3] distance={distance:.0f}, range={attack_range}, reload={self._reload_timer:.2f}, attack_timer={self._attack_timer:.2f}, spell_cd={spell_mod.spell_cooldown if spell_mod else 'N/A'}")

        # Priority 1: Use spell if ready
        if spell_mod and spell_mod.spell_cooldown <= 0:
            print(f"[AI3] spell ready, using spell")
            if spell_mod.try_spell():
                print(f"[AI3] SPELL CAST!")
                self.unit.add_status("attacking")
                self.unit.set_status_with_timer("attacking", 1.0)
                self.unit._attack_type = "spell"
                self._reload_timer = spell_mod.spell_cd
                return

        # Priority 2: Use attack if spell in cooldown
        spell_ready = spell_mod and spell_mod.spell_cooldown > 0
        attack_ready = self._reload_timer <= 0 and self._attack_timer <= 0
        
        if spell_ready and attack_ready and distance <= attack_range:
            print(f"[AI3] ATTACK! Adding attacking status")
            self.unit.add_status("attacking")
            self.unit.set_status_with_timer("attacking", getattr(self.unit, 'attack_duration', 0.5))
            self.unit._attack_type = "basic"
            self._reload_timer = getattr(self.unit, 'attack_cooldown', 5.0)
            self._attack_timer = getattr(self.unit, 'attack_duration', 0.5)
            return

        # Priority 3: Move to far edge if both spell and attack in cooldown
        if spell_ready and attack_ready:
            margin = 50
            if self.unit.x < margin or self.unit.x > ARENA_W - margin or self.unit.y < margin or self.unit.y > BATTLE_ARENA_H - margin:
                print(f"[AI3] at edge, staying idle")
                self.unit.remove_status("moving")
            else:
                print(f"[AI3] both on cooldown, moving to far edge")
                far_x = 50 if target.x > ARENA_W / 2 else ARENA_W - 50
                far_y = 50 if target.y > BATTLE_ARENA_H / 2 else BATTLE_ARENA_H - 50
                
                dx = far_x - self.unit.x
                dy = far_y - self.unit.y
                length = math.sqrt(dx * dx + dy * dy) or 1
                speed = self.unit.speed * 80 * dt
                self.unit.x += (dx / length) * speed
                self.unit.y += (dy / length) * speed
                self.unit.add_status("moving")
            return

        # If in attack range, attack; otherwise move toward target
        if distance > attack_range:
            print(f"[AI3] out of range, moving toward target")
            dx = target.x - self.unit.x
            dy = target.y - self.unit.y
            length = math.sqrt(dx * dx + dy * dy) or 1
            speed = self.unit.speed * 80 * dt
            self.unit.x += (dx / length) * speed
            self.unit.y += (dy / length) * speed
            self.unit.add_status("moving")

        super().update(dt, target)

    def _update_flee_from_fear(self, dt):
        fear_source = self.unit.fear_source
        if not fear_source or not fear_source.alive:
            self.unit.remove_status("fear")
            self.unit.fear_source = None
            return

        dx = self.unit.x - fear_source.x
        dy = self.unit.y - fear_source.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist == 0:
            dist = 1

        if hasattr(self.unit, '_facing_right'):
            self.unit._facing_right = fear_source.x < self.unit.x

        flee_speed = self.unit.speed * 120 * dt
        margin = 40
        new_x = self.unit.x + (dx / dist) * flee_speed
        new_y = self.unit.y + (dy / dist) * flee_speed

        if margin < new_x < ARENA_W - margin and margin < new_y < BATTLE_ARENA_H - margin:
            self.unit.x = new_x
            self.unit.y = new_y
        else:
            angle = math.atan2(dy, dx)
            angle += math.pi / 2
            self.unit.x += math.cos(angle) * flee_speed * 0.5
            self.unit.y += math.sin(angle) * flee_speed * 0.5

        self.unit.add_status("moving")