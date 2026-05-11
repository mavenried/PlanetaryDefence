#!/bin/env python3
import sys
import random
from math import radians, sin, cos, degrees

import pygame


WIDTH = 1200
HEIGHT = 800
PLAY_WIDTH = 800
FPS = 60

BACKGROUND = "#000030"
WHITE = "#FFFFFF"

PLAYER_X = 400
PLAYER_Y = 800

MAX_LIVES = 10
MAX_HYPERCLEAR = 5

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()


try:
    with open("Highscore.txt", "r") as f:
        highscore = int(f.read().strip())
except (FileNotFoundError, ValueError):
    highscore = 0


BULLET_IMAGE = pygame.image.load("Assets/bullet.png").convert_alpha()


class Bullet:
    def __init__(self, pos, speed, angle, color=False):
        angle = radians(angle)

        self.x = pos[0]
        self.y = pos[1]

        self.xvel = speed * cos(angle)
        self.yvel = -speed * sin(angle)

        self.heading = angle
        self.color = color

        self.rect = pygame.Rect(self.x - 5, self.y - 5, 10, 10)

    def update(self, dt):
        self.x += self.xvel * dt * 60
        self.y += self.yvel * dt * 60

        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        if self.color:
            pygame.draw.rect(surface, "blue", self.rect)
        else:
            img = pygame.transform.rotozoom(
                BULLET_IMAGE,
                degrees(self.heading) - 90,
                0.25,
            )
            imgrect = img.get_rect(center=(self.x, self.y))
            surface.blit(img, imgrect)

    def alive(self):
        return -50 <= self.x <= PLAY_WIDTH + 50 and -50 <= self.y <= HEIGHT + 50


class Enemy:
    def __init__(self):
        self.randomize()

    def randomize(self):
        self.x = random.choice(range(20, PLAY_WIDTH, 20))
        self.y = 0

        self.health = random.randint(3, 5)
        self.currenthealth = self.health

        self.speed = random.randint(1, 5)

        self.rect = pygame.Rect(self.x - 20, self.y - 20, 40, 40)

    def update(self, dt):
        self.y += self.speed * dt * 60
        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        hp = (self.currenthealth / self.health) * 100

        if hp >= 90:
            color = "green"
        elif hp >= 50:
            color = "orange"
        elif hp >= 30:
            color = "yellow"
        else:
            color = "red"

        pygame.draw.rect(surface, color, self.rect)


class Game:
    def __init__(self):
        self.bullets = []
        self.enemies = [Enemy() for _ in range(5)]

        self.lives = MAX_LIVES
        self.angle = 90

        self.score = 0
        self.highscore = highscore

        self.hyperclear_remaining = MAX_HYPERCLEAR
        self.points = 0

        self.fire_timer = 0
        self.fire_interval = 0.033

        self.tip = (0, 0)

    def spawn_bullet(self):
        spread = random.randint(-10, 10)
        self.bullets.append(Bullet(self.tip, 20, self.angle + spread))

    def hyperclear(self):
        for i in range(20, PLAY_WIDTH, 20):
            for j in range(5):
                self.bullets.append(Bullet((i, HEIGHT - (15 * j)), 40, 90, True))

    def update_bullets(self, dt):
        for bullet in self.bullets[:]:
            bullet.update(dt)

            if bullet.color and bullet.y < 200:
                self.bullets.remove(bullet)
                continue

            if not bullet.alive():
                self.bullets.remove(bullet)

    def update_enemies(self, dt):
        for enemy in self.enemies:
            enemy.update(dt)

            for bullet in self.bullets[:]:
                if enemy.rect.collidepoint((bullet.x, bullet.y)):
                    enemy.currenthealth -= 1

                    if bullet in self.bullets:
                        self.bullets.remove(bullet)

            if enemy.currenthealth <= 0:
                enemy.randomize()

                self.score += 1
                self.points += 1

                self.highscore = max(self.highscore, self.score)

                if self.points >= 50:
                    self.points = 0

                    if self.hyperclear_remaining < MAX_HYPERCLEAR:
                        self.hyperclear_remaining += 1

            if enemy.y >= HEIGHT:
                self.lives -= 1
                enemy.randomize()

    def update(self, dt):
        keys = pygame.key.get_pressed()

        if (keys[pygame.K_a] or keys[pygame.K_LEFT]) and self.angle < 175:
            self.angle += 180 * dt

        if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) and self.angle > 5:
            self.angle -= 180 * dt

        self.fire_timer += dt

        while self.fire_timer >= self.fire_interval:
            self.spawn_bullet()
            self.fire_timer -= self.fire_interval

        self.update_bullets(dt)
        self.update_enemies(dt)

    def draw_cannon(self):
        angle = self.angle

        if angle > 0:
            x = PLAYER_X + 125 * cos(radians(angle))
            y = PLAYER_Y - 125 * sin(radians(angle))
        else:
            angle += 180
            x = PLAYER_X + 125 * cos(radians(angle))
            y = PLAYER_Y - 125 * sin(radians(angle))

        pygame.draw.line(
            screen,
            WHITE,
            (PLAYER_X, PLAYER_Y),
            (x, y),
            10,
        )

        pygame.draw.rect(screen, WHITE, (x - 5, y - 5, 10, 10))

        self.tip = (x, y)

    def draw_ui(self):
        pygame.draw.rect(screen, "#000030", (810, 0, WIDTH - 810, HEIGHT))
        pygame.draw.line(screen, "white", (810, 0), (810, HEIGHT), 10)

        font_small = pygame.font.SysFont("Monospace", 22)
        font_big = pygame.font.SysFont("Monospace", 32)

        label = font_small.render("Health", True, "black", "white")
        screen.blit(label, label.get_rect(topleft=(860, 750)))

        label = font_small.render("Hyperclear(<S>)", True, "black", "white")
        screen.blit(label, label.get_rect(topleft=(980, 750)))

        label = font_big.render(f"Score: {self.score}", True, "white")
        screen.blit(label, label.get_rect(topleft=(860, 50)))

        label = font_big.render(f"Highscore: {self.highscore}", True, "white")
        screen.blit(label, label.get_rect(topleft=(860, 100)))

        pygame.draw.rect(
            screen,
            "red",
            (
                870,
                int(700 - ((self.lives / MAX_LIVES) * 500)),
                60,
                int((self.lives / MAX_LIVES) * 500),
            ),
        )

        pygame.draw.rect(
            screen,
            "blue",
            (
                1050,
                int(700 - ((self.hyperclear_remaining / MAX_HYPERCLEAR) * 500)),
                60,
                int((self.hyperclear_remaining / MAX_HYPERCLEAR) * 500),
            ),
        )

    def draw(self):
        screen.fill(BACKGROUND)

        self.draw_cannon()

        for bullet in self.bullets:
            bullet.draw(screen)

        for enemy in self.enemies:
            enemy.draw(screen)

        pygame.draw.circle(screen, WHITE, (PLAYER_X, PLAYER_Y), 75)

        self.draw_ui()

        pygame.display.update()

    def run(self):
        while self.lives > 0:
            dt = clock.tick(FPS) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if (
                        event.key in (pygame.K_s, pygame.K_DOWN)
                        and self.hyperclear_remaining > 0
                    ):
                        self.hyperclear_remaining -= 1
                        self.hyperclear()

            self.update(dt)
            self.draw()

        if self.score > self.highscore:
            with open("Highscore.txt", "w") as f:
                f.write(str(self.score))


if __name__ == "__main__":
    Game().run()
