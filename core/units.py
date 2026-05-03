# core/units.py
import pygame
import yaml
import math
from pathlib import Path
from assets.units.bot_animation import BotAnimationController
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from config import GRID_SZ, COLORS

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

class MeleeUnit:
    def get_attack_action_time(self) -> float:
        return 0.3

class RangedUnit:
    def get_projectile_speed(self) -> float:
        return 200

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
    attack_cooldown: float = 0.0
    target: 'Unit' = None
    
    attack_state: str = "idle"
    attack_timer: float = 0.0

    def __post_init__(self):
        self.current_hp = self.hp
        self._is_moving = False
    
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
        self.anim_timer += dt
        if self.anim_timer >= 0.15:
            self.anim_timer = 0
            self.frame = (self.frame + 1) % 4
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

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

class Warrior(Unit):
    def get_attack_action_time(self) -> float:
        return 0.3

class Archer(Unit, RangedUnit):
    def get_projectile_speed(self) -> float:
        return self.speed * 250

class Mage(Unit, RangedUnit):
    def get_projectile_speed(self) -> float:
        return self.speed * 200

class Tank(Unit):
    def get_attack_action_time(self) -> float:
        return 0.4

class Rogue(Unit):
    def get_attack_action_time(self) -> float:
        return 0.2

class BotWheel(Unit, RangedUnit):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dash_cooldown = 0.0
        self.dash_cd = 3.0
        self.dash_distance = 160
        self.dash_dir = 0
        self.dash_timer = 0.0
        self.dashing = False
        self._anim = None
        self._facing_right = kwargs.get('team', 'A') == "A"
        self._can_shoot = True
    
    def _start_battle(self):
        self._state = "static_idle"
        self._can_shoot = True
    
    def _try_dash(self, enemy, engine) -> bool:
        if self.dash_cooldown > 0 or self.dashing:
            return False
        dist = engine.get_distance(self, enemy)
        if dist >= self.attack_range * 0.7:
            return False
        self.dashing = True
        self.dash_timer = 0.3
        self.dash_cooldown = self.dash_cd
        dx = self.x - enemy.x
        dy = self.y - enemy.y
        d = math.sqrt(dx * dx + dy * dy)
        if d > 0:
            self._dash_target_x = self.x + (dx / d) * self.dash_distance
            self._dash_target_y = self.y + (dy / d) * self.dash_distance
        return True
    
    def _update_dash(self, dt):
        if not self.dashing:
            return
        self.dash_timer -= dt
        if self.dash_timer <= 0:
            self.dashing = False
            return
        dx = self._dash_target_x - self.x
        dy = self._dash_target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 5:
            speed = self.speed * self.dash_distance * 5 * dt
            self.x += (dx / dist) * speed
            self.y += (dy / dist) * speed
    
    def load_assets(self):
        self._anim = BotAnimationController("idle")
    
    def set_action(self, action_name):
        map = {
            "static_idle": "idle",
            "idle": "idle",
            "move": "move",
            "attack": "shoot",
            "reload": "charge",
            "dash": "dash",
            "damage": "damage",
            "death": "death",
        }
        if self._anim:
            anim_name = map.get(action_name, "idle")
            loop = action_name in ["idle", "move"]
            self._anim.set_animation(anim_name, loop=loop)
    
    def update_sprite(self, dt, target=None):
        if not self._anim:
            return
        
        self._anim.update(dt)
        frame = self._anim.current_frame
        
        if target and hasattr(target, 'x'):
            self._facing_right = target.x > self.x
        
        if not self._facing_right and frame:
            frame = pygame.transform.flip(frame, True, False)
        
        self.sprite = frame
    
    UNIT_CLASSES = {
    "warrior": Warrior,
    "archer": Archer,
    "mage": Mage,
    "tank": Tank,
    "rogue": Rogue,
    "bot_wheel": BotWheel,
}

def create_unit_from_data_v2(data, team, x, y):
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
    unit.load_assets()
    return unit