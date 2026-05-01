# core/battle.py
import random
import math
from dataclasses import dataclass
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
    
    def update(self, dt: float, engine: 'BattleEngine') -> bool:
        if not self.target.alive:
            return False
        
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist < 20:
            self.target.take_damage(self.damage)
            return False
        
        speed = self.speed * dt
        self.x += (dx / dist) * speed
        self.y += (dy / dist) * speed
        return True

class BattleEngine:
    def __init__(self, team_a: list, team_b: list):
        self.team_a = team_a
        self.team_b = team_b
        self.all_units = team_a + team_b
        self.tick = 0
        self.max_ticks = 600
        self.logs = []
        self.projectiles = []
        
        for u in self.all_units:
            u.attack_state = "idle"
            u.attack_timer = 0.0

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
            
            distance = self.get_distance(unit, target)
            attack_range = unit.attack_range if unit.attack_range > 0 else GRID_SZ * 1.5
            
            if unit.attack_state == "idle":
                if distance <= attack_range:
                    if "ranged" in unit.tags:
                        proj = Projectile(
                            x=unit.x,
                            y=unit.y,
                            target=target,
                            speed=unit.speed * 250,
                            damage=unit.atk,
                            color=unit.color,
                            team=unit.team
                        )
                        self.projectiles.append(proj)
                        unit.attack_cooldown = 1.0 / unit.speed
                        unit.attack_state = "cooldown"
                    else:
                        unit.attack_state = "attacking"
                        unit.attack_timer = 0.3
                else:
                    dx = target.x - unit.x
                    dy = target.y - unit.y
                    length = math.sqrt(dx * dx + dy * dy) or 1
                    speed = unit.speed * 100 * dt
                    unit.x += (dx / length) * speed
                    unit.y += (dy / length) * speed
            
            elif unit.attack_state == "attacking":
                unit.attack_timer -= dt
                if unit.attack_timer <= 0:
                    dmg = target.take_damage(unit.atk)
                    unit.regen_mana(3.0)
                    self.logs.append(f"{unit.name} -> {target.name}: -{dmg:.0f} HP")
                    if not target.alive:
                        self.logs.append(f"{target.name} defeated!")
                    unit.attack_state = "cooldown"
                    unit.attack_cooldown = 1.0 / unit.speed
            
            elif unit.attack_state == "cooldown":
                if unit.attack_cooldown > 0:
                    unit.attack_cooldown -= dt
                else:
                    unit.attack_state = "idle"
            
            unit.update_animation(dt)

        a_alive = any(u.alive for u in self.team_a)
        b_alive = any(u.alive for u in self.team_b)
        
        if not a_alive or not b_alive:
            return False
        return True

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