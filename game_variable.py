from enum import Enum
import pygame

# игровые константы
class GameConstants(Enum):
    SCREEN_WIDTH: int = 800
    SCREEN_HEIGHT: int = 600
    ROWS: int = 16
    MAX_LEVEL: int = 3
    COLS: int = 150
    SCROLL_THRESH: int = 200
    TILE_TYPES: int = 21
    TILE_SIZE: int = SCREEN_HEIGHT // ROWS
    GRAVITY: float = 0.8
    BG: tuple[int] = (72, 61, 139)
    RED: tuple[int] = (255, 0, 0)
    GREEN: tuple[int] = (0, 255, 0)
    BLACK: tuple[int] = (0, 0, 0)

# создание групп спрайтов
class SpriteGroups:
    bullets_group: pygame.sprite.Group = pygame.sprite.Group()
    grenade_group: pygame.sprite.Group = pygame.sprite.Group()
    explosion_group: pygame.sprite.Group = pygame.sprite.Group()
    enemy_group: pygame.sprite.Group = pygame.sprite.Group()
    item_box_group: pygame.sprite.Group = pygame.sprite.Group()
    decoration_group: pygame.sprite.Group = pygame.sprite.Group()
    water_group: pygame.sprite.Group = pygame.sprite.Group()
    exit_group: pygame.sprite.Group = pygame.sprite.Group()

    @staticmethod
    def reset_group() -> None:
        SpriteGroups.bullets_group.empty()
        SpriteGroups.grenade_group.empty()
        SpriteGroups.explosion_group.empty()
        SpriteGroups.enemy_group.empty()
        SpriteGroups.item_box_group.empty()
        SpriteGroups.decoration_group.empty()
        SpriteGroups.water_group.empty()
        SpriteGroups.exit_group.empty()


# создание пустого уровня
def reset_level() -> list[list[int]]:
    SpriteGroups.reset_group()

    data: list[list[int]] = []
    for row in range(GameConstants.ROWS.value):
        r: list[int] = [-1] * GameConstants.COLS.value
        data.append(r)
    return data
