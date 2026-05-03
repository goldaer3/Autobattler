# core/units.py
import pygame
import yaml
import math
from pathlib import Path
from assets.units.bot_animation import BotAnimationController
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from config import GRID_SZ, COLORS

class RangedUnit:
    def get_projectile_speed(self) -> float:
        return 400


class UnitBase(ABC):
    @property
    @abstractmethod
    def id(self) -> str: pass
    
    @property
    @abstractmethod
    def name(self) -> str: pass
    
    @property
    @abstractmethod
    def color(self) -> tuple: pass
    
    @property
    @abstractmethod
    def hp(self) -> float: pass
    
    @property
    @abstractmethod
    def atk(self) -> float: pass
    
    @property
    @abstractmethod
    def def_stat(self) -> float: pass
    
    @property
    @abstractmethod
    def speed(self) -> float: pass
    
    @property
    @abstractmethod
    def attack_range(self) -> float: pass
    
    @property
    @abstractmethod
    def tags(self) -> list: pass
    
    @property
    @abstractmethod
    def current_hp(self) -> float: pass
    
    @property
    @abstractmethod
    def alive(self) -> bool: pass
    
    @property
    @abstractmethod
    def team(self) -> str: pass
    
    @property
    @abstractmethod
    def sprite(self) -> pygame.Surface: pass
    
    @abstractmethod
    def take_damage(self, amount: float) -> float: pass
    
    @abstractmethod
    def regen_mana(self, amount: float): pass
    
    @abstractmethod
    def update_animation(self, dt: float): pass
    
    @abstractmethod
    def load_assets(self): pass



@dataclass
class Unit:
    id: str
    name: str
    color: tuple
    hp: float
    atk: float
    def_stat: float
    speed: float
    attack_range: float = 0.0
    tags: list = field(default_factory=list)
    current_hp: float = 0.0
    mana: float = 0.0
    max_mana: float = 100.0
    alive: bool = True
    x: float = 0.0
    y: float = 0.0
    team: str = "A"
    sprite: pygame.Surface = None
    frame: int = 0
    anim_timer: float = 0.0
    attack_cooldown: float = 0.5
    attack_duration: float = 0.5
    target: 'Unit' = None

    status: set = field(default_factory=set)
    _status_timers: dict = field(default_factory=dict)
    _status_durations: dict = field(default_factory=dict)

    attack_state: str = "idle"
    attack_timer: float = 0.0
    _pos_history: list = field(default_factory=list)

    def __post_init__(self):
        self.current_hp = self.hp
        self._is_moving = False

    def add_status(self, s: str):
        self.status.add(s)

    def remove_status(self, s: str):
        self.status.discard(s)

    def has_status(self, s: str) -> bool:
        return s in self.status

    def clear_status(self):
        self.status.clear()
        self._status_timers.clear()
        self._status_durations.clear()

    def set_status_with_timer(self, s: str, duration: float):
        self.status.add(s)
        self._status_timers[s] = duration
        self._status_durations[s] = duration

    def set_action(self, action_name):
        pass
    
    def on_battle_start(self):
        pass
    
    def load_assets(self):
        size = GRID_SZ - 20
        self.sprite = pygame.Surface((size, size), pygame.SRCALPHA)
        self.sprite.fill(self.color)

    def take_damage(self, amount: float) -> float:
        dmg = max(1.0, amount - self.def_stat)
        self.current_hp -= dmg
        if self.current_hp <= 0:
            self.current_hp = 0
            self.alive = False
        return dmg

    def regen_mana(self, amount: float):
        self.mana = min(self.max_mana, self.mana + amount)

    def update_animation(self, dt: float, target=None):
        self.remove_status("moving")
        self.anim_timer += dt
        if self.anim_timer >= 0.15:
            self.anim_timer = 0
            self.frame = (self.frame + 1) % 4
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        self.update_status_timers(dt)

    def add_status(self, s: str):
        self.status.add(s)

    def remove_status(self, s: str):
        self.status.discard(s)

    def has_status(self, s: str) -> bool:
        return s in self.status

    def set_status_with_timer(self, s: str, duration: float):
        self.status.add(s)
        self._status_timers[s] = duration
        if s == "moving":
            self._pos_history.append((self.x, self.y))
            if len(self._pos_history) > 10:
                self._pos_history.pop(0)

    def get_velocity(self, time_horizon=0.5) -> tuple:
        if len(self._pos_history) < 2:
            return 0.0, 0.0
        recent = self._pos_history[-min(5, len(self._pos_history)):]
        if len(recent) < 2:
            return 0.0, 0.0
        x1, y1 = recent[0]
        x2, y2 = recent[-1]
        dt = time_horizon
        if dt > 0:
            return (x2 - x1) / dt, (y2 - y1) / dt
        return 0.0, 0.0

    def update_status_timers(self, dt: float):
        to_remove = []
        for s, timer in list(self._status_timers.items()):
            self._status_timers[s] -= dt
            if self._status_timers[s] <= 0:
                to_remove.append(s)
                self.status.discard(s)
        for s in to_remove:
            del self._status_timers[s]

    def take_damage(self, amount: float) -> float:
        dmg = max(1.0, amount - self.def_stat)
        self.current_hp -= dmg
        if self.current_hp <= 0:
            self.current_hp = 0
            self.alive = False
            self.add_status("death")
        else:
            self.set_status_with_timer("damage", 0.3)
        return dmg

def load_units_from_yaml(path="data/units.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {u["id"]: u for u in data.get("units", [])}

def create_unit_from_data(data, team, x, y):
    unit = Unit(
        id=data["id"],
        name=data["name"],
        color=tuple(data.get("color", [255, 105, 180])),
        hp=float(data["hp"]),
        atk=float(data["atk"]),
        def_stat=float(data.get("def", 0)),
        speed=float(data.get("speed", 1.0)),
        attack_range=float(data.get("range", 0)),
        tags=data.get("tags", []),
        team=team,
        x=x,
        y=y
    )
    unit.load_assets()
    return unit


class AnimatedUnit(Unit):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._anim = None
        self._facing_right = kwargs.get('team', 'A') == "A"

    def load_assets(self):
        raise NotImplementedError

    def _get_current_animation(self) -> str:
        raise NotImplementedError

    def _is_loop_animation(self, anim_name: str) -> bool:
        raise NotImplementedError

    def set_action(self, action_name):
        if self._anim:
            loop = self._is_loop_animation(action_name)
            self._anim.set_animation(action_name, loop=loop)

    def update_sprite(self, dt, target=None):
        if not self._anim:
            return

        if self.has_status("death"):
            if self._anim._current_anim_name != "death":
                self._anim.set_animation("death", loop=False)
            target = None

        self._anim.update(dt)

        frame = self._anim.current_frame

        if target and hasattr(target, 'x') and self.alive:
            self._facing_right = target.x > self.x

        if not self._facing_right and frame:
            frame = pygame.transform.flip(frame, True, False)

        self.sprite = frame

    def _update_anim_state(self, dt, target):
        is_dead = not self.alive
        effective_target = None if is_dead else target

        anim_name = self._get_current_animation()
        
        should_switch = True
        if self._anim:
            if self._anim._current_anim_name == anim_name:
                should_switch = False
        
        if should_switch:
            loop = self._is_loop_animation(anim_name)
            status_duration = self._status_durations.get(anim_name)
            self._anim.set_animation(anim_name, loop=loop, status_duration=status_duration)
        
        self.update_sprite(dt, effective_target)


class Knight(AnimatedUnit):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._roll_cooldown = 0.0
        self._roll_cd = 2.0
        self._roll_distance = 100
        self._roll_target_x = 0.0
        self._roll_target_y = 0.0

    def load_assets(self):
        from assets.units.bot_animation import BotAnimationController
        self._anim = BotAnimationController("idle", unit_type="knight")

    def _get_current_animation(self) -> str:
        priority_order = ["death", "rolling", "attacking", "hurt", "moving"]
        anim_map = {
            "death": "death",
            "rolling": "roll",
            "attacking": "attack2",
            "hurt": "hurt",
            "moving": "move",
        }
        for status in priority_order:
            if status in self.status:
                return anim_map.get(status, "idle")
        return "idle"

    def _is_loop_animation(self, anim_name: str) -> bool:
        status_loop = self.status & {"idle", "moving", "attacking"}
        return bool(status_loop)

    def _try_roll(self, enemy_x, enemy_y):
        if self._roll_cooldown > 0:
            return False
        if self.has_status("rolling") or self.has_status("attacking"):
            return False
        if not self.alive:
            return False
        
        dx = enemy_x - self.x
        dy = enemy_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            self._roll_target_x = self.x - (dx / dist) * self._roll_distance
            self._roll_target_y = self.y - (dy / dist) * self._roll_distance
        
        self.add_status("rolling")
        self.set_status_with_timer("rolling", 0.3)
        self._roll_cooldown = self._roll_cd
        return True

    def _update_roll(self, dt):
        if not self.has_status("rolling"):
            return
        
        dx = self._roll_target_x - self.x
        dy = self._roll_target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 5:
            speed = self._roll_distance / 0.3
            self.x += (dx / dist) * speed * dt
            self.y += (dy / dist) * speed * dt
        else:
            self.remove_status("rolling")

    def _check_incoming_projectiles(self, engine):
        for proj in getattr(engine, 'projectiles', []):
            if proj.team == self.team:
                continue
            dx = proj.x - self.x
            dy = proj.y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 80 and dist > 0:
                return True
        return False

    def update(self, dt, engine, target):
        self.update_status_timers(dt)

        is_dead = not self.alive
        effective_target = None if is_dead else target

        if not is_dead:
            if self._roll_cooldown > 0:
                self._roll_cooldown -= dt
            
            self._update_roll(dt)
            
            if not self.has_status("rolling"):
                if self._check_incoming_projectiles(engine):
                    for proj in getattr(engine, 'projectiles', []):
                        if proj.team != self.team:
                            self._try_roll(proj.x, proj.y)
                            break

        if not hasattr(self, 'ai') or not self.ai:
            pass

        self._update_anim_state(dt, effective_target)


class BotWheel(AnimatedUnit, RangedUnit):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dash_cooldown = 0.0
        self.dash_cd = 3.0
        self.dash_distance = 160
        self.dash_timer = 0.0
        self._dash_target_x = 0.0
        self._dash_target_y = 0.0
        self._attack_target = None
        self._reload_timer: float = 0.0

    def load_assets(self):
        from assets.units.bot_animation import BotAnimationController
        self._anim = BotAnimationController("idle", unit_type="bot_wheel")

    def _try_dash(self, enemy, engine) -> bool:
        if self.has_status("attacking") or self.has_status("dashing"):
            return False
        if self.dash_cooldown > 0:
            return False
        if engine.get_distance(self, enemy) >= self.attack_range:
            return False

        self.add_status("dashing")
        self.set_status_with_timer("dashing", 0.3)
        self.dash_cooldown = self.dash_cd
        dx = self.x - enemy.x
        dy = self.y - enemy.y
        d = math.sqrt(dx * dx + dy * dy)
        if d > 0:
            self._dash_target_x = self.x + (dx / d) * self.dash_distance
            self._dash_target_y = self.y + (dy / d) * self.dash_distance
        return True

    def _update_dash(self, dt):
        if not self.has_status("dashing"):
            return
        dx = self._dash_target_x - self.x
        dy = self._dash_target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 5:
            speed = self.speed * self.dash_distance * 5 * dt
            self.x += (dx / dist) * speed
            self.y += (dy / dist) * speed

    def start_attack(self, target):
        if self.has_status("dashing") or self.has_status("attacking"):
            return
        self._attack_target = target
        self._reload_timer = self.attack_cooldown
        self.add_status("attacking")
        self.set_status_with_timer("attacking", self.attack_duration)

    def _fire_projectile(self):
        if self._attack_target and self._attack_target.alive:
            from core.battle import BattleEngine
            engine = getattr(self, '_battle_engine', None)
            if engine:
                engine.create_projectile(self, self._attack_target)
        self._attack_target = None

    def take_damage(self, amount: float) -> float:
        dmg = super().take_damage(amount)
        if self.alive:
            self.set_status_with_timer("damaged", 0.3)
        return dmg

    def _get_current_animation(self) -> str:
        priority_order = ["death", "dashing", "damaged", "attacking", "reloading", "moving"]
        anim_map = {
            "death": "death",
            "dashing": "dash",
            "damaged": "damage",
            "attacking": "shoot",
            "reloading": "charge",
            "moving": "move",
        }
        for status in priority_order:
            if status in self.status:
                return anim_map.get(status, "idle")
        return "idle"

    def _is_loop_animation(self, anim_name: str) -> bool:
        status_loop = self.status & {"idle", "moving", "dashing", "attacking"}
        return bool(status_loop)

    def update(self, dt, engine, target):
        self._battle_engine = engine
        self.update_status_timers(dt)

        is_dead = not self.alive
        effective_target = None if is_dead else target

        if not is_dead and not hasattr(self, 'ai') or not self.ai:
            self._update_dash(dt)

            was_attacking = getattr(self, '_was_attacking', False)
            is_attacking = self.has_status("attacking")
            self._was_attacking = is_attacking

            if was_attacking and not is_attacking:
                self._fire_projectile()
                self._reload_timer = self.attack_cooldown

            if self._reload_timer > 0:
                self._reload_timer -= dt
                if self._reload_timer <= 0:
                    self._reload_timer = 0.0
                if not is_attacking:
                    self.add_status("reloading")
            else:
                self.remove_status("reloading")

            if self.dash_cooldown > 0:
                self.dash_cooldown -= dt

        self._update_anim_state(dt, effective_target)


UNIT_CLASSES = {
    "knight": Knight,
    "bot_wheel": BotWheel,
}

def create_unit_from_data_v2(data, team, x, y, engine=None):
    unit_id = data.get("id", "unknown")
    unit_class = UNIT_CLASSES.get(unit_id, Unit)

    unit = unit_class(
        id=data["id"],
        name=data["name"],
        color=tuple(data.get("color", [255, 105, 180])),
        hp=float(data["hp"]),
        atk=float(data["atk"]),
        def_stat=float(data.get("def", 0)),
        speed=float(data.get("speed", 1.0)),
        attack_range=float(data.get("range", 0)),
        tags=data.get("tags", []),
        team=team,
        x=x,
        y=y
    )

    ai_level = data.get("ai_level")
    if ai_level and engine:
        from core.ai.behaviors import AI1, AI2
        if ai_level == 1:
            unit.ai = AI1(unit, engine)
        elif ai_level == 2:
            unit.ai = AI2(unit, engine)

        modules = data.get("modules", [])
        from core.ai.modules import DashModule
        for mod in modules:
            if mod == "dash":
                unit.ai.add_module(DashModule(unit, engine))

    unit.load_assets()
    return unit