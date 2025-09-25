import pygame, sys, random
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

# --------- Clase Protagonista (Visual) ----------
class ProtagonistaSprite:
    def __init__(self, x, y):
        # Cargar la imagen del protagonista
        self.image = pygame.image.load("assets/protagonista/idle.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (400, 400)) # Ajuste de la imagen a 400x400
        self.rect = self.image.get_rect(center=(x, y))

    def draw(self, surf):
        surf.blit(self.image, self.rect)

# --------- Clase Protagonista (protagonista lógica simple) ----------
class Protagonista:
    def __init__(self, vida=100):
        self.vida = vida                            # ← Vida del jugador

    def recibir_daño(self, daño):
        self.vida = max(0, self.vida - daño)        # ← Resta vida al recibir daño
        
# --------- Clase Hacker (Visual) ----------
class HackerSprite:
    def __init__(self, x, y, image_paths, scale=(400,400)):
        # image_paths es una lista de rutas ["idle1.png", "idle2.png", ...]
        self.frames = []
        for path in image_paths:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, scale)
            self.frames.append(img)
        
        self.rect = self.frames[0].get_rect(center=(x, y))

        # Animación
        self.frame_index = 0
        self.animation_timer = 0
        self.frame_duration = 450  # ms por frame

    def update(self, dt):
        """Avanza la animación idle en loop infinito"""
        self.animation_timer += dt
        if self.animation_timer >= self.frame_duration:
            self.animation_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)

    def draw(self, surf):
        surf.blit(self.frames[self.frame_index], self.rect)

# --------- Clase Hacker (lógica de juego) ----------
class HackerLogic:
    """
    Representa la lógica de un hacker (vida, ataques, probabilidades).
    - tipo_ataque: dict nombre->daño
    - probabilidad: dict nombre->peso (no necesita sumar 1; se usan pesos)
    """
    def __init__(self, vida, tipo_ataque: dict, probabilidad: dict):
        self.vida = vida
        self.tipo_ataque = tipo_ataque
        self.probabilidad = probabilidad
        self.ataque_actual = None
        self.turno = 0

    def preparar_ataque(self):
        # Elegir ataque con probabilidades
        opciones = list(self.probabilidad.keys())
        pesos = [self.probabilidad[k] for k in opciones]
        elegido = random.choices(opciones, weights=pesos, k=1)[0]
        daño = self.tipo_ataque.get(elegido, 0)
        self.ataque_actual = {"nombre": elegido, "daño": daño}
        return self.ataque_actual

    def lanzar_ataque(self, objetivo: Protagonista):
        """
        Aplica el daño al objetivo (Protagonista) y avanza el turno.
        Devuelve el nuevo valor de turno.
        """
        if not self.ataque_actual:
            return self.turno  # nada que lanzar

        daño = self.ataque_actual["daño"]
        # Aplicar daño
        objetivo.recibir_daño(daño)
        # Aumentar turno
        self.turno += 1
        # limpiar ataque actual (se podría mantener si se desea)
        atac = self.ataque_actual
        self.ataque_actual = None
        return self.turno, atac
    
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
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:        # Detecta clic izquierdo
            mx, my = event.pos                                                # Coordenadas del clic
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
        self.levels.append(("Nivel 1", rect))                 # ← Carga Nivel 1

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:    # ← Detecta clic izquierdo
            mx, my = event.pos                                            # ← Coordenadas del clic
            for name, rect in self.levels:
                if rect.collidepoint(mx,my):                              # ← ¿El clic fue dentro del botón?               
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

class BaseLevelScreen(Screen):
    def __init__(self, game, narrative_lines, attack_templates, hacker_config, hacker_image):
        super().__init__(game)
        self.font = pygame.font.SysFont("Consolas", 28)
        self.option_font = pygame.font.SysFont("Consolas", 20)

        # Lógica y sprites

        #Protagonista
        self.protagonista = Protagonista(vida=100)
        self.protagonista_sprite = ProtagonistaSprite(180, 290)

        #Hacker
        self.hacker_logic = HackerLogic(vida=100,
                                        tipo_ataque=hacker_config["tipo_ataque"],
                                        probabilidad=hacker_config["probabilidad"])
        #(Visual) → recibe imagen distinta según el nivel
        self.hacker_sprite = HackerSprite(
            620, 290,
            ["assets/hacker/idle/idle1.png","assets/hacker/idle/idle2.png","assets/hacker/idle/idle3.png",
             "assets/hacker/idle/idle4.png","assets/hacker/idle/idle5.png","assets/hacker/idle/idle6.png"]
        )

        # Botones
        self.option_rects = []
        btn_w, btn_h = 700, 42
        start_x, start_y = 50, 440
        for i in range(4):
            self.option_rects.append(pygame.Rect(start_x, start_y + i*(btn_h+12), btn_w, btn_h))

        # Estado del juego
        self.state = "waiting_narrative"
        self.current_attack_key = None
        self.last_result_text = ""
        self.turno_num = 0
        self.timer = 0

        # Narrativa
        self.narrative_lines = narrative_lines
        self.narrative_index = 0
        self.show_narrative = True

        # Plantillas de ataques
        self.attack_templates = attack_templates

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # --- Narrativa avance por click ---
            if self.show_narrative:
                self.narrative_index += 1
                if self.narrative_index >= len(self.narrative_lines):
                    self.show_narrative = False
                    self.state = "idle"
                    self.timer = 0
                return

            # --- Si estamos esperando la elección del jugador ---
            if self.state == "player_choice" and self.current_attack_key:
                # sólo comprobamos los rects de opciones visibles
                tpl = self.attack_templates[self.current_attack_key]
                for i, opt_rect in enumerate(self.option_rects[:len(tpl["options"])]):
                    if opt_rect.collidepoint(mx, my):        # ¿El clic fue dentro del botón?
                        # evaluar elección
                        chosen = i
                        correct = tpl["correct"]
                        # acierto
                        if chosen == correct:
                            dmg = tpl["damage_if_correct"]
                            # hacer daño al hacker
                            self.hacker_logic.vida = max(0, self.hacker_logic.vida - dmg)     # Acción correcta daña al hacker
                            self.last_result_text = f"Respuesta correcta: infligiste {dmg} al hacker."
                        else:
                            # fallo: se aplica daño al jugador y chance de efecto especial (narrativo)
                            dmg = tpl["damage_if_wrong"]
                            self.protagonista.recibir_daño(dmg)                        # Acción incorrecta daña al jugador
                            special = False
                            if random.random() < tpl.get("chance_special", 0):
                                special = True
                            if special and self.current_attack_key == "Phishing":
                                # narrativo: robo de credenciales
                                self.last_result_text = f"Fallo: te robaron credenciales. Vida -{dmg}."
                            elif special and self.current_attack_key == "FuerzaBruta":
                                self.last_result_text = f"Fallo: contraseña descifrada rápidamente. Vida -{dmg}."
                            elif special and self.current_attack_key == "IngenieriaSocial":
                                self.last_result_text = f"Fallo: compartiste dato sensible. Vida -{dmg}."
                            else:
                                self.last_result_text = f"Fallo: recibiste {dmg} de daño."
                        # finalizar elección → cooldown para el hacker preparar siguiente ataque
                        self.state = "cooldown"
                        self.current_attack_key = None
                        self.timer = 0
                        self.turno_num += 1
                        return

            # --- clic fuera de opciones: volver al menú (comportamiento anterior) ---
            # (Si el juego está en otros estados, seguimos permitiendo volver con click fuera)
            # detectamos si se hizo click fuera de las áreas importantes (simplificado)
            # Aquí asumimos que si haces click fuera de las opciones, vuelves al menú (como antes)
            # Si prefieres desactivar esto durante combate, quítalo o añade condiciones.
            # Para mantener comportamiento previo:
            # si se clickeó en la mitad izquierda (donde no hay botones), volvemos al menú:
            # (ajusta según prefieras)
            if mx < 120:
                self.game.change_screen(MenuScreen(self.game))


    def update(self, dt):
        # dt en ms
        self.timer += dt
        self.hacker_sprite.update(dt)
        # si estamos en narrativa no hacemos nada más
        if self.show_narrative:
            return

        # Estado idle: elegir próximo ataque (preparación inmediata)
        if self.state == "idle":
            attack = self.hacker_logic.preparar_ataque()  # devuelve dict con nombre y daño (si lo usas)
            # mapear nombre elegido a la plantilla: algunos nombres cambian de clave
            chosen_name = attack["nombre"]
            # si el nombre está con espacios o diferentes, normalizar:
            # en nuestras plantillas usamos claves 'Phishing','FuerzaBruta','IngenieriaSocial'
            # asumimos que preparado es una de esas (ajusta si tu HackerLogic devuelve otros nombres)
            # Para seguridad, hacemos una búsqueda tolerante:
            key = None
            for k in self.attack_templates.keys():
                if k.lower() in chosen_name.replace(" ", "").lower() or chosen_name.lower() in k.lower():
                    key = k
                    break
            if key is None:
                # fallback: si no coincide, forzamos Phishing
                key = "Phishing"
            self.current_attack_key = key
            self.state = "player_choice"
            self.timer = 0
            return

        # Estado cooldown: esperar un poco antes de siguiente ataque
        if self.state == "cooldown":
            # damos un pequeño tiempo para mostrar resultado (ej. 1.6s)
            if self.timer >= 1600:
                # si el hacker murió → terminar nivel
                if self.hacker_logic.vida <= 0:
                    self.state = "finished"
                    self.last_result_text = "¡Hacker derrotado! Nivel superado."
                    return
                # si el jugador murió → terminar (puedes cambiar por pantalla de game over)
                if self.protagonista.vida <= 0:
                    self.state = "finished"
                    self.last_result_text = "Has sido derrotado. Game Over."
                    return
                # volver a preparar próximo ataque
                self.state = "idle"
                self.timer = 0
                return
        
                
    def _wrap_text(self, text, font, max_width):
        """Devuelve una lista de líneas que caben en max_width."""
        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def render(self, surf):
        surf.fill((0,0,0))

        # Dibujar personajes
        self.protagonista_sprite.draw(surf)
        self.hacker_sprite.draw(surf)

        # HUD: vidas jugador
        vida_txt = self.font.render(f"Vida Jugador: {self.protagonista.vida}", True, (200,200,200))
        surf.blit(vida_txt, (20,20))

        # HUD: vida hacker lógica (por si la usas)
        hack_txt = self.font.render(f"Vida Hacker: {self.hacker_logic.vida}", True, (200,200,200))
        surf.blit(hack_txt, (SCREEN_W-250,20))

                # Si estamos en player_choice: mostrar mensaje del hacker y botones de opciones
        if self.state == "player_choice" and self.current_attack_key:
            tpl = self.attack_templates[self.current_attack_key]
            # mostrar el texto del reto (envuelto si es largo)
            wrap_w = SCREEN_W - 180
            wrapped = self._wrap_text(tpl["message"], self.font, wrap_w)
            txt_y = 80
            for line in wrapped:
                ts = self.font.render(line, True, (255,220,180))
                surf.blit(ts, (SCREEN_W//2 - wrap_w//2, txt_y))
                txt_y += ts.get_height() + 4

            # dibujar opciones como botones
            mx, my = pygame.mouse.get_pos()
            for i, opt in enumerate(tpl["options"]):
                r = self.option_rects[i]
                # color hover
                color_rect = (200,200,70) if r.collidepoint(mx,my) else (160,160,160)
                pygame.draw.rect(surf, color_rect, r, border_radius=6)
                txt = self.option_font.render(opt, True, (10,10,10))
                surf.blit(txt, (r.x + 12, r.y + (r.height - txt.get_height())//2))

        # Mostrar resultado reciente (last_result_text) en cooldown o finished
        if self.last_result_text and (self.state == "cooldown" or self.state == "finished"):
            res_txt = self.font.render(self.last_result_text, True, (220,180,180))
            surf.blit(res_txt, (SCREEN_W//2 - res_txt.get_width()//2, SCREEN_H - 110))

        # --- Renderizar narrativa (si corresponde) ---
        if self.show_narrative:
            box_h = 160
            box_surf = pygame.Surface((SCREEN_W - 60, box_h), pygame.SRCALPHA)
            box_surf.fill((10, 10, 10, 200))
            box_x = 30
            box_y = SCREEN_H - box_h - 10
            surf.blit(box_surf, (box_x, box_y))

            # texto actual y ajuste automático
            line = self.narrative_lines[self.narrative_index]
            wrapped_lines = self._wrap_text(line, self.font, box_surf.get_width() - 40)

            y_offset = 20
            for wrapped in wrapped_lines:
                text_surf = self.font.render(wrapped, True, (230,230,230))
                surf.blit(text_surf, (box_x + 20, box_y + y_offset))
                y_offset += text_surf.get_height() + 5

            # indicador de clic
            skip_txt = self.font.render("Haz clic para continuar", True, (180,180,180))
            surf.blit(skip_txt, (box_x + (box_surf.get_width() - skip_txt.get_width()) - 10,
                                 box_y + box_h - skip_txt.get_height() - 10))

# --------- Pantalla del Nivel 1 ----------
class Level1Screen(BaseLevelScreen):
    def __init__(self, game):
        narrative = [
            "Nivel 1: Intento de PHISHING",
            "Has recibido un correo sospechoso que solicita tu contraseña.",
            "Debes identificar si el correo es legítimo o un intento de suplantación.",
            "Responde correctamente durante el combate para contrarrestar al hacker."
        ]

        attack_templates = {
            "Phishing": {
                "message": "¡Alerta! Hemos detectado actividad sospechosa en tu cuenta. Para protegerla, haz clic en el siguiente enlace y verifica tu identidad. Si no lo haces en las próximas 2 horas, tu cuenta será suspendida permanentemente.",
                "options": [
                    "Revisar dirección del remitente y reportar/ignorar (seguro)",
                    "Hacer clic en el enlace y meter usuario/clave (pánico)",
                    "Responder pidiendo más información"
                ],
                "correct": 0,
                "damage_if_correct": 25,
                "damage_if_wrong": 18,
                "chance_special": 0.6,  # si falla, 60% de chance de 'robo de credenciales' efecto narrativo
            },
            "FuerzaBruta": {
                "message": "Para obtener el 'Ítem Legendario', solo tienes que crear una contraseña. Consejo: usa tu nombre y año o palabras simples como '123456'. ¿Qué haces?",
                "options": [
                    "Crear una contraseña fuerte (larga, mezcla, símbolo) (seguro)",
                    "Usar nombre+año o '123456' (débil)",
                    "Reutilizar una contraseña antigua"
                ],
                "correct": 0,
                "damage_if_correct": 20,
                "damage_if_wrong": 25,
                "chance_special": 0.25,  # probabilidad de que el hacker la descifre instantáneamente si es débil
            },
            "IngenieriaSocial": {
                "message": "(Chat) '¡Hola! Soy tu amigo. Necesito la respuesta a tu pregunta de seguridad para recuperar un objeto: ¿Cuál fue el nombre de tu primera mascota?'",
                "options": [
                    "No compartir la respuesta y reportar (seguro)",
                    "Dar la respuesta rápidamente (peligro)",
                    "Preguntar por qué la necesita y colgar"
                ],
                "correct": 0,
                "damage_if_correct": 22,
                "damage_if_wrong": 20,
                "chance_special": 0.5,
            }
        }

        hacker_config = {
            "tipo_ataque": {
                "Phishing": 12, 
                "FuerzaBruta": 8, 
                "IngenieriaSocial": 10
            },
            "probabilidad": {
                "Phishing": 50,
                "FuerzaBruta": 25,      
                "IngenieriaSocial": 25
            }
        }

        super().__init__(game, narrative, attack_templates, hacker_config, hacker_image="assets/hacker/idle.png")

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
        while self.running:                                # ← INICIO DEL BUCLE PRINCIPAL
            dt = self.clock.tick(FPS)  # dt en ms          #  Gesiton de FPS
            for event in pygame.event.get():               #  Gestioón de eventos 
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.current.handle_event(event)

            self.current.update(dt)                        # Actualización logica
            self.current.render(self.screen)               # Renderizado en pantalla
            pygame.display.flip()                          # Refrescar pantalla
                                                           # ← FIN DEL BUCLE PRINCIPAL
        pygame.quit()

# --------- Main ---------
if __name__ == "__main__":
    Game().run()
