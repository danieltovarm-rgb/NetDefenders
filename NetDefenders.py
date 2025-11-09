import math
import pygame, sys, random
import numpy as np
from abc import ABC, abstractmethod
from moviepy import VideoFileClip
# NUEVO: Importar sistema de estadísticas
from stats_system import PlayerStats, ScoreManager, MistakeLog

# ----- Limpieza opcional de archivos compilados (.pyc) y __pycache__ -----
# Para ahorrar espacio en entornos con capacidad limitada, eliminamos
# los ficheros .pyc y carpetas __pycache__ al iniciar. Esto no crea
# archivos adicionales en el proyecto.
import os, shutil

def _cleanup_pyc_caches(root_path=None):
    try:
        root = root_path or os.path.dirname(__file__)
    except Exception:
        return
    for dirpath, dirnames, filenames in os.walk(root):
        # Eliminar directorios __pycache__ completos
        if os.path.basename(dirpath) == "__pycache__":
            try:
                shutil.rmtree(dirpath)
            except Exception:
                pass
            # no seguir iterando dentro de este directorio
            continue

        # Eliminar archivos .pyc sueltos
        for fname in filenames:
            if fname.endswith('.pyc'):
                try:
                    os.remove(os.path.join(dirpath, fname))
                except Exception:
                    pass

# Ejecutar limpieza ligera solo si la variable de entorno NETDEFENDERS_CLEAN_PYC
# está activada (para evitar borrados indeseados en máquinas de desarrollo).
# Valores aceptados: '1', 'true', 'yes' (case-insensitive).
try:
    val = os.environ.get("NETDEFENDERS_CLEAN_PYC", "").lower()
    if val in ("1", "true", "yes"):
        try:
            _cleanup_pyc_caches()
        except Exception:
            pass
except Exception:
    # No queremos que errores en esta comprobación impidan el juego
    pass


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

# --------- Clase del jugador para Nivel 2 ----------
class PlayerAvatar:
    def __init__(self, x, y):
        self.position = pygame.math.Vector2(x, y)
        self.speed = 200  # Velocidad en píxeles por segundo
        self.size = (30, 30)  # Tamaño del avatar
        self.rect = pygame.Rect(x, y, self.size[0], self.size[1])
        
    def update(self, dt, keys, bounds_rect=None): # Añadimos bounds_rect
        # Vector de movimiento basado en input
        movement = pygame.math.Vector2(0, 0)
        
        # WASD para movimiento
        if keys[pygame.K_w]:
            movement.y = -1
        if keys[pygame.K_s]:
            movement.y = 1
        if keys[pygame.K_a]:
            movement.x = -1
        if keys[pygame.K_d]:
            movement.x = 1
            
        # Normalizar el vector si hay movimiento diagonal
        if movement.length() > 0:
            movement = movement.normalize()
            
        # Aplicar velocidad y deltatime
        movement *= self.speed * (dt / 1000.0)
        
        # Actualizar posición
        new_pos = self.position + movement
        
        # Colisiones con bordes
        if bounds_rect:
            # Confinar al rectángulo de límites
            new_pos.x = max(bounds_rect.left, min(new_pos.x, bounds_rect.right - self.size[0]))
            new_pos.y = max(bounds_rect.top, min(new_pos.y, bounds_rect.bottom - self.size[1]))
        else:
            # Fallback a bordes de pantalla si no se proveen límites
            new_pos.x = max(0, min(new_pos.x, SCREEN_W - self.size[0]))
            new_pos.y = max(0, min(new_pos.y, SCREEN_H - self.size[1]))
        
        # Actualizar posición y rectángulo
        self.position = new_pos
        self.rect.x = self.position.x
        self.rect.y = self.position.y
        
    def draw(self, surface):
        # Dibujar el avatar (por ahora un rectángulo simple)
        pygame.draw.rect(surface, (0, 255, 0), self.rect)

# --------- Nivel 2: Análisis y limpieza de PC ----------
class Level2Screen(Screen):
    def __init__(self, game):
        super().__init__(game)
        # Estados del nivel
        self.state = "narrativa_inicial"  # Estados: narrativa_inicial, jugando, fin_juego
        
        # Crear el avatar del jugador (centrado en pantalla)
        # --- BLOQUE REESTRUCTURADO Y MEJORADO ---
        
        # Estructura de directorios (Sin cambios)
        self.directory_structure = {
            "C:/": ["Users", "Program Files", "Windows", "Temp"],
            "C:/Users": ["Admin", "Public"],
            "C:/Users/Admin": ["Documents", "Downloads", "AppData"],
            "C:/Users/Admin/Downloads": [],
            "C:/Users/Admin/AppData": ["Local", "Roaming"],
            "C:/Users/Admin/AppData/Local": ["Temp"],
            "C:/Program Files": [],
            "C:/Windows": ["System32"],
            "C:/Windows/System32": [],
            "C:/Temp": []
        }
        
        # Directorio actual y anterior
        self.current_directory = "C:/"
        self.previous_directory = None
        
        # ... (Variables de control del juego, timers, etc. van aquí) ...
        self.game_time = 0
        # ... (El resto de tus variables de estado) ...
        self.door_interaction_distance = 50
        
        # HUD zones y configuración (Definir layout PRIMERO)
        margin = 10
        panel_top = 50
        log_height = 80
        
        # Calculamos anchos de paneles
        available_width = SCREEN_W - (margin * 4)
        left_width = int(available_width * 0.25)
        right_width = int(available_width * 0.25)
        center_width = available_width - left_width - right_width
        
        # Altura de los paneles principales
        panel_height = SCREEN_H - panel_top - log_height - (margin * 2)
        
        self.hud_rects = {
            "left_files": pygame.Rect(
                margin, 
                panel_top, 
                left_width, 
                panel_height
            ),
            "center_preview": pygame.Rect(  # Esta es el área de juego
                margin * 2 + left_width,
                panel_top,
                center_width,
                panel_height
            ),
            "right_tools": pygame.Rect(
                SCREEN_W - right_width - margin,
                panel_top,
                right_width,
                panel_height
            ),
            "bottom_log": pygame.Rect(
                margin,
                SCREEN_H - log_height,
                SCREEN_W - (margin * 2),
                log_height - margin
            ),
            "resource_bar": pygame.Rect(
                margin,
                30,
                SCREEN_W - (margin * 2),
                10
            )
        }
        
        # Colores del HUD (Paleta pulida)
        self.hud_colors = {
            "background": (20, 25, 35),      # Azul/morado muy oscuro
            "border": (40, 50, 70),          # Borde sutil
            "highlight": (0, 255, 255),      # Cian neón para el panel activo
            "text": (220, 220, 220),          # Texto más brillante
            "resource": (0, 255, 0),         # Verde neón para recursos
            "door": (0, 150, 200),           # Color de puerta
            "door_highlight": (255, 255, 0)  # Amarillo para highlight
        }

        # Crear el avatar del jugador (AHORA, centrado en el panel central)
        center_panel = self.hud_rects["center_preview"]
        self.avatar = PlayerAvatar(center_panel.centerx, center_panel.centery)
        
        # Definir puertas DENTRO del panel central (RE-CENTRADAS)
        door_width, door_height = 80, 50
        cp_x, cp_y = center_panel.centerx, center_panel.centery # Puntos centrales del panel
        dw, dh = door_width, door_height

        self.doors = {
            "C:/": {
                # Una cuadrícula 2x2 en el centro
                "Users": (pygame.Rect(cp_x - dw - 40, cp_y - dh - 10, dw, dh), "C:/Users"),
                "Program Files": (pygame.Rect(cp_x + 40, cp_y - dh - 10, dw, dh), "C:/Program Files"),
                "Windows": (pygame.Rect(cp_x - dw - 40, cp_y + 10, dw, dh), "C:/Windows"),
                "Temp": (pygame.Rect(cp_x + 40, cp_y + 10, dw, dh), "C:/Temp")
            },
            "C:/Users": {
                # Dos puertas en el centro
                "Admin": (pygame.Rect(cp_x - dw - 10, cp_y - (dh//2), dw, dh), "C:/Users/Admin"),
                "Public": (pygame.Rect(cp_x + 10, cp_y - (dh//2), dw, dh), "C:/Users/Public"),
                # Puerta de regreso centrada en la parte inferior
                "Back": (pygame.Rect(cp_x - (dw//2), center_panel.bottom - dh - 20, dw, dh), "C:/") 
            }
            # ... más puertas para otros directorios
        }
        
        # Estado del HUD
        self.active_panel = "center_preview" # Empezar con el panel de juego activo
        self.hud_elements = {
            "left_files": [ # Llenar con datos de ejemplo
                {"name": "system.dll", "size": "1.2 MB", "type": "File"},
                {"name": "user_data.ini", "size": "1 KB", "type": "File"},
                {"name": "x_virus.exe", "size": "420 KB", "type": "File"},
                {"name": "logs", "size": "--", "type": "Folder"},
            ],    
            "tools": [
                "Inspeccionar", 
                "Escanear",     
                "Cuarentena",   
                "Limpiar"       
            ]
        }
        
        # Fuentes para el HUD
        self.fonts = {
            "title": pygame.font.Font(None, 24),
            "normal": pygame.font.Font(None, 20),
            "small": pygame.font.Font(None, 16)
        }
        
        # --- (NUEVO) Calcular y guardar rectángulos de botones de herramientas ---
        self.tool_button_rects = []
        tool_rect = self.hud_rects["right_tools"].copy()
        tool_rect.y += 35  # Espacio para el título
        tool_rect.x += 10
        tool_rect.width -= 20 # Padding
        
        for tool in self.hud_elements["tools"]:
            button_rect = pygame.Rect(tool_rect.x, tool_rect.y, tool_rect.width, 30)
            self.tool_button_rects.append(button_rect)
            tool_rect.y += 40 # Espacio para el siguiente botón
        
        # --- (NUEVO) Inicialización de variables de estado faltantes ---
        
        # Estado del juego
        self.resources = 100  # Usado en render()
        self.max_mistakes = 5
        self.mistakes_made = 0
        self.total_viruses = 10 # Deberás ajustar esto
        self.viruses_cleaned = 0
        self.victory_condition = False
        self.game_over_reason = ""
        
        # Estado de transición (Usado en update() y render())
        self.in_transition = False
        self.transition_time = 0.0
        self.transition_duration = 0.5 # 500ms
        self.transition_target = None
        self.transition_start_pos = pygame.math.Vector2(0, 0)
        self.transition_end_pos = pygame.math.Vector2(0, 0)

        # Interacción con puertas (Usado en update() y render())
        self.near_door = None
        self.door_highlight_time = 0.0
        
        # Interacción con archivos (NUEVO)
        self.files_in_room = {} # Contenedor para los objetos de archivo
        self.file_interaction_distance = 40
        self.near_file = None
        self.file_highlight_time = 0.0
        
        
        # Mensajes en el log (Usado en show_message(), add_mistake(), etc.)
        self.current_message = "Log: Esperando acciones..."
        self.message_duration = 3.0 # 3 segundos
        self.effect_timers = {
            "message": 0.0
        }
        
        # --- Fin del bloque de inicialización ---
        # Inicialización de variables de estado
        self.current_directory = "C:/"
        self.game_time = 0
        # --- (NUEVO) Definición de archivos en las salas ---
        cp_x, cp_y = self.hud_rects["center_preview"].centerx, self.hud_rects["center_preview"].centery
        file_w, file_h = 30, 30

        self.files_in_room = {
            "C:/": [
                {"name": "readme.txt", "rect": pygame.Rect(cp_x - 100, cp_y + 100, file_w, file_h), "type": "clean"},
                {"name": "config.sys", "rect": pygame.Rect(cp_x + 70, cp_y + 100, file_w, file_h), "type": "system"}
            ],
            "C:/Users/Admin/Downloads": [
                {"name": "GIMP_Installer.exe", "rect": pygame.Rect(cp_x - 50, cp_y - 50, file_w, file_h), "type": "clean"},
                {"name": "Free_Game.exe", "rect": pygame.Rect(cp_x, cp_y, file_w, file_h), "type": "infected"},
                {"name": "invoice_2025.pdf", "rect": pygame.Rect(cp_x + 50, cp_y + 50, file_w, file_h), "type": "clean"}
            ],
            "C:/Windows/System32": [
                {"name": "kernel32.dll", "rect": pygame.Rect(cp_x - 100, cp_y, file_w, file_h), "type": "system"},
                {"name": "x_virus.exe", "rect": pygame.Rect(cp_x, cp_y - 50, file_w, file_h), "type": "infected"},
                {"name": "user32.dll", "rect": pygame.Rect(cp_x + 100, cp_y, file_w, file_h), "type": "system"}
            ]
        }
        
        self.paused = False
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.paused = not self.paused
            elif self.state == "narrativa_inicial" and event.key == pygame.K_RETURN:
                self.state = "jugando"
            elif self.state == "fin_juego" and event.key == pygame.K_r:
                self.__init__(self.game)  # Reiniciar nivel
            elif self.state == "jugando":
                
                # --- Regresar con la tecla Q ---
                if event.key == pygame.K_q:
                    # Solo podemos regresar si no estamos en C:/ y no estamos ya en transición
                    if self.previous_directory is not None and not self.in_transition:
                        
                        # Usamos 'None' para el door_rect porque no estamos usando una puerta física
                        self.start_transition(self.previous_directory, None) 
                        self.show_message(f"Regresando a {self.previous_directory}...")

        # --- (NUEVO) Manejar clics del mouse ---
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == "jugando":
                
                # Revisar si el clic fue en un botón de herramienta
                for i, button_rect in enumerate(self.tool_button_rects):
                    if button_rect.collidepoint(event.pos):
                        # Obtener el nombre de la herramienta
                        tool_name = self.hud_elements["tools"][i]
                        
                        # (Aquí es donde irá la lógica)
                        # Por ahora, solo muestra un mensaje en el log
                        self.show_message(f"Clic en {tool_name}")
                        
                        # Rompemos el bucle porque ya encontramos el botón
                        break
    
    def update(self, dt):
        if self.paused or self.state != "jugando":
            return
            
        self.game_time += dt
        
        # Manejar transición entre directorios
        if self.in_transition:
            self.transition_time += dt
            progress = min(1.0, self.transition_time / self.transition_duration)
            
            if progress >= 1.0:
                self.in_transition = False
                self.current_directory = self.transition_target
                # Posicionar el jugador en la nueva habitación (Corregido)
                center_panel = self.hud_rects["center_preview"]
                self.avatar.position.x = center_panel.centerx
                self.avatar.position.y = center_panel.centery # Posición de entrada (Centrada)
            else:
                # Animación de transición (Simple)
                self.avatar.position.y = self.transition_start_pos.y + (SCREEN_H * progress)
            return
        
        # Actualizar posición del jugador (Corregido)
        keys = pygame.key.get_pressed()
        # Pasamos el panel central como el límite de movimiento
        self.avatar.update(dt, keys, self.hud_rects["center_preview"])
        
        # Verificar proximidad a puertas y archivos
        self.near_door = None
        self.near_file = None
        
        if self.current_directory in self.doors:
            for door_name, (door_rect, target_dir) in self.doors[self.current_directory].items():
                # Calcular distancia al centro de la puerta
                door_center = pygame.math.Vector2(door_rect.centerx, door_rect.centery)
                player_center = pygame.math.Vector2(self.avatar.rect.centerx, self.avatar.rect.centery)
                distance = door_center.distance_to(player_center)
                
                if distance < self.door_interaction_distance:
                    self.near_door = (door_name, door_rect, target_dir)
                    self.door_highlight_time += dt
                    
                    # Presionar E para entrar
                    if keys[pygame.K_e]:
                        self.start_transition(target_dir, door_rect)
                        self.show_message(f"Entrando a {door_name}...")
                        break
                elif self.near_door and self.near_door[0] == door_name:
                    self.near_door = None
                    self.door_highlight_time = 0
        # Verificar proximidad a archivos (NUEVO)
        if self.current_directory in self.files_in_room:
            for file_data in self.files_in_room[self.current_directory]:
                file_rect = file_data["rect"]
                
                # Calcular distancia al centro del archivo
                file_center = pygame.math.Vector2(file_rect.centerx, file_rect.centery)
                player_center = pygame.math.Vector2(self.avatar.rect.centerx, self.avatar.rect.centery)
                distance = file_center.distance_to(player_center)
                
                if distance < self.file_interaction_distance:
                    self.near_file = file_data
                    self.file_highlight_time += dt
                    
                    # Presionar E para interactuar
                    if keys[pygame.K_e]:
                        self.interact_with_file(self.near_file)
                        break # Interactuar solo con un archivo a la vez
                
                elif self.near_file and self.near_file["name"] == file_data["name"]:
                    self.near_file = None
                    self.file_highlight_time = 0
    
    def start_transition(self, target_directory, door_rect):
        if not self.in_transition:
            self.in_transition = True
            self.transition_time = 0
            self.transition_target = target_directory
            self.previous_directory = self.current_directory
            
            # Guardar posición inicial para la animación
            self.transition_start_pos = pygame.math.Vector2(
                self.avatar.position.x,
                self.avatar.position.y
            )
            
            # Calcular posición final basada en la puerta de destino
            target_doors = self.doors.get(target_directory, {})
            back_door = None
            for name, (rect, dir_) in target_doors.items():
                if dir_ == self.current_directory or name == "Back":
                    back_door = rect
                    break
            
            # Si encontramos la puerta de regreso, posicionar cerca de ella
            if back_door:
                self.transition_end_pos = pygame.math.Vector2(
                    back_door.centerx,
                    back_door.bottom + 50
                )
            else:
                # Posición por defecto si no hay puerta de regreso
                self.transition_end_pos = pygame.math.Vector2(
                    SCREEN_W // 2,
                    SCREEN_H - 100
                )
                
    def interact_with_file(self, file_data):
        """Acción placeholder al interactuar con un archivo."""
        self.show_message(f"Interactuando con {file_data['name']}...")
        
        # Aquí es donde, en el futuro, activarías el panel de herramientas
        # para aplicar "Inspeccionar", "Escanear", etc.
        
        # Por ahora, solo cambiamos el panel activo al de herramientas
        self.active_panel = "right_tools"
        
    
    def get_door_position(self, from_dir, to_dir):
        # Devuelve la posición de la puerta para posicionar al jugador
        if from_dir in self.doors and to_dir in [door[1] for door in self.doors[from_dir].values()]:
            for door_rect, target in self.doors[from_dir].values():
                if target == to_dir:
                    return door_rect.centerx, door_rect.bottom
        return SCREEN_W // 2, SCREEN_H - 100  # Posición por defecto
        
    def check_game_state(self):
        """Verifica las condiciones de victoria y derrota"""
        # Victoria
        if self.viruses_cleaned >= self.total_viruses:
            self.victory_condition = True
            self.game_over_reason = "¡Has limpiado todos los virus!"
            self.state = "fin_juego"
            
        # Derrota por recursos
        elif self.resources <= 0:
            self.victory_condition = False
            self.game_over_reason = "¡Te has quedado sin recursos!"
            self.state = "fin_juego"
            
        # Derrota por errores
        elif self.mistakes_made >= self.max_mistakes:
            self.victory_condition = False
            self.game_over_reason = "¡Has cometido demasiados errores!"
            self.state = "fin_juego"
            
    def show_message(self, message, duration=None):
        """Muestra un mensaje temporal en pantalla"""
        self.current_message = message
        self.effect_timers["message"] = duration or self.message_duration
        
    def consume_resources(self, amount):
        """Consume recursos y verifica si quedan suficientes"""
        self.resources = max(0, self.resources - amount)
        if self.resources <= 0:
            self.check_game_state()
        return self.resources > 0
        
    def add_mistake(self):
        """Añade un error y verifica si se ha superado el límite"""
        self.mistakes_made += 1
        self.show_message(f"¡Error! ({self.mistakes_made}/{self.max_mistakes})")
        self.check_game_state()
        
    def virus_cleaned(self):
        """Registra un virus limpiado y verifica la victoria"""
        self.viruses_cleaned += 1
        self.show_message(f"¡Virus eliminado! ({self.viruses_cleaned}/{self.total_viruses})")
        self.check_game_state()
        
    def draw_panel_title(self, surf, rect, title):
        """Dibuja el título de un panel del HUD"""
        text = self.fonts["title"].render(title, True, self.hud_colors["text"])
        text_rect = text.get_rect(
            midtop=(rect.centerx, rect.top + 5)
        )
        surf.blit(text, text_rect)
        
    def switch_active_panel(self, direction):
        """Cambia el panel activo en la dirección especificada"""
        panels = ["left_files", "center_preview", "right_tools"]
        current_index = panels.index(self.active_panel)
        
        if direction == "right":
            new_index = (current_index + 1) % len(panels)
        else:  # left
            new_index = (current_index - 1) % len(panels)
            
        self.active_panel = panels[new_index]
        
    def render(self, surf):
        # Limpiar pantalla
        surf.fill((0, 0, 0))
        
        # Renderizar según el estado
        if self.state == "narrativa_inicial":
            # Mostrar narrativa inicial (texto del tutor)
            pass
        elif self.state == "jugando":
            # Dibujar HUD base (paneles)
            for name, rect in self.hud_rects.items():
                if name == "resource_bar": continue # Se dibuja por separado
                
                # Fondo del panel
                pygame.draw.rect(surf, self.hud_colors["background"], rect)
                
                # Borde (más brillante si es el panel activo)
                if name == self.active_panel:
                    border_color = self.hud_colors["highlight"]
                    border_width = 3 # Más grueso
                else:
                    border_color = self.hud_colors["border"]
                    border_width = 2 # Normal
                pygame.draw.rect(surf, border_color, rect, border_width, border_radius=5) # Bordes redondeados
            
            # Dibujar barra de recursos
            resource_rect = self.hud_rects["resource_bar"]
            pygame.draw.rect(surf, (10, 10, 10), resource_rect)  # Fondo oscuro
            
            # Calcular ancho de barra de recursos
            resource_width = (self.resources / 100) * (resource_rect.width - 4)
            current_resource_rect = pygame.Rect(resource_rect.x + 2, resource_rect.y + 2, resource_width, resource_rect.height - 4)
            pygame.draw.rect(surf, self.hud_colors["resource"], current_resource_rect) # Barra
            pygame.draw.rect(surf, self.hud_colors["border"], resource_rect, 1) # Borde sutil
            
            # Títulos de los paneles
            self.draw_panel_title(surf, self.hud_rects["left_files"], "Archivos")
            self.draw_panel_title(surf, self.hud_rects["center_preview"], "Sistema") # "Sistema" tiene más sentido que "Vista Previa"
            self.draw_panel_title(surf, self.hud_rects["right_tools"], "Herramientas")
            
            # Dibujar archivos en panel izquierdo (Placeholder)
            file_rect = self.hud_rects["left_files"].copy()
            file_rect.y += 35  # Espacio para el título
            file_rect.x += 10
            file_rect.width -= 20
            
            for file_info in self.hud_elements["left_files"]:
                # Placeholder para el ícono (un cuadrado)
                icon_rect = pygame.Rect(file_rect.x, file_rect.y + 2, 16, 16)
                pygame.draw.rect(surf, self.hud_colors["border"], icon_rect)
                
                # Nombre del archivo
                text = self.fonts["normal"].render(file_info["name"], True, self.hud_colors["text"])
                surf.blit(text, (file_rect.x + 22, file_rect.y))
                file_rect.y += 25
                if file_rect.y > self.hud_rects["left_files"].bottom - 20: # Evitar desbordamiento
                    break

            # Dibujar herramientas en panel derecho (Usando rects guardados)
            for i, tool_name in enumerate(self.hud_elements["tools"]):
                # Obtener el rectángulo que ya calculamos
                button_rect = self.tool_button_rects[i]
                
                # --- (NUEVO) Resaltar si el mouse está encima ---
                hover_color = self.hud_colors["highlight"] if button_rect.collidepoint(pygame.mouse.get_pos()) else self.hud_colors["border"]
                
                # Botón de herramienta (rectángulo de fondo)
                pygame.draw.rect(surf, hover_color, button_rect, border_radius=5)
                
                # Placeholder para el ícono (un cuadrado)
                icon_rect = pygame.Rect(button_rect.x + 5, button_rect.y + 7, 16, 16)
                pygame.draw.rect(surf, self.hud_colors["highlight"], icon_rect) # Usar color highlight para el ícono
                
                # Texto de la herramienta
                text = self.fonts["normal"].render(tool_name, True, self.hud_colors["text"])
                surf.blit(text, (button_rect.x + 28, button_rect.y + 7))
            
            # Log en la parte inferior
            log_rect = self.hud_rects["bottom_log"]
            # (El fondo y borde ya se dibujaron en el bucle principal)
            text = self.fonts["small"].render("Log: Esperando acciones...", True, self.hud_colors["text"])
            surf.blit(text, (log_rect.x + 10, log_rect.y + 10))
            
            # Dibujar puertas del directorio actual (Ahora relativo al panel central)
            if self.current_directory in self.doors:
                for door_name, (door_rect, _) in self.doors[self.current_directory].items():
                    # Color base de la puerta
                    color = self.hud_colors["door"]
                    
                    # Resaltar puerta cercana
                    if self.near_door and self.near_door[1] == door_rect:
                        color = self.hud_colors["door_highlight"]
                        
                        # Dibujar indicador de interacción (FUERA de la puerta)
                        indicator_text = self.fonts["normal"].render("Presiona E", True, color)
                        indicator_pos = (door_rect.centerx, door_rect.top - 20)
                        text_rect = indicator_text.get_rect(center=indicator_pos)
                        surf.blit(indicator_text, text_rect)
                        
                        # Dibujar borde brillante
                        pygame.draw.rect(surf, color, door_rect.inflate(4, 4), 2, border_radius=5)
                    
                    # Dibujar puerta (Rectángulo placeholder)
                    pygame.draw.rect(surf, color, door_rect, border_radius=5)
                    
                    # Dibujar nombre de la puerta
                    text = self.fonts["normal"].render(door_name, True, (0,0,0)) # Texto oscuro sobre fondo claro
                    text_rect = text.get_rect(center=door_rect.center)
                    surf.blit(text, text_rect)
            
            # Dibujar archivos del directorio actual (NUEVO)
            if self.current_directory in self.files_in_room:
                for file_data in self.files_in_room[self.current_directory]:
                    file_rect = file_data["rect"]
                    
                    # Color basado en el tipo de archivo (placeholder)
                    if file_data["type"] == "infected":
                        color = (255, 0, 0) # Rojo
                    elif file_data["type"] == "system":
                        color = (100, 100, 255) # Azul
                    else:
                        color = (200, 200, 200) # Gris/Blanco
                    
                    # Resaltar archivo cercano
                    if self.near_file and self.near_file["name"] == file_data["name"]:
                        color = (255, 255, 0) # Amarillo highlight
                        
                        # Dibujar indicador de interacción
                        indicator_text = self.fonts["small"].render("E", True, color)
                        indicator_pos = (file_rect.centerx, file_rect.top - 10)
                        text_rect = indicator_text.get_rect(center=indicator_pos)
                        surf.blit(indicator_text, text_rect)
                        
                        # Borde brillante
                        pygame.draw.rect(surf, color, file_rect.inflate(4, 4), 2, border_radius=3)
                    
                    # Dibujar archivo (Rectángulo placeholder)
                    pygame.draw.rect(surf, color, file_rect, border_radius=3)
            
            # Mostrar directorio actual (Arriba, como en la captura)
            dir_text = self.fonts["title"].render(f"Directory: {self.current_directory}", True, (255, 255, 255))
            surf.blit(dir_text, (10, 10))
            
            # Dibujar el avatar del jugador (Se dibuja al final, sobre el panel central)
            self.avatar.draw(surf)
            
            # Efecto de transición
            if self.in_transition:
                progress = self.transition_time / self.transition_duration
                alpha = int(255 * (0.5 - abs(0.5 - progress)))
                overlay = pygame.Surface((SCREEN_W, SCREEN_H))
                overlay.fill((0, 0, 0))
                overlay.set_alpha(alpha)
                surf.blit(overlay, (0, 0))
            
        elif self.state == "fin_juego":
            # Mostrar pantalla de fin de juego
            pass
            
        # Mostrar pausa si es necesario
        if self.paused:
            # Dibujar overlay de pausa
            pass

# --------- Utilidades visuales (Matrix Rain y Glitch Text) ----------
class MatrixRain:
    def __init__(self, width, height, font_name="Consolas", font_size=16, charset=None, column_density=1.0, font_path=None):
        self.w = width
        self.h = height
        # prefer a provided TTF path, fallback to SysFont
        try:
            if font_path:
                self.font = pygame.font.Font(font_path, font_size)
            else:
                self.font = pygame.font.SysFont(font_name, font_size)
        except Exception:
            self.font = pygame.font.SysFont(font_name, font_size)
        self.char_h = self.font.get_height()
        self.char_w = self.font.size("M")[0]
        # columnas efectivas: permitir bajar densidad para hacerlo más sutil
        base_cols = max(1, self.w // self.char_w)
        density = max(0.2, min(1.0, column_density or 1.0))
        self.cols = max(1, int(base_cols * density))
        self.charset = charset or list("01ABCDEFGHJKLMNPQRSTUVWXYZ1234567890")
        # pre-render glyphs in green and head brighter
        self.glyphs = {}
        for ch in self.charset:
            # tonos más oscuros y menos saturados para efecto en el fondo
            surf = self.font.render(ch, True, (0, 110, 40))
            head = self.font.render(ch, True, (120, 190, 120))
            self.glyphs[ch] = (surf, head)

        self.columns = []
        import random as _r
        # espaciado uniforme entre columnas efectivas
        spacing = self.w / self.cols
        for i in range(self.cols):
            speed = _r.uniform(40, 90)  # más lento
            length = _r.randint(8, 16)
            y = _r.uniform(-self.h, 0)
            # populate char sequence
            seq = [_r.choice(self.charset) for _ in range(length)]
            self.columns.append({
                "x": int(i * spacing),
                "y": y,
                "speed": speed,
                "len": length,
                "seq": seq,
            })

    def update(self, dt):
        dy_factor = dt / 1000.0
        for col in self.columns:
            col["y"] += col["speed"] * dy_factor
            if col["y"] - col["len"] * self.char_h > self.h:
                # reset above the screen
                import random as _r
                col["y"] = _r.uniform(-self.h * 0.3, 0)
                col["speed"] = _r.uniform(40, 90)  # mantener lento al reiniciar
                col["len"] = _r.randint(8, 16)
                col["seq"] = [_r.choice(self.charset) for _ in range(col["len"])]

    def draw(self, surf, alpha=140):
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        for col in self.columns:
            x = col["x"]
            y_head = col["y"]
            for i in range(col["len"]):
                y = int(y_head - i * self.char_h)
                if y < -self.char_h or y > self.h:
                    continue
                ch = col["seq"][i % len(col["seq"])]
                glyph, head = self.glyphs[ch]
                g = head if i == 0 else glyph
                # vary alpha along the trail
                a = max(12, 120 - i * 10)  # más tenue
                g.set_alpha(a)
                overlay.blit(g, (x, y))
        overlay.set_alpha(alpha)
        surf.blit(overlay, (0, 0))

def draw_glitch_text_surf(dest_surf, text_surf, center, scale=1.0, glitch_prob=0.08):
    # scale base
    tw, th = text_surf.get_size()
    dw, dh = max(1, int(tw * scale)), max(1, int(th * scale))
    base = pygame.transform.smoothscale(text_surf, (dw, dh))
    x = center[0] - dw // 2
    y = center[1] - dh // 2
    dest_surf.blit(base, (x, y))
    import random as _r
    if _r.random() < glitch_prob:
        # cyan shadow left
        c1 = base.copy()
        c1.fill((0, 200, 255), special_flags=pygame.BLEND_RGB_ADD)
        c1.set_alpha(120)
        dest_surf.blit(c1, (x - 1, y))
        # magenta shadow right
        c2 = base.copy()
        c2.fill((255, 50, 200), special_flags=pygame.BLEND_RGB_ADD)
        c2.set_alpha(120)
        dest_surf.blit(c2, (x + 1, y + 0))
    
# --------- Text helpers ----------
def truncate_ellipsis(text: str, font: pygame.font.Font, max_w: int, ellipsis: str = "...") -> str:
    """Truncate a single-line string to fit within max_w by appending ellipsis if needed."""
    if font.size(text)[0] <= max_w:
        return text
    ell_w = font.size(ellipsis)[0]
    if ell_w >= max_w:
        return ellipsis
    lo, hi = 0, len(text)
    best = ellipsis
    while lo <= hi:
        mid = (lo + hi) // 2
        cand = text[:mid] + ellipsis
        if font.size(cand)[0] <= max_w:
            best = cand
            lo = mid + 1
        else:
            hi = mid - 1
    return best

def wrap_ellipsis(text: str, font: pygame.font.Font, max_w: int, max_h: int, line_spacing: int = 5) -> list:
    """Envuelve el texto al ancho y lo recorta con '...' si max_h no es None.
    Si max_h es None, devuelve todas las líneas envueltas sin límite de altura.
    Devuelve una lista de líneas renderizables.
    """
    # Convertir saltos de línea en tokens para respetarlos
    words = text.replace('\n', ' \n ').split(' ')
    lines = []
    current = ""
    line_h = font.get_height()
    
    # --- MODIFICACIÓN ---
    # Si max_h es None, no hay límite de líneas
    if max_h is not None:
        max_lines = max(1, (max_h + line_spacing) // (line_h + line_spacing))
    else:
        max_lines = float('inf') # Infinitas líneas
    # --- FIN MODIFICACIÓN ---

    for w in words:
        if w == '\n':
            # fuerza salto de línea
            lines.append(current)
            current = ""
            if len(lines) >= max_lines:
                break
            continue
        test = (current + (" " if current else "") + w) if w else current
        if font.size(test)[0] <= max_w:
            current = test
        else:
            # si la palabra sola es demasiado ancha, forzar corte por caracteres
            if not current and w:
                cut = w
                while cut and font.size(cut)[0] > max_w:
                    cut = cut[:-1]
                if cut:
                    lines.append(cut)
                    rest = w[len(cut):]
                    current = rest
                else:
                    lines.append("")
            else:
                lines.append(current)
                current = w
        if len(lines) >= max_lines:
            break

    if len(lines) < max_lines and current:
        lines.append(current)

    # --- MODIFICACIÓN ---
    # Solo truncar si max_h fue especificado
    if max_h is not None and lines:
        lines[-1] = truncate_ellipsis(lines[-1], font, max_w)
    
    # --- (NUEVA CORRECCIÓN) ---
    if max_h is None:
        return lines # Devuelve la lista completa si no hay límite de altura
    
    # Limita a la cantidad de líneas que caben (esto solo se ejecuta si max_h NO es None)
    return lines[:int(max_lines)]


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
        if getattr(self, 'finished', False):
            return
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


# --------- Glitch Transition Screen ----------
class GlitchTransitionScreen(Screen):
    def __init__(self, game, target_screen, duration=600, slices=18):
        super().__init__(game)
        self.target = target_screen
        self.duration = duration
        self.timer = 0
        self.slices = slices
        self._snapshot = pygame.Surface((SCREEN_W, SCREEN_H))
        self._noise = pygame.Surface((SCREEN_W, SCREEN_H))
        self._noise.set_alpha(80)
        self._rng = random.Random()

    def handle_event(self, event):
        pass

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.duration:
            self.game.set_screen(self.target)

    def render(self, surf):
        # render target once into snapshot
        self.target.render(self._snapshot)
        # draw snapshot with glitch slices
        t = min(1.0, self.timer / self.duration)
        offset_amp = int(10 + 30 * (1.0 - (1.0 - t) ** 2))  # ease-out increase
        slice_h = max(2, SCREEN_H // self.slices)
        for i in range(self.slices):
            y = i * slice_h
            if y >= SCREEN_H:
                break
            h = slice_h if y + slice_h <= SCREEN_H else (SCREEN_H - y)
            # horizontal offset jitter
            jitter = self._rng.randint(-offset_amp, offset_amp)
            src_rect = pygame.Rect(0, y, SCREEN_W, h)
            dst_rect = pygame.Rect(jitter, y, SCREEN_W, h)
            surf.blit(self._snapshot, dst_rect, src_rect)
        # add noise flashes
        arr = pygame.surfarray.pixels3d(self._noise)
        arr[:, :, 0] = self._rng.randint(0, 60)
        arr[:, :, 1] = self._rng.randint(0, 60)
        arr[:, :, 2] = self._rng.randint(0, 60)
        del arr
        self._noise.set_alpha(self._rng.randint(40, 120))
        surf.blit(self._noise, (0, 0), special_flags=pygame.BLEND_ADD)


# --------- (NUEVA) Clase Correo ----------
class Correo:
    def __init__(self, es_legitimo, tipo_malicioso, contenido, remitente, asunto, razones_correctas, logo_path=None, inbox_icon_path=None, panel_logo_path=None):
        self.es_legitimo = es_legitimo
        self.tipo_malicioso = tipo_malicioso
        self.contenido = contenido
        self.remitente = remitente
        self.asunto = asunto
        self.razones_correctas = razones_correctas
        # Compat: logo_path original se usa como fallback para ambos contextos
        self.logo_path = logo_path  # legado / fallback
        self._inbox_icon_path = inbox_icon_path
        self._panel_logo_path = panel_logo_path
        self.procesado = False
        self.visible = True

    def _load_scaled_image(self, path, max_size):
        """Carga y escala una imagen desde path con cache por (path, w, h).
        Escala forzada a (w,h) sin preservar aspecto (uso legacy)."""
        try:
            w, h = int(max_size[0]), int(max_size[1])
        except Exception:
            w, h = 36, 36
        if path is None:
            return None
        if not hasattr(self, "_image_cache"):
            self._image_cache = {}
        key = (path, w, h)
        if key in self._image_cache:
            return self._image_cache[key]
        surf = None
        try:
            img = pygame.image.load(path).convert_alpha()
            surf = pygame.transform.smoothscale(img, (w, h))
        except Exception:
            surf = None
        self._image_cache[key] = surf
        return surf

    def _load_image_fit(self, path, max_size, crop_transparent=True, min_alpha=10):
        """Carga una imagen, opcionalmente recorta transparencias y la ajusta a max_size preservando aspecto.
        Cache por (path, w, h, 'fit', crop_transparent)."""
        try:
            max_w, max_h = int(max_size[0]), int(max_size[1])
        except Exception:
            max_w, max_h = 36, 36
        if path is None:
            return None
        if not hasattr(self, "_image_cache"):
            self._image_cache = {}
        cache_key = (path, max_w, max_h, 'fit', bool(crop_transparent))
        if cache_key in self._image_cache:
            return self._image_cache[cache_key]

        scaled = None
        try:
            img = pygame.image.load(path).convert_alpha()
            src = img
            if crop_transparent:
                # Recorta a los píxeles no transparentes
                crop_rect = img.get_bounding_rect(min_alpha)
                if crop_rect and crop_rect.w > 0 and crop_rect.h > 0:
                    src = img.subsurface(crop_rect).copy()
            sw, sh = src.get_width(), src.get_height()
            if sw <= 0 or sh <= 0:
                scaled = None
            else:
                scale = min(max_w / sw, max_h / sh) if max_w > 0 and max_h > 0 else 1.0
                new_w = max(1, int(round(sw * scale)))
                new_h = max(1, int(round(sh * scale)))
                scaled = pygame.transform.smoothscale(src, (new_w, new_h))
        except Exception:
            scaled = None

        self._image_cache[cache_key] = scaled
        return scaled

    def _load_image_fit_square(self, path, max_size, crop_transparent=False, min_alpha=10):
        """Ajusta la imagen a un lienzo cuadrado (w,h) preservando aspecto (letterbox),
        opcionalmente recortando transparencias antes de escalar. Devuelve una Surface cuadrada.
        Cache por (path, w, h, 'fit_square', crop_transparent)."""
        try:
            max_w, max_h = int(max_size[0]), int(max_size[1])
        except Exception:
            max_w, max_h = 36, 36
        if path is None:
            return None
        if not hasattr(self, "_image_cache"):
            self._image_cache = {}
        cache_key = (path, max_w, max_h, 'fit_square', bool(crop_transparent))
        if cache_key in self._image_cache:
            return self._image_cache[cache_key]

        result = None
        try:
            img = pygame.image.load(path).convert_alpha()
            src = img
            if crop_transparent:
                crop_rect = img.get_bounding_rect(min_alpha)
                if crop_rect and crop_rect.w > 0 and crop_rect.h > 0:
                    src = img.subsurface(crop_rect).copy()
            sw, sh = src.get_width(), src.get_height()
            if sw <= 0 or sh <= 0:
                result = None
            else:
                scale = min(max_w / sw, max_h / sh) if max_w > 0 and max_h > 0 else 1.0
                new_w = max(1, int(round(sw * scale)))
                new_h = max(1, int(round(sh * scale)))
                scaled = pygame.transform.smoothscale(src, (new_w, new_h))
                # Componer sobre lienzo cuadrado
                canvas = pygame.Surface((max_w, max_h), pygame.SRCALPHA)
                off_x = (max_w - new_w) // 2
                off_y = (max_h - new_h) // 2
                canvas.blit(scaled, (off_x, off_y))
                result = canvas
        except Exception:
            result = None

        self._image_cache[cache_key] = result
        return result

    def load_logo(self, max_size=(36, 36)):
        """Logo del panel (dentro del correo).
        Ajusta la imagen a un lienzo cuadrado del tamaño pedido, recortando transparencias
        para que el objeto se vea más grande sin deformar (letterbox).
        Usa panel_logo_path o logo_path (fallback)."""
        path = self._panel_logo_path or self.logo_path
        return self._load_image_fit_square(path, max_size, crop_transparent=True)

    def load_panel_logo(self, max_size=(64, 64)):
        """Alias explícito para el logo del panel."""
        return self.load_logo(max_size=max_size)
    
    def has_panel_logo(self) -> bool:
        """Indica si hay ruta de logo definida para el panel (sin considerar fallas de carga)."""
        return bool(self._panel_logo_path or self.logo_path)

    def load_inbox_icon(self, max_size=(36, 36)):
        """Icono para la lista de correos (inbox). Usa inbox_icon_path o logo_path como fallback.
        Escala legacy (no preserva aspecto)."""
        path = self._inbox_icon_path or self.logo_path
        return self._load_scaled_image(path, max_size)

    def load_inbox_icon_fit(self, max_size=(36, 36)):
        """Icono para inbox que recorta transparencia y preserva aspecto al ajustar a max_size."""
        path = self._inbox_icon_path or self.logo_path
        return self._load_image_fit(path, max_size, crop_transparent=True)

    def load_inbox_icon_square(self, max_size=(36, 36), crop_transparent=False):
        """Devuelve un icono cuadrado del tamaño pedido, preservando aspecto (letterbox) y sin deformación.
        Si crop_transparent=True, primero recorta zonas transparentes antes de ajustar."""
        path = self._inbox_icon_path or self.logo_path
        return self._load_image_fit_square(path, max_size, crop_transparent=crop_transparent)

    @property
    def dominio(self):
        try:
            return self.remitente.split("@", 1)[1]
        except Exception:
            return ""


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


# --------- UI Orientada a Objetos para Nivel 1 ----------
class ImageButton:
    """Botón basado en imagen, con fallback a rectángulo + texto."""
    def __init__(self, pos, size, image_paths=None, label_text=None, font=None):
        self.rect = pygame.Rect(pos[0], pos[1], size[0], size[1])
        self.images = []
        self.label_text = label_text
        self.font = font
        if image_paths:
            for p in image_paths:
                try:
                    img = pygame.image.load(p).convert_alpha()
                    self.images.append(pygame.transform.smoothscale(img, size))
                except Exception:
                    continue

    def draw(self, surf):
        if self.images:
            surf.blit(self.images[0], self.rect.topleft)
        else:
            # fallback simple
            hover = self.rect.collidepoint(pygame.mouse.get_pos())
            color = (200, 200, 100) if hover else (100, 100, 100)
            pygame.draw.rect(surf, color, self.rect, border_radius=6)
            if self.label_text and self.font:
                t = self.font.render(self.label_text, True, (0, 0, 0))
                surf.blit(t, (self.rect.centerx - t.get_width() // 2, self.rect.centery - t.get_height() // 2))

    def handle_event(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)


class Inbox:
    """Bandeja de entrada con cabecera y filas de 2 líneas (asunto + dominio), estilo del mock."""
    def __init__(self, correos, font_title, font_row):
        self.correos = correos
        self.font_title = font_title  # usada para header principal
        self.font_row = font_row      # usada para filas
        # métricas
        self.header_h = 28
        self.row_h = self.font_row.get_height() * 2 + 10
        self.vgap = 8
        # Scroll state
        self.desplazamiento_y = 0
        self.alto_visible = 0
        self.alto_total = 0
        self.max_desplazamiento_y = 0
        self.necesita_scrollbar = False
        self.scrollbar_fondo_rect = None
        self.scrollbar_manija_rect = None
        self.esta_arrastrando = False
        self.arrastre_inicio_y = 0
        self.arrastre_inicio_manija_y = 0

    def _calc_rects(self, hacker_rect=None):
        # header en top debajo del HUD
        header = pygame.Rect(20, 56, max(320, SCREEN_W - 40), self.header_h)
        # ancho seguro evita solaparse con hacker
        right_limit = SCREEN_W - 20
        if hacker_rect is not None:
            right_limit = min(right_limit, hacker_rect.left - 24)
        width = max(320, right_limit - 20)
        panel = pygame.Rect(20, header.bottom + 10, width, 320)
        return header, panel

    def _recalc_scroll(self, panel):
        # Altura visible dentro del panel para filas (padding superior+inferior ~12)
        self.alto_visible = max(0, panel.h - 24)
        total = 0
        for c in self.correos:
            if not c.visible or c.procesado:
                continue
            total += self.row_h + self.vgap
        if total > 0:
            total -= self.vgap  # quitar el último espacio
        self.alto_total = max(self.alto_visible, total)
        self.necesita_scrollbar = self.alto_total > self.alto_visible
        if self.necesita_scrollbar:
            self.max_desplazamiento_y = self.alto_total - self.alto_visible
            # Barra pegada al borde derecho interno del panel
            bar_w = 14
            self.scrollbar_fondo_rect = pygame.Rect(panel.right - bar_w - 6, panel.y + 8, bar_w, panel.h - 16)
            # Altura de la manija proporcional
            if self.alto_total > 0:
                handle_h = max(24, int(self.alto_visible * (self.alto_visible / self.alto_total)))
            else:
                handle_h = self.scrollbar_fondo_rect.h
            self.scrollbar_manija_rect = pygame.Rect(self.scrollbar_fondo_rect.x, self.scrollbar_fondo_rect.y, bar_w, handle_h)
            # Clamp desplazamiento y actualizar manija
            self.desplazamiento_y = max(0, min(self.desplazamiento_y, self.max_desplazamiento_y))
            self._actualizar_pos_manija()
        else:
            self.desplazamiento_y = 0
            self.max_desplazamiento_y = 0
            self.scrollbar_fondo_rect = None
            self.scrollbar_manija_rect = None

    def _actualizar_pos_manija(self):
        if not self.necesita_scrollbar or not self.scrollbar_fondo_rect or not self.scrollbar_manija_rect:
            return
        rango = self.scrollbar_fondo_rect.h - self.scrollbar_manija_rect.h
        if rango <= 0:
            self.scrollbar_manija_rect.y = self.scrollbar_fondo_rect.y
            return
        porcentaje = 0 if self.max_desplazamiento_y == 0 else (self.desplazamiento_y / self.max_desplazamiento_y)
        self.scrollbar_manija_rect.y = int(self.scrollbar_fondo_rect.y + porcentaje * rango)

    def handle_event(self, event, hacker_rect=None):
        header, panel = self._calc_rects(hacker_rect)
        self._recalc_scroll(panel)

        # Área de filas útil (excluye margen y scrollbar si existe)
        scroll_w = 18 if self.necesita_scrollbar else 0
        filas_area = pygame.Rect(panel.x + 8, panel.y + 8, panel.w - 16 - scroll_w, panel.h - 16)

        # Rueda del mouse
        if event.type == pygame.MOUSEWHEEL:
            if filas_area.collidepoint(pygame.mouse.get_pos()) and self.necesita_scrollbar:
                self.desplazamiento_y -= event.y * 40
                self.desplazamiento_y = max(0, min(self.desplazamiento_y, self.max_desplazamiento_y))
                self._actualizar_pos_manija()
            return None

        # Drag en scrollbar
        if event.type == pygame.MOUSEMOTION and self.esta_arrastrando and self.necesita_scrollbar:
            dy = event.pos[1] - self.arrastre_inicio_y
            rango = self.scrollbar_fondo_rect.h - self.scrollbar_manija_rect.h
            bg_y = self.scrollbar_fondo_rect.y
            nueva_y = max(bg_y, min(self.arrastre_inicio_manija_y + dy, bg_y + rango))
            self.scrollbar_manija_rect.y = nueva_y
            porcentaje = 0 if rango <= 0 else (nueva_y - bg_y) / rango
            self.desplazamiento_y = porcentaje * self.max_desplazamiento_y
            return None

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.esta_arrastrando = False
            return None

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        # Clicks dentro del panel: primero scrollbar, luego filas
        if self.necesita_scrollbar and self.scrollbar_fondo_rect:
            if self.scrollbar_manija_rect.collidepoint(event.pos):
                self.esta_arrastrando = True
                self.arrastre_inicio_y = event.pos[1]
                self.arrastre_inicio_manija_y = self.scrollbar_manija_rect.y
                return None
            if self.scrollbar_fondo_rect.collidepoint(event.pos):
                # Page up/down
                if event.pos[1] < self.scrollbar_manija_rect.y:
                    self.desplazamiento_y -= self.alto_visible
                else:
                    self.desplazamiento_y += self.alto_visible
                self.desplazamiento_y = max(0, min(self.desplazamiento_y, self.max_desplazamiento_y))
                self._actualizar_pos_manija()
                return None

        if not panel.collidepoint(event.pos):
            return None

        # calcular clicks por fila (considerando desplazamiento)
        y = panel.y + 12 - self.desplazamiento_y
        row_right_limit = panel.right - (10 + (18 if self.necesita_scrollbar else 0))
        row_x = panel.x + 10
        row_w = max(10, row_right_limit - row_x)
        for c in self.correos:
            if not c.visible or c.procesado:
                continue
            row = pygame.Rect(row_x, int(y), row_w, self.row_h)
            if row.collidepoint(event.pos) and filas_area.collidepoint(event.pos):
                return c
            y += self.row_h + self.vgap
        return None

    def render(self, surf, hacker_rect=None):
        header, panel = self._calc_rects(hacker_rect)
        # Recalcular scroll según tamaño actual
        self._recalc_scroll(panel)
        # header pill
        pygame.draw.rect(surf, (24, 32, 40), header, border_radius=8)
        left_txt = self.font_row.render(">_ SYSTEM:  INBOX_ACCESS_LEVEL_1", True, (0, 255, 170))
        surf.blit(left_txt, (header.x + 10, header.y + (header.h - left_txt.get_height()) // 2))
        total_vis = sum(1 for c in self.correos if c.visible and not c.procesado)
        right_txt = self.font_row.render(f"{total_vis}/{len(self.correos)} MESSAGES", True, (220, 220, 220))
        surf.blit(right_txt, (header.right - right_txt.get_width() - 10, header.y + (header.h - right_txt.get_height()) // 2))
        # panel
        pygame.draw.rect(surf, (18, 22, 28), panel, border_radius=12)
        pygame.draw.rect(surf, (80, 80, 110), panel, 1, border_radius=12)
        # filas (con clipping y desplazamiento)
        scroll_w = 18 if self.necesita_scrollbar else 0
        clip_rect = pygame.Rect(panel.x + 8, panel.y + 8, panel.w - 16 - scroll_w, panel.h - 16)
        prev_clip = surf.get_clip()
        surf.set_clip(clip_rect)
        y = panel.y + 12 - self.desplazamiento_y
        mx, my = pygame.mouse.get_pos()
        row_right_limit = panel.right - (10 + (scroll_w if self.necesita_scrollbar else 0))
        row_x = panel.x + 10
        row_w = max(10, row_right_limit - row_x)
        for c in self.correos:
            if not c.visible or c.procesado:
                continue
            row = pygame.Rect(row_x, int(y), row_w, self.row_h)
            hovered = row.collidepoint(mx, my)
            bg = (35, 42, 64) if hovered else (28, 34, 48)
            pygame.draw.rect(surf, bg, row, border_radius=10)
            pygame.draw.rect(surf, (60, 70, 100), row, 1, border_radius=10)
            # padding interno
            pad_x = 10
            pad_y = 6
            # reservar espacio para el cuadro de icono a la derecha (logo por correo)
            # hacerlo más grande: altura casi toda la fila y cuadrado 1:1
            right_box_h = max(20, row.h - 6)
            right_box_w = right_box_h
            right_box_gap = 8
            inner_w = row.w - pad_x * 2 - (right_box_w + right_box_gap)
            # asunto en color
            subj_color = (120, 255, 140) if c.es_legitimo else (255, 120, 120)
            subj = truncate_ellipsis(c.asunto, self.font_row, inner_w)
            surf.blit(self.font_row.render(subj, True, subj_color), (row.x + pad_x, row.y + pad_y))
            # dominio en gris
            dom = truncate_ellipsis(c.remitente, self.font_row, inner_w)
            dom_color = (200, 200, 200)
            surf.blit(self.font_row.render(dom, True, dom_color), (row.x + pad_x, row.y + pad_y + self.font_row.get_height() + 2))
            # icono a la derecha (logo por correo) con recorte y aspecto preservado
            box_h = right_box_h
            box = pygame.Rect(row.right - (right_box_w + 8), row.y + (row.h - box_h) // 2, right_box_w, box_h)
            # 1:1 garantizado: surface cuadrada del tamaño del slot, sin deformación
            # recorta transparencia para aprovechar más el área
            logo = c.load_inbox_icon_square(max_size=(box_h - 4, box_h - 4), crop_transparent=True)
            if logo:
                lx = box.x + (box.w - logo.get_width()) // 2
                ly = box.y + (box.h - logo.get_height()) // 2
                surf.blit(logo, (lx, ly))
            y += self.row_h + self.vgap
        surf.set_clip(prev_clip)
        # Scrollbar
        if self.necesita_scrollbar and self.scrollbar_fondo_rect and self.scrollbar_manija_rect:
            pygame.draw.rect(surf, (40, 40, 60), self.scrollbar_fondo_rect, border_radius=7)
            color_manija = (180, 180, 200) if self.esta_arrastrando else (120, 120, 150)
            pygame.draw.rect(surf, color_manija, self.scrollbar_manija_rect, border_radius=7)


class EmailPanel:
    """Panel del correo abierto, con barra de scroll y botones de imagen."""
    def __init__(self, correo, font_text, font_buttons, hacker_rect_provider=None):
        self.correo = correo
        self.font_text = font_text
        self.font_buttons = font_buttons
        self._hacker_rect_provider = hacker_rect_provider
        self.rect = pygame.Rect(150, 100, 500, 350)
        # Tamaño del logo mostrado dentro del correo (no afecta iconos del inbox)
        # Volver al slot original para mantener el layout.
        self.panel_logo_size = (64, 64)

        # --- (CORREGIDO) Solo el contenido va en el cuerpo ---
        self.texto_completo = self.correo.contenido
        self.texto_actual = self.texto_completo # Desactivar typewriter para el scroll
        self.tiempo_escritura = 0
        self.velocidad_escritura = 30 

        # botones
        self.btn_back = ImageButton((0, 0), (80, 30), label_text="Volver", font=font_text)
        self.btn_responder = ImageButton((0, 0), (160, 44),
            image_paths=["assets/btn_responder.png", "assets/btn_reply.png"], label_text="Responder", font=font_buttons)
        self.btn_eliminar = ImageButton((0, 0), (160, 44),
            image_paths=["assets/btn_eliminar.png", "assets/btn_delete.png"], label_text="Eliminar", font=font_buttons)
        self.btn_reportar = ImageButton((0, 0), (160, 44),
            image_paths=["assets/btn_reportar.png", "assets/btn_report.png"], label_text="Reportar", font=font_buttons)

        # flujo de razones
        self.mode = "reading"
        self.razones_sel = []
        self.btn_razones = [
            {"rect": pygame.Rect(0, 0, 120, 30), "razon": "Logo", "texto": "Logo"},
            {"rect": pygame.Rect(0, 0, 120, 30), "razon": "Dominio", "texto": "Dominio"},
            {"rect": pygame.Rect(0, 0, 120, 30), "razon": "Texto", "texto": "Texto"},
        ]
        self.btn_confirmar = pygame.Rect(0, 0, 120, 38)
        self._accion_pendiente = None

        # --- (NUEVO) Estado de la barra de Scroll (en español) ---
        self._area_texto_rect = pygame.Rect(0, 0, 0, 0)
        self.desplazamiento_y = 0
        self.alto_linea = self.font_text.get_height() + 5
        self.lineas_envueltas_completas = []
        self.alto_total_texto = 0
        self.alto_visible_texto = 0
        self.max_desplazamiento_y = 0
        self.scrollbar_fondo_rect = None
        self.scrollbar_manija_rect = None
        self.necesita_scrollbar = False
        self.esta_arrastrando = False
        self.arrastre_inicio_y = 0
        self.arrastre_inicio_manija_y = 0

        self._calcular_layout() # Calcular layout y scroll

    def _calcular_layout(self):
        """Calcula el área de texto y la configuración de la barra de scroll."""
        header_h = 24
        show_logo = self.correo.has_panel_logo()
        logo = self.correo.load_logo(max_size=self.panel_logo_size) if show_logo else None
        used_logo_h = logo.get_height() if logo else (self.panel_logo_size[1] if show_logo else 0)
        add_after_header = (used_logo_h + 14) if show_logo else 0
        top_y = self.rect.y + 8 + header_h + 10 + add_after_header
        
        # Área de texto es más angosta para dar espacio al scrollbar
        text_w = self.rect.w - 20 - 18 # 18px para scrollbar + padding
        text_h = self.rect.bottom - 10 - top_y
        self._area_texto_rect = pygame.Rect(self.rect.x + 10, top_y, text_w, text_h)

        # Calcular scroll
        self.alto_visible_texto = self._area_texto_rect.h
        self.lineas_envueltas_completas = wrap_ellipsis(self.texto_completo, self.font_text, text_w, max_h=None) # Usar la función modificada
        self.alto_total_texto = max(len(self.lineas_envueltas_completas) * self.alto_linea, self.alto_visible_texto)
        self.necesita_scrollbar = self.alto_total_texto > self.alto_visible_texto

        if self.necesita_scrollbar:
            self.max_desplazamiento_y = self.alto_total_texto - self.alto_visible_texto
            self.scrollbar_fondo_rect = pygame.Rect(self._area_texto_rect.right + 4, self._area_texto_rect.y, 15, self._area_texto_rect.h)
            
            handle_h = max(20, self.alto_visible_texto * (self.alto_visible_texto / self.alto_total_texto))
            self.scrollbar_manija_rect = pygame.Rect(self.scrollbar_fondo_rect.x, self.scrollbar_fondo_rect.y, 15, handle_h)
            self._actualizar_pos_manija() # Sincronizar posición

    def _actualizar_pos_manija(self):
        """Actualiza la posición Y de la manija del scrollbar basado en self.desplazamiento_y"""
        if not self.necesita_scrollbar:
            return
        porcentaje_scroll = 0
        if self.max_desplazamiento_y > 0:
            porcentaje_scroll = self.desplazamiento_y / self.max_desplazamiento_y
        
        rango_y_manija = self.scrollbar_fondo_rect.h - self.scrollbar_manija_rect.h
        self.scrollbar_manija_rect.y = self.scrollbar_fondo_rect.y + (porcentaje_scroll * rango_y_manija)

    def update(self, dt):
        # Lógica de arrastre del scroll
        if self.esta_arrastrando:
            mx, my = pygame.mouse.get_pos()
            
            # Movimiento relativo del mouse
            dy = my - self.arrastre_inicio_y
            
            # Rango de movimiento de la manija
            rango_y_manija = self.scrollbar_fondo_rect.h - self.scrollbar_manija_rect.h
            bg_y = self.scrollbar_fondo_rect.y

            # Nueva posición de la manija
            nueva_y_manija = self.arrastre_inicio_manija_y + dy
            # Limitar a los bordes del scrollbar_fondo
            nueva_y_manija = max(bg_y, min(nueva_y_manija, bg_y + rango_y_manija))
            
            # Calcular el porcentaje de scroll basado en la posición de la manija
            porcentaje_scroll = 0
            if rango_y_manija > 0:
                porcentaje_scroll = (nueva_y_manija - bg_y) / rango_y_manija
            
            # Actualizar el desplazamiento_y (pixel offset del texto)
            self.desplazamiento_y = porcentaje_scroll * self.max_desplazamiento_y
            
            self._actualizar_pos_manija() # Sincronizar la manija visualmente

    def handle_event(self, event):
        # --- (NUEVO) Manejo de Rueda del Mouse ---
        if event.type == pygame.MOUSEWHEEL and self.necesita_scrollbar:
             # Solo scrollear si el mouse está sobre el panel de texto
            if self._area_texto_rect.collidepoint(pygame.mouse.get_pos()):
                self.desplazamiento_y -= event.y * 30 # event.y es 1 o -1. 30 es velocidad
                self.desplazamiento_y = max(0, min(self.desplazamiento_y, self.max_desplazamiento_y))
                self._actualizar_pos_manija()
                return None # Consumir el evento

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # --- (NUEVO) Manejo de Clic en Scrollbar ---
            if self.necesita_scrollbar:
                if self.scrollbar_manija_rect.collidepoint(event.pos):
                    self.esta_arrastrando = True
                    self.arrastre_inicio_y = event.pos[1]
                    self.arrastre_inicio_manija_y = self.scrollbar_manija_rect.y
                    return None # Consumir evento
                elif self.scrollbar_fondo_rect.collidepoint(event.pos):
                    # Clic en la barra (no en la manija) - Paginación
                    if event.pos[1] < self.scrollbar_manija_rect.y:
                        self.desplazamiento_y -= self.alto_visible_texto # Page Up
                    else:
                        self.desplazamiento_y += self.alto_visible_texto # Page Down
                    self.desplazamiento_y = max(0, min(self.desplazamiento_y, self.max_desplazamiento_y))
                    self._actualizar_pos_manija()
                    return None # Consumir evento

            # (Existente) Manejo de botones de acción
            if self.btn_back.handle_event(event):
                return {"type": "back"}
            if self.mode == "reading":
                if self.btn_responder.handle_event(event):
                    return {"type": "accion", "accion": "responder"}
                if self.btn_eliminar.handle_event(event):
                    self.mode = "reasons"; self._accion_pendiente = "eliminar"; return None
                if self.btn_reportar.handle_event(event):
                    self.mode = "reasons"; self._accion_pendiente = "reportar"; return None
            else:
                for b in self.btn_razones:
                    if b["rect"].collidepoint(event.pos):
                        r = b["razon"]
                        if r in self.razones_sel:
                            self.razones_sel.remove(r)
                        else:
                            self.razones_sel.append(r)
                if self.btn_confirmar.collidepoint(event.pos):
                    acc = self._accion_pendiente
                    self.mode = "reading"
                    return {"type": "reasons_confirm", "accion": acc, "razones": list(self.razones_sel)}

        # --- (NUEVO) Manejo de Soltar Clic ---
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.esta_arrastrando = False

        return None

    def render(self, surf):
        # panel
        pygame.draw.rect(surf, (30, 30, 50), self.rect, border_radius=10)
        pygame.draw.rect(surf, (150, 150, 200), self.rect, 2, border_radius=10)
        
        # --- (CORREGIDO) Header ahora muestra el ASUNTO ---
        header_rect = pygame.Rect(self.rect.x + 8, self.rect.y + 8, self.rect.w - 16, 24)
        pygame.draw.rect(surf, (22, 22, 34), header_rect, border_radius=8)
        
        subj_str = truncate_ellipsis(self.correo.asunto, self.font_text, header_rect.w - 12)
        subj_surf = self.font_text.render(subj_str, True, (220, 220, 220))
        
        # Centrar el asunto
        subj_x = header_rect.centerx - subj_surf.get_width() // 2
        subj_y = header_rect.centery - subj_surf.get_height() // 2
        surf.blit(subj_surf, (subj_x, subj_y))
        # --- FIN CORRECCIÓN HEADER ---

        # logo centrado arriba
        show_logo = self.correo.has_panel_logo()
        logo = self.correo.load_logo(max_size=self.panel_logo_size) if show_logo else None
        logo_y = header_rect.bottom + 10
        if logo:
            logo_x = self.rect.centerx - logo.get_width() // 2
            surf.blit(logo, (logo_x, logo_y))
            logo_rect = pygame.Rect(logo_x, logo_y, logo.get_width(), logo.get_height())
        elif show_logo:
            # Placeholder si no hay logo, del mismo tamaño objetivo
            ph_w, ph_h = self.panel_logo_size
            logo_rect = pygame.Rect(self.rect.centerx - ph_w // 2, logo_y, ph_w, ph_h)
            pygame.draw.rect(surf, (60, 70, 90), logo_rect)
            pygame.draw.rect(surf, (220, 220, 235), logo_rect, 2)
        else:
            # No reservar espacio ni dibujar placeholder si no hay logo configurado
            logo_rect = pygame.Rect(self.rect.centerx, logo_y, 0, 0)

        # --- (CORREGIDO) Renderizado de Texto con Scroll y Clipping ---
        text_x = self._area_texto_rect.x
        text_y_start = self._area_texto_rect.y
        text_h = self._area_texto_rect.h

        if text_h > 0:
            # Establecer clip para asegurar que no se dibuje fuera
            prev_clip = surf.get_clip()
            clip_rect = self._area_texto_rect.copy() # Usar el rect del área de texto
            surf.set_clip(clip_rect)
            
            y_pos = text_y_start - self.desplazamiento_y # Aplicar offset de scroll
            
            for line in self.lineas_envueltas_completas:
                # Optimización: no dibujar líneas que están completamente fuera de la vista
                if y_pos + self.alto_linea < text_y_start:
                    y_pos += self.alto_linea
                    continue
                if y_pos > text_y_start + text_h:
                    break

                t = self.font_text.render(line, True, (255, 255, 255))
                surf.blit(t, (text_x, y_pos))
                y_pos += self.alto_linea
                
            surf.set_clip(prev_clip) # Restaurar clip
        
        # --- (NUEVO) Renderizar Scrollbar ---
        if self.necesita_scrollbar:
            # Fondo de la barra
            pygame.draw.rect(surf, (40, 40, 60), self.scrollbar_fondo_rect, border_radius=7)
            # Manija (handle)
            color_manija = (180, 180, 200) if self.esta_arrastrando else (120, 120, 150)
            pygame.draw.rect(surf, color_manija, self.scrollbar_manija_rect, border_radius=7)
        # --- FIN RENDER SCROLLBAR ---
        # layout botones: colocar 'Volver' pegado al borde izquierdo del panel, a la altura del logo
        btn_w, btn_h = 80, 30
        left_pad = 10
        bx = self.rect.x + left_pad
        by = max(header_rect.bottom + 4, logo_rect.y)
        self.btn_back.rect.update(bx, by, btn_w, btn_h)
        self.btn_back.draw(surf)

        base_y = self.rect.bottom + 12
        self.btn_responder.rect.update(self.rect.x, base_y, 160, 44)
        self.btn_eliminar.rect.update(self.rect.x + 170, base_y, 160, 44)
        self.btn_reportar.rect.update(self.rect.x + 340, base_y, 160, 44)
        self.btn_responder.draw(surf)
        self.btn_eliminar.draw(surf)
        self.btn_reportar.draw(surf)

        # overlay de razones
        if self.mode == "reasons":
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            surf.blit(overlay, (0, 0))
            bx = self.rect.x; by = self.rect.bottom + 60
            for i, b in enumerate(self.btn_razones):
                b["rect"].update(bx + i * 140, by, 120, 30)
                color = (100, 200, 100) if b["razon"] in self.razones_sel else (100, 100, 100)
                pygame.draw.rect(surf, color, b["rect"], border_radius=5)
                s = self.font_text.render(b["texto"], True, (0, 0, 0))
                surf.blit(s, (b["rect"].centerx - s.get_width() // 2, b["rect"].centery - s.get_height() // 2))
            self.btn_confirmar.update(self.rect.x + 2*140, by + 40, 120, 38)
            pygame.draw.rect(surf, (100, 200, 100), self.btn_confirmar, border_radius=5)
            s = self.font_buttons.render("Confirmar", True, (0, 0, 0))
            surf.blit(s, (self.btn_confirmar.centerx - s.get_width() // 2, self.btn_confirmar.centery - s.get_height() // 2))

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

        # Fuentes básicas (esencial) - preferir TTF del proyecto
        try:
            self.font = pygame.font.Font(self.game.font_path, 40)
        except Exception:
            self.font = pygame.font.SysFont("Consolas", 28)
        try:
            self.option_font = pygame.font.Font(self.game.font_path, 32)
        except Exception:
            self.option_font = pygame.font.SysFont("Consolas", 20)
        try:
            self.small_font = pygame.font.Font(self.game.font_path, 28)
        except Exception:
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

# --------- Pantalla Selección de Nivel ----------
class LevelSelectScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        try:
            self.font = pygame.font.Font(self.game.font_path, 42)
        except Exception:
            self.font = pygame.font.SysFont("Consolas", 30)
        # Botones imagen para niveles
        self.level_buttons = []
        self.create_levels()
        #imagen de fondo en la selección de niveles
        try:
            self.background = pygame.image.load("assets/fondo_niveles 2.png").convert()
            self.background = pygame.transform.scale(self.background, (SCREEN_W, SCREEN_H))
        except Exception:
            self.background = None
        # matrix rain (más pequeño y sutil)
        self.matrix = MatrixRain(
            SCREEN_W, SCREEN_H,
            font_size=12,
            column_density=0.45,
            font_path=getattr(self.game, 'font_path', None)
        )
        # Botón 'Volver' en esquina superior izquierda (imagen si existe)
        try:
            self.small_font = pygame.font.Font(self.game.font_path, 16)
        except Exception:
            self.small_font = pygame.font.SysFont("Consolas", 16)
        # Fuente para la etiqueta 'Volver' (más grande y visible)
        try:
            self.back_label_font = pygame.font.Font(self.game.font_path, 40)
        except Exception:
            self.back_label_font = pygame.font.SysFont("Consolas", 22)
        self.volver_image = None
        try:
            for p in ("assets/boton_volver final 2.png", "assets/volver_button.png"):
                try:
                    img = pygame.image.load(p).convert_alpha()
                    img = pygame.transform.smoothscale(img, (48, 48))
                    self.volver_image = img
                    break
                except Exception:
                    continue
        except Exception:
            self.volver_image = None
        if self.volver_image:
            self.boton_volver_rect = self.volver_image.get_rect(topleft=(20, 20))
        else:
            self.boton_volver_rect = pygame.Rect(20, 20, 80, 30)

    def create_levels(self):
        # Crear tres botones imagen: nivel1, nivel2, nivel3
        # Mantener la proporción original 622x233 al escalar los botones
        orig_w, orig_h = 689, 735
        aspect = orig_w / orig_h
        # Altura objetivo reducida para botones más pequeños
        btn_h = 240
        btn_w = int(btn_h * aspect)  # ancho manteniendo proporción

        # Espacio entre centros de botones
        spacing = btn_w + 24
        center_y = SCREEN_H // 2
        center_x = SCREEN_W // 2

        centers = [ (center_x - spacing, center_y), (center_x, center_y), (center_x + spacing, center_y) ]

        names = ["Nivel 1", "Nivel 2", "Nivel 3"]
        # Estado dinámico de Nivel 2
        n2_unlocked = bool(self.game.unlocked_levels.get("Nivel 2", False))
        enabled_flags = [True, n2_unlocked, False]
        # Elegir imágenes; para Nivel 2 usar locked/unlocked con fallback
        n2_img_primary = "assets/nivel2_unlocked.png" if n2_unlocked else "assets/nivel2_locked.png"
        # Fallbacks conocidos del repo anterior
        n2_img_fallback = "assets/malware_unlocked.png" if n2_unlocked else "assets/malware_locked.png"
        image_paths = [
            "assets/nivel1_unlocked final 3.png",
            n2_img_primary,
            "assets/nivel3_locked.png"
        ]

        for i in range(3):
            cx, cy = centers[i]
            if i == 0:
                size_w = int(btn_w * 1.05)  # ~6% wider
                size_h = int(btn_h * 1.05)  # ~6% taller
            else:
                size_w = btn_w
                size_h = btn_h
            rect = pygame.Rect(0, 0, size_w, size_h)
            rect.center = (cx, cy)
            self.level_buttons.append({
                "name": names[i],
                "image_path": image_paths[i],
                "rect": rect,
                "enabled": enabled_flags[i],
                # animation fields
                "base_image": None,
                "base_size": (size_w, size_h),
                "scale": 0.85,
                "hover_scale": 1.08,
                "press_scale": 0.96,
                "speed": 8.0,
                "revealed": False,
                "reveal_delay": i * 120
            })

        # precargar imágenes
        for btn in self.level_buttons:
            path = btn.get("image_path")
            loaded = None
            if btn.get("name") == "Nivel 2":
                # Probar principal y luego fallback
                for p in [path, n2_img_fallback]:
                    if not p:
                        continue
                    try:
                        img = pygame.image.load(p).convert_alpha()
                        img = pygame.transform.smoothscale(img, (btn["rect"].width, btn["rect"].height))
                        loaded = img
                        break
                    except Exception:
                        continue
            else:
                try:
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.smoothscale(img, (btn["rect"].width, btn["rect"].height))
                    loaded = img
                except Exception:
                    loaded = None
            btn["base_image"] = loaded

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Comprobar botón volver
            if self.boton_volver_rect.collidepoint(mx, my):
                self.game.change_screen(MenuScreen(self.game))
                return
            for btn in self.level_buttons:
                if btn["rect"].collidepoint(mx, my):
                    btn["scale"] = btn.get("press_scale", 0.96)  # click tap anim
                    if btn.get("enabled", False):
                        if btn["name"] == "Nivel 1":
                            target = Level1Screen(self.game)
                            self.game.set_screen(GlitchTransitionScreen(self.game, target, duration=650, slices=22))

                        # --- CÓDIGO AÑADIDO ---
                        elif btn["name"] == "Nivel 2":
                            # La clase Level2Screen ya existe en tu código
                            target = Level2Screen(self.game)
                            # Usamos la misma transición
                            self.game.set_screen(GlitchTransitionScreen(self.game, target, duration=650, slices=22))
                        # --- FIN CÓDIGO AÑADIDO ---

                    else:
                        #Añadir feedback si intentan pulsar un nivel bloqueado
                        pass

    def update(self, dt):
        self.matrix.update(dt)
        mx, my = pygame.mouse.get_pos()
        for i in range(len(self.level_buttons)):
            btn = self.level_buttons[i]
            # reveal grid-like (staggered by index)
            btn.setdefault('_time', 0)
            btn['_time'] += dt
            if not btn["revealed"] and btn['_time'] >= btn.get("reveal_delay", 0):
                btn["revealed"] = True
                btn["scale"] = 0.85
            if not btn["revealed"]:
                continue
            target = 1.0
            if btn.get("enabled", False) and btn["rect"].collidepoint(mx, my):
                target = btn.get("hover_scale", 1.08)
            factor = min(1.0, btn.get("speed", 8.0) * dt / 1000.0)
            btn["scale"] = btn["scale"] + (target - btn["scale"]) * factor

    def render(self, surf):
        # Dibujar fondo compartido con el menú si existe
        if getattr(self, 'background', None):
            surf.blit(self.background, (0, 0))
        else:
            surf.fill((20, 50, 70))
        self.matrix.draw(surf, alpha=80)
        header = self.font.render("Selecciona un nivel (haz click)", True, (255, 255, 255))
        draw_glitch_text_surf(surf, header, (SCREEN_W // 2, 100), scale=1.0, glitch_prob=0.1)

        mx, my = pygame.mouse.get_pos()
        for btn in self.level_buttons:
            if not btn.get("revealed", True):
                continue
            rect = btn["rect"]
            base_img = btn.get("base_image")
            enabled = btn.get("enabled", False)
            scale = btn.get("scale", 1.0)

            if base_img:
                w, h = btn.get("base_size", (rect.width, rect.height))
                draw_w = int(w * scale)
                draw_h = int(h * scale)
                img = pygame.transform.smoothscale(base_img, (draw_w, draw_h))
                draw_x = rect.centerx - draw_w // 2
                draw_y = rect.centery - draw_h // 2
                surf.blit(img, (draw_x, draw_y))
            else:
                hover = rect.collidepoint(mx, my)
                color = (200, 200, 100) if hover and enabled else (120, 120, 120)
                if not enabled:
                    color = (80, 80, 80)
                pygame.draw.rect(surf, color, rect, border_radius=8)
                txt = self.font.render(btn["name"], True, (0, 0, 0))
                surf.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

        # Dibujar botón 'Volver' en esquina superior izquierda (imagen o fallback)
        mx, my = pygame.mouse.get_pos()
        if self.volver_image:
            surf.blit(self.volver_image, self.boton_volver_rect.topleft)
        else:
            color_volver = (180, 180, 180) if self.boton_volver_rect.collidepoint(mx, my) else (130, 130, 130)
            pygame.draw.rect(surf, color_volver, self.boton_volver_rect, border_radius=4)
            volver_txt = self.small_font.render("Volver", True, (0, 0, 0))
            surf.blit(volver_txt, (self.boton_volver_rect.x + 10, self.boton_volver_rect.y + 6))

        # Etiqueta 'Volver' un poco a la derecha del botón
        try:
            # Color hex #81c7cf -> (129,199,207)
            label = self.back_label_font.render("Volver", True, (129, 199, 207))
            label_x = self.boton_volver_rect.right + 8
            label_y = self.boton_volver_rect.centery - label.get_height() // 2
            surf.blit(label, (label_x, label_y))
        except Exception:
            pass
        
        # NUEVO: Mostrar puntajes por nivel en la esquina inferior derecha
        stats = self.game.player_stats
        stats_x = SCREEN_W - 300
        stats_y = SCREEN_H - 150
        
        # Fondo semitransparente para las estadísticas
        stats_bg = pygame.Surface((280, 160), pygame.SRCALPHA)
        stats_bg.fill((0, 0, 0, 150))
        surf.blit(stats_bg, (stats_x, stats_y))
        
        # Título
        title_text = self.small_font.render("MEJORES PUNTAJES", True, (255, 215, 0))
        surf.blit(title_text, (stats_x + 10, stats_y + 10))
        
        # Mostrar puntajes por nivel
        y_offset = 40
        for level_num in [1, 2, 3]:
            best_score = stats.get_level_best_score(level_num)
            rank = stats.get_level_rank(level_num)
            
            # Color según disponibilidad del nivel
            enabled = self.game.unlocked_levels.get(f"Nivel {level_num}", False)
            color = (255, 255, 255) if enabled else (120, 120, 120)
            
            level_text = self.small_font.render(f"Nivel {level_num}:", True, color)
            score_text = self.small_font.render(f"{best_score} pts", True, (100, 255, 100) if enabled else (80, 80, 80))
            rank_text = self.small_font.render(f"[{rank}]", True, (255, 200, 100) if enabled else (80, 80, 80))
            
            surf.blit(level_text, (stats_x + 10, stats_y + y_offset))
            surf.blit(score_text, (stats_x + 100, stats_y + y_offset))
            surf.blit(rank_text, (stats_x + 200, stats_y + y_offset))
            
            y_offset += 30

# --------- Pantalla Menú ----------
class MenuScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        # use project's TTF font if available
        try:
            self.font = pygame.font.Font(self.game.font_path, 70)
        except Exception:
            self.font = pygame.font.SysFont("Consolas", 40)
        self.options = ["JUGAR", "SALIR"]
        self.buttons = []  # (opt, txt, rect, anim)
        self.create_buttons()
        # Fondo del menú 
        try:
            self.menu_background = pygame.image.load("assets/fondo_menu.png").convert()
            self.menu_background = pygame.transform.scale(self.menu_background, (SCREEN_W, SCREEN_H))
        except Exception:
            self.menu_background = None
        # reveal animation
        self._start_time = 0
        # Matrix Rain background 
        self.matrix = MatrixRain(
            SCREEN_W, SCREEN_H,
            font_size=12,  
            column_density=0.5, 
            font_path=getattr(self.game, 'font_path', None)
        )

    def create_buttons(self):
        for i, opt in enumerate(self.options):
            txt = self.font.render(opt, True, (255, 255, 255))
            rect = txt.get_rect(center=(SCREEN_W // 2, 250 + i * 80))
            anim = {
                "scale": 0.8,
                "target": 1.0,
                "hover_scale": 1.08,
                "press_scale": 0.95,
                "speed": 8.0,
                "reveal_delay": i * 120,
                "revealed": False
            }
            self.buttons.append([opt, txt, rect, anim])

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for opt, txt, rect, anim in self.buttons:
                if rect.collidepoint(mx, my):
                    anim["scale"] = anim.get("press_scale", 0.95)  # click tap animation
                    if opt == "JUGAR":
                        self.game.change_screen(LevelSelectScreen(self.game))
                    elif opt == "SALIR":
                        pygame.quit();
                        sys.exit()

    def update(self, dt):
        # lazy start timer (could be time since screen created)
        self._start_time += dt
        self.matrix.update(dt)
        mx, my = pygame.mouse.get_pos()
        for i in range(len(self.buttons)):
            opt, txt, rect, anim = self.buttons[i]
            # reveal
            if not anim["revealed"] and self._start_time >= anim["reveal_delay"]:
                anim["revealed"] = True
                anim["scale"] = 0.8
            if not anim["revealed"]:
                continue
            # hover target
            target = anim["hover_scale"] if rect.collidepoint(mx, my) else 1.0
            # interpolate
            factor = min(1.0, anim.get("speed", 8.0) * dt / 1000.0)
            anim["scale"] = anim["scale"] + (target - anim["scale"]) * factor

    def render(self, surf):
        # Dibujar fondo del menú si existe
        if self.menu_background:
            surf.blit(self.menu_background, (0, 0))
        else:
            surf.fill((30, 30, 50))
        # Matrix rain overlay
        self.matrix.draw(surf, alpha=85)  # más oscuro/sutil
        title = self.font.render("NetDefenders", True, (255, 255, 255))
        draw_glitch_text_surf(surf, title, (SCREEN_W // 2, 100), scale=1.0, glitch_prob=0.12)

        mx, my = pygame.mouse.get_pos()
        for opt, txt, rect, anim in self.buttons:
            if not anim.get("revealed", True):
                continue
            scale = anim.get("scale", 1.0)
            color = (255, 255, 100) if rect.collidepoint(mx, my) else (200, 200, 200)
            txt = self.font.render(opt, True, color)
            # scale text surface
            tw, th = txt.get_size()
            draw_w = int(tw * scale)
            draw_h = int(th * scale)
            txt_scaled = pygame.transform.smoothscale(txt, (draw_w, draw_h))
            draw_x = rect.centerx - draw_w // 2
            draw_y = rect.centery - draw_h // 2
            surf.blit(txt_scaled, (draw_x, draw_y))


# --------- (NUEVA) Pantalla del Nivel 1 con Sistema de Correos ----------
class Level1Screen(BaseLevelScreen):
    def __init__(self, game):
        # --- NARRATIVA DEL TUTOR MEJORADA ---
        narrative_lines = [
            "Tutor: Conectando a la Red de Simulación... ¿Listo, analista?",
            "Tutor: Escenario: Eres el analista de seguridad principal de 'Synergy Corp'. Tu 'Integridad de Red' es tu vida.",
            "Tutor: Detectamos un intruso (míralo). Está lanzando un ataque de phishing para robar credenciales y dañar los sistemas.",
            "Tutor: Tu trabajo: Analiza la bandeja de entrada. Reporta lo malicioso para dañar al hacker. Responde o elimina lo legítimo.",
            "Tutor: ¡Cuidado! Si respondes a un correo falso o reportas uno legítimo, ¡pierdes integridad de red!",
            "Tutor: Revisa siempre 3 cosas: El **Dominio** (quién envía), el **Texto** (qué pide) y el **Logo** (si es auténtico).",
            "Tutor: Soy tu 'Blue Team Lead' (Jefe de Defensa). Te guiaré si fallas. ¡Iniciando simulación... ya!"
        ]
        super().__init__(game, narrative_lines)
        
        # NUEVO: Configurar nivel 1 en sistema de estadísticas
        self.game.player_stats.set_current_level(1)
        self.game.player_stats.reset_session_stats()
    
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
        self.max_apariciones_tutor = 3 # Límite de ayudas del tutor

        # --- BURLAS DEL HACKER (en español) ---
        self.burla_hacker = ""
        self.burla_hacker_timer = 0
        self.lista_burlas = [
            "¡Clic! Gracias por las llaves del reino. 🔑",
            "Jaja, ¿paranoico? Estás bloqueando a tus compañeros.",
            "Demasiado fácil. Tu 'firewall' mental tiene agujeros.",
            "¡Ups! ¿Eso dolió? 💥",
            "Sigue intentando, 'genio'."
        ]

        # Sistema de correos
        self.correos = self.cargar_correos()
        self.correo_actual_index = 0
        self.correo_abierto = None
        self.estado = "narrativa_inicial"
        self.razones_seleccionadas = []
        self.accion_pendiente = None
        # UI OO: bandeja e email panel
        self.inbox = Inbox(self.correos, self.font, self.small_font)
        self.email_panel = None

        # proveedor de rect del hacker para EmailPanel
        self._get_hacker_rect = lambda: self.hacker_sprite.rect

        # Texto animado (solo para narrativa)
        self.texto_actual = ""
        self.texto_completo = ""
        self.tiempo_escritura = 0
        self.velocidad_escritura = 30

        # Iniciar animación de la primera línea de narrativa
        if self.show_narrative and self.narrative_lines:
            self.iniciar_texto_animado(self.narrative_lines[self.narrative_index])

        self.last_feedback = ""
        # Nota: El botón 'Volver' dentro del correo ahora lo gestiona EmailPanel

    def _player_won(self):
        # Ganó si el hacker llegó a 0 o si al finalizar tiene más vida
        if self.hacker_logic.vida <= 0:
            return True
        if self.protagonista.vida <= 0:
            return False
        # En empate o fin por correos, gana si tiene más vida
        return self.protagonista.vida > self.hacker_logic.vida

    def cargar_correos(self):
        # --- PAQUETE DE CORREOS MEJORADO Y EXTENDIDO ---
        # (Asegúrate de tener los logos en 'assets/logos/')
        return [
            # MALICIOSO 1 (Falla: Dominio y Texto)
            Correo(
                es_legitimo=False,
                tipo_malicioso="contraseñas",
                remitente="soporte@microsft-office.com",
                asunto="ALERTA DE SEGURIDAD: Su contraseña ha caducado",
                contenido="Estimado usuario,\n\nDetectamos un inicio de sesión inusual en su cuenta de Microsoft desde una ubicación no reconocida. Como medida de precaución, hemos caducado su contraseña.\n\nPara evitar la pérdida de acceso permanente a sus archivos de OneDrive y Outlook, debe verificar su cuenta inmediatamente.\n\nHaga clic en el siguiente enlace para actualizar su contraseña:\n[Enlace a portal falso]\n\nSi no completa esta acción en las próximas 2 horas, su cuenta será suspendida de forma permanente según nuestros términos de servicio. Apreciamos su cooperación.\n\nGracias,\nEquipo de Soporte de Microsoft",
                razones_correctas=["Dominio", "Texto"],
                logo_path="assets/logos/microsoft.png", # Usa el logo real para confundir
                inbox_icon_path="assets/logos/microsoft_inbox.png",
            ),

            # LEGÍTIMO 1 (Interno)
            Correo(
                es_legitimo=True,
                tipo_malicioso=None,
                remitente="rh@synergy-corp.com",
                asunto="Recordatorio: Nuevas políticas de vacaciones",
                contenido="Hola equipo,\n\nEste es un recordatorio amistoso de que las nuevas políticas de solicitud de vacaciones entrarán en vigor el próximo mes, como se discusitó en la reunión trimestral.\n\nEl cambio principal es que todas las solicitudes de más de 3 días deben enviarse con al menos 30 días de antelación.\n\nPueden revisar el documento completo (PDF) en el portal interno de RH. No es necesario que respondan a este correo.\n\nQue tengan un buen día.\n\nSaludos,\nEl equipo de Recursos Humanos",
                razones_correctas=[],
                logo_path="assets/logos/synergy_corp.png", # Logo legítimo de la empresa
                inbox_icon_path="assets/logos/synergy_corp_rh_inbox.png",
            ),

            # MALICIOSO 2 (Falla: Logo y Texto)
            Correo(
                es_legitimo=False,
                tipo_malicioso="dinero",
                remitente="notificaciones@ganadores-lotto.net",
                asunto="¡Felicidades! Ha ganado $500,000",
                contenido="¡Es su día de suerte! ¡Ha ganado la Lotería Internacional!\n\nSu dirección de correo electrónico fue seleccionada al azar de una base de datos global como el ganador de nuestro sorteo mensual. ¡Ha ganado $500,000 USD!\n\nPara reclamar su premio, solo debe cubrir una pequeña 'tasa de procesamiento y transferencia bancaria internacional' de $20. Este pago es requerido por las regulaciones financieras.\n\nHaga clic aquí para pagar la tasa y recibir su premio. La oferta caduca en 24 horas.\n\n¡Felicidades de nuevo!",
                razones_correctas=["Logo", "Texto"],
                logo_path="assets/logos/loteria_falsa.png", # Un logo que se vea poco profesional
                inbox_icon_path="assets/logos/loteria_falsa_inbox.png",
            ),

            # LEGÍTIMO 2 (Externo)
            Correo(
                es_legitimo=True,
                tipo_malicioso=None,
                remitente="notificaciones@linkedin.com",
                asunto="Tienes una nueva invitación para conectar",
                contenido="Hola Analista,\n\nJuan Pérez, quien es Gerente de Ciberseguridad en la empresa 'CyberCore Dynamics', te ha enviado una invitación para conectar en LinkedIn.\n\nExpandir tu red profesional es una excelente forma de mantenerte al día con las tendencias de la industria.\n\nPor favor, inicia sesión de forma segura en el sitio web o la aplicación oficial de LinkedIn para ver el perfil de Juan y aceptar o rechazar la invitación.\n\nSaludos,\nEl equipo de LinkedIn",
                razones_correctas=[],
                logo_path="assets/logos/linkedin.png", # Logo legítimo
                inbox_icon_path="assets/logos/linkedin_inbox.png",
            ),

            # MALICIOSO 3 (Falla: Texto PURO) - El más difícil
            Correo(
                es_legitimo=False,
                tipo_malicioso="contraseñas",
                remitente="it-soporte@synergy-corp.com",
                asunto="[ACCIÓN REQUERIDA] Migración de buzón de correo",
                contenido="Hola empleado,\n\nDebido a una actualización crítica de seguridad, estamos migrando todos los buzones al nuevo servidor en la nube (Exchange vNext) esta noche a las 2:00 AM.\n\nPara asegurar que sus correos, contactos y calendario se sincronicen correctamente, necesitamos que valide sus credenciales en el portal de migración ANTES de esa hora.\n\nPor favor, inicie sesión en el portal de migración con su correo y contraseña habituales:\n[Enlace a portal de phishing]\n\nSi no completa esta validación, su buzón podría corromperse y perdería sus datos. Entendemos que esto es urgente, pero es necesario para proteger la red.\n\nGracias,\nDepartamento de IT.",
                razones_correctas=["Texto"],
                logo_path="assets/logos/synergy_corp.png", # Logo legítimo de la empresa
                inbox_icon_path="assets/logos/synergy_corp_it_inbox.png",
            ),

            # MALICIOSO 4 (Spear Phishing del Hacker) - Correo final
            Correo(
                es_legitimo=False,
                tipo_malicioso="spear_phishing",
                remitente="unknown_user@192.168.1.10", # Una IP como remitente
                asunto="Te estoy viendo...",
                contenido="\nLindo simulador, 'analista'.\n\nHas estado fastidioso reportando mis correos. Pero todos cometen un error...\n\n¿Estás seguro de que ese correo de 'RH' era realmente de RH? ¿O el de 'IT'? Qué paranoia.\n\nSigue jugando a proteger tu red. Sigue haciendo clic en 'Reportar'.\n\nNos veremos en el mundo real. ;-)\n\n- BlackHat",
                razones_correctas=["Dominio", "Texto"],
                logo_path=None, # Sin logo
                inbox_icon_path="assets/logos/hacker_inbox.png"
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
            "dinero": 5,
            "contraseñas": 10,
            "suscripciones": 3,
            "spear_phishing": 15 # Daño extra por el correo del hacker
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
        
        hubo_error_accion = False

        # Preparar detalles de errores para stats
        mistake_details = {}
        
        # Procesar razones si es eliminar o reportar
        daño_razones = 0
        bonus_hacker = 0
        if razones_seleccionadas is not None:
            daño_razones, bonus_hacker = self.procesar_razones(correo, razones_seleccionadas, accion)
            
            # Detectar errores en las razones marcadas
            if correo.es_legitimo == False:  # Si era malicioso (phishing)
                razones_correctas_set = set(correo.razones_correctas)
                razones_seleccionadas_set = set(razones_seleccionadas)
                
                # Contar errores: opciones marcadas cuando NO debían (de más) + opciones NO marcadas cuando SÍ debían (de menos)
                mistake_details["logo"] = ("Logo" in razones_seleccionadas_set and "Logo" not in razones_correctas_set) or \
                                         ("Logo" not in razones_seleccionadas_set and "Logo" in razones_correctas_set)
                mistake_details["dominio"] = ("Dominio" in razones_seleccionadas_set and "Dominio" not in razones_correctas_set) or \
                                            ("Dominio" not in razones_seleccionadas_set and "Dominio" in razones_correctas_set)
                mistake_details["texto"] = ("Texto" in razones_seleccionadas_set and "Texto" not in razones_correctas_set) or \
                                          ("Texto" not in razones_seleccionadas_set and "Texto" in razones_correctas_set)
            else:  # Si era legítimo pero lo marcaron como amenaza (falso positivo)
                # Cualquier razón marcada en un correo legítimo es un error
                razones_seleccionadas_set = set(razones_seleccionadas)
                mistake_details["logo"] = "Logo" in razones_seleccionadas_set
                mistake_details["dominio"] = "Dominio" in razones_seleccionadas_set
                mistake_details["texto"] = "Texto" in razones_seleccionadas_set

            # Aplicar daño por razones incorrectas
            if daño_razones > 0:
                self.protagonista.recibir_daño(daño_razones)
                hubo_error_accion = True # Error en razones también cuenta

            # Aplicar bonus al hacker por razones correctas
            if bonus_hacker > 0:
                self.hacker_logic.vida = max(0, self.hacker_logic.vida - bonus_hacker)

        # NUEVO: Registrar en sistema de estadísticas automáticamente con detalles
        es_amenaza = not correo.es_legitimo
        respuesta_correcta = resultado["correcto"] and daño_razones == 0
        self.game.player_stats.analyze_email(es_amenaza, respuesta_correcta, mistake_details)

        # Aplicar daño base de la acción
        if resultado["daño_jugador"] > 0:
            self.protagonista.recibir_daño(resultado["daño_jugador"])
            hubo_error_accion = True

        if resultado["daño_hacker"] > 0:
            self.hacker_logic.vida = max(0, self.hacker_logic.vida - resultado["daño_hacker"])

        self.mostrar_feedback_completo(resultado, daño_razones, bonus_hacker, razones_seleccionadas)

        # --- GESTIÓN DE TUTOR Y BURLAS ---
        if hubo_error_accion:
            self.mostrar_tutor_si_corresponde(correo, accion, razones_seleccionadas)
            self.mostrar_burla_hacker(resultado) # Mostrar burla si hubo error
        
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
                mensajes.append(f"Error: Perdiste {resultado['daño_jugador']} puntos de integridad")

        if daño_razones > 0:
            mensajes.append(f"Razones incorrectas: -{daño_razones} integridad")

        if bonus_hacker > 0:
            mensajes.append(f"Razones correctas: -{bonus_hacker} al hacker")

        self.last_feedback = " | ".join(mensajes)

    def mostrar_tutor_si_corresponde(self, correo, accion, razones_seleccionadas):
        if self.contador_tutor < self.max_apariciones_tutor:
            self.contador_tutor += 1
            self.tutor_visible = True
            self.tutor_mensaje = self.obtener_mensaje_tutor(correo, accion, razones_seleccionadas)
            self.tutor_timer = 0 # Reinicia timer para 3 segundos

    def mostrar_burla_hacker(self, resultado_accion):
        if resultado_accion["correcto"]: # No mostrar burla si acertó
            return
            
        import random
        # Elegir burla específica si es posible
        if resultado_accion.get("accion") == "reportar" and self.correo_abierto.es_legitimo:
             self.burla_hacker = "Jaja, ¿paranoico? Estás bloqueando a tus compañeros."
        elif resultado_accion.get("accion") == "responder" and not self.correo_abierto.es_legitimo:
             self.burla_hacker = "¡Clic! Gracias por las llaves del reino. 🔑"
        else:
             self.burla_hacker = random.choice(self.lista_burlas)
        
        self.burla_hacker_timer = 3000 # Mostrar burla por 3 segundos

    def obtener_mensaje_tutor(self, correo, accion, razones_seleccionadas):
        if correo.es_legitimo and accion != "responder":
            return "¡Cuidado! Ese correo era legítimo. Reportarlos crea 'falsos positivos' y perdemos tiempo valioso."

        elif not correo.es_legitimo and accion == "responder":
            if correo.tipo_malicioso == "contraseñas":
                return "¡Alerta Roja! Nunca entregues tus credenciales. Ningún admin te pedirá tu contraseña por correo. Fíjate en el dominio."
            elif correo.tipo_malicioso == "dinero":
                return "¡Error! Caíste en una estafa de 'pago por adelantado'. Nadie regala dinero así. ¡Debes reportarlo!"
            else:
                return "Revisa siempre los términos antes de aceptar nada. Era una trampa."

        elif razones_seleccionadas is not None and not correo.es_legitimo:
            razones_incorrectas = set(razones_seleccionadas) - set(correo.razones_correctas)
            razones_faltantes = set(correo.razones_correctas) - set(razones_seleccionadas)
            
            if razones_incorrectas:
                return f"Buen instinto, pero te equivocaste en el 'por qué'. '{list(razones_incorrectas)[0]}' no era la falla aquí."
            if razones_faltantes:
                 return f"Detectaste el correo, pero te faltó notar la falla en '{list(razones_faltantes)[0]}'. Los detalles importan."

        return "Sigue practicando tu criterio de seguridad."

    def siguiente_correo(self):
        self.correo_abierto = None
        self.estado = "esperando_correo"
        self.razones_seleccionadas = []

        # Verificar si quedan correos por procesar
        correos_pendientes = [c for c in self.correos if not c.procesado]
        if not correos_pendientes or self.protagonista.vida <= 0 or self.hacker_logic.vida <= 0:
            self.estado = "fin_juego"
            # NUEVO: Completar nivel y guardar estadísticas
            self.game.player_stats.complete_level()

    def iniciar_texto_animado(self, texto):
        self.texto_completo = texto
        # Mostrar chaletazamente el primer carácter para evitar un frame en blanco
        self.texto_actual = texto[0] if texto else ""
        self.tiempo_escritura = 0

    def handle_event(self, event):
        # --- (MODIFICADO) El panel de email ahora maneja MOUSEWHEEL y otros ---
        if self.estado == "correo_abierto" and self.email_panel:
            # Pasar todos los eventos no-click al panel por si los necesita (rueda, soltar, mover)
            if event.type == pygame.MOUSEWHEEL:
                self.email_panel.handle_event(event) # Enviar evento de rueda
                return # Consumir evento
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.email_panel.handle_event(event) # Enviar evento de soltar
                return # Consumir evento
            if event.type == pygame.MOUSEMOTION:
                self.email_panel.handle_event(event) # Enviar evento de mover (para drag)
                return # Consumir evento

        # --- (NUEVO) La bandeja de entrada maneja scroll y drag del scrollbar ---
        if self.estado == "esperando_correo" and not self.show_narrative:
            if event.type in (pygame.MOUSEWHEEL, pygame.MOUSEMOTION) or (event.type == pygame.MOUSEBUTTONUP and event.button == 1):
                # Forward para scroll/drag de scrollbar
                self.inbox.handle_event(event, hacker_rect=self.hacker_sprite.rect)
                # No hacer return aquí para permitir otros manejos si fuera necesario

        # Procesar solo el clic izquierdo
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        mx, my = event.pos

        if self.estado == "narrativa_inicial":
            # Si el texto aún se está animando, completarlo al hacer click (no avanzar todavía)
            if len(self.texto_actual) < len(self.texto_completo):
                self.texto_actual = self.texto_completo
                return

            # Si el texto ya está completo, avanzar a la siguiente línea
            if not self.avanzar_narrativa():
                self.estado = "esperando_correo"
            else:
                # Iniciar animación para la siguiente línea
                self.iniciar_texto_animado(self.narrative_lines[self.narrative_index])
            return

        if self.tutor_visible:
            self.tutor_visible = False
            return

        if self.estado == "fin_juego":
            # Desbloquear Nivel 2 si ganó el jugador
            if self._player_won():
                self.game.unlocked_levels["Nivel 2"] = True
            self.game.change_screen(MenuScreen(self.game))
            return

        if self.estado == "esperando_correo":
            # Delegar selección al Inbox OO (usa rect del hacker para layout seguro)
            seleccionado = self.inbox.handle_event(event, hacker_rect=self.hacker_sprite.rect)
            if seleccionado:
                self.correo_abierto = seleccionado
                self.estado = "correo_abierto"
                # Crear panel con botones de imagen
                self.email_panel = EmailPanel(self.correo_abierto, self.small_font, self.option_font, self._get_hacker_rect)

        elif self.estado == "correo_abierto":
            # Delegar al EmailPanel OO
            if self.email_panel:
                res = self.email_panel.handle_event(event) # Enviar solo el MOUSEBUTTONDOWN
                if res:
                    if res.get("type") == "back":
                        self.siguiente_correo()
                        self.email_panel = None
                        return
                    if res.get("type") == "accion":
                        # Acciones directas (p.ej. Responder)
                        self.procesar_respuesta_completa(res.get("accion"))
                        self.email_panel = None
                        return
                    if res.get("type") == "reasons_confirm":
                        self.procesar_respuesta_completa(res.get("accion"), res.get("razones", []))
                        self.email_panel = None
                        return

    def update(self, dt):
        self.hacker_sprite.update(dt)

        # Actualizar texto animado (solo narrativa inicial)
        if (self.show_narrative and self.estado == "narrativa_inicial") and len(self.texto_actual) < len(self.texto_completo):
            self.tiempo_escritura += dt
            if self.tiempo_escritura >= self.velocidad_escritura:
                self.tiempo_escritura = 0
                self.texto_actual += self.texto_completo[len(self.texto_actual)]

        # Actualizar email panel (ahora maneja drag)
        if self.estado == "correo_abierto" and self.email_panel:
            self.email_panel.update(dt)

        # Actualizar tutor
        if self.tutor_visible:
            self.tutor_timer += dt
            if self.tutor_timer >= 5000: # Aumentado a 5 segundos
                self.tutor_visible = False
                
        # Actualizar timer de burla del hacker
        if self.burla_hacker_timer > 0:
            self.burla_hacker_timer -= dt
            if self.burla_hacker_timer <= 0:
                self.burla_hacker = ""

    def render(self, surf):
        surf.fill((0, 0, 0))

        # Dibujar personajes
        self.protagonista_sprite.draw(surf)
        self.hacker_sprite.draw(surf)

        # Dibujar burla del hacker
        if self.burla_hacker_timer > 0 and self.burla_hacker:
            # Caja de diálogo para el hacker
            hacker_box_w = 280
            hacker_box_h = 80
            hacker_box_rect = pygame.Rect(
                self.hacker_sprite.rect.left - hacker_box_w - 10, 
                self.hacker_sprite.rect.top, 
                hacker_box_w, 
                hacker_box_h
            )
            # Asegurarse que no se salga por la izquierda
            if hacker_box_rect.left < 10:
                hacker_box_rect.left = 10
                
            pygame.draw.rect(surf, (50, 20, 20), hacker_box_rect, border_radius=10)
            pygame.draw.rect(surf, (200, 100, 100), hacker_box_rect, 2, border_radius=10)
            
            # Envolver texto de la burla
            wrapped_lines = self._wrap_text(self.burla_hacker, self.small_font, hacker_box_rect.width - 20)
            y_offset = 10
            for line in wrapped_lines:
                taunt_text = self.small_font.render(line, True, (255, 200, 200))
                surf.blit(taunt_text, (hacker_box_rect.x + 10, hacker_box_rect.y + y_offset))
                y_offset += taunt_text.get_height() + 5

        # Dibujar tutor si está visible
        if self.tutor_visible:
            self.tutor_sprite.draw(surf)
            tutor_box = pygame.Rect(SCREEN_W - 600, SCREEN_H - 120, 380, 80)
            pygame.draw.rect(surf, (30, 30, 60), tutor_box, border_radius=10)
            pygame.draw.rect(surf, (100, 100, 200), tutor_box, 2, border_radius=10)
            # Envolver texto para que quepa en la caja
            wrapped_lines = self._wrap_text(self.tutor_mensaje, self.small_font, tutor_box.width - 20) # -20 por el padding

            y_offset = 10
            for line in wrapped_lines:
                tutor_text = self.small_font.render(line, True, (255, 255, 255))
                surf.blit(tutor_text, (tutor_box.x + 10, tutor_box.y + y_offset))
                y_offset += tutor_text.get_height() + 5 # Añadir espacio entre líneas

        # HUD: vidas
        vida_txt = self.font.render(f"Integridad Red: {self.protagonista.vida}", True, (200, 200, 200))
        surf.blit(vida_txt, (20, 20))
        hack_txt = self.font.render(f"Progreso Hacker: {self.hacker_logic.vida}", True, (200, 200, 200))
        surf.blit(hack_txt, (SCREEN_W - 280, 20)) # Ajustado para el texto

        # Bandeja de entrada (solo cuando no hay narrativa ni correo abierto)
        if self.estado in ("esperando_correo",) and not self.show_narrative:
            self.inbox.render(surf, hacker_rect=self.hacker_sprite.rect)

        # Narrativa inicial
        if self.show_narrative:
            box = pygame.Rect(100, 150, 600, 300)
            pygame.draw.rect(surf, (20, 20, 40), box, border_radius=10)
            pygame.draw.rect(surf, (100, 100, 200), box, 2, border_radius=10)

            # Mostrar narrativa con animación de texto (usar self.texto_actual)
            # Usar self.texto_actual si no está vacío, si no, el texto completo (para el primer frame)
            texto_a_mostrar = self.texto_actual if self.texto_actual else self.narrative_lines[self.narrative_index]
            wrapped_lines = self._wrap_text(texto_a_mostrar, self.small_font, box.width - 40)

            y_offset = 20
            for wrapped in wrapped_lines:
                text_surf = self.small_font.render(wrapped, True, (255, 255, 255))
                surf.blit(text_surf, (box.x + 20, box.y + y_offset))
                y_offset += text_surf.get_height() + 5

            continue_text = self.small_font.render("Haz clic para continuar", True, (200, 200, 200))
            surf.blit(continue_text, (box.centerx - continue_text.get_width() // 2, box.bottom - 30))

        # Correo abierto
        elif self.estado == "correo_abierto" and self.correo_abierto:
            if self.email_panel:
                self.email_panel.render(surf)

        # Selección de razones
        # La selección de razones ahora se maneja dentro de EmailPanel

        # Fin del juego
        elif self.estado == "fin_juego":
            fin_box = pygame.Rect(200, 200, 400, 200)
            pygame.draw.rect(surf, (20, 20, 40), fin_box, border_radius=10)
            pygame.draw.rect(surf, (100, 100, 200), fin_box, 2, border_radius=10)
            
            mensaje = "" # Mensaje por defecto
            
            if self.protagonista.vida <= 0:
                mensaje = "¡Brecha de Seguridad! El hacker te ha derrotado."
            elif self.hacker_logic.vida <= 0:
                mensaje = "¡Red Asegurada! Has derrotado al hacker."
            else:
                # Todos los correos procesados - gana el que tenga más vida
                if self.protagonista.vida > self.hacker_logic.vida:
                    mensaje = "¡Nivel Completado! Has procesado todo y ganado."
                elif self.hacker_logic.vida > self.protagonista.vida:
                    mensaje = "¡Brecha de Seguridad! El hacker ganó por puntos."
                else:
                    mensaje = "¡Empate! La red está comprometida."

            # Envolver mensaje final
            wrapped_lines = self._wrap_text(mensaje, self.option_font, fin_box.width - 40)
            y_offset = fin_box.centery - (len(wrapped_lines) * self.option_font.get_height()) // 2 - 10
            
            for line in wrapped_lines:
                text = self.option_font.render(line, True, (255, 255, 255))
                surf.blit(text, (fin_box.centerx - text.get_width() // 2, y_offset))
                y_offset += text.get_height() + 5

            continue_text = self.small_font.render("Haz clic para volver al menú", True, (200, 200, 200))
            surf.blit(continue_text, (fin_box.centerx - continue_text.get_width() // 2, fin_box.bottom - 40))

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
        # NUEVO: Sistema de estadísticas del jugador
        self.player_stats = PlayerStats("Jugador1")
        
        # Estado de desbloqueo de niveles (memoria de sesión)
        self.unlocked_levels = {
            "Nivel 1": True,
            "Nivel 2": False,
            "Nivel 3": False,
        }
        # Ruta a la fuente TTF del proyecto (archivo 'texto.ttf' en la raíz del proyecto)
        self.font_path = "texto.ttf"
        try:
            self.font = pygame.font.Font(self.font_path, 18)
        except Exception:
            self.font = pygame.font.SysFont("Consolas", 18)
        # Fade transition state
        self._next_screen = None
        self._fade_time = 350  # ms total for each phase
        self._fade_timer = 0
        self._fade_phase = None  # None | 'out' | 'in'
        self._fade_surface = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

    def change_screen(self, new_screen):
        # Start fade-out if already running, else switch immediately before intro
        if self._fade_phase is None:
            self._next_screen = new_screen
            self._fade_phase = 'out'
            self._fade_timer = 0
        else:
            # If a fade already ongoing, just set next screen
            self._next_screen = new_screen

    def set_screen(self, screen):
        """Cambio inmediato, sin transición de fade global"""
        self.current = screen
        self._next_screen = None
        self._fade_phase = None
        self._fade_timer = 0

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

            # Handle fade transitions
            if self._fade_phase is not None:
                self._fade_timer += dt
                t = min(1.0, self._fade_timer / self._fade_time)
                if self._fade_phase == 'out':
                    # fade to black
                    alpha = int(255 * t)
                    self._fade_surface.fill((0, 0, 0, alpha))
                    self.screen.blit(self._fade_surface, (0, 0))
                    if t >= 1.0:
                        # switch screen and start fade-in
                        if self._next_screen is not None:
                            self.current = self._next_screen
                            self._next_screen = None
                        self._fade_phase = 'in'
                        self._fade_timer = 0
                elif self._fade_phase == 'in':
                    # from black to scene
                    alpha = int(255 * (1.0 - t))
                    self._fade_surface.fill((0, 0, 0, alpha))
                    self.screen.blit(self._fade_surface, (0, 0))
                    if t >= 1.0:
                        self._fade_phase = None

            # Mostrar FPS en esquina superior derecha
            fps_text = self.font.render(f"FPS: {int(self.clock.get_fps())}", True, (255, 255, 0))
            fps_x = SCREEN_W - fps_text.get_width() - 10
            self.screen.blit(fps_text, (fps_x, 10))

            pygame.display.flip()

        pygame.quit()


# --------- Main ---------
if __name__ == "__main__":
    Game().run()