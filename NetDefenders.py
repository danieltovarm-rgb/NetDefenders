import pygame, sys, random
import numpy as np
from abc import ABC, abstractmethod
from moviepy import VideoFileClip

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


# --------- Clase para el video de inicio ----------
class IntroVideoScreen(Screen):
    def __init__(self, game, video_path):
        super().__init__(game)
        self.video = VideoFileClip(video_path)
        self.frame_gen = self.video.iter_frames(fps=25, dtype='uint8')
        self.finished = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            self.finished = True
            self.video.close()
            self.game.change_screen(MenuScreen(self.game))

    def update(self, dt):
        try:
            frame = next(self.frame_gen)
            frame_surface = pygame.surfarray.make_surface(np.transpose(frame, (1, 0, 2)))
            frame_surface = pygame.transform.scale(frame_surface, (SCREEN_W, SCREEN_H))
            self.current_frame = frame_surface
        except StopIteration:
            self.finished = True
            self.video.close()
            self.game.change_screen(MenuScreen(self.game))

    def render(self, surf):
        if hasattr(self, "current_frame"):
            surf.blit(self.current_frame, (0, 0))


# --------- (NUEVA) Clase Correo ----------
class Correo:
    def __init__(self, es_legitimo, tipo_malicioso, contenido, remitente, asunto, razones_correctas):
        self.es_legitimo = es_legitimo
        self.tipo_malicioso = tipo_malicioso
        self.contenido = contenido
        self.remitente = remitente
        self.asunto = asunto
        self.razones_correctas = razones_correctas
        self.procesado = False
        self.visible = True


# --------- Clase Protagonista (Visual) ----------
class ProtagonistaSprite:
    def __init__(self, x, y):
        self.image = pygame.image.load("assets/protagonista/idle.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (200, 200))
        self.rect = self.image.get_rect(center=(x, y))

    def draw(self, surf):
        surf.blit(self.image, self.rect)


# --------- Clase Protagonista (lógica) ----------
class Protagonista:
    def __init__(self, vida=100):
        self.vida = vida

    def recibir_daño(self, daño):
        self.vida = max(0, self.vida - daño)


# --------- Clase Hacker (Visual) ----------
class HackerSprite:
    def __init__(self, x, y, image_paths, scale=(200, 200)):
        self.frames = []
        for path in image_paths:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, scale)
            self.frames.append(img)

        self.rect = self.frames[0].get_rect(center=(x, y))
        self.frame_index = 0
        self.animation_timer = 0
        self.frame_duration = 450

    def update(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= self.frame_duration:
            self.animation_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)

    def draw(self, surf):
        surf.blit(self.frames[self.frame_index], self.rect)


# --------- Clase Hacker (lógica) ----------
class HackerLogic:
    def __init__(self, vida, tipo_ataque: dict, probabilidad: dict):
        self.vida = vida
        self.tipo_ataque = tipo_ataque
        self.probabilidad = probabilidad
        self.ataque_actual = None
        self.turno = 0

    def preparar_ataque(self):
        opciones = list(self.probabilidad.keys())
        pesos = [self.probabilidad[k] for k in opciones]
        elegido = random.choices(opciones, weights=pesos, k=1)[0]
        daño = self.tipo_ataque.get(elegido, 0)
        self.ataque_actual = {"nombre": elegido, "daño": daño}
        return self.ataque_actual

    def lanzar_ataque(self, objetivo: Protagonista):
        if not self.ataque_actual:
            return self.turno

        daño = self.ataque_actual["daño"]
        objetivo.recibir_daño(daño)
        self.turno += 1
        atac = self.ataque_actual
        self.ataque_actual = None
        return self.turno, atac


# --------- (NUEVA) BaseLevelScreen con elementos esenciales ----------
class BaseLevelScreen(Screen):
    def __init__(self, game, narrative_lines):
        super().__init__(game)

        # Sistema de vidas y personajes (esencial)
        self.protagonista = Protagonista(vida=100)
        self.hacker_logic = HackerLogic(vida=100, tipo_ataque={}, probabilidad={})

        # Sistema de narrativa (esencial)
        self.narrative_lines = narrative_lines
        self.narrative_index = 0
        self.show_narrative = True

        # Fuentes básicas (esencial)
        self.font = pygame.font.SysFont("Consolas", 28)
        self.option_font = pygame.font.SysFont("Consolas", 20)
        self.small_font = pygame.font.SysFont("Consolas", 16)

    def _wrap_text(self, text, font, max_width):
        words = text.replace('\n', ' \n ').split(' ')  
        lines = []
        current_line = ""

        for word in words:
            if word == '\n':  # respeta salto de línea manual
                lines.append(current_line)
                current_line = ""
                continue

            test_line = current_line + (" " if current_line else "") + word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def avanzar_narrativa(self):
        """Avanza la narrativa y retorna False si terminó"""
        self.narrative_index += 1
        if self.narrative_index >= len(self.narrative_lines):
            self.show_narrative = False
            return False
        return True

    # Métodos abstractos que deben ser implementados por las subclases
    @abstractmethod
    def handle_event(self, event):
        ...

    @abstractmethod
    def update(self, dt):
        ...

    @abstractmethod
    def render(self, surf):
        ...


# --------- Pantalla Menú ----------
class MenuScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.SysFont("Consolas", 40)
        self.options = ["Jugar", "Salir"]
        self.buttons = []
        self.create_buttons()

    def create_buttons(self):
        for i, opt in enumerate(self.options):
            txt = self.font.render(opt, True, (255, 255, 255))
            rect = txt.get_rect(center=(SCREEN_W // 2, 250 + i * 80))
            self.buttons.append((opt, txt, rect))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for opt, txt, rect in self.buttons:
                if rect.collidepoint(mx, my):
                    if opt == "Jugar":
                        self.game.change_screen(LevelSelectScreen(self.game))
                    elif opt == "Salir":
                        pygame.quit();
                        sys.exit()

    def update(self, dt):
        pass

    def render(self, surf):
        surf.fill((30, 30, 50))
        title = self.font.render("Juego de Ciberseguridad", True, (255, 255, 255))
        surf.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 100))

        mx, my = pygame.mouse.get_pos()
        for opt, txt, rect in self.buttons:
            color = (255, 255, 100) if rect.collidepoint(mx, my) else (200, 200, 200)
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
        rect = pygame.Rect(SCREEN_W // 2 - 100, SCREEN_H // 2 - 50, 200, 100)
        self.levels.append(("Nivel 1", rect))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for name, rect in self.levels:
                if rect.collidepoint(mx, my):
                    if name == "Nivel 1":
                        self.game.change_screen(Level1Screen(self.game))

    def update(self, dt):
        pass

    def render(self, surf):
        surf.fill((20, 50, 70))
        header = self.font.render("Selecciona un nivel (haz click)", True, (255, 255, 255))
        surf.blit(header, (SCREEN_W // 2 - header.get_width() // 2, 100))

        mx, my = pygame.mouse.get_pos()
        for name, rect in self.levels:
            color = (200, 200, 100) if rect.collidepoint(mx, my) else (100, 100, 100)
            pygame.draw.rect(surf, color, rect)
            txt = self.font.render(name, True, (0, 0, 0))
            surf.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))


# --------- (NUEVA) Pantalla del Nivel 1 con Sistema de Correos ----------
class Level1Screen(BaseLevelScreen):
    def __init__(self, game):
        # Narrativa inicial del tutor
        narrative_lines = [
            "Tutor: ¡Ten cuidado con los correos sospechosos!",
            "Algunos correos buscan engañarte para obtener tu dinero o contraseñas.",
            "Debes identificar cuáles son legítimos y cuáles son maliciosos.",
            "Usa las opciones Responder, Eliminar o Reportar según corresponda."
        ]
        super().__init__(game, narrative_lines)
    
        # Sprites de personajes en nuevas posiciones
        self.protagonista_sprite = ProtagonistaSprite(100, SCREEN_H - 100)
        self.hacker_sprite = HackerSprite(
            SCREEN_W - 100, 100,
            ["assets/hacker/idle/idle1.png", "assets/hacker/idle/idle2.png", "assets/hacker/idle/idle3.png",
             "assets/hacker/idle/idle4.png", "assets/hacker/idle/idle5.png", "assets/hacker/idle/idle6.png"],
            scale=(200, 200)
        )

        # Tutor
        self.tutor_sprite = ProtagonistaSprite(SCREEN_W - 150, SCREEN_H - 100)
        self.tutor_visible = False
        self.tutor_mensaje = ""
        self.tutor_timer = 0
        self.contador_tutor = 0
        self.max_apariciones_tutor = 3

        # Sistema de correos
        self.correos = self.cargar_correos()
        self.correo_actual_index = 0
        self.correo_abierto = None
        self.estado = "narrativa_inicial"
        self.razones_seleccionadas = []
        self.accion_pendiente = None

        # Texto animado
        self.texto_actual = ""
        self.texto_completo = ""
        self.tiempo_escritura = 0
        self.velocidad_escritura = 30

        # Botones de interfaz
        self.botones_accion = [
            {"rect": pygame.Rect(SCREEN_W // 2 - 300, SCREEN_H - 150, 180, 40), "accion": "responder",
             "texto": "Responder"},
            {"rect": pygame.Rect(SCREEN_W // 2 - 100, SCREEN_H - 150, 180, 40), "accion": "eliminar",
             "texto": "Eliminar"},
            {"rect": pygame.Rect(SCREEN_W // 2 + 100, SCREEN_H - 150, 180, 40), "accion": "reportar",
             "texto": "Reportar"}
        ]

        self.botones_razones = [
            {"rect": pygame.Rect(SCREEN_W // 2 - 200, SCREEN_H - 100, 120, 30), "razon": "Logo", "texto": "Logo"},
            {"rect": pygame.Rect(SCREEN_W // 2 - 60, SCREEN_H - 100, 120, 30), "razon": "Dominio", "texto": "Dominio"},
            {"rect": pygame.Rect(SCREEN_W // 2 + 80, SCREEN_H - 100, 120, 30), "razon": "Texto", "texto": "Texto"}
        ]
        self.boton_confirmar = pygame.Rect(SCREEN_W // 2 - 60, SCREEN_H - 60, 120, 40)

        self.last_feedback = ""

    def cargar_correos(self):
        return [
            # CORREOS MALICIOSOS
            Correo(
                es_legitimo=False,
                tipo_malicioso="dinero",
                remitente="premios@loteria-falsa.com",
                asunto="¡GANASTE $1,000,000! Reclama tu premio",
                contenido="Felicidades, has sido seleccionado para recibir $1,000,000. Haz clic aquí y paga $50 de procesamiento para reclamar tu premio inmediatamente. ¡Oferta por tiempo limitado!",
                razones_correctas=["Dominio", "Texto"]
            ),
            Correo(
                es_legitimo=False,
                tipo_malicioso="contraseñas",
                remitente="soporte@faceb00k-security.com",
                asunto="Problema de seguridad en tu cuenta",
                contenido="Hemos detectado acceso no autorizado a tu cuenta. Para protegerla, verifica tu identidad ingresando tu contraseña actual aquí. De lo contrario, tu cuenta será suspendida en 24 horas.",
                razones_correctas=["Dominio", "Logo", "Texto"]
            ),
            Correo(
                es_legitimo=False,
                tipo_malicioso="suscripciones",
                remitente="servicio@premium-gratis.com",
                asunto="Servicio Premium por tiempo limitado",
                contenido="Obtén 3 meses gratis de nuestro servicio premium. Solo ingresa tus datos de tarjeta para verificación. ¡No te cobraremos nada hasta después del periodo de prueba!",
                razones_correctas=["Dominio", "Texto"]
            ),

            # CORREOS LEGÍTIMOS
            Correo(
                es_legitimo=True,
                tipo_malicioso=None,
                remitente="soporte@bancoreal.com",
                asunto="Actualización de términos de servicio",
                contenido="Estimado cliente, hemos actualizado nuestros términos de servicio. No se requiere acción de tu parte. Puedes revisar los cambios en nuestra página web oficial.",
                razones_correctas=[]
            ),
            Correo(
                es_legitimo=True,
                tipo_malicioso=None,
                remitente="notificaciones@red-social.com",
                asunto="Nueva solicitud de amistad",
                contenido="Tienes una nueva solicitud de amistad de un contacto conocido. Inicia sesión en la plataforma para aceptar o rechazar la solicitud.",
                razones_correctas=[]
            )
        ]

    def procesar_accion_correo(self, accion, correo):
        if correo.es_legitimo:
            return self._procesar_correo_legitimo(accion, correo)
        else:
            return self._procesar_correo_malicioso(accion, correo)

    def _procesar_correo_legitimo(self, accion, correo):
        if accion == "responder":
            return {"daño_jugador": 0, "daño_hacker": 0, "correcto": True}
        elif accion == "eliminar":
            return {"daño_jugador": 10, "daño_hacker": 0, "correcto": False}
        elif accion == "reportar":
            return {"daño_jugador": 20, "daño_hacker": 0, "correcto": False}

    def _procesar_correo_malicioso(self, accion, correo):
        if accion == "reportar":
            return {"daño_jugador": 0, "daño_hacker": 25, "correcto": True}
        elif accion == "eliminar":
            return {"daño_jugador": 0, "daño_hacker": 10, "correcto": True}
        elif accion == "responder":
            daño_extra = self._calcular_daño_por_tipo(correo.tipo_malicioso)
            return {"daño_jugador": 15 + daño_extra, "daño_hacker": 0, "correcto": False}

    def _calcular_daño_por_tipo(self, tipo_malicioso):
        daños = {
            "dinero": 2,
            "contraseñas": 3,
            "suscripciones": 1
        }
        return daños.get(tipo_malicioso, 0)

    def procesar_razones(self, correo, razones_seleccionadas, accion_original):
        """CORREGIDO: Ahora siempre retorna una tupla (daño_razones, bonus_hacker)"""
        if correo.es_legitimo:
            # Para correos legítimos, cualquier razón seleccionada es incorrecta
            if razones_seleccionadas:
                daño_razones = len(razones_seleccionadas) * 3
                return daño_razones, 0  # ← CORREGIDO: siempre retorna tupla
            return 0, 0  # ← CORREGIDO: siempre retorna tupla
        else:
            # Para correos maliciosos, verificar coincidencia con razones correctas
            razones_correctas = set(correo.razones_correctas)
            razones_seleccionadas_set = set(razones_seleccionadas)

            # Calcular razones incorrectas y faltantes
            razones_incorrectas = razones_seleccionadas_set - razones_correctas
            daño_razones_incorrectas = len(razones_incorrectas) * 2

            razones_faltantes = razones_correctas - razones_seleccionadas_set
            daño_razones_faltantes = len(razones_faltantes) * 1

            # Bonus al hacker por razones correctas seleccionadas
            razones_correctas_seleccionadas = razones_correctas.intersection(razones_seleccionadas_set)
            bonus_hacker = len(razones_correctas_seleccionadas) * 2

            return daño_razones_incorrectas + daño_razones_faltantes, bonus_hacker

    def procesar_respuesta_completa(self, accion, razones_seleccionadas=None):
        correo = self.correo_abierto
        resultado = self.procesar_accion_correo(accion, correo)

        # Aplicar daño base de la acción
        if resultado["daño_jugador"] > 0:
            self.protagonista.recibir_daño(resultado["daño_jugador"])

        if resultado["daño_hacker"] > 0:
            self.hacker_logic.vida = max(0, self.hacker_logic.vida - resultado["daño_hacker"])

        # Procesar razones si es eliminar o reportar
        daño_razones = 0
        bonus_hacker = 0
        if razones_seleccionadas is not None:
            daño_razones, bonus_hacker = self.procesar_razones(correo, razones_seleccionadas, accion)

            # Aplicar daño por razones incorrectas
            if daño_razones > 0:
                self.protagonista.recibir_daño(daño_razones)

            # Aplicar bonus al hacker por razones correctas
            if bonus_hacker > 0:
                self.hacker_logic.vida = max(0, self.hacker_logic.vida - bonus_hacker)

        self.mostrar_feedback_completo(resultado, daño_razones, bonus_hacker, razones_seleccionadas)

        if not resultado["correcto"] or daño_razones > 0:
            self.mostrar_tutor_si_corresponde(correo, accion, razones_seleccionadas)

        correo.procesado = True
        correo.visible = False
        self.siguiente_correo()

    def mostrar_feedback_completo(self, resultado, daño_razones, bonus_hacker, razones_seleccionadas):
        mensajes = []

        if resultado["correcto"]:
            if resultado["daño_hacker"] > 0:
                mensajes.append(f"¡Bien! Dañaste al hacker en {resultado['daño_hacker']} puntos")
        else:
            if resultado["daño_jugador"] > 0:
                mensajes.append(f"Error: Perdiste {resultado['daño_jugador']} puntos de vida")

        if daño_razones > 0:
            mensajes.append(f"Razones incorrectas: -{daño_razones} vida")

        if bonus_hacker > 0:
            mensajes.append(f"Razones correctas: -{bonus_hacker} al hacker")

        self.last_feedback = " | ".join(mensajes)

    def mostrar_tutor_si_corresponde(self, correo, accion, razones_seleccionadas):
        if self.contador_tutor < self.max_apariciones_tutor:
            self.contador_tutor += 1
            self.tutor_visible = True
            self.tutor_mensaje = self.obtener_mensaje_tutor(correo, accion, razones_seleccionadas)
            self.tutor_timer = 0

    def obtener_mensaje_tutor(self, correo, accion, razones_seleccionadas):
        if correo.es_legitimo and accion != "responder":
            return "Recuerda: los correos legítimos deben responderse, no eliminarse ni reportarse"

        elif not correo.es_legitimo and accion == "responder":
            if correo.tipo_malicioso == "dinero":
                return "¡Cuidado! Las ofertas de dinero fácil suelen ser estafas"
            elif correo.tipo_malicioso == "contraseñas":
                return "Nunca compartas contraseñas por correo. Las empresas legítimas no las piden"
            else:
                return "Revisa siempre los términos antes de aceptar suscripciones"

        elif razones_seleccionadas and not correo.es_legitimo:
            razones_incorrectas = set(razones_seleccionadas) - set(correo.razones_correctas)
            if razones_incorrectas:
                return f"Revisa mejor las razones: {', '.join(razones_incorrectas)} no aplican aquí"

        return "Sigue practicando tu criterio de seguridad"

    def siguiente_correo(self):
        self.correo_abierto = None
        self.estado = "esperando_correo"
        self.razones_seleccionadas = []

        # Verificar si quedan correos por procesar
        correos_pendientes = [c for c in self.correos if not c.procesado]
        if not correos_pendientes or self.protagonista.vida <= 0 or self.hacker_logic.vida <= 0:
            self.estado = "fin_juego"

    def iniciar_texto_animado(self, texto):
        self.texto_completo = texto
        self.texto_actual = ""
        self.tiempo_escritura = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            if self.estado == "narrativa_inicial":
                if not self.avanzar_narrativa():
                    self.estado = "esperando_correo"
                return

            if self.tutor_visible:
                self.tutor_visible = False
                return

            if self.estado == "fin_juego":
                self.game.change_screen(MenuScreen(self.game))
                return

            if self.estado == "esperando_correo":
                # Hacer clic en bandeja de entrada para abrir correo
                bandeja_rect = pygame.Rect(200, 150, 400, 300)
                if bandeja_rect.collidepoint(mx, my):
                    correos_disponibles = [c for c in self.correos if c.visible and not c.procesado]
                    if correos_disponibles:
                        self.correo_abierto = correos_disponibles[0]
                        self.estado = "correo_abierto"
                        texto_correo = f"De: {self.correo_abierto.remitente}\nAsunto: {self.correo_abierto.asunto}\n\n{self.correo_abierto.contenido}"
                        self.iniciar_texto_animado(texto_correo)

            elif self.estado == "correo_abierto":
                for boton in self.botones_accion:
                    if boton["rect"].collidepoint(mx, my):
                        if boton["accion"] in ["eliminar", "reportar"]:
                            self.accion_pendiente = boton["accion"]
                            self.estado = "seleccion_razones"
                        else:
                            self.procesar_respuesta_completa(boton["accion"])
                        return

            elif self.estado == "seleccion_razones":
                for boton in self.botones_razones:
                    if boton["rect"].collidepoint(mx, my):
                        if boton["razon"] in self.razones_seleccionadas:
                            self.razones_seleccionadas.remove(boton["razon"])
                        else:
                            self.razones_seleccionadas.append(boton["razon"])

                if self.boton_confirmar.collidepoint(mx, my):
                    self.procesar_respuesta_completa(self.accion_pendiente, self.razones_seleccionadas)

    def update(self, dt):
        self.hacker_sprite.update(dt)

        # Actualizar texto animado
        if self.estado == "correo_abierto" and len(self.texto_actual) < len(self.texto_completo):
            self.tiempo_escritura += dt
            if self.tiempo_escritura >= self.velocidad_escritura:
                self.tiempo_escritura = 0
                self.texto_actual += self.texto_completo[len(self.texto_actual)]

        # Actualizar tutor
        if self.tutor_visible:
            self.tutor_timer += dt
            if self.tutor_timer >= 3000:
                self.tutor_visible = False

    def render(self, surf):
        surf.fill((0, 0, 0))

        # Dibujar personajes
        self.protagonista_sprite.draw(surf)
        self.hacker_sprite.draw(surf)

        # Dibujar tutor si está visible
        if self.tutor_visible:
            self.tutor_sprite.draw(surf)
            tutor_box = pygame.Rect(SCREEN_W - 600, SCREEN_H - 120, 380, 80)
            pygame.draw.rect(surf, (30, 30, 60), tutor_box, border_radius=10)
            pygame.draw.rect(surf, (100, 100, 200), tutor_box, 2, border_radius=10)
            tutor_text = self.small_font.render(self.tutor_mensaje, True, (255, 255, 255))
            surf.blit(tutor_text, (tutor_box.x + 10, tutor_box.y + 10))

        # HUD: vidas
        vida_txt = self.font.render(f"Vida Jugador: {self.protagonista.vida}", True, (200, 200, 200))
        surf.blit(vida_txt, (20, 20))
        hack_txt = self.font.render(f"Vida Hacker: {self.hacker_logic.vida}", True, (200, 200, 200))
        surf.blit(hack_txt, (SCREEN_W - 250, 20))

        # Bandeja de entrada
        bandeja_rect = pygame.Rect(200, 150, 400, 300)
        pygame.draw.rect(surf, (40, 40, 80), bandeja_rect, border_radius=10)
        pygame.draw.rect(surf, (100, 100, 200), bandeja_rect, 2, border_radius=10)

        bandeja_titulo = self.font.render("Bandeja de Entrada", True, (255, 255, 255))
        surf.blit(bandeja_titulo, (bandeja_rect.centerx - bandeja_titulo.get_width() // 2, bandeja_rect.y + 10))

        # Mostrar correos en la bandeja
        y_offset = 50
        for correo in self.correos:
            if correo.visible and not correo.procesado:
                color = (150, 255, 150) if correo.es_legitimo else (255, 150, 150)
                asunto_text = self.small_font.render(f"{correo.remitente}: {correo.asunto}", True, color)
                surf.blit(asunto_text, (bandeja_rect.x + 10, bandeja_rect.y + y_offset))
                y_offset += 25

        # Narrativa inicial
        if self.show_narrative:
            box = pygame.Rect(100, 150, 600, 300)
            pygame.draw.rect(surf, (20, 20, 40), box, border_radius=10)
            pygame.draw.rect(surf, (100, 100, 200), box, 2, border_radius=10)

            line = self.narrative_lines[self.narrative_index]
            wrapped_lines = self._wrap_text(line, self.font, box.width - 40)

            y_offset = 20
            for wrapped in wrapped_lines:
                text_surf = self.font.render(wrapped, True, (255, 255, 255))
                surf.blit(text_surf, (box.x + 20, box.y + y_offset))
                y_offset += text_surf.get_height() + 5

            continue_text = self.small_font.render("Haz clic para continuar", True, (200, 200, 200))
            surf.blit(continue_text, (box.centerx - continue_text.get_width() // 2, box.bottom - 30))

        # Correo abierto
        elif self.estado == "correo_abierto" and self.correo_abierto:
            correo_box = pygame.Rect(150, 100, 500, 350)
            pygame.draw.rect(surf, (30, 30, 50), correo_box, border_radius=10)
            pygame.draw.rect(surf, (150, 150, 200), correo_box, 2, border_radius=10)

            # Mostrar texto animado
            max_width = correo_box.width - 20
            wrapped_lines = self._wrap_text(self.texto_actual, self.small_font, max_width)
            
            y_pos = correo_box.y + 20
            for line in wrapped_lines:
                text_surf = self.small_font.render(line, True, (255, 255, 255))
                surf.blit(text_surf, (correo_box.x + 10, y_pos))
                y_pos += text_surf.get_height() + 5

            # Botones de acción
            mx, my = pygame.mouse.get_pos()
            for boton in self.botones_accion:
                color = (200, 200, 100) if boton["rect"].collidepoint(mx, my) else (100, 100, 100)
                pygame.draw.rect(surf, color, boton["rect"], border_radius=5)
                text = self.option_font.render(boton["texto"], True, (0, 0, 0))
                surf.blit(text, (boton["rect"].centerx - text.get_width() // 2,
                                 boton["rect"].centery - text.get_height() // 2))

        # Selección de razones
        elif self.estado == "seleccion_razones":
            razones_box = pygame.Rect(150, 400, 500, 150)
            pygame.draw.rect(surf, (30, 30, 50), razones_box, border_radius=10)
            pygame.draw.rect(surf, (150, 150, 200), razones_box, 2, border_radius=10)

            titulo = self.option_font.render("Selecciona las razones (puedes elegir varias):", True, (255, 255, 255))
            surf.blit(titulo, (razones_box.centerx - titulo.get_width() // 2, razones_box.y + 10))

            mx, my = pygame.mouse.get_pos()
            for boton in self.botones_razones:
                color = (200, 200, 100) if boton["rect"].collidepoint(mx, my) else (100, 100, 100)
                if boton["razon"] in self.razones_seleccionadas:
                    color = (100, 200, 100)
                pygame.draw.rect(surf, color, boton["rect"], border_radius=5)
                text = self.small_font.render(boton["texto"], True, (0, 0, 0))
                surf.blit(text, (boton["rect"].centerx - text.get_width() // 2,
                                 boton["rect"].centery - text.get_height() // 2))

            # Botón confirmar
            color_confirmar = (100, 200, 100) if self.boton_confirmar.collidepoint(mx, my) else (100, 100, 100)
            pygame.draw.rect(surf, color_confirmar, self.boton_confirmar, border_radius=5)
            confirm_text = self.option_font.render("Confirmar", True, (0, 0, 0))
            surf.blit(confirm_text, (self.boton_confirmar.centerx - confirm_text.get_width() // 2,
                                     self.boton_confirmar.centery - confirm_text.get_height() // 2))

        # Fin del juego
        elif self.estado == "fin_juego":
            fin_box = pygame.Rect(200, 200, 400, 200)
            pygame.draw.rect(surf, (20, 20, 40), fin_box, border_radius=10)
            pygame.draw.rect(surf, (100, 100, 200), fin_box, 2, border_radius=10)

            if self.protagonista.vida <= 0:
                mensaje = "¡Game Over! El hacker te ha derrotado."
            elif self.hacker_logic.vida <= 0:
                mensaje = "¡Felicidades! Has derrotado al hacker."
            else:
                # Todos los correos procesados - gana el que tenga más vida
                if self.protagonista.vida > self.hacker_logic.vida:
                    mensaje = "¡Felicidades! Has procesado todos los correos y ganado."
                elif self.hacker_logic.vida > self.protagonista.vida:
                    mensaje = "¡Game Over! El hacker tenía más vida al final."
                else:
                    mensaje = "¡Empate! Ambos tienen la misma vida."

            text = self.font.render(mensaje, True, (255, 255, 255))
            surf.blit(text, (fin_box.centerx - text.get_width() // 2, fin_box.centery - 30))

            continue_text = self.small_font.render("Haz clic para volver al menú", True, (200, 200, 200))
            surf.blit(continue_text, (fin_box.centerx - continue_text.get_width() // 2, fin_box.centery + 30))

        # Feedback
        if self.last_feedback:
            feedback_text = self.small_font.render(self.last_feedback, True, (255, 255, 100))
            surf.blit(feedback_text, (SCREEN_W // 2 - feedback_text.get_width() // 2, SCREEN_H - 40))


# --------- Clase principal del juego ----------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("NetDefenders")
        self.clock = pygame.time.Clock()
        self.current = IntroVideoScreen(self, "intro.mp4")
        self.running = True
        self.font = pygame.font.SysFont("Consolas", 18)

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

            # Mostrar FPS
            fps_text = self.font.render(f"FPS: {int(self.clock.get_fps())}", True, (255, 255, 0))
            self.screen.blit(fps_text, (10, 10))

            pygame.display.flip()

        pygame.quit()


# --------- Main ---------
if __name__ == "__main__":
    Game().run()