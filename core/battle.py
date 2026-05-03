# core/battle.py
import random
import math
from dataclasses import dataclass
from pathlib import Path
from config import GRID_SZ

@dataclass
class Projectile:
    x: float
    y: float
    target: 'Unit'
    speed: float
    damage: float
    color: tuple
    team: str
    target_vx: float = 0.0
    target_vy: float = 0.0
    dir_x: float = 0.0
    dir_y: float = 0.0
    _initialized: bool = False

    def _init_direction(self):
        if self._initialized:
            return
        tx, ty = self.target.x, self.target.y
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            time_to_hit = dist / self.speed
            predict_x = tx + self.target_vx * time_to_hit
            predict_y = ty + self.target_vy * time_to_hit
            lead_dx = predict_x - self.x
            lead_dy = predict_y - self.y
            lead_dist = math.sqrt(lead_dx * lead_dx + lead_dy * lead_dy)
            if lead_dist > 0:
                offset = random.uniform(-0.03, 0.03)
                self.dir_x = (lead_dx / lead_dist) + offset
                self.dir_y = (lead_dy / lead_dist) + offset
                d = math.sqrt(self.dir_x * self.dir_x + self.dir_y * self.dir_y)
                self.dir_x /= d
                self.dir_y /= d
            else:
                self.dir_x = dx / dist
                self.dir_y = dy / dist
        else:
            self.dir_x = 1.0
            self.dir_y = 0.0
        self._initialized = True
        self.speed *= 2.5

    def update(self, dt: float, engine: 'BattleEngine') -> bool:
        if not self.target.alive:
            return False

        self._init_direction()

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 20:
            self.target.take_damage(self.damage)
            return False

        speed = self.speed * dt
        self.x += self.dir_x * speed
        self.y += self.dir_y * speed
        return True

class BattleEngine:
    def __init__(self, team_a: list, team_b: list, arena_w=None, arena_h=None):
        self.team_a = team_a
        self.team_b = team_b
        self.all_units = team_a + team_b
        self.tick = 0
        self.max_ticks = 600
        self.logs = []
        self.projectiles = []

        from config import ARENA_W, BATTLE_ARENA_H
        self.arena_w = arena_w if arena_w is not None else ARENA_W
        self.arena_h = arena_h if arena_h is not None else BATTLE_ARENA_H

        for u in self.all_units:
            u.attack_state = "idle"
            u.attack_timer = 0.0

        self._initialize_ai()

    def clamp_position(self, unit):
        radius = 30
        unit.x = max(radius, min(self.arena_w - radius, unit.x))
        unit.y = max(radius, min(self.arena_h - radius, unit.y))

    def _initialize_ai(self):
        from core.ai.behaviors import AI1, AI2
        from core.ai.modules import DashModule

        units_db_path = Path(__file__).resolve().parent.parent / "data" / "units.yaml"
        import yaml
        with open(units_db_path, "r", encoding="utf-8") as f:
            units_db = {u["id"]: u for u in yaml.safe_load(f).get("units", [])}

        for unit in self.all_units:
            unit_data = units_db.get(unit.id, {})
            ai_level = unit_data.get("ai_level")

            if ai_level == 1:
                unit.ai = AI1(unit, self)
            elif ai_level == 2:
                unit.ai = AI2(unit, self)

            modules = unit_data.get("modules", [])
            if unit.ai and modules:
                for mod in modules:
                    if mod == "dash":
                        unit.ai.add_module(DashModule(unit, self))

    def create_projectile(self, unit, target):
        vx, vy = target.get_velocity()
        proj = Projectile(
            x=unit.x,
            y=unit.y,
            target=target,
            target_vx=vx,
            target_vy=vy,
            speed=unit.get_projectile_speed(),
            damage=unit.atk,
            color=unit.color,
            team=unit.team
        )
        self.projectiles.append(proj)
        return proj

    def get_distance(self, u1, u2) -> float:
        dx = u1.x - u2.x
        dy = u1.y - u2.y
        return math.sqrt(dx * dx + dy * dy)

    def find_nearest_enemy(self, unit) -> 'Unit':
        enemies = self.team_b if unit.team == "A" else self.team_a
        alive_enemies = [e for e in enemies if e.alive]
        if not alive_enemies:
            return None
        return min(alive_enemies, key=lambda e: self.get_distance(unit, e))

    def step(self, dt: float) -> bool:
        self.tick += 1

        self.projectiles = [p for p in self.projectiles if p.update(dt, self)]

        for unit in self.all_units:
            if not unit.alive:
                continue

            target = self.find_nearest_enemy(unit)
            if not target:
                continue

            if hasattr(unit, 'ai') and unit.ai:
                unit.ai.update(dt, target)
            else:
                self._process_ai(unit, target, dt)

            if hasattr(unit, 'update'):
                unit.update(dt, self, target)
            else:
                if hasattr(unit, 'update_status_timers'):
                    unit.update_status_timers(dt)
                unit.update_animation(dt)

            self.clamp_position(unit)

        a_alive = any(u.alive for u in self.team_a)
        b_alive = any(u.alive for u in self.team_b)

        if not a_alive or not b_alive:
            return False

        for unit in self.all_units:
            if hasattr(unit, 'update_sprite'):
                target = self.find_nearest_enemy(unit)
                unit.update_sprite(dt, target)

        return True

    def _process_ai(self, unit, target, dt):
        distance = self.get_distance(unit, target)
        attack_range = unit.attack_range if unit.attack_range > 0 else GRID_SZ * 1.5

        if hasattr(unit, 'has_status'):
            if unit.has_status("attacking") or unit.has_status("dashing"):
                return

        if unit.id == "bot_wheel":
            self._bot_wheel_ai(unit, target, distance, attack_range, dt)
            return

        if "ranged" in unit.tags:
            if distance <= attack_range:
                vx, vy = target.get_velocity()
                proj = Projectile(
                    x=unit.x,
                    y=unit.y,
                    target=target,
                    speed=unit.speed * 250,
                    damage=unit.atk,
                    color=unit.color,
                    team=unit.team,
                    target_vx=vx,
                    target_vy=vy
                )
                self.projectiles.append(proj)
                unit.attack_cooldown = 1.0 / unit.speed
        else:
            if distance <= attack_range:
                dmg = target.take_damage(unit.atk)
                unit.regen_mana(3.0)
                self.logs.append(f"{unit.name} -> {target.name}: -{dmg:.0f} HP")
                if not target.alive:
                    self.logs.append(f"{target.name} defeated!")
            else:
                dx = target.x - unit.x
                dy = target.y - unit.y
                length = math.sqrt(dx * dx + dy * dy) or 1
                speed = unit.speed * 100 * dt
                unit.x += (dx / length) * speed
                unit.y += (dy / length) * speed
                if hasattr(unit, 'add_status'):
                    unit.add_status("moving")

    def _bot_wheel_ai(self, unit, target, distance, attack_range, dt):
        retreat_range = attack_range * 0.7

        if unit.has_status("attacking") or unit.has_status("dashing"):
            return

        if unit.has_status("reloading"):
            return

        dx = target.x - unit.x
        dy = target.y - unit.y
        length = math.sqrt(dx * dx + dy * dy) or 1

        if distance < retreat_range:
            speed = unit.speed * 80 * dt
            unit.x -= (dx / length) * speed
            unit.y -= (dy / length) * speed
            unit.add_status("moving")

            if "dash_ability" in unit.tags and hasattr(unit, '_try_dash'):
                if distance < retreat_range * 0.6:
                    unit._try_dash(target, self)
            return

        if distance <= attack_range:
            unit.start_attack(target)
            return

        speed = unit.speed * 100 * dt
        unit.x += (dx / length) * speed
        unit.y += (dy / length) * speed
        unit.add_status("moving")

    def run_simulation(self, dt: float = 1/60) -> dict:
        while self.step(dt):
            pass
        
        a_alive = sum(1 for u in self.team_a if u.alive)
        b_alive = sum(1 for u in self.team_b if u.alive)
        winner = "A" if a_alive > b_alive else ("B" if b_alive > a_alive else "draw")
        
        return {
            "winner": winner,
            "ticks": self.tick,
            "survivors_a": a_alive,
            "survivors_b": b_alive,
            "logs": self.logs[-20:]
        }