"""
Sistema de puntuaciones y registro de errores para NetDefenders
Implementación con POO
"""

import time
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


# ========== SISTEMA DE PUNTUACIONES POR NIVEL ==========

class ScoreManager:
    """
    Maneja el sistema de puntuaciones del juego por nivel.
    """
    def __init__(self, level_number=1):
        self.level_number = level_number
        self.current_score = 0
        self.best_score = 0  # mejor puntaje histórico del nivel
        self.combo = 0
        self.score_multiplier = 1.0
    
    def add_points(self, points, with_combo=True):
        """Añade puntos, considera combo si está activo"""
        if with_combo and self.combo > 0:
            bonus = min(self.combo * 0.1, 2.0)  # max 2x
            points = int(points * (1 + bonus))
        
        self.current_score += int(points * self.score_multiplier)
        self.combo += 1
        
        # actualizar mejor puntaje si superamos el anterior
        if self.current_score > self.best_score:
            self.best_score = self.current_score
        
    def subtract_points(self, penalty):
        """Resta puntos por error"""
        self.current_score = max(0, self.current_score - penalty)
        self.combo = 0
    
    def reset_combo(self):
        """Resetea la racha"""
        self.combo = 0
    
    def get_rank(self, score=None):
        """Devuelve ranking basado en puntos (usa current_score si no se especifica)"""
        score_to_rank = score if score is not None else self.current_score
        if score_to_rank >= 5000:
            return "S"
        elif score_to_rank >= 3000:
            return "A"
        elif score_to_rank >= 1500:
            return "B"
        elif score_to_rank >= 500:
            return "C"
        else:
            return "D"
    
    def reset_current_score(self):
        """Reinicia puntuación actual (mantiene best_score)"""
        self.current_score = 0
        self.combo = 0


# ========== SISTEMA DE REGISTRO DE ERRORES ==========

class Mistake:
    """Representa un error/equivocación individual"""
    def __init__(self, level: int, mistake_type: str, description: str, 
                 mistake_details: Dict = None, timestamp: str = None):
        self.level = level
        self.type = mistake_type
        self.description = description
        self.mistake_details = mistake_details or {}  # Detalles específicos: logo, dominio, texto
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.severity = self._calculate_severity()
    
    def _calculate_severity(self):
        """Calcula gravedad: baja, media, alta, crítica"""
        critical_types = ["contraseña_expuesta", "fuga_datos", "malware_ejecutado"]
        high_types = ["malware_no_detectado", "descarga_sospechosa", "phishing_no_detectado"]
        medium_types = ["falso_positivo", "respuesta_lenta"]
        
        if self.type in critical_types:
            return "crítica"
        elif self.type in high_types:
            return "alta"
        elif self.type in medium_types:
            return "media"
        else:
            return "baja"
    
    def get_severity_color(self):
        """Retorna color RGB según gravedad"""
        colors = {
            "crítica": (220, 20, 20),
            "alta": (255, 100, 0),
            "media": (255, 200, 0),
            "baja": (100, 200, 100)
        }
        return colors.get(self.severity, (255, 255, 255))
    
    def to_dict(self):
        """Convierte a diccionario para guardar/mostrar"""
        return {
            "nivel": self.level,
            "tipo": self.type,
            "descripcion": self.description,
            "detalles": self.mistake_details,
            "fecha_hora": self.timestamp,
            "gravedad": self.severity
        }


class MistakeLog:
    """
    Tabla/log de errores. Almacena todas las equivocaciones.
    Solo guarda datos de la PRIMERA vez que se juega cada nivel.
    Exporta a Excel o JSON.
    """
    def __init__(self, excel_filename: str = "datos_recolectados.xlsx"):
        self.excel_filename = excel_filename
        self.mistakes: List[Mistake] = []
        self.mistake_counts: Dict[str, int] = {}
        self.first_play_per_level: Dict[int, bool] = {}  # Track si es primera vez en cada nivel
        self._load_existing_data()
    
    def _load_existing_data(self):
        """Carga datos existentes para saber qué niveles ya se jugaron"""
        if not EXCEL_AVAILABLE or not os.path.exists(self.excel_filename):
            return
        
        try:
            wb = openpyxl.load_workbook(self.excel_filename)
            if "Registro_Errores" in wb.sheetnames:
                ws = wb["Registro_Errores"]
                # Identificar niveles ya registrados
                for row in ws.iter_rows(min_row=2, values_only=True):
                    if row[0]:  # Si hay nivel
                        self.first_play_per_level[row[0]] = False  # Ya se jugó
            wb.close()
        except Exception as e:
            print(f"Error cargando datos existentes: {e}")
    
    def is_first_play(self, level: int) -> bool:
        """Verifica si es la primera vez jugando este nivel"""
        return self.first_play_per_level.get(level, True)
    
    def mark_level_played(self, level: int):
        """Marca un nivel como ya jugado"""
        self.first_play_per_level[level] = False
    
    def add_mistake(self, level: int, mistake_type: str, description: str, 
                   mistake_details: Dict = None, force_save: bool = False):
        """Registra una nueva equivocación (solo en primera jugada o si force_save=True)"""
        # Solo guardar si es primera vez jugando este nivel o force_save
        if not self.is_first_play(level) and not force_save:
            return  # No guardar en jugadas posteriores
        
        mistake = Mistake(level, mistake_type, description, mistake_details)
        self.mistakes.append(mistake)
        
        # actualizar contador
        self.mistake_counts[mistake_type] = self.mistake_counts.get(mistake_type, 0) + 1
    
    def get_mistakes_by_level(self, level: int) -> List[Mistake]:
        """Obtiene errores de un nivel específico"""
        return [m for m in self.mistakes if m.level == level]
    
    def get_total_mistakes(self) -> int:
        """Total de errores"""
        return len(self.mistakes)
    
    def save_to_excel(self):
        """Guarda el log en Excel con formato"""
        if not EXCEL_AVAILABLE:
            print("openpyxl no está instalado. Usando JSON como alternativa.")
            return self.save_to_json()
        
        try:
            # Crear o cargar workbook
            if os.path.exists(self.excel_filename):
                wb = openpyxl.load_workbook(self.excel_filename)
            else:
                wb = openpyxl.Workbook()
                if "Sheet" in wb.sheetnames:
                    wb.remove(wb["Sheet"])
            
            # Crear o seleccionar hoja
            if "Registro_Errores" not in wb.sheetnames:
                ws = wb.create_sheet("Registro_Errores")
                # Crear encabezados
                headers = ["Nivel", "Fecha/Hora", "Tipo de Acción", "Descripción", 
                          "Error en Logo", "Error en Dominio", "Error en Texto", "Número de Errores"]
                ws.append(headers)
                
                # Estilo de encabezados
                header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                header_font = Font(bold=True, color="FFFFFF")
                for cell in ws[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                ws = wb["Registro_Errores"]
            
            # Agregar todas las acciones con contador de errores individual por acción
            action_count = len([row for row in ws.iter_rows(min_row=2)]) + 1  # Contar acciones existentes
            
            for mistake in self.mistakes:
                details = mistake.mistake_details
                
                # Contar errores en esta acción específica (Logo, Dominio, Texto marcados incorrectamente)
                errores_en_esta_accion = 0
                if details.get("logo"):  # Si cometió error en Logo
                    errores_en_esta_accion += 1
                if details.get("dominio"):  # Si cometió error en Dominio
                    errores_en_esta_accion += 1
                if details.get("texto"):  # Si cometió error en Texto
                    errores_en_esta_accion += 1
                
                # Si no hay errores específicos pero la acción es un error general, contar como 1
                if errores_en_esta_accion == 0 and mistake.type in ["phishing_no_detectado", "falso_positivo"]:
                    errores_en_esta_accion = 1
                
                ws.append([
                    mistake.level,
                    mistake.timestamp,
                    mistake.type,
                    mistake.description,
                    "Sí" if details.get("logo") else "No",
                    "Sí" if details.get("dominio") else "No",
                    "Sí" if details.get("texto") else "No",
                    errores_en_esta_accion  # Puede ser 0, 1, 2, o 3 dependiendo de cuántos errores
                ])
                action_count += 1
            
            # Ajustar ancho de columnas
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # Guardar
            wb.save(self.excel_filename)
            wb.close()
            
            # Limpiar lista temporal (ya se guardó)
            self.mistakes.clear()
            
            return True
        except Exception as e:
            print(f"Error guardando Excel: {e}")
            return self.save_to_json()
    
    def save_to_json(self):
        """Guarda en JSON como alternativa"""
        filename = self.excel_filename.replace('.xlsx', '.json')
        try:
            # Cargar datos existentes si existen
            existing_data = []
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # Agregar nuevos errores
            for mistake in self.mistakes:
                existing_data.append(mistake.to_dict())
            
            # Guardar todo
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            # Limpiar lista temporal
            self.mistakes.clear()
            
            return True
        except Exception as e:
            print(f"Error guardando JSON: {e}")
            return False
    
    def clear(self):
        """Limpia el log temporal (no afecta archivo guardado)"""
        self.mistakes.clear()
        self.mistake_counts.clear()


# ========== ESTADÍSTICAS DEL JUGADOR POR NIVEL ==========

class PlayerStats:
    """
    Centraliza estadísticas por nivel.
    - Puntajes separados por nivel
    - Solo guarda errores en primera jugada
    - Actualiza mejor puntaje si se supera
    """
    def __init__(self, player_name: str = "Jugador"):
        self.name = player_name
        
        # Sistema de puntuación por nivel (3 niveles)
        self.level_scores = {
            1: ScoreManager(level_number=1),
            2: ScoreManager(level_number=2),
            3: ScoreManager(level_number=3)
        }
        
        # Sistema de registro de errores (único para todos los niveles)
        self.mistake_log = MistakeLog()
        
        # Nivel actual
        self.current_level = 1
        
        # Estadísticas temporales por sesión (no se guardan permanentemente)
        self.session_stats = {
            "emails_analyzed": 0,
            "threats_detected": 0,
            "threats_missed": 0,
            "false_positives": 0
        }
    
    def set_current_level(self, level: int):
        """Cambia el nivel actual"""
        if level in self.level_scores:
            self.current_level = level
            # Resetear puntuación actual del nivel para nueva partida
            self.level_scores[level].reset_current_score()
    
    def get_current_score_manager(self) -> ScoreManager:
        """Obtiene el ScoreManager del nivel actual"""
        return self.level_scores.get(self.current_level)
    
    def analyze_email(self, is_threat: bool, detected_correctly: bool, 
                     mistake_details: Dict = None):
        """
        Registra análisis de un email.
        Guarda TODAS las acciones (aciertos y errores) en Excel/JSON si es primera vez jugando el nivel.
        """
        self.session_stats["emails_analyzed"] += 1
        score_mgr = self.get_current_score_manager()
        
        if is_threat and detected_correctly:
            # Detectó correctamente una amenaza
            self.session_stats["threats_detected"] += 1
            score_mgr.add_points(100)
            
            # NUEVO: Registrar acierto también
            self.mistake_log.add_mistake(
                level=self.current_level,
                mistake_type="amenaza_detectada_correctamente",
                description="Amenaza identificada y reportada correctamente",
                mistake_details=mistake_details or {}
            )
            
        elif is_threat and not detected_correctly:
            # Dejó pasar una amenaza (ERROR GRAVE)
            self.session_stats["threats_missed"] += 1
            
            # Guardar error si es primera jugada del nivel
            self.mistake_log.add_mistake(
                level=self.current_level,
                mistake_type="phishing_no_detectado",
                description="Amenaza no detectada en el correo",
                mistake_details=mistake_details or {}
            )
            
            score_mgr.subtract_points(80)
            
        elif not is_threat and detected_correctly:
            # Identificó correctamente un email legítimo
            score_mgr.add_points(50)
            
            # NUEVO: Registrar acierto también
            self.mistake_log.add_mistake(
                level=self.current_level,
                mistake_type="correo_legitimo_identificado",
                description="Correo legítimo procesado correctamente",
                mistake_details=mistake_details or {}
            )
            
        else:  # not is_threat and not detected_correctly
            # Falso positivo (marcó como amenaza algo legítimo)
            self.session_stats["false_positives"] += 1
            
            # Guardar error si es primera jugada del nivel
            self.mistake_log.add_mistake(
                level=self.current_level,
                mistake_type="falso_positivo",
                description="Correo legítimo marcado como amenaza",
                mistake_details=mistake_details or {}
            )
            
            score_mgr.subtract_points(30)
    
    def complete_level(self):
        """
        Completa el nivel actual.
        Guarda errores a Excel si es primera jugada.
        Actualiza mejor puntaje si se superó.
        """
        score_mgr = self.get_current_score_manager()
        
        # Actualizar mejor puntaje si se superó
        if score_mgr.current_score > score_mgr.best_score:
            score_mgr.best_score = score_mgr.current_score
        
        # Guardar errores a Excel solo si fue primera jugada
        if self.mistake_log.is_first_play(self.current_level):
            self.mistake_log.save_to_excel()
            self.mistake_log.mark_level_played(self.current_level)
        
        # Limpiar errores temporales
        self.mistake_log.clear()
    
    def get_accuracy(self) -> float:
        """Calcula precisión de la sesión actual (0-100)"""
        total = self.session_stats["emails_analyzed"]
        if total == 0:
            return 100.0
        
        correct = (self.session_stats["threats_detected"] + 
                  (total - self.session_stats["threats_detected"] - 
                   self.session_stats["threats_missed"] - 
                   self.session_stats["false_positives"]))
        return (correct / total) * 100
    
    def get_level_rank(self, level: int) -> str:
        """Obtiene el rango del nivel basado en su mejor puntaje"""
        if level in self.level_scores:
            return self.level_scores[level].get_rank(self.level_scores[level].best_score)
        return "D"
    
    def get_level_best_score(self, level: int) -> int:
        """Obtiene el mejor puntaje de un nivel"""
        if level in self.level_scores:
            return self.level_scores[level].best_score
        return 0
    
    def get_level_current_score(self, level: int) -> int:
        """Obtiene el puntaje actual de un nivel"""
        if level in self.level_scores:
            return self.level_scores[level].current_score
        return 0
    
    def reset_session_stats(self):
        """Reinicia estadísticas de la sesión"""
        self.session_stats = {
            "emails_analyzed": 0,
            "threats_detected": 0,
            "threats_missed": 0,
            "false_positives": 0
        }
