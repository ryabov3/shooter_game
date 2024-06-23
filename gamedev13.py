import pygame
import os
import random
import csv
from pygame import mixer
from button import Button
from enum import Enum

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# игровые константы
ROWS = 16
COLS = 150
SCROLL_THRESH = 200
TILE_TYPES = 21
TILE_SIZE = SCREEN_HEIGHT // ROWS
GRAVITY = 0.8
level = 1
screen_scroll = 0
bg_scroll = 0
BG = (72, 61, 139)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('shooter')

# загрузка звуковых эффектов
mixer.music.load('audio/embient.wav')
mixer.music.set_volume(0.3)
mixer.music.play(-1, 0.0, 5000)
shoot_audio = mixer.Sound('audio/shot_audio2.wav')
shoot_audio.set_volume(1)
grenade_audio = mixer.Sound('audio/grenade.wav')
grenade_audio.set_volume(0.2)
jump_audio = mixer.Sound('audio/jump.mp3')
jump_audio.set_volume(0.05)


# загрузка изображений
# кнопки
start_button_img = pygame.image.load('IMG/button/start_button.png').convert_alpha()
exit_button_img = pygame.image.load('IMG/button/exit_button.png').convert_alpha()
restart_game_img = pygame.image.load('IMG/button/restart_button.png').convert_alpha()

# фон
bg = pygame.image.load('IMG/background/bg.png').convert_alpha()
bg = pygame.transform.scale(bg, (bg.get_width() * 3, bg.get_height() * 3))

mountain_far = pygame.image.load('IMG/background/mountain far.png').convert_alpha()
mountain_far = pygame.transform.scale(mountain_far, (mountain_far.get_width() * 2, mountain_far.get_height() * 2))

mountains = pygame.image.load('IMG/background/mountains.png').convert_alpha()
mountains = pygame.transform.scale(mountains, (mountains.get_width() * 2, mountains.get_height() * 2))

trees = pygame.image.load('IMG/background/trees.png').convert_alpha()
trees = pygame.transform.scale(trees, (trees.get_width() * 2, trees.get_height() * 2))

grass = pygame.image.load('IMG/background/grass.png').convert_alpha()
grass = pygame.transform.scale(grass, (grass.get_width() * 2, grass.get_height() * 2))

# игровые плиты
img_list = []
for i in range(TILE_TYPES):
    img = pygame.image.load(f'img/tile/{i}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)
# изображение пули
bullet_img = pygame.image.load('IMG/icons/bullet.png').convert_alpha()
# изображение гранаты
grenade_img = pygame.image.load('IMG/icons/grenade.png').convert_alpha()
# изображение ящика с аптечкой
health_box_img = pygame.image.load('IMG/icons/boxes/health_box.png').convert_alpha()
# изображение ящика с гранатами
ammo_box_img = pygame.image.load('IMG/icons/boxes/ammo_box.png').convert_alpha()
# изображение ящика с гранатами
grenade_box_img = pygame.image.load('IMG/icons/boxes/grenade_box.png').convert_alpha()

# словарь со всеми ящиками
item_boxes = {
    'Health': health_box_img,
    'Grenade': grenade_box_img,
    'Ammo': ammo_box_img
}

# шрифт для информации об игроке
font = pygame.font.SysFont('Futura', 30)
def draw_information_player(text, font, color, x, y):
    font = font.render(text, 1, color, RED)
    screen.blit(font, (x, y))

# отрисовка фона
def draw_bg():
    screen.fill(BG)
    width = mountains.get_width()
    for x in range(5):
        screen.blit(bg, ((x * width), 0))
        screen.blit(mountain_far, ((x * width) - bg_scroll * 0.6, SCREEN_HEIGHT - mountain_far.get_height() - 200))
        screen.blit(mountains, ((x * width) - bg_scroll * 0.6, SCREEN_HEIGHT - mountains.get_height() - 200))
        screen.blit(grass, ((x * width) - bg_scroll * 0.8, SCREEN_HEIGHT - grass.get_height() - -200))

clock = pygame.time.Clock()
FPS = 60

# создание действий игрока
moving_left = False
moving_right = False
shoot = False
attack = False
start_game = False
grenade, grenade_throw = False, False

# создание класса игрока/противника
class Fighter(pygame.sprite.Sprite):
    def __init__(self, player_or_enemy, x, y, scale, speed, ammo, grenades):
        pygame.sprite.Sprite.__init__(self)
        self.player_or_enemy = player_or_enemy
        self.alive = True
        self.jump = False
        self.speed = speed
        self.score = 0
        self.grenades = grenades
        self.ammo = ammo
        self.start_ammo = ammo
        self.health = 100
        self.max_health = self.health
        self.shoot_cooldown = 0
        self.direction = 1
        self.flip = False
        self.animations = []
        self.action = 0
        self.vel_y = 0
        self.in_air = True
        self.scale = scale
        self.attack_cooldown = 100
        # переменные только для ИИ
        self.move_counter = 0 # счётчик, который определяет смену направления ИИ
        self.iddling = False
        self.iddling_counter = 0 # счётчик, который определяет время бездействия ИИ
        self.vision = pygame.Rect(0, 0, 200, 30)

        # загрузка всех анимаций персонажа
        for animation in ['Idle', 'Run', 'Death', 'Shot', 'Grenade', 'Attack']:
            self.__load_images(animation)
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.image = self.animations[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def update(self):
        self.update_animation()
        self.check_alive()
        # постепенное уменьшение кулдауна для выстрела
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self, moving_left, moving_right):
        screen_scroll = 0
        dx = 0
        dy = 0

        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
            self.direction = -1

        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1

        if self.jump and not self.in_air:
            self.vel_y = -11.5
            self.jump = False
            self.in_air = True

        self.vel_y += GRAVITY
        dy += self.vel_y

        # коллизия с окружением
        for tile in world.obstacle_list:
            # проверка коллизии для движения влево/вправо
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.rect.width, self.rect.height):
                dx = 0
                # если враг врезался в стену, он меняет направление
                if self.player_or_enemy == 'enemy':
                    self.direction *= -1
                    self.move_counter = 0
            # проверка коллизии для движения вверх/вниз
            if tile[1].colliderect(self.rect.x, self.rect.y + dy + 1, self.rect.width, self.rect.height):
                # если персонаж находится в прыжке
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                # если персонаж не в прыжке или упал
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    dy = tile[1].top - self.rect.bottom
                    self.in_air = False

        # в перспективе для разных уровней, учитываем границы самого экрана, чтобы игрок за них не вышел
        if self.player_or_enemy == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0

        # если игрок упал в пропасть (провалился под карту)
        if self.rect.bottom + dx > SCREEN_HEIGHT:
            self.health = 0

        # если игрок упал в воду
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0

        self.rect.x += dx
        self.rect.y += dy


        # обновление перемещения экрана исходя из позиции игрока
        if self.player_or_enemy == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < (world.world_length * TILE_SIZE) - SCREEN_WIDTH) \
                    or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx
        return screen_scroll

    def attack(self):
        for enemy in enemy_group:
            if pygame.sprite.collide_rect(self, enemy):
                enemy.health = 0

    # стрельба
    def shoot(self):
        # проверка кулдауна
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20
            bullet = Bullet(self.rect.centerx + (0.7 * self.rect.size[0] * self.direction), self.rect.centery - 19, self.direction)
            bullets_group.add(bullet)
            # уменьшение количества патронов после выстрела
            self.ammo -= 1
            shoot_audio.play()

    # контроль ИИ
    def ai_control(self):
        # остановка противника в случайный момент
        if random.randint(1, 500) == 1 and self.iddling == False and self.alive:
            self.update_action(0)  # idle: 0
            self.iddling = True
            self.iddling_counter = 100

        # если игрок находится в поле зрения противника
        if self.vision.colliderect(player.rect) and self.alive:
            # прекращение бега и открытие огня по игроку
            self.update_action(3) # idle: 0
            self.shoot()
        else:
            if self.iddling == False:
                if self.alive and player.alive:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1) # run: 1
                    self.move_counter += 1
                    self.vision.center = (self.rect.centerx + 100 * self.direction, self.rect.centery)
                if self.move_counter > TILE_SIZE:
                    self.direction *= -1
                    self.move_counter = 0
            else:
                self.iddling_counter -= 1
                if self.iddling_counter == 0:
                    self.iddling = False

        # перемещение противников
        self.rect.x += screen_scroll

    # проверка на то, жив ли игрок/противник
    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(2)

    def update_animation(self):
        ANIMATION_COOLDOWN = 100

        self.image = self.animations[self.action][self.frame_index]

        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1

        if self.frame_index >= len(self.animations[self.action]):
            if self.action == 2:
                self.frame_index = len(self.animations[self.action]) - 1
            else:
                self.frame_index = 0

    # обновление анимации персонажа
    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.update_time = pygame.time.get_ticks()
            self.frame_index = 0

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

    def __load_images(self, path):
        temp_list = []
        n = len(os.listdir(f'IMG/{self.player_or_enemy}/{path}'))
        for i in range(n):
            img = pygame.image.load(fr'IMG/{self.player_or_enemy}/{path}/{i}.png').convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * self.scale), int(img.get_height() * self.scale)))
            temp_list.append(img)
        self.animations.append(temp_list)

# создание класса полоски хп
class HealthBar:
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        self.health = health

        # вычисляем в процентном соотношении количество хп у игрока
        hp_per = self.health / self.max_health

        # рисуем полоски здоровья
        pygame.draw.rect(screen, BLACK, (self.x - 1, self.y - 1, 152, 22))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * hp_per, 20))

# создание класса мира игры
class World:
    def __init__(self):
        self.obstacle_list = []

    def process_data(self, data):
        self.world_length = len(data[0])
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                # проверяем >= 0, так как это будет какое-то изображение
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    if 0 <= tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif 9 <= tile <= 10: # блоки воды
                        water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
                        water_group.add(water)
                    elif 11 <= tile <= 14: # декорации
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 15: # создание игрока
                        player = Fighter('player', x * TILE_SIZE, y * TILE_SIZE, 1, 5, 20, 5)
                        health_bar = HealthBar(20, 20, 100, 100)
                    elif tile == 16: # создание врага
                        enemy = Fighter('enemy', x * TILE_SIZE, y * TILE_SIZE, 1, 2, 20, 0)
                        enemy_group.add(enemy)
                    elif tile == 17: # создание ящика с патронами
                        ammo_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(ammo_box)
                    elif tile == 18: # создание ящика с гранатами
                        grenade_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(grenade_box)
                    elif tile == 19: # создание ящика с аптечкой
                        health_box = ItemBox('Health', x * TILE_SIZE,  y * TILE_SIZE)
                        item_box_group.add(health_box)
                    elif tile == 20: # выход
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)

        return player, health_bar

    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])

# создание класса пуль
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(bullet_img, (bullet_img.get_width() * 0.7, bullet_img.get_height() * 0.7))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction
        self.speed = 10

    def update(self):
        # движение пули
        self.rect.x += (self.direction) * self.speed + screen_scroll

        # проверяем положение пули, находится ли она на экране
        if self.rect.left > SCREEN_WIDTH or self.rect.right < 0:
            self.kill()

        # проверка коллизии пули с объектами
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()

        # проверка коллизии пули с игроком/противником
        if pygame.sprite.spritecollide(player, bullets_group, False):
            if player.alive:
                player.health -= 5
                self.kill()

        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullets_group, False):
                if enemy.alive:
                    enemy.health -= 25
                    self.kill()

# создание класса гранат
class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = 100
        self.direction = direction
        self.speed = 7
        self.vel_y = -11
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def update(self):
        self.vel_y += GRAVITY
        dx = self.direction * self.speed + screen_scroll
        dy = self.vel_y

        for tile in world.obstacle_list:
            # коллизия гранаты с объектами по оси x
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.rect.width, self.rect.height):
                self.direction *= -1
                dx = self.direction * self.speed
                # проверка коллизии для движения вверх/вниз
            if tile[1].colliderect(self.rect.x, self.rect.y + dy + 1, self.rect.width, self.rect.height):
                self.speed = 0
                # если граната находится в воздухе
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                    # если граната на земле
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    dy = tile[1].top - self.rect.bottom

        # обновление позиции гранаты
        self.rect.x += dx
        self.rect.y += dy

        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            grenade_audio.play()
            exp = Explosion(self.rect.x, self.rect.y, 1)
            explosion_group.add(exp)

            # нанесение урона кому-либо
            if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and \
                    abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
                player.health -= 50

            for enemy in enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and \
                        abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
                    enemy.health -= 100

# создание класса взрывов
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.animations_for_explosion = []
        for i in range(len(os.listdir('IMG/explosion'))):
            img = pygame.image.load(f'IMG/explosion/{i}.png').convert_alpha()
            img = pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))
            self.animations_for_explosion.append(img)
        self.frame_index = 0
        self.image = self.animations_for_explosion[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y - 50)
        self.counter = 0

    def update(self):
        self.rect.x += screen_scroll
        EXPLOSION_SPEED = 4
        # обновление анимации взрыва
        self.counter += 1

        if self.counter > EXPLOSION_SPEED:
            self.frame_index += 1
            self.counter = 0
            # если анимация завершена, удаляем взрыв
            if self.frame_index > len(self.animations_for_explosion) - 1:
                self.kill()
            else:
                self.image = self.animations_for_explosion[self.frame_index]

# создание класса декораций
class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

# создание класса объектов воды
class Water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

#создание класса выхода с уровня
class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

# создание класса ящиков
class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_box_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_box_type = item_box_type
        self.image = item_boxes[self.item_box_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll
        # проверка на коллизию с ящиками
        if pygame.sprite.collide_rect(self, player):
            # какой ящик подобрал игрок
            if self.item_box_type == 'Health':
                if player.health == 100:
                    pass
                elif player.health + 20 > 100:
                    player.health = 100
                    self.kill()
                else:
                    player.health += 20
                    self.kill()
            elif self.item_box_type == 'Ammo':
                if player.ammo == 20:
                    pass
                elif player.ammo + 10 > 20:
                    player.ammo = 20
                    self.kill()
                else:
                    player.ammo += 10
                    self.kill()
            elif self.item_box_type == 'Grenade':
                if player.grenades == 5:
                    pass
                elif player.grenades + 1 > 5:
                    player.grenades = 5
                    self.kill()
                else:
                    player.grenades += 1
                    self.kill()

# создание групп спрайтов
bullets_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()


run = True
# создаём базу данных игрового мира и заполняем её пустыми клетками (-1 = пустое пространство)
world_data = []
for row in range(ROWS):
    r = [-1] * COLS
    world_data.append(r)
# загрузка мира и создание уровня
with open(f'level{level}_data.csv', newline='') as csv_file:
    reader = csv.reader(csv_file, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data)

# создание кнопок
start_button = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 170, start_button_img, 1.2)
exit_button = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2  + 50, exit_button_img, 1.2)

# основной игровой цикл
while run:

    clock.tick(FPS)

    if not start_game:
        screen.fill(BG)
        if start_button.draw(screen):
            start_game = True
        if exit_button.draw(screen):
            run = False
        start_game = True
    else:

        draw_bg()

        # прорисовка мира
        world.draw()

        for enemy in enemy_group:
            enemy.draw()
            enemy.ai_control()
            enemy.update()

        player.draw()
        player.update()

        # обновление и отросовка всех групп спрайтов
        bullets_group.update()
        bullets_group.draw(screen)
        grenade_group.update()
        grenade_group.draw(screen)
        explosion_group.update()
        explosion_group.draw(screen)
        item_box_group.update()
        item_box_group.draw(screen)
        decoration_group.update()
        decoration_group.draw(screen)
        water_group.update()
        water_group.draw(screen)
        exit_group.update()
        exit_group.draw(screen)

        # обновление табличек с информации о состоянии игрока
        health_bar.draw(player.health)
        draw_information_player(f'Ammo: {player.ammo}', font, (144, 17, 20), 20, 50)
        draw_information_player(f'Grenades: {player.grenades}', font, (244, 15, 200), 20, 80)

        if player.alive:
            if moving_left or moving_right:
                player.update_action(1) # run: 1
            elif shoot:
                player.update_action(3) # shot: 3
                player.shoot()
            elif grenade:
                player.update_action(4) # grenade: 4
                if grenade_throw == False and player.grenades > 0:
                    gnd = Grenade(player.rect.centerx + (0.65 * player.rect.size[0] * player.direction), player.rect.top, player.direction)
                    grenade_group.add(gnd)
                    player.grenades -= 1
                    grenade_throw = True
            elif attack:
                player.update_action(5)
                player.attack()
            else:
                player.update_action(0) # idle: 0
            screen_scroll = player.move(moving_left, moving_right)
            bg_scroll -= screen_scroll

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a and player.alive:
                    moving_left = True
                if event.key == pygame.K_d and player.alive:
                    moving_right = True
                if event.key == pygame.K_w and player.alive:
                    player.jump = True
                    jump_audio.play()
                if event.key == pygame.K_SPACE and player.alive:
                    shoot = True
                if event.key == pygame.K_l and player.alive:
                    grenade = True
                if event.key == pygame.K_e:
                    attack = True

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    moving_left = False
                if event.key == pygame.K_d:
                    moving_right = False
                if event.key == pygame.K_SPACE:
                    shoot = False
                if event.key == pygame.K_l:
                    grenade = False
                    grenade_throw = False
                if event.key == pygame.K_e:
                    attack = False

    pygame.display.update()

pygame.quit()