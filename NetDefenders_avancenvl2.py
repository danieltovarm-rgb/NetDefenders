import math
import pygame, sys, random
import numpy as np
from abc import ABC, abstractmethod
from moviepy import VideoFileClip
# NUEVO: Importar sistema de estadísticas
from stats_system import PlayerStats, ScoreManager, MistakeLog, Level2GameManager

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

# Helper para obtener rutas de assets
def get_asset_path(relative_path):
    """Obtiene la ruta absoluta de un archivo en assets"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, relative_path)

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
        max_lines = float('inf')  # Infinitas líneas
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
        return lines  # Devuelve la lista completa si no hay límite de altura

    # Limita a la cantidad de líneas que caben (esto solo se ejecuta si max_h NO es None)
    return lines[:int(max_lines)]

# --------- Clase base para pantallas
class Screen(ABC):
    def __init__(self, game):
        self.game = game

    @abstractmethod
    def handle_event(self, event): ...

    @abstractmethod
    def update(self, dt): ...

    @abstractmethod
    def render(self, surf): ...

# --------- Utilidades visuales (Matrix Rain y Glitch Text) ----------
class MatrixRain:
    def __init__(self, width, height, font_name="Consolas", font_size=16, charset=None, column_density=1.0,
                 font_path=None):
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


# --------- Pantalla de Victoria (Video + Mensaje) ----------
class VictoryVideoScreen(Screen):
    def __init__(self, game, mensaje_adicional=""):
        super().__init__(game)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        video_path = os.path.join(script_dir, "ganaste.mp4")
        
        self.video = VideoFileClip(video_path)
        self.frame_gen = self.video.iter_frames(fps=25, dtype='uint8')
        self.video_finished = False
        self.mensaje_adicional = mensaje_adicional
        
        # Fuentes para mensaje
        try:
            self.font_titulo = pygame.font.Font(game.font_path, 36)
            self.font_mensaje = pygame.font.Font(game.font_path, 22)
        except:
            self.font_titulo = pygame.font.SysFont("Arial", 36, bold=True)
            self.font_mensaje = pygame.font.SysFont("Arial", 22)

    def handle_event(self, event):
        if self.video_finished and (event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN):
            self.video.close()
            self.game.change_screen(MenuScreen(self.game))

    def update(self, dt):
        if self.video_finished:
            return
        try:
            frame = next(self.frame_gen)
            frame_surface = pygame.surfarray.make_surface(np.transpose(frame, (1, 0, 2)))
            frame_surface = pygame.transform.scale(frame_surface, (SCREEN_W, SCREEN_H))
            self.current_frame = frame_surface
        except StopIteration:
            self.video_finished = True

    def render(self, surf):
        if hasattr(self, "current_frame") and not self.video_finished:
            surf.blit(self.current_frame, (0, 0))
        elif self.video_finished:
            # Pantalla de mensaje después del video
            surf.fill((10, 20, 30))
            
            # Título
            titulo = self.font_titulo.render("¡FELICIDADES!", True, (0, 255, 100))
            surf.blit(titulo, (SCREEN_W // 2 - titulo.get_width() // 2, 150))
            
            # Mensajes alentadores
            mensajes = [
                "Has completado exitosamente la misión de ciberseguridad.",
                "Tu conocimiento y habilidades han protegido el sistema.",
                "",
                "La ciberseguridad es esencial en el mundo digital.",
                "Cada virus eliminado es un paso hacia un entorno más seguro.",
                "",
                self.mensaje_adicional if self.mensaje_adicional else "",
                "",
                "Presiona cualquier tecla para continuar..."
            ]
            
            y_offset = 250
            for msg in mensajes:
                if msg:
                    texto = self.font_mensaje.render(msg, True, (200, 200, 200))
                    surf.blit(texto, (SCREEN_W // 2 - texto.get_width() // 2, y_offset))
                y_offset += 35


# --------- Pantalla de Derrota (Video + Mensaje) ----------
class DefeatVideoScreen(Screen):
    def __init__(self, game, razon_derrota=""):
        super().__init__(game)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        video_path = os.path.join(script_dir, "perdiste.mp4")
        
        self.video = VideoFileClip(video_path)
        self.frame_gen = self.video.iter_frames(fps=25, dtype='uint8')
        self.video_finished = False
        self.razon_derrota = razon_derrota
        
        # Fuentes para mensaje
        try:
            self.font_titulo = pygame.font.Font(game.font_path, 36)
            self.font_mensaje = pygame.font.Font(game.font_path, 22)
        except:
            self.font_titulo = pygame.font.SysFont("Arial", 36, bold=True)
            self.font_mensaje = pygame.font.SysFont("Arial", 22)

    def handle_event(self, event):
        if self.video_finished and (event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN):
            self.video.close()
            self.game.change_screen(MenuScreen(self.game))

    def update(self, dt):
        if self.video_finished:
            return
        try:
            frame = next(self.frame_gen)
            frame_surface = pygame.surfarray.make_surface(np.transpose(frame, (1, 0, 2)))
            frame_surface = pygame.transform.scale(frame_surface, (SCREEN_W, SCREEN_H))
            self.current_frame = frame_surface
        except StopIteration:
            self.video_finished = True

    def render(self, surf):
        if hasattr(self, "current_frame") and not self.video_finished:
            surf.blit(self.current_frame, (0, 0))
        elif self.video_finished:
            # Pantalla de mensaje después del video
            surf.fill((30, 10, 10))
            
            # Título
            titulo = self.font_titulo.render("¡NO TE RINDAS!", True, (255, 100, 100))
            surf.blit(titulo, (SCREEN_W // 2 - titulo.get_width() // 2, 150))
            
            # Mensajes alentadores
            mensajes = [
                self.razon_derrota if self.razon_derrota else "El sistema ha sido comprometido.",
                "",
                "Cada error es una oportunidad de aprendizaje.",
                "La ciberseguridad requiere práctica y perseverancia.",
                "",
                "Los profesionales cometen errores, pero aprenden de ellos.",
                "¡Vuelve a intentarlo! Ahora tienes más conocimiento.",
                "",
                "Presiona cualquier tecla para volver al menú..."
            ]
            
            y_offset = 250
            for msg in mensajes:
                if msg:
                    texto = self.font_mensaje.render(msg, True, (220, 220, 220))
                    surf.blit(texto, (SCREEN_W // 2 - texto.get_width() // 2, y_offset))
                y_offset += 35


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
            self.background = pygame.image.load(get_asset_path("assets/fondo_niveles 2.png")).convert()
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
            for p in (get_asset_path("assets/boton_volver final 2.png"), get_asset_path("assets/volver_button.png")):
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
        # Crear dos botones imagen: nivel1, nivel2
        # Mantener la proporción original 622x233 al escalar los botones
        orig_w, orig_h = 689, 735
        aspect = orig_w / orig_h
        # Altura objetivo reducida para botones más pequeños
        btn_h = 240
        btn_w = int(btn_h * aspect)  # ancho manteniendo proporción

        # Espacio entre centros de botones (layout simétrico con 2 botones)
        spacing = btn_w + 50
        center_y = SCREEN_H // 2
        center_x = SCREEN_W // 2

        # Solo 2 botones centrados simétricamente
        centers = [ (center_x - spacing // 2, center_y), (center_x + spacing // 2, center_y) ]

        names = ["Nivel 1", "Nivel 2"]
        # Estado dinámico de Nivel 2
        n2_unlocked = bool(self.game.unlocked_levels.get("Nivel 2", False))
        enabled_flags = [True, n2_unlocked]
        # Elegir imágenes; para Nivel 2 usar locked/unlocked con fallback
        n2_img_primary = get_asset_path("assets/nivel2_unlocked.png" if n2_unlocked else "assets/nivel2_locked.png")
        # Fallbacks conocidos del repo anterior
        n2_img_fallback = get_asset_path("assets/malware_unlocked.png" if n2_unlocked else "assets/malware_locked.png")
        image_paths = [
            get_asset_path("assets/nivel1_unlocked final 3.png"),
            n2_img_primary
        ]

        for i in range(2):
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
        stats_y = SCREEN_H - 120
        
        # Fondo semitransparente para las estadísticas (más compacto para 2 niveles)
        stats_bg = pygame.Surface((280, 110), pygame.SRCALPHA)
        stats_bg.fill((0, 0, 0, 150))
        surf.blit(stats_bg, (stats_x, stats_y))
        
        # Título
        title_text = self.small_font.render("MEJORES PUNTAJES", True, (255, 215, 0))
        surf.blit(title_text, (stats_x + 10, stats_y + 10))
        
        # Mostrar puntajes por nivel
        y_offset = 40
        for level_num in [1, 2]:
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
            self.menu_background = pygame.image.load(get_asset_path("assets/fondo_menu.png")).convert()
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
                logo_path=get_asset_path("assets/logos/microsoft.png"), # Usa el logo real para confundir
                inbox_icon_path=get_asset_path("assets/logos/microsoft_inbox.png"),
            ),

            # LEGÍTIMO 1 (Interno)
            Correo(
                es_legitimo=True,
                tipo_malicioso=None,
                remitente="rh@synergy-corp.com",
                asunto="Recordatorio: Nuevas políticas de vacaciones",
                contenido="Hola equipo,\n\nEste es un recordatorio amistoso de que las nuevas políticas de solicitud de vacaciones entrarán en vigor el próximo mes, como se discusitó en la reunión trimestral.\n\nEl cambio principal es que todas las solicitudes de más de 3 días deben enviarse con al menos 30 días de antelación.\n\nPueden revisar el documento completo (PDF) en el portal interno de RH. No es necesario que respondan a este correo.\n\nQue tengan un buen día.\n\nSaludos,\nEl equipo de Recursos Humanos",
                razones_correctas=[],
                logo_path=get_asset_path("assets/logos/synergy_corp.png"), # Logo legítimo de la empresa
                inbox_icon_path=get_asset_path("assets/logos/synergy_corp_rh_inbox.png"),
            ),

            # MALICIOSO 2 (Falla: Logo y Texto)
            Correo(
                es_legitimo=False,
                tipo_malicioso="dinero",
                remitente="notificaciones@ganadores-lotto.net",
                asunto="¡Felicidades! Ha ganado $500,000",
                contenido="¡Es su día de suerte! ¡Ha ganado la Lotería Internacional!\n\nSu dirección de correo electrónico fue seleccionada al azar de una base de datos global como el ganador de nuestro sorteo mensual. ¡Ha ganado $500,000 USD!\n\nPara reclamar su premio, solo debe cubrir una pequeña 'tasa de procesamiento y transferencia bancaria internacional' de $20. Este pago es requerido por las regulaciones financieras.\n\nHaga clic aquí para pagar la tasa y recibir su premio. La oferta caduca en 24 horas.\n\n¡Felicidades de nuevo!",
                razones_correctas=["Logo", "Texto"],
                logo_path=get_asset_path("assets/logos/loteria_falsa.png"), # Un logo que se vea poco profesional
                inbox_icon_path=get_asset_path("assets/logos/loteria_falsa_inbox.png"),
            ),

            # LEGÍTIMO 2 (Externo)
            Correo(
                es_legitimo=True,
                tipo_malicioso=None,
                remitente="notificaciones@linkedin.com",
                asunto="Tienes una nueva invitación para conectar",
                contenido="Hola Analista,\n\nJuan Pérez, quien es Gerente de Ciberseguridad en la empresa 'CyberCore Dynamics', te ha enviado una invitación para conectar en LinkedIn.\n\nExpandir tu red profesional es una excelente forma de mantenerte al día con las tendencias de la industria.\n\nPor favor, inicia sesión de forma segura en el sitio web o la aplicación oficial de LinkedIn para ver el perfil de Juan y aceptar o rechazar la invitación.\n\nSaludos,\nEl equipo de LinkedIn",
                razones_correctas=[],
                logo_path=get_asset_path("assets/logos/linkedin.png"), # Logo legítimo
                inbox_icon_path=get_asset_path("assets/logos/linkedin_inbox.png"),
            ),

            # MALICIOSO 3 (Falla: Texto PURO) - El más difícil
            Correo(
                es_legitimo=False,
                tipo_malicioso="contraseñas",
                remitente="it-soporte@synergy-corp.com",
                asunto="[ACCIÓN REQUERIDA] Migración de buzón de correo",
                contenido="Hola empleado,\n\nDebido a una actualización crítica de seguridad, estamos migrando todos los buzones al nuevo servidor en la nube (Exchange vNext) esta noche a las 2:00 AM.\n\nPara asegurar que sus correos, contactos y calendario se sincronicen correctamente, necesitamos que valide sus credenciales en el portal de migración ANTES de esa hora.\n\nPor favor, inicie sesión en el portal de migración con su correo y contraseña habituales:\n[Enlace a portal de phishing]\n\nSi no completa esta validación, su buzón podría corromperse y perdería sus datos. Entendemos que esto es urgente, pero es necesario para proteger la red.\n\nGracias,\nDepartamento de IT.",
                razones_correctas=["Texto"],
                logo_path=get_asset_path("assets/logos/synergy_corp.png"), # Logo legítimo de la empresa
                inbox_icon_path=get_asset_path("assets/logos/synergy_corp_it_inbox.png"),
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
                inbox_icon_path=get_asset_path("assets/logos/hacker_inbox.png")
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


# --------- Clase Protagonista (Visual) ----------
class ProtagonistaSprite:
    def __init__(self, x, y):
        self.image = pygame.image.load(get_asset_path("assets/protagonista/idle.png")).convert_alpha()
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
            img = pygame.image.load(get_asset_path(path)).convert_alpha()
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
            image_paths=[get_asset_path("assets/btn_responder.png"), get_asset_path("assets/btn_reply.png")], label_text="Responder", font=font_buttons)
        self.btn_eliminar = ImageButton((0, 0), (160, 44),
            image_paths=[get_asset_path("assets/btn_eliminar.png"), get_asset_path("assets/btn_delete.png")], label_text="Eliminar", font=font_buttons)
        self.btn_reportar = ImageButton((0, 0), (160, 44),
            image_paths=[get_asset_path("assets/btn_reportar.png"), get_asset_path("assets/btn_report.png")], label_text="Reportar", font=font_buttons)

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


# =============================================================================
# CLASE ARCHIVOSISTEMA PARA GESTIÓN COMPLETA DE ARCHIVOS
# =============================================================================
class ArchivoSistema:
    """Clase que representa un archivo del sistema con todos sus metadatos y estado"""

    def __init__(self, nombre, extension, tamaño, fecha_mod, permisos, es_infectado=False,
                 tipo_virus=None, probabilidad_infeccion=0, sintoma_asociado=None, image_path=None):
        self.nombre = nombre
        self.extension = extension
        self.extension_real = self._detectar_extension_real(nombre, extension)
        self.tamaño = tamaño
        self.fecha_mod = fecha_mod
        self.permisos = permisos
        self.es_infectado = es_infectado
        self.tipo_virus = tipo_virus
        self.probabilidad_infeccion = probabilidad_infeccion
        self.sintoma_asociado = sintoma_asociado
        self.image_path = image_path
        self.en_cuarentena = False
        self.eliminado = False
        self.rect = None  # Se asignará cuando se coloque en una habitación

    def _detectar_extension_real(self, nombre, extension_visible):
        """Detecta extensiones dobles o engañosas"""
        if '.' in nombre:
            partes = nombre.split('.')
            if len(partes) > 2:
                return f".{partes[-1]}"
            elif len(partes) == 2:
                return f".{partes[1]}"
        return extension_visible

    def obtener_metadatos(self):
        """Retorna metadatos formateados para mostrar en UI"""
        return {
            "Nombre": self.nombre,
            "Extensión": self.extension,
            "Extensión Real": self.extension_real,
            "Tamaño": self.tamaño,
            "Fecha Modificación": self.fecha_mod,
            "Permisos": self.permisos,
            "Estado": "INFECTADO" if self.es_infectado else "LIMPIO",
            "Tipo Virus": self.tipo_virus if self.es_infectado else "Ninguno",
            "Probabilidad": f"{self.probabilidad_infeccion}%" if self.es_infectado else "0%"
        }

    def es_sospechoso(self):
        """Determina si el archivo tiene características sospechosas"""
        # Extensiones dobles
        if self.extension != self.extension_real:
            return True
        # Tamaños incongruentes
        if self.extension in [".txt", ".ini"] and "MB" in self.tamaño:
            return True
        if self.extension == ".exe" and "KB" not in self.tamaño:
            return True
        # Horas extrañas de modificación
        if "04:30" in self.fecha_mod or "03:15" in self.fecha_mod:
            return True
        return False


# =============================================================================
# CLASE GESTOR VIRUS PARA CONTROLAR INFECCIONES Y SÍNTOMAS
# =============================================================================
class GestorVirus:
    """Gestiona los virus, síntomas y su relación con archivos"""

    def __init__(self):
        self.tipos_virus = {
            "ransomware": {"sintoma": "pantalla_bloqueada", "daño": 25},
            "adware": {"sintoma": "popups", "daño": 15},
            "miner": {"sintoma": "ralentizacion", "daño": 20},
            "spyware": {"sintoma": "teclas_fantasma", "daño": 10}
        }
        self.sintomas_activos = {
            "ralentizacion": False,
            "popups": False,
            "pantalla_bloqueada": False,
            "teclas_fantasma": False
        }
        self.archivos_infectados = {}  # archivo_id -> tipo_virus

    def activar_sintoma(self, tipo_virus):
        """Activa el síntoma asociado a un tipo de virus"""
        if tipo_virus in self.tipos_virus:
            sintoma = self.tipos_virus[tipo_virus]["sintoma"]
            self.sintomas_activos[sintoma] = True

    def desactivar_sintoma(self, tipo_virus):
        """Desactiva el síntoma asociado a un tipo de virus"""
        if tipo_virus in self.tipos_virus:
            sintoma = self.tipos_virus[tipo_virus]["sintoma"]
            self.sintomas_activos[sintoma] = False

    def verificar_sintoma_por_archivo(self, archivo):
        """Verifica si un archivo está causando algún síntoma activo"""
        if archivo.es_infectado and archivo.tipo_virus:
            sintoma = self.tipos_virus.get(archivo.tipo_virus, {}).get("sintoma")
            return self.sintomas_activos.get(sintoma, False)
        return False

    def hay_sintomas_activos(self):
        """Verifica si hay algún síntoma activo"""
        return any(self.sintomas_activos.values())


# ========== SISTEMA EDUCATIVO NIVEL 2 ==========

class MensajeOverlay:
    """Representa un mensaje educativo en el overlay"""
    def __init__(self, tipo, titulo, bullets, sabias_que="", prioridad=60, callback=None):
        self.tipo = tipo  # 'quiz', 'tutor_refuerzo', 'tutor_error', 'tutor_tip'
        self.titulo = titulo
        self.bullets = bullets  # Lista de 2-3 strings
        self.sabias_que = sabias_que
        self.prioridad = prioridad
        self.callback = callback  # Función a llamar al cerrar
        self.timestamp = pygame.time.get_ticks()


class QuizManager:
    """Gestiona los quizzes educativos del Nivel 2"""
    def __init__(self):
        # Banco de quizzes hardcodeado
        self.quizzes = {
            'ransomware': {
                'pregunta': "¿Qué señal del sistema indica ransomware?",
                'opciones': [
                    "CPU al 100% en reposo",
                    "Cifrado y notas de rescate",  # CORRECTA
                    "Barras de navegador nuevas"
                ],
                'correcta': 1,
                'tip': "El cifrado + notas son rasgos clave de ransomware."
            },
            'adware': {
                'pregunta': "Tras instalar 'gratis', aparece... ¿qué sugiere adware?",
                'opciones': [
                    "Teclas fantasma",
                    "Pop-ups/barras no deseadas",  # CORRECTA
                    "Archivos cifrados"
                ],
                'correcta': 1,
                'tip': "Los pop-ups y barras se asocian a adware."
            },
            'miner': {
                'pregunta': "¿Qué te hace sospechar de un cripto-minero?",
                'opciones': [
                    "100% CPU en idle",  # CORRECTA
                    "Notas de rescate",
                    "Correos pidiendo contraseñas"
                ],
                'correcta': 0,
                'tip': "Miner explota CPU/GPU de forma constante."
            },
            'spyware': {
                'pregunta': "¿Qué indicio encaja con spyware?",
                'opciones': [
                    "Teclas fantasma + exfiltración",  # CORRECTA
                    "Pop-ups",
                    "Extensiones cifradas"
                ],
                'correcta': 0,
                'tip': "Spyware registra/extrae información."
            }
        }
    
    def obtener_quiz(self, tipo_malware):
        """Retorna el quiz para un tipo de malware"""
        return self.quizzes.get(tipo_malware)


class GestorMensajesEducativos:
    """Gestiona los mensajes educativos por síntoma/malware"""
    def __init__(self):
        self.mensajes = {
            'ransomware': {
                'sintoma': 'pantalla_bloqueada',
                'tip_bullets': [
                    "Bloquea el acceso y exige pago.",
                    "Señal: notas RECOVER/README. Cambios masivos de extensión.",
                    "Evita pagar; prioriza aislar/quitar."
                ],
                'sabias_que': "El ransomware puede cifrar archivos en minutos. Las copias de seguridad son tu mejor defensa.",
                'refuerzo_bullets': [
                    "Correcto: aislaste/eliminaste el origen del bloqueo.",
                    "Buena práctica: copias de seguridad + lista de procesos confiables."
                ]
            },
            'adware': {
                'sintoma': 'popups',
                'tip_bullets': [
                    "Anuncios intrusivos tras instaladores 'gratis'.",
                    "Señal: barras de navegador, ejecutables genéricos.",
                    "Evita instalar 'bundles'."
                ],
                'sabias_que': "El adware se instala junto con software 'gratuito'. Lee siempre los permisos de instalación.",
                'refuerzo_bullets': [
                    "Aislar/quitar corta los popups.",
                    "Revisa descargas sospechosas."
                ]
            },
            'miner': {
                'sintoma': 'ralentizacion',
                'tip_bullets': [
                    "Usa CPU/GPU para minar criptomonedas.",
                    "Señal: 100% CPU en reposo, procesos con nombres 'de sistema'.",
                    "Consulta uso CPU antes de borrar."
                ],
                'sabias_que': "Los mineros pueden generar calor excesivo y dañar tu hardware a largo plazo.",
                'refuerzo_bullets': [
                    "La limpieza recupera rendimiento.",
                    "Actualiza y limita ejecución desconocida."
                ]
            },
            'spyware': {
                'sintoma': 'teclas_fantasma',
                'tip_bullets': [
                    "Roba pulsaciones/pantalla.",
                    "Señal: envío de datos inusual.",
                    "Desconfía de adjuntos ejecutables."
                ],
                'sabias_que': "El spyware puede capturar contraseñas y datos bancarios sin que lo notes.",
                'refuerzo_bullets': [
                    "Eliminaste el keylogger: cambio de credenciales recomendado.",
                    "Activa 2FA cuando sea posible."
                ]
            }
        }
        
        # Mensajes de error puntuales
        self.errores = {
            'limpiar_seguro': {
                'titulo': "⚠️ Error: Archivo seguro eliminado",
                'bullets': [
                    "Confirma extensión real y horario de modificación.",
                    "No borres archivos de sistema sin evidencia clara."
                ],
                'sabias_que': "Eliminar archivos del sistema puede causar inestabilidad. Verifica dos veces antes de actuar."
            },
            'cuarentena_seguro': {
                'titulo': "⚠️ Falso positivo",
                'bullets': [
                    "Este archivo era seguro.",
                    "Valida el tipo de archivo y su ubicación antes de aislar."
                ],
                'sabias_que': "Los falsos positivos pueden interrumpir operaciones legítimas. Analiza con cuidado."
            }
        }
    
    def obtener_tip(self, tipo_malware):
        """Obtiene el tip educativo para cuando se activa un síntoma"""
        datos = self.mensajes.get(tipo_malware, {})
        return {
            'titulo': f"🔍 Detectado: {tipo_malware.capitalize()}",
            'bullets': datos.get('tip_bullets', []),
            'sabias_que': datos.get('sabias_que', '')
        }
    
    def obtener_refuerzo(self, tipo_malware):
        """Obtiene el refuerzo educativo tras limpiar/aislar"""
        datos = self.mensajes.get(tipo_malware, {})
        return {
            'titulo': f"✅ Bien hecho",
            'bullets': datos.get('refuerzo_bullets', []),
            'sabias_que': f"Síntoma '{datos.get('sintoma', '')}' desactivado correctamente."
        }
    
    def obtener_error(self, tipo_error):
        """Obtiene mensaje de error educativo"""
        return self.errores.get(tipo_error, {
            'titulo': '⚠️ Error',
            'bullets': ['Verifica antes de actuar.'],
            'sabias_que': ''
        })


class OverlayEducativo:
    """Sistema de overlay con cola de prioridades y cooldowns"""
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.cola_mensajes = []  # Cola con prioridades
        self.mensaje_actual = None
        self.ultimo_mensaje_tiempo = 0
        self.cooldowns = {
            'quiz': 0,
            'tutor_refuerzo': 8000,  # 8 segundos
            'tutor_error': 6000,      # 6 segundos
            'tutor_tip': 10000        # 10 segundos
        }
        self.ultimo_por_tipo = {}  # tipo -> timestamp
        
        # Configuración visual
        self.ancho = 600
        self.alto = 350
        self.x = (screen_w - self.ancho) // 2
        self.y = (screen_h - self.alto) // 2 + 30
        
        # Fuentes
        try:
            self.font_titulo = pygame.font.Font(get_asset_path("texto.ttf"), 24)
            self.font_bullet = pygame.font.Font(get_asset_path("texto.ttf"), 18)
            self.font_pequeño = pygame.font.Font(get_asset_path("texto.ttf"), 16)
        except:
            self.font_titulo = pygame.font.SysFont("Arial", 24, bold=True)
            self.font_bullet = pygame.font.SysFont("Arial", 18)
            self.font_pequeño = pygame.font.SysFont("Arial", 16, italic=True)
    
    def puede_mostrar(self, tipo):
        """Verifica si se puede mostrar un mensaje de este tipo (cooldown)"""
        cooldown = self.cooldowns.get(tipo, 0)
        if cooldown == 0:  # Quiz no tiene cooldown
            return True
        
        ahora = pygame.time.get_ticks()
        ultimo = self.ultimo_por_tipo.get(tipo, 0)
        return (ahora - ultimo) >= cooldown
    
    def agregar_mensaje(self, mensaje):
        """Agrega un mensaje a la cola con prioridad"""
        if not self.puede_mostrar(mensaje.tipo):
            return False
        
        # Insertar en cola ordenada por prioridad (mayor primero)
        self.cola_mensajes.append(mensaje)
        self.cola_mensajes.sort(key=lambda m: m.prioridad, reverse=True)
        
        # Si no hay mensaje actual, mostrar inmediatamente
        if self.mensaje_actual is None:
            self.mostrar_siguiente()
        
        return True
    
    def mostrar_siguiente(self):
        """Muestra el siguiente mensaje de la cola"""
        if self.cola_mensajes:
            self.mensaje_actual = self.cola_mensajes.pop(0)
            self.ultimo_por_tipo[self.mensaje_actual.tipo] = pygame.time.get_ticks()
        else:
            self.mensaje_actual = None
    
    def cerrar_actual(self):
        """Cierra el mensaje actual y ejecuta callback si existe"""
        if self.mensaje_actual:
            if self.mensaje_actual.callback:
                self.mensaje_actual.callback()
            self.mensaje_actual = None
            self.mostrar_siguiente()
    
    def esta_activo(self):
        """Verifica si hay un overlay visible"""
        return self.mensaje_actual is not None
    
    def update(self, dt):
        """Actualiza el sistema de overlay (cooldowns, etc)"""
        # Por ahora solo necesitamos que exista el método
        # Los cooldowns se manejan con pygame.time.get_ticks()
        pass
    
    def handle_event(self, event):
        """Maneja eventos de click/ESC para cerrar overlay"""
        if not self.esta_activo():
            return False
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.cerrar_actual()
            return True
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Click dentro del overlay
            overlay_rect = pygame.Rect(self.x, self.y, self.ancho, self.alto)
            if overlay_rect.collidepoint(event.pos):
                # Si es quiz, no cerrar con click genérico (tiene sus propios botones)
                if self.mensaje_actual.tipo != 'quiz':
                    self.cerrar_actual()
                return True
        
        return False
    
    def render(self, surf):
        """Renderiza el overlay actual"""
        if not self.esta_activo():
            return
        
        # Fondo semitransparente oscuro
        overlay_bg = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay_bg.fill((0, 0, 0, 180))
        surf.blit(overlay_bg, (0, 0))
        
        # Caja del mensaje
        caja_rect = pygame.Rect(self.x, self.y, self.ancho, self.alto)
        pygame.draw.rect(surf, (30, 35, 45), caja_rect, border_radius=10)
        pygame.draw.rect(surf, (0, 200, 255), caja_rect, 3, border_radius=10)
        
        # Título
        titulo_surf = self.font_titulo.render(self.mensaje_actual.titulo, True, (255, 255, 100))
        titulo_x = self.x + (self.ancho - titulo_surf.get_width()) // 2
        surf.blit(titulo_surf, (titulo_x, self.y + 20))
        
        # Bullets
        y_offset = self.y + 70
        for bullet in self.mensaje_actual.bullets:
            bullet_surf = self.font_bullet.render(f"• {bullet}", True, (220, 220, 220))
            surf.blit(bullet_surf, (self.x + 30, y_offset))
            y_offset += 35
        
        # ¿Sabías que...?
        if self.mensaje_actual.sabias_que:
            y_offset += 15
            sabias_titulo = self.font_bullet.render("¿Sabías que...?", True, (100, 200, 255))
            surf.blit(sabias_titulo, (self.x + 30, y_offset))
            y_offset += 30
            
            # Wrap del texto
            palabras = self.mensaje_actual.sabias_que.split()
            linea = ""
            for palabra in palabras:
                test_linea = linea + palabra + " "
                if self.font_pequeño.size(test_linea)[0] < self.ancho - 60:
                    linea = test_linea
                else:
                    linea_surf = self.font_pequeño.render(linea, True, (180, 180, 180))
                    surf.blit(linea_surf, (self.x + 40, y_offset))
                    y_offset += 25
                    linea = palabra + " "
            
            if linea:
                linea_surf = self.font_pequeño.render(linea, True, (180, 180, 180))
                surf.blit(linea_surf, (self.x + 40, y_offset))
        
        # Instrucción para cerrar (si no es quiz)
        if self.mensaje_actual.tipo != 'quiz':
            cerrar_text = self.font_pequeño.render("Click o ESC para continuar", True, (150, 150, 150))
            cerrar_x = self.x + (self.ancho - cerrar_text.get_width()) // 2
            surf.blit(cerrar_text, (cerrar_x, self.y + self.alto - 35))


# --------- Nivel 2: Análisis y limpieza de PC ----------
class Level2Screen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.state = "tutor_inicial"  # Cambiado de "narrativa_inicial" a "tutor_inicial"
        
        # Mensaje del tutor
        self.tutor_mensaje = [
            "¡Bienvenido al Nivel 2: Defensa Avanzada!",
            "",
            "Tu misión es proteger el sistema de múltiples amenazas:",
            "- RANSOMWARE: Cifra archivos y bloquea la pantalla",
            "- ADWARE: Muestra anuncios molestos",
            "- MINER: Usa tu CPU para minar criptomonedas",
            "- SPYWARE: Registra tus teclas y roba información",
            "",
            "Herramientas disponibles:",
            "• INSPECCIONAR: Ver detalles del archivo (gratis)",
            "• ESCANEAR: Detectar virus (10 recursos por archivo, 15 por carpeta)",
            "• CUARENTENA: Aislar virus temporalmente (8 recursos)",
            "• LIMPIAR: Eliminar virus permanentemente (gratis si es virus)",
            "",
            "¡CUIDADO! Los síntomas aparecerán si no actúas rápido.",
            "Elimina TODOS los virus antes de quedarte sin recursos.",
            "",
            "Presiona ENTER para comenzar..."
        ]

        # Sistema de archivos y virus
        self.gestor_virus = GestorVirus()
        self.archivo_seleccionado = None
        self.accion_en_progreso = None
        self.tiempo_accion = 0
        self.duracion_escaneo = 3000

        # Sistema de recursos
        self.recursos = 100
        self.recursos_display = 100.0  # Para animación suave del número
        self.recursos_anterior = 100  # Para detectar cambios
        self.costos_acciones = {
            "inspeccionar": 0,
            "escanear_archivo": 10,
            "escanear_carpeta": 15,
            "cuarentena": 8,
            "limpiar_malware": 0,
            "limpiar_seguro": 12
        }

        # Estructura de directorios completa
        self.directory_structure = {
            "C:/": ["Users", "Program Files", "Windows", "Temp"],
            "C:/Users": ["Admin", "Public"],
            "C:/Users/Admin": ["Documents", "Downloads", "AppData"],
            "C:/Users/Admin/Documents": [],
            "C:/Users/Admin/Downloads": [],
            "C:/Users/Admin/AppData": ["Local", "Roaming"],
            "C:/Users/Admin/AppData/Local": ["Temp"],
            "C:/Program Files": ["Common Files", "Internet Explorer"],
            "C:/Windows": ["System32", "SysWOW64", "Temp"],
            "C:/Windows/System32": [],
            "C:/Temp": []
        }

        # Directorio actual y anterior
        self.current_directory = "C:/"
        self.previous_directory = None

        self.game_time = 0
        self.door_interaction_distance = 50

        # HUD configuration
        margin = 10
        panel_top = 50
        log_height = 120  # Aumentado de 80 a 120

        available_width = SCREEN_W - (margin * 4)
        left_width = int(available_width * 0.25)
        right_width = int(available_width * 0.25)
        center_width = available_width - left_width - right_width

        panel_height = SCREEN_H - panel_top - log_height - (margin * 2)

        self.hud_rects = {
            "left_files": pygame.Rect(margin, panel_top, left_width, panel_height),
            "center_preview": pygame.Rect(margin * 2 + left_width, panel_top, center_width, panel_height),
            "right_tools": pygame.Rect(SCREEN_W - right_width - margin, panel_top, right_width, panel_height),
            "bottom_log": pygame.Rect(margin, SCREEN_H - log_height, SCREEN_W - (margin * 2), log_height - margin),
            "resource_bar": pygame.Rect(margin, 30, SCREEN_W - (margin * 2), 10)
        }

        # Colores del HUD
        self.hud_colors = {
            "background": (20, 25, 35),
            "border": (40, 50, 70),
            "highlight": (0, 255, 255),
            "text": (220, 220, 220),
            "resource": (0, 255, 0),
            "door": (0, 150, 200),
            "door_highlight": (255, 255, 0)
        }

        # Imágenes para puertas (1:1). Si no existen, se usa fallback (rectángulo).
        self.door_image_path = get_asset_path(os.path.join("assets", "doors", "door.png"))
        self.back_door_image_path = get_asset_path(os.path.join("assets", "doors", "back_door.png"))
        # Cache unificado para todas las imágenes por (ruta, tamaño)
        self._image_cache = {}

        # Imágenes para las herramientas (iconos de acciones)
        self.tool_images = {
            "Inspeccionar": get_asset_path(os.path.join("assets", "tools", "inspeccionar.png")),
            "Escanear": get_asset_path(os.path.join("assets", "tools", "escanear.png")),
            "Cuarentena": get_asset_path(os.path.join("assets", "tools", "cuarentena.png")),
            "Limpiar": get_asset_path(os.path.join("assets", "tools", "limpiar.png"))
        }

        # Panel central de referencia para puertas
        center_panel = self.hud_rects["center_preview"]

        # Definir puertas reubicadas: cuadrícula horizontal en esquina superior izquierda del panel central.
        # Además, la puerta "Back" se sitúa centrada en la parte inferior del panel central.
        door_width, door_height = 72, 72  # Tamaño para puertas normales (más pequeñas)
        back_door_width, back_door_height = 96, 96  # Tamaño para puerta Back (más grande)
        dw, dh = door_width, door_height
        tlx = center_panel.left + 20  # margen interno izquierdo
        # MOVER CUADRÍCULA UN POCO MÁS ABAJO PARA NO CHOCAR CON TEXTO DEL SISTEMA
        tly = center_panel.top + 50   # margen interno superior ajustado (+30)
        gap = 8
        usable_w = center_panel.w - 40  # márgenes internos totales (20 izquierda, 20 derecha)
        cols = max(1, usable_w // (dw + gap))

        def rect_at(index):
            row = index // cols
            col = index % cols
            x = tlx + col * (dw + gap)
            y = tly + row * (dh + gap)
            return pygame.Rect(x, y, dw, dh)

        def back_rect():
            # Posicionar en esquina inferior izquierda del panel con tamaño más grande
            bx = center_panel.left + 20
            by = center_panel.bottom - back_door_height - 20
            return pygame.Rect(bx, by, back_door_width, back_door_height)

        self.doors = {
            "C:/": {
                "Users": (rect_at(0), "C:/Users"),
                "Program Files": (rect_at(1), "C:/Program Files"),
                "Windows": (rect_at(2), "C:/Windows"),
                "Temp": (rect_at(3), "C:/Temp")
            },
            "C:/Users": {
                "Admin": (rect_at(0), "C:/Users/Admin"),
                "Public": (rect_at(1), "C:/Users/Public"),
                "Back": (back_rect(), "C:/")
            },
            "C:/Users/Admin": {
                "Documents": (rect_at(0), "C:/Users/Admin/Documents"),
                "Downloads": (rect_at(1), "C:/Users/Admin/Downloads"),
                "AppData": (rect_at(2), "C:/Users/Admin/AppData"),
                "Back": (back_rect(), "C:/Users")
            },
            "C:/Users/Admin/Documents": {
                "Back": (back_rect(), "C:/Users/Admin")
            },
            "C:/Users/Admin/Downloads": {
                "Back": (back_rect(), "C:/Users/Admin")
            },
            "C:/Users/Admin/AppData": {
                "Local": (rect_at(0), "C:/Users/Admin/AppData/Local"),
                "Roaming": (rect_at(1), "C:/Users/Admin/AppData/Roaming"),
                "Back": (back_rect(), "C:/Users/Admin")
            },
            "C:/Users/Admin/AppData/Local": {
                "Temp": (rect_at(0), "C:/Users/Admin/AppData/Local/Temp"),
                "Back": (back_rect(), "C:/Users/Admin/AppData")
            },
            "C:/Program Files": {
                "Common Files": (rect_at(0), "C:/Program Files/Common Files"),
                "Internet Explorer": (rect_at(1), "C:/Program Files/Internet Explorer"),
                "Back": (back_rect(), "C:/")
            },
            "C:/Windows": {
                "System32": (rect_at(0), "C:/Windows/System32"),
                "SysWOW64": (rect_at(1), "C:/Windows/SysWOW64"),
                "Temp": (rect_at(2), "C:/Windows/Temp"),
                "Back": (back_rect(), "C:/")
            },
            "C:/Windows/System32": {
                "Back": (back_rect(), "C:/Windows")
            },
            "C:/Users/Public": {
                "Back": (back_rect(), "C:/Users")
            },
            "C:/Users/Admin/AppData/Roaming": {
                "Back": (back_rect(), "C:/Users/Admin/AppData")
            },
            "C:/Users/Admin/AppData/Local/Temp": {
                "Back": (back_rect(), "C:/Users/Admin/AppData/Local")
            },
            "C:/Program Files/Common Files": {
                "Back": (back_rect(), "C:/Program Files")
            },
            "C:/Program Files/Internet Explorer": {
                "Back": (back_rect(), "C:/Program Files")
            },
            "C:/Windows/SysWOW64": {
                "Back": (back_rect(), "C:/Windows")
            },
            "C:/Windows/Temp": {
                "Back": (back_rect(), "C:/Windows")
            },
            "C:/Temp": {
                "Back": (back_rect(), "C:/")
            }
        }

        # Estado del HUD
        self.active_panel = "center_preview"
        self.hud_elements = {
            "left_files": [],
            "tools": ["Inspeccionar", "Escanear", "Cuarentena", "Limpiar"]
        }

        # Fuentes
        # Cargar fuente personalizada desde archivo texto.ttf (fallback a default si falla)
        try:
            custom_font_title = pygame.font.Font(get_asset_path("texto.ttf"), 24)
            custom_font_normal = pygame.font.Font(get_asset_path("texto.ttf"), 20)
            custom_font_small = pygame.font.Font(get_asset_path("texto.ttf"), 16)
        except Exception:
            custom_font_title = pygame.font.Font(None, 24)
            custom_font_normal = pygame.font.Font(None, 20)
            custom_font_small = pygame.font.Font(None, 16)

        self.fonts = {
            "title": custom_font_title,
            "normal": custom_font_normal,
            "small": custom_font_small
        }

        # Botones de herramientas
        self.tool_button_rects = []
        tool_rect = self.hud_rects["right_tools"].copy()
        tool_rect.y += 35
        tool_rect.x += 10
        tool_rect.width -= 20

        for tool in self.hud_elements["tools"]:
            button_rect = pygame.Rect(tool_rect.x, tool_rect.y, tool_rect.width, 50)
            self.tool_button_rects.append(button_rect)
            tool_rect.y += 60

        # Variables de estado del juego
        self.max_mistakes = 5
        self.mistakes_made = 0
        self.total_viruses = 0  # Se calculará después
        self.viruses_cleaned = 0
        self.victory_condition = False
        self.game_over_reason = ""

        # Estado de transición
        self.in_transition = False
        self.transition_time = 0.0
        self.transition_duration = 0.5
        self.transition_target = None
        self.transition_start_pos = pygame.math.Vector2(0, 0)
        self.transition_end_pos = pygame.math.Vector2(0, 0)

        # Interacción
        self.near_door = None
        self.door_highlight_time = 0.0
        self.pressed_door = None
        self.pressed_file = None

        # Archivos
        self.files_in_room = {}
        self.file_interaction_distance = 40
        self.near_file = None
        self.file_highlight_time = 0.0
        # Estado previo de la tecla E para disparo solo en flanco
        self._e_prev = False

        # Mensajes
        self.current_message = "Log: Esperando acciones..."
        self.message_duration = 3.0
        self.effect_timers = {"message": 0.0}
        
        # Sistema de scroll para el log
        self.log_lines = []
        self.log_scroll_offset = 0
        self.log_max_scroll = 0
        self.log_scrollbar_dragging = False
        self.log_drag_start_y = 0
        self.log_drag_start_offset = 0

        # =============================================================================
        # GENERACIÓN DE ARCHIVOS CON METADATOS COMPLETOS (MÁS DE 10 ARCHIVOS)
        # =============================================================================
        cp_x, cp_y = self.hud_rects["center_preview"].centerx, self.hud_rects["center_preview"].centery
        # Los archivos ahora tienen el mismo tamaño que las puertas normales
        file_w, file_h = door_width, door_height  # 72x72, igual que puertas normales

        # Generar archivos para cada directorio - MÁS DE 10 ARCHIVOS TOTAL
        self.files_in_room = {
            "C:/": [
                ArchivoSistema("readme.txt", ".txt", "1 KB", "15/03/2024 10:30", "Lectura", False, 
                               image_path=get_asset_path(os.path.join("assets", "files", "txt.png"))),
                ArchivoSistema("config.sys", ".sys", "2 KB", "14/03/2024 14:15", "Sistema", False,
                               image_path=get_asset_path(os.path.join("assets", "files", "sys.png"))),
                ArchivoSistema("autoexec.bat", ".bat", "1 KB", "13/03/2024 09:20", "Ejecución", False,
                               image_path=get_asset_path(os.path.join("assets", "files", "bat.png")))
            ],
            "C:/Users/Admin/Documents": [
                ArchivoSistema("document1.doc", ".doc", "250 KB", "16/03/2024 11:00", "Lectura/Escritura", False,
                               image_path=get_asset_path(os.path.join("assets", "files", "doc.png"))),
                ArchivoSistema("budget.xlsx", ".xlsx", "450 KB", "16/03/2024 10:00", "Lectura/Escritura", False,
                               image_path=get_asset_path(os.path.join("assets", "files", "xlsx.png"))),
                ArchivoSistema("presentation.ppt", ".ppt", "1.2 MB", "15/03/2024 16:30", "Lectura", False,
                               image_path=get_asset_path(os.path.join("assets", "files", "ppt.png")))
            ],
            "C:/Users/Admin/Downloads": [
                ArchivoSistema("GIMP_Installer.exe", ".exe", "120 MB", "16/03/2024 09:45", "Ejecución", False,
                               image_path=get_asset_path(os.path.join("assets", "files", "exe.png"))),
                ArchivoSistema("Free_Game.exe", ".exe", "420 KB", "15/03/2024 04:30", "Ejecución", True, "adware", 85,
                               "popups", image_path=get_asset_path(os.path.join("assets", "files", "exe.png"))),
                ArchivoSistema("invoice_2025.pdf", ".pdf", "2.3 MB", "16/03/2024 11:20", "Lectura", False,
                               image_path=get_asset_path(os.path.join("assets", "files", "pdf.png"))),
                ArchivoSistema("crypto_miner.exe", ".exe", "320 KB", "15/03/2024 03:15", "Ejecución", True, "miner", 92,
                               "ralentizacion", image_path=get_asset_path(os.path.join("assets", "files", "exe.png"))),
                ArchivoSistema("movie.mp4", ".mp4", "1.5 GB", "14/03/2024 20:15", "Lectura", False,
                               image_path=get_asset_path(os.path.join("assets", "files", "mp4.png")))
            ],
            "C:/Windows/System32": [
                ArchivoSistema("kernel32.dll", ".dll", "1.2 MB", "10/03/2024 08:00", "Sistema", False,
                               image_path=get_asset_path(os.path.join("assets", "files", "dll.png"))),
                ArchivoSistema("x_virus.exe", ".exe", "520 KB", "14/03/2024 04:30", "Ejecución", True, "ransomware", 95,
                               "pantalla_bloqueada", image_path=get_asset_path(os.path.join("assets", "files", "exe.png"))),
                ArchivoSistema("user32.dll", ".dll", "890 KB", "10/03/2024 08:00", "Sistema", False,
                               image_path=get_asset_path(os.path.join("assets", "files", "dll.png"))),
                ArchivoSistema("spy_tool.exe", ".exe", "280 KB", "15/03/2024 02:45", "Ejecución", True, "spyware", 78,
                               "teclas_fantasma", image_path=get_asset_path(os.path.join("assets", "files", "exe.png"))),
                ArchivoSistema("winlogon.exe", ".exe", "1.1 MB", "10/03/2024 08:00", "Sistema", False,
                               image_path=get_asset_path(os.path.join("assets", "files", "exe.png")))
            ],
            "C:/Temp": [
                ArchivoSistema("temp_file.tmp", ".tmp", "15 KB", "16/03/2024 12:05", "Lectura/Escritura", False,
                               image_path=get_asset_path(os.path.join("assets", "files", "temp.png"))),
                ArchivoSistema("adware_bundle.exe", ".exe", "650 KB", "15/03/2024 04:30", "Ejecución", True, "adware",
                               88, "popups", image_path=get_asset_path(os.path.join("assets", "files", "exe.png"))),
                ArchivoSistema("logfile.log", ".log", "3 KB", "16/03/2024 12:10", "Lectura", False,
                               image_path=get_asset_path(os.path.join("assets", "files", "log.png")))
            ],
            "C:/Program Files": [
                ArchivoSistema("program1.exe", ".exe", "5.2 MB", "13/03/2024 12:00", "Ejecución", False,
                               image_path=get_asset_path(os.path.join("assets", "files", "exe.png"))),
                ArchivoSistema("program2.dll", ".dll", "1.8 MB", "13/03/2024 12:00", "Sistema", False,
                               image_path=get_asset_path(os.path.join("assets", "files", "dll.png")))
            ]
        }

        # Calcular el total de virus
        for directorio, archivos in self.files_in_room.items():
            for archivo in archivos:
                if archivo.es_infectado:
                    self.total_viruses += 1

        # Asignar rectángulos a los archivos - POSICIONADOS EN LA MISMA CUADRÍCULA QUE LAS PUERTAS
        # Los archivos continúan después de las puertas normales (no Back), en la misma cuadrícula
        for directorio, archivos in self.files_in_room.items():
            # Contar cuántas puertas normales (no Back) hay en este directorio
            num_normal_doors = 0
            if directorio in self.doors:
                for door_name in self.doors[directorio].keys():
                    if door_name != "Back":
                        num_normal_doors += 1
            
            # Los archivos empiezan después de las puertas normales
            for i, archivo in enumerate(archivos):
                # índice global en la cuadrícula (después de las puertas normales)
                grid_index = num_normal_doors + i
                archivo.rect = rect_at(grid_index)
                
                # Activar síntomas de archivos infectados
                if archivo.es_infectado and archivo.tipo_virus:
                    self.gestor_virus.activar_sintoma(archivo.tipo_virus)

        self.paused = False

        # INTEGRACIÓN: Sistema de gestión de Nivel 2 (OOP)
        self.level2_manager = Level2GameManager(total_threats=self.total_viruses)
        
        # INTEGRACIÓN: Configurar nivel en PlayerStats
        self.game.player_stats.set_current_level(2)
        
        # Registrar síntomas iniciales en el manager
        for directorio, archivos in self.files_in_room.items():
            for archivo in archivos:
                if archivo.es_infectado and archivo.tipo_virus:
                    self.level2_manager.activate_virus_symptom(archivo.tipo_virus, archivo.nombre)

        # SISTEMA EDUCATIVO
        self.overlay_educativo = OverlayEducativo(SCREEN_W, SCREEN_H)
        self.quiz_manager = QuizManager()
        self.gestor_mensajes = GestorMensajesEducativos()
        self.archivos_con_quiz = set()  # IDs de archivos que ya tuvieron quiz
        self.sintomas_tip_mostrado = set()  # Síntomas que ya mostraron tip

        # Actualizar panel de archivos inicial
        self.actualizar_panel_archivos()

    # --- Soporte de imagen para puertas ---
    def _get_image_scaled(self, image_path: str, side: int) -> pygame.Surface | None:
        """Retorna una Surface cuadrada (side x side) con la imagen 1:1 escalada (cached).
        1) Carga imagen desde image_path si existe
        2) Recorta zonas transparentes con get_bounding_rect() para maximizar el área del objeto.
        3) Escala manteniendo aspecto al tamaño cuadrado (side, side).
        4) Centra el resultado en un lienzo cuadrado transparente.
        Retorna None si no existe la imagen o side<=0.
        """
        if side <= 0:
            return None
        
        # Cache key por ruta y tamaño
        cache_key = (image_path, int(side))
        if cache_key in self._image_cache:
            return self._image_cache[cache_key]
        
        # Intentar cargar imagen
        if not os.path.isfile(image_path):
            self._image_cache[cache_key] = None
            return None
        
        try:
            raw_img = pygame.image.load(image_path).convert_alpha()
        except Exception:
            self._image_cache[cache_key] = None
            return None
        
        # recortar transparencias (min_alpha=1 para eliminar todo el espacio vacío)
        try:
            bbox = raw_img.get_bounding_rect(min_alpha=1)
            if bbox.width > 0 and bbox.height > 0:
                cropped = raw_img.subsurface(bbox).copy()
            else:
                cropped = raw_img
        except Exception:
            cropped = raw_img

        # ajustar a cuadrado manteniendo aspecto
        cw, ch = cropped.get_size()
        if cw <= 0 or ch <= 0:
            self._image_cache[cache_key] = None
            return None
        scale = side / max(cw, ch)
        new_w = max(1, int(cw * scale))
        new_h = max(1, int(ch * scale))
        scaled = pygame.transform.smoothscale(cropped, (new_w, new_h))

        # centrar en lienzo cuadrado
        canvas = pygame.Surface((side, side), pygame.SRCALPHA)
        canvas.fill((0, 0, 0, 0))
        x = (side - new_w) // 2
        y = (side - new_h) // 2
        canvas.blit(scaled, (x, y))

        self._image_cache[cache_key] = canvas
        return canvas

    def actualizar_panel_archivos(self):
        """Actualiza la lista de archivos en el panel izquierdo según el directorio actual"""
        self.hud_elements["left_files"] = []

        # Agregar las carpetas (subdirectorios) del directorio actual
        if self.current_directory in self.directory_structure:
            for subdir in self.directory_structure[self.current_directory]:
                self.hud_elements["left_files"].append({
                    "name": subdir,
                    "size": "--",
                    "type": "Folder"
                })

        # Agregar los archivos del directorio actual
        if self.current_directory in self.files_in_room:
            for archivo in self.files_in_room[self.current_directory]:
                if not archivo.eliminado:
                    self.hud_elements["left_files"].append({
                        "name": archivo.nombre,
                        "size": archivo.tamaño,
                        "type": "File",
                        "object": archivo  # Referencia al objeto real
                    })

    # =============================================================================
    # MÉTODOS PARA ACCIONES DE ANÁLISIS DE ARCHIVOS
    # =============================================================================

    def ejecutar_accion(self, accion, archivo=None):
        """Ejecuta una acción sobre un archivo o directorio"""
        if self.accion_en_progreso:
            self.show_message("Ya hay una acción en progreso...")
            return

        costo = self.costos_acciones.get(accion, 0)
        if self.recursos < costo:
            self.show_message("¡Recursos insuficientes!")
            return

        self.accion_en_progreso = accion
        self.tiempo_accion = 0
        self.archivo_seleccionado = archivo

        # Aplicar costo de recursos inmediatamente
        if costo > 0:
            self.recursos -= costo
            self.show_message(f"Recursos: -{costo} | {self.recursos} restantes")

    def actualizar_acciones(self, dt):
        """Actualiza las acciones en progreso y sus temporizadores"""
        if not self.accion_en_progreso:
            return

        self.tiempo_accion += dt

        if self.tiempo_accion >= self.duracion_escaneo:
            # Acción completada
            if self.accion_en_progreso == "inspeccionar":
                self._completar_inspeccion()
            elif self.accion_en_progreso == "escanear_archivo":
                self._completar_escaneo_archivo()
            elif self.accion_en_progreso == "escanear_carpeta":
                self._completar_escaneo_carpeta()
            elif self.accion_en_progreso == "cuarentena":
                self._completar_cuarentena()
            elif self.accion_en_progreso == "limpiar":
                self._completar_limpieza()

            self.accion_en_progreso = None
            self.archivo_seleccionado = None

    def _completar_inspeccion(self):
        """Completa la acción de inspeccionar un archivo"""
        if self.archivo_seleccionado:
            metadatos = self.archivo_seleccionado.obtener_metadatos()
            mensaje = f"INSPECCIÓN: {self.archivo_seleccionado.nombre}\n"
            for key, value in metadatos.items():
                mensaje += f"{key}: {value}\n"
            self.show_message(mensaje)

    def _completar_escaneo_archivo(self):
        """Completa el escaneo individual de un archivo"""
        if self.archivo_seleccionado:
            probabilidad = self.archivo_seleccionado.probabilidad_infeccion
            if self.archivo_seleccionado.es_infectado:
                mensaje = f"ESCANEO: {self.archivo_seleccionado.nombre} - {probabilidad}% riesgo - {self.archivo_seleccionado.tipo_virus.upper()}"
                self.show_message(mensaje)
                
                # SISTEMA EDUCATIVO: Mostrar quiz si no se ha mostrado antes
                archivo_id = id(self.archivo_seleccionado)
                if archivo_id not in self.archivos_con_quiz:
                    self.mostrar_quiz_malware(self.archivo_seleccionado)
                    self.archivos_con_quiz.add(archivo_id)
            else:
                # Para archivos limpios, mostrar un porcentaje bajo aleatorio
                riesgo = random.randint(0, 15)
                mensaje = f"ESCANEO: {self.archivo_seleccionado.nombre} - {riesgo}% riesgo - LIMPIO"
                self.show_message(mensaje)

    def _completar_escaneo_carpeta(self):
        """Completa el escaneo de la carpeta actual"""
        archivos_riesgo = []

        # Escanear subcarpetas
        if self.current_directory in self.directory_structure:
            for subdir in self.directory_structure[self.current_directory]:
                # Simular riesgo en carpetas
                riesgo_carpeta = random.randint(0, 30)
                archivos_riesgo.append((f"[CARPETA] {subdir}", riesgo_carpeta))

        # Escanear archivos
        if self.current_directory in self.files_in_room:
            for archivo in self.files_in_room[self.current_directory]:
                if not archivo.eliminado and not archivo.en_cuarentena:
                    if archivo.es_infectado:
                        riesgo = archivo.probabilidad_infeccion
                    else:
                        riesgo = random.randint(0, 20)
                    archivos_riesgo.append((archivo.nombre, riesgo))

        mensaje = "ESCANEO CARPETA:\n"
        for nombre, riesgo in archivos_riesgo[:6]:  # Mostrar máximo 6 elementos
            estado = "ALTO RIESGO" if riesgo > 50 else "BAJO RIESGO"
            mensaje += f"{nombre}: {riesgo}% - {estado}\n"
        self.show_message(mensaje)

    # =============================================================================
    # MÉTODOS DEL SISTEMA EDUCATIVO
    # =============================================================================

    def mostrar_quiz_malware(self, archivo):
        """Muestra un quiz educativo sobre el tipo de malware detectado"""
        quiz_data = self.quiz_manager.obtener_quiz(archivo.tipo_virus)
        if not quiz_data:
            return
        
        # Crear overlay de quiz con botones
        def responder_quiz(opcion_elegida):
            correcta = quiz_data['correcta']
            es_correcto = (opcion_elegida == correcta)
            
            if es_correcto:
                # +4 recursos
                self.recursos += 4
                self.level2_manager.resource_bar.add(4)
                
                bullets = [
                    f"✅ Correcto: {quiz_data['opciones'][correcta]}",
                    quiz_data['tip'],
                    f"+4 recursos (total: {self.recursos})"
                ]
                titulo = "🎯 ¡Bien hecho!"
                
                # Telemetría
                self.game.player_stats.mistake_log.add_mistake(
                    level=2,
                    mistake_type="quiz_ok",
                    description=f"Quiz respondido correctamente: {archivo.tipo_virus}",
                    mistake_details={
                        "archivo": archivo.nombre,
                        "malware": archivo.tipo_virus,
                        "delta_recursos": 4
                    }
                )
            else:
                # -2 recursos
                self.recursos = max(0, self.recursos - 2)
                self.level2_manager.resource_bar.consume(2)
                
                bullets = [
                    f"❌ Incorrecto. Correcta: {quiz_data['opciones'][correcta]}",
                    quiz_data['tip'],
                    f"-2 recursos (total: {self.recursos})"
                ]
                titulo = "📚 Aprende de esto"
                
                # Telemetría
                self.game.player_stats.mistake_log.add_mistake(
                    level=2,
                    mistake_type="quiz_fail",
                    description=f"Quiz respondido incorrectamente: {archivo.tipo_virus}",
                    mistake_details={
                        "archivo": archivo.nombre,
                        "malware": archivo.tipo_virus,
                        "delta_recursos": -2
                    }
                )
            
            # Mostrar resultado
            msg = MensajeOverlay('tutor_refuerzo', titulo, bullets, "", prioridad=80)
            self.overlay_educativo.agregar_mensaje(msg)
        
        # Crear mensaje de quiz con opciones
        bullets = [
            quiz_data['pregunta'],
            "",
            f"A) {quiz_data['opciones'][0]}",
            f"B) {quiz_data['opciones'][1]}",
            f"C) {quiz_data['opciones'][2]}"
        ]
        
        # Por ahora, simplificamos: el quiz se "auto-responde" aleatoriamente
        # En una implementación completa, necesitarías botones interactivos
        import random
        opcion_elegida = random.randint(0, 2)  # Simula elección del jugador
        responder_quiz(opcion_elegida)
    
    def mostrar_tip_sintoma(self, tipo_malware):
        """Muestra un tip educativo cuando se detecta un síntoma por primera vez"""
        if tipo_malware in self.sintomas_tip_mostrado:
            return
        
        tip_data = self.gestor_mensajes.obtener_tip(tipo_malware)
        msg = MensajeOverlay(
            'tutor_tip',
            tip_data['titulo'],
            tip_data['bullets'],
            tip_data['sabias_que'],
            prioridad=60
        )
        
        if self.overlay_educativo.agregar_mensaje(msg):
            self.sintomas_tip_mostrado.add(tipo_malware)
    
    def mostrar_refuerzo_sintoma(self, tipo_malware):
        """Muestra refuerzo educativo tras eliminar/aislar un malware"""
        refuerzo_data = self.gestor_mensajes.obtener_refuerzo(tipo_malware)
        msg = MensajeOverlay(
            'tutor_refuerzo',
            refuerzo_data['titulo'],
            refuerzo_data['bullets'],
            refuerzo_data['sabias_que'],
            prioridad=80
        )
        self.overlay_educativo.agregar_mensaje(msg)
    
    def mostrar_error_educativo(self, tipo_error):
        """Muestra mensaje educativo tras un error"""
        error_data = self.gestor_mensajes.obtener_error(tipo_error)
        msg = MensajeOverlay(
            'tutor_error',
            error_data['titulo'],
            error_data['bullets'],
            error_data.get('sabias_que', ''),
            prioridad=70
        )
        self.overlay_educativo.agregar_mensaje(msg)

    def _completar_cuarentena(self):
        """Completa la acción de poner en cuarentena un archivo"""
        if self.archivo_seleccionado:
            self.archivo_seleccionado.en_cuarentena = True

            if self.archivo_seleccionado.es_infectado:
                # INTEGRACIÓN: Registrar en Level2GameManager
                self.level2_manager.file_quarantined(
                    had_virus=True,
                    symptom_type=self.archivo_seleccionado.tipo_virus
                )
                
                # INTEGRACIÓN: Registrar en Excel
                self.game.player_stats.mistake_log.add_mistake(
                    level=2,
                    mistake_type="archivo_infectado_detectado",
                    description=f"Archivo {self.archivo_seleccionado.nombre} puesto en cuarentena (Virus: {self.archivo_seleccionado.tipo_virus})",
                    mistake_details={
                        "nombre_archivo": self.archivo_seleccionado.nombre,
                        "tipo_virus": self.archivo_seleccionado.tipo_virus,
                        "accion": "cuarentena"
                    }
                )
                
                self.show_message(f"CUARENTENA: {self.archivo_seleccionado.nombre} - Virus aislado")
                # Programar desactivación de síntoma
                pygame.time.set_timer(pygame.USEREVENT + 1, 20000)
                
                # SISTEMA EDUCATIVO: No mostrar refuerzo aquí (se mostrará cuando se apague el síntoma)
            else:
                # INTEGRACIÓN: Registrar falso positivo
                self.level2_manager.file_quarantined(had_virus=False)
                
                # INTEGRACIÓN: Registrar error en Excel
                self.game.player_stats.mistake_log.add_mistake(
                    level=2,
                    mistake_type="archivo_limpio_cuarentena",
                    description=f"Falso positivo: {self.archivo_seleccionado.nombre} era seguro pero fue puesto en cuarentena",
                    mistake_details={
                        "nombre_archivo": self.archivo_seleccionado.nombre,
                        "accion": "cuarentena",
                        "error": True
                    }
                )
                
                # Penalización por archivo seguro
                self.recursos -= 5
                self.mistakes_made += 1
                # INTEGRACIÓN: Sincronizar ResourceBar del manager
                self.level2_manager.resource_bar.consume(5)
                self.show_message(f"ERROR: {self.archivo_seleccionado.nombre} era seguro! -5 recursos")
                
                # SISTEMA EDUCATIVO: Mostrar mensaje de error
                self.mostrar_error_educativo('cuarentena_seguro')

    def _completar_limpieza(self):
        """Completa la acción de limpiar/eliminar un archivo"""
        if self.archivo_seleccionado:
            if self.archivo_seleccionado.es_infectado:
                # INTEGRACIÓN: Registrar limpieza exitosa
                self.level2_manager.file_cleaned(
                    had_virus=True,
                    symptom_type=self.archivo_seleccionado.tipo_virus
                )
                
                # Éxito - eliminar virus
                self.archivo_seleccionado.eliminado = True
                self.viruses_cleaned += 1

                # Desactivar síntoma inmediatamente
                if self.archivo_seleccionado.tipo_virus:
                    self.gestor_virus.desactivar_sintoma(self.archivo_seleccionado.tipo_virus)
                    # INTEGRACIÓN: Resolver síntoma en el manager
                    self.level2_manager.symptom_manager.deactivate_symptom(self.archivo_seleccionado.tipo_virus)
                    
                    # INTEGRACIÓN: Registrar resolución de síntoma en Excel
                    self.game.player_stats.mistake_log.add_mistake(
                        level=2,
                        mistake_type="sintoma_resuelto",
                        description=f"Virus {self.archivo_seleccionado.tipo_virus} eliminado de {self.archivo_seleccionado.nombre}",
                        mistake_details={
                            "nombre_archivo": self.archivo_seleccionado.nombre,
                            "tipo_virus": self.archivo_seleccionado.tipo_virus,
                            "accion": "limpiar"
                        }
                    )

                self.show_message(
                    f"¡VIRUS ELIMINADO! {self.archivo_seleccionado.nombre} - {self.viruses_cleaned}/{self.total_viruses}")
                    
                # SISTEMA EDUCATIVO: Mostrar refuerzo educativo
                self.mostrar_refuerzo_sintoma(self.archivo_seleccionado.tipo_virus)

            else:
                # INTEGRACIÓN: Registrar error de limpieza
                self.level2_manager.file_cleaned(had_virus=False)
                
                # INTEGRACIÓN: Registrar eliminación incorrecta en Excel
                self.game.player_stats.mistake_log.add_mistake(
                    level=2,
                    mistake_type="archivo_limpio_eliminado",
                    description=f"Error: {self.archivo_seleccionado.nombre} era un archivo limpio y fue eliminado",
                    mistake_details={
                        "nombre_archivo": self.archivo_seleccionado.nombre,
                        "accion": "limpiar",
                        "error": True
                    }
                )
                
                # Error - eliminar archivo seguro
                penalizacion = self.costos_acciones["limpiar_seguro"]
                self.recursos -= penalizacion
                self.mistakes_made += 1
                # INTEGRACIÓN: Sincronizar ResourceBar del manager
                self.level2_manager.resource_bar.consume(penalizacion)
                self.show_message(
                    f"ERROR: Eliminaste archivo seguro! -{penalizacion} recursos")
                    
                # SISTEMA EDUCATIVO: Mostrar mensaje de error
                self.mostrar_error_educativo('limpiar_seguro')

    def manejar_evento_cuarentena(self, event):
        """Maneja el evento de temporizador para desactivar síntomas"""
        if event.type == pygame.USEREVENT + 1:
            for directorio, archivos in self.files_in_room.items():
                for archivo in archivos:
                    if (archivo.en_cuarentena and archivo.es_infectado and
                            self.gestor_virus.verificar_sintoma_por_archivo(archivo)):
                        self.gestor_virus.desactivar_sintoma(archivo.tipo_virus)
                        self.show_message(f"Síntoma desactivado: {archivo.tipo_virus}")
                        
                        # SISTEMA EDUCATIVO: Mostrar refuerzo al resolver síntoma vía cuarentena
                        self.mostrar_refuerzo_sintoma(archivo.tipo_virus)
                        break
            pygame.time.set_timer(pygame.USEREVENT + 1, 0)

    def dibujar_sintomas_globales(self, surf):
        """Dibuja los síntomas activos en la parte superior de la pantalla"""
        if not self.gestor_virus.hay_sintomas_activos():
            return

        sintomas_texto = "SÍNTOMAS: "
        if self.gestor_virus.sintomas_activos["ralentizacion"]:
            sintomas_texto += "LENTITUD "
        if self.gestor_virus.sintomas_activos["popups"]:
            sintomas_texto += "POPUPS "
        if self.gestor_virus.sintomas_activos["pantalla_bloqueada"]:
            sintomas_texto += "BLOQUEO "
        if self.gestor_virus.sintomas_activos["teclas_fantasma"]:
            sintomas_texto += "TECLAS "

        sintoma_surf = self.fonts["normal"].render(sintomas_texto, True, (255, 50, 50))
        surf.blit(sintoma_surf, (SCREEN_W // 2 - sintoma_surf.get_width() // 2, 5))

    def dibujar_progreso_accion(self, surf):
        """Dibuja la barra de progreso de la acción en curso"""
        if not self.accion_en_progreso:
            return

        progreso = min(1.0, self.tiempo_accion / self.duracion_escaneo)
        bar_width = 200
        bar_height = 20
        bar_x = SCREEN_W // 2 - bar_width // 2
        bar_y = SCREEN_H - 120

        # Fondo de la barra
        pygame.draw.rect(surf, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        # Barra de progreso
        pygame.draw.rect(surf, (0, 200, 255), (bar_x, bar_y, bar_width * progreso, bar_height))
        # Texto
        accion_text = self.fonts["small"].render(f"{self.accion_en_progreso.upper()}...", True, (255, 255, 255))
        surf.blit(accion_text, (bar_x, bar_y - 25))

    def handle_event(self, event):
        # SISTEMA EDUCATIVO: Dar prioridad a eventos del overlay
        if self.overlay_educativo.handle_event(event):
            return  # El overlay consumió el evento
        
        if event.type == pygame.USEREVENT + 1:
            self.manejar_evento_cuarentena(event)
        
        # Manejo de scroll del log con rueda del mouse
        if event.type == pygame.MOUSEWHEEL:
            log_rect = self.hud_rects["bottom_log"]
            if log_rect.collidepoint(pygame.mouse.get_pos()):
                self.log_scroll_offset = max(0, min(self.log_max_scroll, self.log_scroll_offset - event.y))
        
        # Drag del scrollbar del log
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            log_rect = self.hud_rects["bottom_log"]
            scrollbar_x = log_rect.right - 20
            scrollbar_area = pygame.Rect(scrollbar_x, log_rect.y + 10, 10, log_rect.h - 20)
            if scrollbar_area.collidepoint(event.pos):
                self.log_scrollbar_dragging = True
                self.log_drag_start_y = event.pos[1]
                self.log_drag_start_offset = self.log_scroll_offset
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.log_scrollbar_dragging = False
            
            # Navegación por puertas al soltar el clic
            if self.pressed_door and not self.in_transition:
                if self.current_directory in self.doors:
                    for door_name, (door_rect, target_dir) in self.doors[self.current_directory].items():
                        if door_rect == self.pressed_door:
                            mx, my = pygame.mouse.get_pos()
                            # Solo abrir si el mouse sigue sobre la puerta
                            if door_rect.collidepoint(mx, my):
                                self.start_transition(target_dir, door_rect)
                            break
            
            self.pressed_door = None
            self.pressed_file = None
        
        if event.type == pygame.MOUSEMOTION and self.log_scrollbar_dragging:
            log_rect = self.hud_rects["bottom_log"]
            scrollbar_h = log_rect.h - 20
            line_height = self.fonts["small"].get_height() + 2
            visible_lines = (log_rect.h - 20) // line_height
            total_lines = len(self.log_lines)
            
            if total_lines > visible_lines:
                delta_y = event.pos[1] - self.log_drag_start_y
                handle_h = max(20, int(scrollbar_h * (visible_lines / total_lines)))
                scroll_range = scrollbar_h - handle_h
                if scroll_range > 0:
                    scroll_delta = int((delta_y / scroll_range) * self.log_max_scroll)
                    self.log_scroll_offset = max(0, min(self.log_max_scroll, self.log_drag_start_offset + scroll_delta))

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.paused = not self.paused
            elif self.state == "tutor_inicial" and event.key == pygame.K_RETURN:
                self.state = "jugando"
            # Interacciones de juego ahora son solo con mouse

        # CLICK IZQUIERDO
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == "jugando" and not self.accion_en_progreso:

                # --------------------------- HERRAMIENTAS ---------------------------
                for i, button_rect in enumerate(self.tool_button_rects):
                    if button_rect.collidepoint(event.pos):
                        tool_name = self.hud_elements["tools"][i]

                        if tool_name == "Inspeccionar":
                            if self.archivo_seleccionado:
                                self.ejecutar_accion("inspeccionar", self.archivo_seleccionado)
                            else:
                                self.show_message("Selecciona un archivo primero")

                        elif tool_name == "Escanear":
                            if self.archivo_seleccionado:
                                self.ejecutar_accion("escanear_archivo", self.archivo_seleccionado)
                            else:
                                self.ejecutar_accion("escanear_carpeta")

                        elif tool_name == "Cuarentena":
                            if self.archivo_seleccionado:
                                self.ejecutar_accion("cuarentena", self.archivo_seleccionado)
                            else:
                                self.show_message("Selecciona un archivo primero")

                        elif tool_name == "Limpiar":
                            if self.archivo_seleccionado:
                                self.ejecutar_accion("limpiar", self.archivo_seleccionado)
                            else:
                                self.show_message("Selecciona un archivo primero")

                        return  # dejar de procesar más clics

                # ------------------------ SELECCIÓN DE ARCHIVOS ------------------------
                file_rect = self.hud_rects["left_files"].copy()
                file_rect.y += 35
                file_rect.x += 10
                file_rect.width -= 20

                for file_info in self.hud_elements["left_files"]:
                    item_rect = pygame.Rect(file_rect.x, file_rect.y, file_rect.width, 25)

                    if item_rect.collidepoint(event.pos) and file_info["type"] == "File":
                        # Al hacer clic, guardar el archivo seleccionado real
                        self.archivo_seleccionado = file_info["object"]
                        self.show_message(f"Archivo seleccionado: {self.archivo_seleccionado.nombre}")
                        return

                    file_rect.y += 30

                # --------------------------- PUERTAS (click en panel central) ---------------------------
                if self.current_directory in self.doors and not self.in_transition:
                    for door_name, (door_rect, target_dir) in self.doors[self.current_directory].items():
                        if door_rect.collidepoint(event.pos):
                            self.pressed_door = door_rect
                            # No navegar aún, esperar al mouseup
                            return

                # --------------------------- ARCHIVOS EN PANEL CENTRAL ---------------------------
                if self.current_directory in self.files_in_room:
                    for archivo in self.files_in_room[self.current_directory]:
                        if archivo.eliminado:
                            continue
                        if archivo.rect.collidepoint(event.pos):
                            self.pressed_file = archivo
                            self.archivo_seleccionado = archivo
                            self.show_message(f"Archivo seleccionado: {archivo.nombre}")
                            return

    def update(self, dt):
        if self.paused:
            return
        
        # No actualizar el juego si estamos en el tutor
        if self.state == "tutor_inicial":
            return
        
        if self.state != "jugando":
            return

        self.actualizar_acciones(dt)
        self.game_time += dt
        
        # INTEGRACIÓN: Actualizar Level2GameManager
        self.level2_manager.update(dt)
        
        # INTEGRACIÓN: Sincronizar recursos con el manager
        self.recursos = max(0, int(self.level2_manager.resource_bar.current))
        
        # ANIMACIÓN: Suavizar el número de recursos mostrado
        # Interpolar suavemente hacia el valor real
        diferencia = self.recursos - self.recursos_display
        velocidad_animacion = 3.0  # Velocidad de interpolación (mayor = más rápido)
        self.recursos_display += diferencia * velocidad_animacion * (dt / 1000.0)
        
        # Si está muy cerca, snappear al valor exacto
        if abs(diferencia) < 0.5:
            self.recursos_display = float(self.recursos)
        
        # SISTEMA EDUCATIVO: Actualizar overlay (cooldowns)
        self.overlay_educativo.update(dt)
        
        # SISTEMA EDUCATIVO: Mostrar tip cuando un síntoma se activa
        for sintoma, activo in self.gestor_virus.sintomas_activos.items():
            if activo and sintoma not in self.sintomas_tip_mostrado:
                # Mapear síntoma a tipo de malware
                tipo_malware = None
                if sintoma == "pantalla_bloqueada":
                    tipo_malware = "ransomware"
                elif sintoma == "popups":
                    tipo_malware = "adware"
                elif sintoma == "ralentizacion":
                    tipo_malware = "miner"
                elif sintoma == "teclas_fantasma":
                    tipo_malware = "spyware"
                
                if tipo_malware:
                    self.mostrar_tip_sintoma(tipo_malware)
                    self.sintomas_tip_mostrado.add(sintoma)

        # BLOQUEAR TODO SI ESTÁ EN TRANSICIÓN
        if self.in_transition:
            self.transition_time += dt
            progress = min(1.0, self.transition_time / self.transition_duration)

            if progress >= 1.0:
                self.in_transition = False
                self.current_directory = self.transition_target
                self.actualizar_panel_archivos()
                print(f"DEBUG: Llegué a {self.current_directory}")  # Para debug
            return
        # MODO MOUSE-ONLY: actualizar resaltados por hover
        self.near_door = None
        self.near_file = None

        mouse_pos = pygame.mouse.get_pos()

        # Puertas bajo el mouse
        if self.current_directory in self.doors:
            for door_name, (door_rect, target_dir) in self.doors[self.current_directory].items():
                if door_rect.collidepoint(mouse_pos):
                    self.near_door = (door_name, door_rect, target_dir)
                    break

        # Archivos bajo el mouse
        if self.current_directory in self.files_in_room:
            for archivo in self.files_in_room[self.current_directory]:
                if archivo.eliminado:
                    continue
                if archivo.rect.collidepoint(mouse_pos):
                    self.near_file = archivo
                    break

        self.check_game_state()

    def start_transition(self, target_directory, door_rect):
        """Inicia una transición a un nuevo directorio (interacción solo con mouse)."""
        if self.in_transition:
            return
        self.in_transition = True
        self.transition_time = 0
        self.transition_target = target_directory
        self.previous_directory = self.current_directory
        self.show_message(f"Cambiando a {target_directory}...")

    def check_game_state(self):
        # INTEGRACIÓN: Usar los checkers del manager
        if self.level2_manager.victory_checker.check_victory():
            # INTEGRACIÓN: Guardar datos a Excel al ganar
            self.game.player_stats.complete_level()
            
            # Cambiar a pantalla de video de victoria
            mensaje = f"Virus eliminados: {self.viruses_cleaned}/{self.total_viruses}"
            self.game.change_screen(VictoryVideoScreen(self.game, mensaje))
            
        elif self.level2_manager.defeat_checker.check_defeat():
            # Determinar razón de derrota
            razon = ""
            if self.recursos <= 0:
                razon = "¡Te has quedado sin recursos!"
                
                # INTEGRACIÓN: Registrar derrota por recursos
                self.game.player_stats.mistake_log.add_mistake(
                    level=2,
                    mistake_type="recursos_agotados",
                    description="Derrota: Se agotaron los recursos",
                    mistake_details={"recursos_restantes": 0}
                )
                
            elif self.mistakes_made >= self.max_mistakes:
                razon = "¡Has cometido demasiados errores!"
            else:
                razon = "¡Derrota!"
            
            # INTEGRACIÓN: Guardar datos a Excel al perder también
            self.game.player_stats.complete_level()
            
            # Cambiar a pantalla de video de derrota
            self.game.change_screen(DefeatVideoScreen(self.game, razon))

    def show_message(self, message, duration=None):
        self.current_message = message
        self.effect_timers["message"] = duration or self.message_duration

    def draw_panel_title(self, surf, rect, title):
        text = self.fonts["title"].render(title, True, self.hud_colors["text"])
        text_rect = text.get_rect(midtop=(rect.centerx, rect.top + 5))
        surf.blit(text, text_rect)

    def render(self, surf):
        surf.fill((0, 0, 0))

        if self.gestor_virus.sintomas_activos["ralentizacion"]:
            if pygame.time.get_ticks() % 1000 < 500:
                surf.fill((30, 30, 60), special_flags=pygame.BLEND_RGB_ADD)

        if self.state == "tutor_inicial":
            # Pantalla de bienvenida del tutor
            surf.fill((10, 15, 25))
            
            # Cuadro central
            box_width = 800
            box_height = 550
            box_x = (SCREEN_W - box_width) // 2
            box_y = (SCREEN_H - box_height) // 2
            box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
            
            # Fondo del cuadro
            pygame.draw.rect(surf, (20, 30, 50), box_rect, border_radius=15)
            pygame.draw.rect(surf, (0, 200, 255), box_rect, 3, border_radius=15)
            
            # Título
            titulo = self.fonts["title"].render("TUTOR DEL SISTEMA", True, (0, 255, 255))
            surf.blit(titulo, (box_rect.centerx - titulo.get_width() // 2, box_y + 20))
            
            # Líneas del mensaje
            y_offset = box_y + 70
            for linea in self.tutor_mensaje:
                if linea == "":
                    y_offset += 15
                    continue
                
                # Detectar si es título (tiene ":" al final)
                if linea.startswith("¡") or linea.startswith("Tu misión") or linea.startswith("Herramientas"):
                    color = (255, 255, 100)
                    texto = self.fonts["normal"].render(linea, True, color)
                elif linea.startswith("•") or linea.startswith("-"):
                    color = (200, 200, 200)
                    texto = self.fonts["small"].render(linea, True, color)
                elif "ENTER" in linea:
                    color = (0, 255, 0)
                    texto = self.fonts["normal"].render(linea, True, color)
                else:
                    color = (220, 220, 220)
                    texto = self.fonts["small"].render(linea, True, color)
                
                surf.blit(texto, (box_x + 40, y_offset))
                y_offset += 22
            
        elif self.state == "jugando":
            # Dibujar paneles
            for name, rect in self.hud_rects.items():
                if name == "resource_bar": continue
                pygame.draw.rect(surf, self.hud_colors["background"], rect)
                border_color = self.hud_colors["highlight"] if name == self.active_panel else self.hud_colors["border"]
                pygame.draw.rect(surf, border_color, rect, 3 if name == self.active_panel else 2, border_radius=5)

            # Barra de recursos
            resource_rect = self.hud_rects["resource_bar"]
            pygame.draw.rect(surf, (10, 10, 10), resource_rect)
            resource_width = (self.recursos / 100) * (resource_rect.width - 4)
            current_resource_rect = pygame.Rect(resource_rect.x + 2, resource_rect.y + 2, resource_width,
                                                resource_rect.height - 4)
            pygame.draw.rect(surf, self.hud_colors["resource"], current_resource_rect)
            pygame.draw.rect(surf, self.hud_colors["border"], resource_rect, 1)
            
            # NUEVO: Indicador numérico de recursos con animación
            recursos_texto = f"{int(self.recursos_display)}/100"
            
            # Color del texto basado en cantidad de recursos
            if self.recursos_display > 60:
                color_texto = (255, 255, 255)  # Blanco
            elif self.recursos_display > 30:
                color_texto = (255, 255, 0)    # Amarillo (advertencia)
            else:
                color_texto = (255, 100, 100)  # Rojo (peligro)
            
            # Renderizar texto con sombra para mejor visibilidad
            texto_recursos = self.fonts["normal"].render(recursos_texto, True, color_texto)
            texto_shadow = self.fonts["normal"].render(recursos_texto, True, (0, 0, 0))
            
            # Posicionar en el centro de la barra
            texto_x = resource_rect.centerx - texto_recursos.get_width() // 2
            texto_y = resource_rect.centery - texto_recursos.get_height() // 2
            
            # Dibujar sombra y texto
            surf.blit(texto_shadow, (texto_x + 1, texto_y + 1))
            surf.blit(texto_recursos, (texto_x, texto_y))

            # Síntomas globales
            self.dibujar_sintomas_globales(surf)

            # Títulos
            self.draw_panel_title(surf, self.hud_rects["left_files"], "Archivos")
            self.draw_panel_title(surf, self.hud_rects["center_preview"], "Sistema")
            self.draw_panel_title(surf, self.hud_rects["right_tools"], "Herramientas")

            # Panel izquierdo - ARCHIVOS DEL DIRECTORIO ACTUAL
            file_rect = self.hud_rects["left_files"].copy()
            file_rect.y += 35
            file_rect.x += 10
            file_rect.width -= 20

            for file_info in self.hud_elements["left_files"]:
                # Icono (azul para carpetas, gris para archivos)
                icon_rect = pygame.Rect(file_rect.x, file_rect.y + 2, 16, 16)
                if file_info["type"] == "Folder":
                    pygame.draw.rect(surf, (100, 100, 255), icon_rect)
                else:
                    pygame.draw.rect(surf, self.hud_colors["border"], icon_rect)

                # Nombre
                text = self.fonts["normal"].render(file_info["name"], True, self.hud_colors["text"])
                surf.blit(text, (file_rect.x + 22, file_rect.y))
                file_rect.y += 25
                if file_rect.y > self.hud_rects["left_files"].bottom - 20:
                    break

            # Herramientas
            for i, tool_name in enumerate(self.hud_elements["tools"]):
                button_rect = self.tool_button_rects[i]
                # Borde fijo
                pygame.draw.rect(surf, self.hud_colors["border"], button_rect, border_radius=5)
                
                # Hover blanco
                if button_rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(surf, (255, 255, 255), button_rect, 2, border_radius=5)

                # Dibujar icono de herramienta (imagen personalizada o fallback) - más grande
                icon_size = 32
                icon_rect = pygame.Rect(button_rect.x + 8, button_rect.y + (button_rect.height - icon_size) // 2, icon_size, icon_size)
                tool_img_path = self.tool_images.get(tool_name)
                tool_img = None
                
                if tool_img_path:
                    tool_img = self._get_image_scaled(tool_img_path, icon_size)
                
                if tool_img is not None:
                    # Dibujar imagen centrada en el área del icono
                    img_rect = tool_img.get_rect(center=icon_rect.center)
                    surf.blit(tool_img, img_rect)
                else:
                    # Fallback: rectángulo cyan si no hay imagen
                    pygame.draw.rect(surf, self.hud_colors["highlight"], icon_rect)

                # Texto más grande usando fuente title
                text = self.fonts["title"].render(tool_name, True, self.hud_colors["text"])
                text_y = button_rect.y + (button_rect.height - text.get_height()) // 2
                surf.blit(text, (button_rect.x + 48, text_y))

            # Log - Soporta saltos de línea con scroll bar
            log_rect = self.hud_rects["bottom_log"]
            # Dividir el mensaje en líneas respetando \n y añadir ">" al inicio
            self.log_lines = [f"> {line}" for line in self.current_message.split('\n')]
            
            line_height = self.fonts["small"].get_height() + 2
            visible_area = pygame.Rect(log_rect.x + 10, log_rect.y + 10, log_rect.w - 40, log_rect.h - 20)
            max_visible_lines = visible_area.h // line_height
            total_lines = len(self.log_lines)
            
            # Calcular scroll
            needs_scrollbar = total_lines > max_visible_lines
            self.log_max_scroll = max(0, total_lines - max_visible_lines)
            self.log_scroll_offset = max(0, min(self.log_scroll_offset, self.log_max_scroll))
            
            # Renderizar líneas con clipping
            prev_clip = surf.get_clip()
            surf.set_clip(visible_area)
            
            y_offset = visible_area.y
            for i in range(self.log_scroll_offset, min(self.log_scroll_offset + max_visible_lines + 2, total_lines)):
                if y_offset < visible_area.bottom:
                    text = self.fonts["small"].render(self.log_lines[i], True, self.hud_colors["text"])
                    surf.blit(text, (visible_area.x, y_offset))
                    y_offset += line_height
            
            surf.set_clip(prev_clip)
            
            # Scrollbar
            if needs_scrollbar:
                scrollbar_x = log_rect.right - 20
                scrollbar_y = log_rect.y + 10
                scrollbar_h = log_rect.h - 20
                scrollbar_w = 10
                
                # Fondo del scrollbar
                scrollbar_bg = pygame.Rect(scrollbar_x, scrollbar_y, scrollbar_w, scrollbar_h)
                pygame.draw.rect(surf, (40, 40, 60), scrollbar_bg, border_radius=5)
                
                # Manija del scrollbar
                handle_h = max(20, int(scrollbar_h * (max_visible_lines / total_lines)))
                handle_y = scrollbar_y + int((scrollbar_h - handle_h) * (self.log_scroll_offset / self.log_max_scroll)) if self.log_max_scroll > 0 else scrollbar_y
                handle_rect = pygame.Rect(scrollbar_x, handle_y, scrollbar_w, handle_h)
                pygame.draw.rect(surf, (100, 100, 140), handle_rect, border_radius=5)

            # Puertas
            if self.current_directory in self.doors:
                for door_name, (door_rect, _) in self.doors[self.current_directory].items():
                    # Determinar si es puerta Back y seleccionar imagen apropiada
                    is_back_door = door_name == "Back"
                    img_path = self.back_door_image_path if is_back_door else self.door_image_path
                    
                    # Calcular escala: 1.15x en hover, 0.95x si presionada
                    is_hovered = self.near_door and self.near_door[1] == door_rect
                    is_pressed = self.pressed_door == door_rect
                    scale = 0.95 if is_pressed else (1.15 if is_hovered else 1.0)
                    
                    # Intentar dibujar imagen 1:1 centrada dentro del rect de la puerta
                    pad = 6
                    base_side = max(1, min(max(0, door_rect.w - pad * 2), max(0, door_rect.h - pad * 2)))
                    side = int(base_side * scale)
                    img = self._get_image_scaled(img_path, side)
                    
                    if img is not None:
                        dst = img.get_rect(center=door_rect.center)
                        # Offset de hundimiento si está presionada
                        if is_pressed:
                            dst.y += 3
                        surf.blit(img, dst)
                    else:
                        # Fallback si no hay imagen: rect tradicional con color
                        color_fill = self.hud_colors["door"]
                        scaled_rect = pygame.Rect(0, 0, int(door_rect.w * scale), int(door_rect.h * scale))
                        scaled_rect.center = door_rect.center
                        if is_pressed:
                            scaled_rect.y += 3
                        pygame.draw.rect(surf, color_fill, scaled_rect, border_radius=5)
                        # Etiqueta del nombre sólo en fallback
                        text = self.fonts["normal"].render(door_name, True, (0, 0, 0))
                        text_rect = text.get_rect(center=scaled_rect.center)
                        surf.blit(text, text_rect)
                    
                    # Mostrar nombre de la puerta en hover
                    if is_hovered:
                        color_hi = self.hud_colors["door_highlight"]
                        indicator_text = self.fonts["normal"].render(door_name, True, color_hi)
                        indicator_pos = (door_rect.centerx, door_rect.top - 20)
                        text_rect = indicator_text.get_rect(center=indicator_pos)
                        surf.blit(indicator_text, text_rect)

            # Archivos en el directorio actual
            if self.current_directory in self.files_in_room:
                for archivo in self.files_in_room[self.current_directory]:
                    if archivo.eliminado:
                        continue

                    file_rect = archivo.rect

                    # Calcular escala: 1.15x en hover solamente (sin efecto de presionado)
                    is_hovered = self.near_file and self.near_file.nombre == archivo.nombre
                    scale = 1.15 if is_hovered else 1.0

                    # Color según estado (para borde o fallback)
                    if archivo.en_cuarentena:
                        color = (255, 165, 0)
                    elif archivo.es_infectado:
                        color = (255, 0, 0)
                    elif archivo.es_sospechoso():
                        color = (255, 255, 0)
                    else:
                        color = (200, 200, 200)

                    # Resaltar si está seleccionado con borde blanco
                    if self.archivo_seleccionado and self.archivo_seleccionado.nombre == archivo.nombre:
                        pygame.draw.rect(surf, (255, 255, 255), file_rect.inflate(6, 6), 2, border_radius=4)

                    # Intentar dibujar imagen personalizada del archivo con escala
                    if archivo.image_path:
                        pad = 2
                        base_side = max(1, min(max(0, file_rect.w - pad * 2), max(0, file_rect.h - pad * 2)))
                        side = int(base_side * scale)
                        img = self._get_image_scaled(archivo.image_path, side)
                        if img is not None:
                            # Dibujar imagen sin tinting para mantener colores originales
                            dst = img.get_rect(center=file_rect.center)
                            surf.blit(img, dst)
                            # Indicar estado con un borde de color en lugar de tinting
                            if archivo.en_cuarentena or archivo.es_infectado or archivo.es_sospechoso():
                                scaled_rect = pygame.Rect(0, 0, int(file_rect.w * scale), int(file_rect.h * scale))
                                scaled_rect.center = file_rect.center
                                pygame.draw.rect(surf, color, scaled_rect, 2, border_radius=3)
                        else:
                            # Fallback: rectángulo con color y escala
                            scaled_rect = pygame.Rect(0, 0, int(file_rect.w * scale), int(file_rect.h * scale))
                            scaled_rect.center = file_rect.center
                            pygame.draw.rect(surf, color, scaled_rect, border_radius=3)
                    else:
                        # Sin imagen: usar rectángulo tradicional con escala
                        scaled_rect = pygame.Rect(0, 0, int(file_rect.w * scale), int(file_rect.h * scale))
                        scaled_rect.center = file_rect.center
                        pygame.draw.rect(surf, color, scaled_rect, border_radius=3)
                        nombre_corto = archivo.nombre[:8] + "..." if len(archivo.nombre) > 8 else archivo.nombre
                        nombre_text = self.fonts["small"].render(nombre_corto, True, (0, 0, 0))
                        text_rect = nombre_text.get_rect(center=scaled_rect.center)
                        surf.blit(nombre_text, text_rect)
                    
                    # Mostrar nombre del archivo en hover
                    if is_hovered:
                        color_txt = (255, 255, 255)
                        indicator_text = self.fonts["small"].render(archivo.nombre, True, color_txt)
                        indicator_pos = (file_rect.centerx, file_rect.top - 10)
                        text_rect = indicator_text.get_rect(center=indicator_pos)
                        surf.blit(indicator_text, text_rect)

            # Directorio actual y archivo seleccionado
            dir_text = self.fonts["title"].render(f"Directory: {self.current_directory}", True, (255, 255, 255))
            surf.blit(dir_text, (10, 10))

            if self.archivo_seleccionado:
                sel_text = self.fonts["normal"].render(f"Seleccionado: {self.archivo_seleccionado.nombre}", True,
                                                       (0, 255, 255))
                surf.blit(sel_text, (SCREEN_W - sel_text.get_width() - 10, 10))

            # Progreso de acciones
            self.dibujar_progreso_accion(surf)

            if self.in_transition:
                progress = self.transition_time / self.transition_duration
                alpha = int(255 * (0.5 - abs(0.5 - progress)))
                overlay = pygame.Surface((SCREEN_W, SCREEN_H))
                overlay.fill((0, 0, 0))
                overlay.set_alpha(alpha)
                surf.blit(overlay, (0, 0))

        if self.paused:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surf.blit(overlay, (0, 0))
            pausa_text = self.fonts["title"].render("PAUSA", True, (255, 255, 255))
            surf.blit(pausa_text,
                      (SCREEN_W // 2 - pausa_text.get_width() // 2, SCREEN_H // 2 - pausa_text.get_height() // 2))
        
        # SISTEMA EDUCATIVO: Renderizar overlay educativo al final (sobre todo)
        self.overlay_educativo.render(surf)

            # --------- Clase principal del juego ----------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("NetDefenders")
        self.clock = pygame.time.Clock()
        
        # Obtener la ruta del directorio del script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        video_path = os.path.join(script_dir, "intro.mp4")
        
        self.current = IntroVideoScreen(self, video_path)
        self.running = True
        # NUEVO: Sistema de estadísticas del jugador
        self.player_stats = PlayerStats("Jugador1")
        
        # Estado de desbloqueo de niveles (memoria de sesión)
        self.unlocked_levels = {
            "Nivel 1": True,
            "Nivel 2": True,
        }
        # Ruta a la fuente TTF del proyecto (archivo 'texto.ttf' en la raíz del proyecto)
        self.font_path = os.path.join(script_dir, "texto.ttf")
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