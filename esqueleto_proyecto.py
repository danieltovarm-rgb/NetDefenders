import pygame, sys
from abc import ABC, abstractmethod

# Configuración
SCREEN_W, SCREEN_H = 800, 600
FPS = 60

# --------- Clase base para pantallas ----------
class Screen(ABC):
    def __init__(self, game):
        self.game = game

    @abstractmethod
    def handle_event(self, event): ...
    @abstractmethod
    def update(self, dt): ...
    @abstractmethod
    def render(self, surf): ...

# --------- Pantalla Menú ----------
class MenuScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.SysFont("Consolas", 40)
        self.options = ["Jugar", "Salir"]
        self.buttons = []
        self.create_buttons()

    def create_buttons(self):
        # Crear rectángulos de botones
        for i, opt in enumerate(self.options):
            txt = self.font.render(opt, True, (255,255,255))
            rect = txt.get_rect(center=(SCREEN_W//2, 250 + i*80))
            self.buttons.append((opt, txt, rect))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for opt, txt, rect in self.buttons:
                if rect.collidepoint(mx, my):
                    if opt == "Jugar":
                        self.game.change_screen(LevelSelectScreen(self.game))
                    elif opt == "Salir":
                        pygame.quit(); sys.exit()

    def update(self, dt): pass

    def render(self, surf):
        surf.fill((30,30,50))
        title = self.font.render("Juego de Ciberseguridad", True, (255,255,255))
        surf.blit(title, (SCREEN_W//2 - title.get_width()//2, 100))

        mx, my = pygame.mouse.get_pos()
        for opt, txt, rect in self.buttons:
            color = (255,255,100) if rect.collidepoint(mx,my) else (200,200,200)
            txt = self.font.render(opt, True, color)
            surf.blit(txt, rect)

# --------- Pantalla Selección de Nivel ----------
class LevelSelectScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.SysFont("Consolas", 30)
        self.levels = []
        self.create_levels()

    def create_levels(self):
        # Por ahora solo Nivel 1
        rect = pygame.Rect(SCREEN_W//2 - 100, SCREEN_H//2 - 50, 200, 100)
        self.levels.append(("Nivel 1", rect))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for name, rect in self.levels:
                if rect.collidepoint(mx,my):
                    if name == "Nivel 1":
                        self.game.change_screen(Level1Screen(self.game))

    def update(self, dt): pass

    def render(self, surf):
        surf.fill((20,50,70))
        header = self.font.render("Selecciona un nivel (haz click)", True, (255,255,255))
        surf.blit(header, (SCREEN_W//2 - header.get_width()//2, 100))

        mx, my = pygame.mouse.get_pos()
        for name, rect in self.levels:
            color = (200,200,100) if rect.collidepoint(mx,my) else (100,100,100)
            pygame.draw.rect(surf, color, rect)
            txt = self.font.render(name, True, (0,0,0))
            surf.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

# --------- Pantalla del Nivel 1 ----------
class Level1Screen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.SysFont("Consolas", 28)
        self.message = "Haz click para volver."

        # Definimos dos cuadrados (rectángulos)
        self.square1 = pygame.Rect(200, 250, 100, 100)  # (x, y, ancho, alto)
        self.square2 = pygame.Rect(500, 250, 100, 100)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.game.change_screen(MenuScreen(self.game))

    def update(self, dt): pass

    def render(self, surf):
        surf.fill((0,0,0))

         # Dibujar cuadrados
        pygame.draw.rect(surf, (200,0,0), self.square1)   # Rojo
        pygame.draw.rect(surf, (0,0,200), self.square2)   # Azul

        # Dibujar mensaje
        txt = self.font.render(self.message, True, (0,200,200))
        surf.blit(txt, (SCREEN_W//2 - txt.get_width()//2, SCREEN_H - 100))

# --------- Clase principal del juego ----------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("NetDefenders")
        self.clock = pygame.time.Clock()
        self.current = MenuScreen(self)
        self.running = True

    def change_screen(self, new_screen):
        self.current = new_screen

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.current.handle_event(event)

            self.current.update(dt)
            self.current.render(self.screen)
            pygame.display.flip()

        pygame.quit()

# --------- Main ---------
if __name__ == "__main__":
    Game().run()
