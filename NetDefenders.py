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
    """Envuelve el texto al ancho y lo recorta con '...' para que no supere el alto disponible.
    Devuelve una lista de líneas renderizables dentro de (max_w x max_h).
    """
    # Convertir saltos de línea en tokens para respetarlos
    words = text.replace('\n', ' \n ').split(' ')
    lines = []
    current = ""
    line_h = font.get_height()
    max_lines = max(1, (max_h + line_spacing) // (line_h + line_spacing))

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

    # Recorta última línea si se pasó del ancho y agrega '...'
    if lines:
        lines[-1] = truncate_ellipsis(lines[-1], font, max_w)
    # Limita a la cantidad de líneas que caben
    return lines[:max_lines]

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
    def __init__(self, es_legitimo, tipo_malicioso, contenido, remitente, asunto, razones_correctas, logo_path=None):
        self.es_legitimo = es_legitimo
        self.tipo_malicioso = tipo_malicioso
        self.contenido = contenido
        self.remitente = remitente
        self.asunto = asunto
        self.razones_correctas = razones_correctas
        self.logo_path = logo_path  # opcional: logo para mostrar en inbox y panel
        self.procesado = False
        self.visible = True

    def load_logo(self, max_size=(36, 36)):
        """Carga el logo si existe, con fallback a None. Cache simple en atributo _logo_surface."""
        if hasattr(self, "_logo_surface"):
            return getattr(self, "_logo_surface")
        surf = None
        if self.logo_path:
            try:
                img = pygame.image.load(self.logo_path).convert_alpha()
                surf = pygame.transform.smoothscale(img, max_size)
            except Exception:
                surf = None
        self._logo_surface = surf
        return surf

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

    def handle_event(self, event, hacker_rect=None):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None
        header, panel = self._calc_rects(hacker_rect)
        if not panel.collidepoint(event.pos):
            return None
        # calcular clicks por fila
        y = panel.y + 12
        for c in self.correos:
            if not c.visible or c.procesado:
                continue
            row = pygame.Rect(panel.x + 10, y, panel.w - 20, self.row_h)
            if row.collidepoint(event.pos):
                return c
            y += self.row_h + self.vgap
        return None

    def render(self, surf, hacker_rect=None):
        header, panel = self._calc_rects(hacker_rect)
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
        # filas
        y = panel.y + 12
        mx, my = pygame.mouse.get_pos()
        for c in self.correos:
            if not c.visible or c.procesado:
                continue
            row = pygame.Rect(panel.x + 10, y, panel.w - 20, self.row_h)
            hovered = row.collidepoint(mx, my)
            bg = (35, 42, 64) if hovered else (28, 34, 48)
            pygame.draw.rect(surf, bg, row, border_radius=10)
            pygame.draw.rect(surf, (60, 70, 100), row, 1, border_radius=10)
            # padding interno
            pad_x = 10
            pad_y = 6
            inner_w = row.w - pad_x * 2 - 30  # 30 para la casilla derecha
            # asunto en color
            subj_color = (120, 255, 140) if c.es_legitimo else (255, 120, 120)
            subj = truncate_ellipsis(c.asunto, self.font_row, inner_w)
            surf.blit(self.font_row.render(subj, True, subj_color), (row.x + pad_x, row.y + pad_y))
            # dominio en gris
            dom = truncate_ellipsis(c.remitente, self.font_row, inner_w)
            dom_color = (200, 200, 200)
            surf.blit(self.font_row.render(dom, True, dom_color), (row.x + pad_x, row.y + pad_y + self.font_row.get_height() + 2))
            # casilla a la derecha
            box = pygame.Rect(row.right - 26, row.y + (row.h - 22) // 2, 22, 22)
            pygame.draw.rect(surf, (40, 46, 66), box, border_radius=5)
            pygame.draw.rect(surf, (120, 130, 160), box, 1, border_radius=5)
            y += self.row_h + self.vgap


class EmailPanel:
    """Panel del correo abierto, con botones de imagen y logo del remitente."""
    def __init__(self, correo, font_text, font_buttons, hacker_rect_provider=None):
        self.correo = correo
        self.font_text = font_text
        self.font_buttons = font_buttons
        self._hacker_rect_provider = hacker_rect_provider
        self.rect = pygame.Rect(150, 100, 500, 350)

        # tipo de escritura
        self.texto_completo = f"De: {correo.remitente}\nAsunto: {correo.asunto}\n\n{correo.contenido}"
        self.texto_actual = self.texto_completo[:1]
        self.tiempo_escritura = 0
        self.velocidad_escritura = 30

        # botones por imagen (con fallback)
        self.btn_back = ImageButton((0, 0), (80, 30), label_text="Volver", font=font_text)
        self.btn_responder = ImageButton((0, 0), (160, 44),
            image_paths=["assets/btn_responder.png", "assets/btn_reply.png"], label_text="Responder", font=font_buttons)
        self.btn_eliminar = ImageButton((0, 0), (160, 44),
            image_paths=["assets/btn_eliminar.png", "assets/btn_delete.png"], label_text="Eliminar", font=font_buttons)
        self.btn_reportar = ImageButton((0, 0), (160, 44),
            image_paths=["assets/btn_reportar.png", "assets/btn_report.png"], label_text="Reportar", font=font_buttons)

        # flujo de razones
        self.mode = "reading"  # reading | reasons
        self.razones_sel = []
        self.btn_razones = [
            {"rect": pygame.Rect(0, 0, 120, 30), "razon": "Logo", "texto": "Logo"},
            {"rect": pygame.Rect(0, 0, 120, 30), "razon": "Dominio", "texto": "Dominio"},
            {"rect": pygame.Rect(0, 0, 120, 30), "razon": "Texto", "texto": "Texto"},
        ]
        self.btn_confirmar = pygame.Rect(0, 0, 120, 38)
        self._accion_pendiente = None

    def update(self, dt):
        if self.mode == "reading" and len(self.texto_actual) < len(self.texto_completo):
            self.tiempo_escritura += dt
            if self.tiempo_escritura >= self.velocidad_escritura:
                self.tiempo_escritura = 0
                self.texto_actual += self.texto_completo[len(self.texto_actual)]

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None
        # completar el texto con click
        # text area comienza debajo del header y del logo centrado
        header_h = 24
        logo_h = 64
        top_y = self.rect.y + 8 + header_h + 10 + logo_h + 14
        text_area = pygame.Rect(self.rect.x + 10, top_y, self.rect.w - 20, self.rect.h - (top_y - self.rect.y) - 60)
        if text_area.collidepoint(event.pos) and len(self.texto_actual) < len(self.texto_completo):
            self.texto_actual = self.texto_completo
            return None

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
        return None

    def render(self, surf):
        # panel
        pygame.draw.rect(surf, (30, 30, 50), self.rect, border_radius=10)
        pygame.draw.rect(surf, (150, 150, 200), self.rect, 2, border_radius=10)
        # header con remitente
        header_rect = pygame.Rect(self.rect.x + 8, self.rect.y + 8, self.rect.w - 16, 24)
        pygame.draw.rect(surf, (22, 22, 34), header_rect, border_radius=8)
        remit = f"De: {self.correo.remitente}"
        remit_txt = truncate_ellipsis(remit, self.font_text, header_rect.w - 12)
        surf.blit(self.font_text.render(remit_txt, True, (220, 220, 220)), (header_rect.x + 6, header_rect.y + 3))

        # logo centrado arriba
        logo = self.correo.load_logo(max_size=(64, 64))
        logo_y = header_rect.bottom + 10
        if logo:
            surf.blit(logo, (self.rect.centerx - logo.get_width() // 2, logo_y))
            used_logo_h = logo.get_height()
        else:
            # placeholder si no hay logo
            ph = pygame.Rect(self.rect.centerx - 32, logo_y, 64, 64)
            pygame.draw.rect(surf, (60, 70, 90), ph)
            pygame.draw.rect(surf, (220, 220, 235), ph, 2)
            used_logo_h = 64

        # área de texto y render con envoltura y clipping para no salir del panel
        text_x = self.rect.x + 10
        text_y = logo_y + used_logo_h + 14
        text_w = self.rect.w - 20
        text_h = self.rect.bottom - 10 - text_y  # deja 10px de margen inferior
        if text_h > 0:
            lines = wrap_ellipsis(self.texto_actual, self.font_text, text_w, text_h, line_spacing=5)
            # establecer clip para asegurar que no se dibuje fuera
            prev_clip = surf.get_clip()
            clip_rect = pygame.Rect(text_x, text_y, text_w, text_h)
            surf.set_clip(clip_rect)
            y_pos = text_y
            for line in lines:
                t = self.font_text.render(line, True, (255, 255, 255))
                surf.blit(t, (text_x, y_pos))
                y_pos += t.get_height() + 5
            surf.set_clip(prev_clip)

        # layout botones
        bx = self.rect.x + 10
        by = self.rect.y + self.rect.h - 30 - 10
        self.btn_back.rect.update(bx, by, 80, 30)
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
        # UI OO: bandeja e email panel
        self.inbox = Inbox(self.correos, self.font, self.small_font)
        self.email_panel = None

        # proveedor de rect del hacker para EmailPanel
        self._get_hacker_rect = lambda: self.hacker_sprite.rect

        # Texto animado
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
        return [
            # CORREOS MALICIOSOS
            Correo(
                es_legitimo=False,
                tipo_malicioso="dinero",
                remitente="premios@loteria-falsa.com",
                asunto="¡GANASTE $1,000,000! Reclama tu premio",
                contenido="Felicidades, has sido seleccionado para recibir $1,000,000. Haz clic aquí y paga $50 de procesamiento para reclamar tu premio inmediatamente. ¡Oferta por tiempo limitado!",
                razones_correctas=["Dominio", "Texto"],
                logo_path="assets/logos/loteria.png"
            ),
            Correo(
                es_legitimo=False,
                tipo_malicioso="contraseñas",
                remitente="soporte@faceb00k-security.com",
                asunto="Problema de seguridad en tu cuenta",
                contenido="Hemos detectado acceso no autorizado a tu cuenta. Para protegerla, verifica tu identidad ingresando tu contraseña actual aquí. De lo contrario, tu cuenta será suspendida en 24 horas.",
                razones_correctas=["Dominio", "Logo", "Texto"],
                logo_path="assets/logos/facebook.png"
            ),
            Correo(
                es_legitimo=False,
                tipo_malicioso="suscripciones",
                remitente="servicio@premium-gratis.com",
                asunto="Servicio Premium por tiempo limitado",
                contenido="Obtén 3 meses gratis de nuestro servicio premium. Solo ingresa tus datos de tarjeta para verificación. ¡No te cobraremos nada hasta después del periodo de prueba!",
                razones_correctas=["Dominio", "Texto"],
                logo_path="assets/logos/premium.png"
            ),

            # CORREOS LEGÍTIMOS
            Correo(
                es_legitimo=True,
                tipo_malicioso=None,
                remitente="soporte@bancoreal.com",
                asunto="Actualización de términos de servicio",
                contenido="Estimado cliente, hemos actualizado nuestros términos de servicio. No se requiere acción de tu parte. Puedes revisar los cambios en nuestra página web oficial.",
                razones_correctas=[],
                logo_path="assets/logos/banco_real.png"
            ),
            Correo(
                es_legitimo=True,
                tipo_malicioso=None,
                remitente="notificaciones@red-social.com",
                asunto="Nueva solicitud de amistad",
                contenido="Tienes una nueva solicitud de amistad de un contacto conocido. Inicia sesión en la plataforma para aceptar o rechazar la solicitud.",
                razones_correctas=[],
                logo_path="assets/logos/red_social.png"
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
        # Mostrar inmediatamente el primer carácter para evitar un frame en blanco
        self.texto_actual = texto[0] if texto else ""
        self.tiempo_escritura = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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
                    res = self.email_panel.handle_event(event)
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

            # selección de razones gestionada por EmailPanel

    def update(self, dt):
        self.hacker_sprite.update(dt)

        # Actualizar texto animado (solo narrativa inicial; el correo lo maneja EmailPanel)
        if (self.show_narrative and self.estado == "narrativa_inicial") and len(self.texto_actual) < len(self.texto_completo):
            self.tiempo_escritura += dt
            if self.tiempo_escritura >= self.velocidad_escritura:
                self.tiempo_escritura = 0
                self.texto_actual += self.texto_completo[len(self.texto_actual)]

        # Actualizar email panel
        if self.estado == "correo_abierto" and self.email_panel:
            self.email_panel.update(dt)

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

        # Bandeja de entrada (solo cuando no hay narrativa ni correo abierto)
        if self.estado in ("esperando_correo",) and not self.show_narrative:
            self.inbox.render(surf, hacker_rect=self.hacker_sprite.rect)

        # Narrativa inicial
        if self.show_narrative:
            box = pygame.Rect(100, 150, 600, 300)
            pygame.draw.rect(surf, (20, 20, 40), box, border_radius=10)
            pygame.draw.rect(surf, (100, 100, 200), box, 2, border_radius=10)

            # Mostrar narrativa con animación de texto (usar self.texto_actual)
            wrapped_lines = self._wrap_text(self.texto_actual if self.texto_actual else self.narrative_lines[self.narrative_index], self.font, box.width - 40)

            y_offset = 20
            for wrapped in wrapped_lines:
                text_surf = self.font.render(wrapped, True, (255, 255, 255))
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