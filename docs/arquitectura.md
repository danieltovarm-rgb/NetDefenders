# 🏗️ Arquitectura del Sistema - NetDefenders

## Visión General

NetDefenders está diseñado siguiendo principios de **Programación Orientada a Objetos (POO)** con una arquitectura modular que facilita la extensibilidad y mantenimiento.

## Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────┐
│                    GAME ENGINE (Pygame)                 │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼──────┐  ┌────────▼────────┐
│  Game Manager  │  │Asset Manager│  │  State Manager  │
│   Principal    │  │             │  │                 │
└───────┬────────┘  └──────┬──────┘  └────────┬────────┘
        │                   │                   │
        ├───────────────────┴───────────────────┤
        │                                       │
┌───────▼────────┐                    ┌────────▼────────┐
│  Level Manager │                    │  Player Stats   │
│                │                    │                 │
│  ┌──────────┐  │                    │  - Puntuación   │
│  │ Nivel 1  │  │                    │  - Progreso     │
│  │ Nivel 2  │  │                    │  - Telemetría   │
│  └──────────┘  │                    └─────────────────┘
└───────┬────────┘
        │
        ├──────────────┬──────────────┬──────────────┐
        │              │              │              │
┌───────▼────┐  ┌─────▼─────┐ ┌─────▼─────┐ ┌──────▼──────┐
│Score       │  │Resource   │ │Overlay    │ │Quiz Bonus   │
│Manager     │  │Manager    │ │Educativo  │ │System       │
└────────────┘  └───────────┘ └───────────┘ └─────────────┘
```

## Componentes Principales

### 1. **Game Manager Principal** (`NetDefenders_AVANCE.py`)
**Responsabilidad**: Controlador central del juego

```python
class GameManager:
    - Inicialización de Pygame
    - Loop principal del juego
    - Gestión de estados (menu, jugando, pausado)
    - Coordinación entre niveles
    - Manejo de eventos globales
```

**Relaciones**:
- Compone: `LevelManager`, `PlayerStats`, `AssetManager`
- Usa: `StateManager` para transiciones

---

### 2. **Level Manager** (Específico por nivel)
**Responsabilidad**: Gestión de la lógica de cada nivel

#### Nivel 1: `PhishingDetectorManager`
```python
class PhishingDetectorManager:
    - emails: List[Email]
    - score_manager: ScoreManager
    - mistake_log: MistakeLog
    - current_email_index: int
    
    Métodos:
    - load_emails()
    - display_email(email)
    - classify_email(decision)
    - check_victory()
```

#### Nivel 2: `Level2GameManager`
```python
class Level2GameManager:
    - resource_bar: ResourceBar
    - score_manager: ScoreManager
    - symptom_manager: SymptomManager
    - virus_manager: GestorVirus
    - overlay_educativo: OverlayEducativo
    
    Métodos:
    - spawn_viruses()
    - activate_symptoms()
    - execute_action(tool, file)
    - check_game_state()
```

---

### 3. **Player Stats** (`PlayerStats`)
**Responsabilidad**: Persistencia y seguimiento del progreso

```python
class PlayerStats:
    - current_level: int
    - best_scores: Dict[int, int]
    - unlocked_levels: Set[int]
    - mistake_log: MistakeLog
    - quiz_stats: Dict
    
    Métodos:
    - complete_level(level, score)
    - get_ranking(score)
    - save_to_excel()
    - load_from_excel()
```

---

### 4. **Score Manager** (`ScoreManager`)
**Responsabilidad**: Gestión de puntuación y combos

```python
class ScoreManager:
    - current_score: int
    - combo_multiplier: float
    - level: int
    
    Métodos:
    - add_points(base_points)
    - apply_combo()
    - reset_combo()
    - get_final_score()
```

---

### 5. **Resource Manager** (`ResourceBar`) - Nivel 2
**Responsabilidad**: Economía de recursos

```python
class ResourceBar:
    - current: int (0-100)
    - max_resources: int
    
    Métodos:
    - consume(amount)
    - restore(amount)
    - is_depleted() -> bool
    - get_percentage() -> float
```

---

### 6. **Overlay Educativo** (`OverlayEducativo`)
**Responsabilidad**: Sistema de tutoriales y feedback

```python
class OverlayEducativo:
    - active_overlays: List[Overlay]
    - cooldowns: Dict[str, float]
    - prioridades: Dict[int, Overlay]
    
    Métodos:
    - mostrar_tip(tipo, mensaje)
    - mostrar_quiz_interactivo(quiz_data, callback)
    - mostrar_error_educativo(error_info)
    - actualizar_cooldowns(dt)
```

---

### 7. **Symptom Manager** (`SymptomManager`) - Nivel 2
**Responsabilidad**: Efectos visuales y mecánicas de síntomas

```python
class SymptomManager:
    - active_symptoms: Set[str]
    - drain_rates: Dict[str, float]
    
    Métodos:
    - activate_symptom(symptom_type)
    - deactivate_symptom(symptom_type)
    - apply_effects(dt, resource_bar)
    - render_effects(screen)
```

---

### 8. **Quiz Bonus System** (`QuizBonusSystem`) - Nivel 2
**Responsabilidad**: Sistema de bonificación por quizzes

```python
class QuizBonusSystem:
    - quiz_correctas: int
    - quiz_totales: int
    
    Métodos:
    - registrar_respuesta(correcta: bool)
    - calcular_bonus() -> int
    - get_porcentaje_aciertos() -> float
```

---

### 9. **Mistake Log** (`MistakeLog`)
**Responsabilidad**: Telemetría y registro de errores

```python
class MistakeLog:
    - mistakes: List[Dict]
    
    Métodos:
    - add_mistake(level, tipo, detalles)
    - export_to_excel(filename)
    - get_statistics() -> Dict
```

---

## Patrones de Diseño Utilizados

### 1. **Singleton** - PlayerStats
```python
class PlayerStats:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**Justificación**: Solo debe existir una instancia de estadísticas del jugador en toda la aplicación.

---

### 2. **Observer** - Sistema de Eventos
```python
class EventManager:
    observers = {}
    
    def subscribe(event_type, callback):
        observers[event_type].append(callback)
    
    def notify(event_type, data):
        for callback in observers[event_type]:
            callback(data)
```

**Uso**: Notificar cambios en recursos, puntuación, síntomas.

---

### 3. **State Pattern** - Estados del Juego
```python
class GameState(Enum):
    MENU = 0
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3
    VICTORY = 4

class StateManager:
    current_state: GameState
    
    def change_state(new_state):
        # Transición y limpieza
```

---

### 4. **Factory** - Creación de Emails y Virus
```python
class EmailFactory:
    @staticmethod
    def create_phishing_email(tipo):
        # Crea email según tipo
        
class VirusFactory:
    @staticmethod
    def create_virus(malware_type):
        # Crea archivo infectado según tipo
```

---

### 5. **Strategy** - Modos de Tutor
```python
class TutorStrategy(ABC):
    @abstractmethod
    def get_tip_cooldown(self): pass
    
class TutorReforzado(TutorStrategy):
    def get_tip_cooldown(self): return 10
    
class TutorRapido(TutorStrategy):
    def get_tip_cooldown(self): return 60
```

---

## Flujo de Datos

### Nivel 1: Clasificación de Email
```
Usuario clasifica email
        │
        ▼
PhishingDetectorManager.classify_email()
        │
        ├─► ScoreManager.add_points()
        ├─► MistakeLog.add_mistake()
        ├─► OverlayEducativo.mostrar_tip()
        └─► OverlayEducativo.mostrar_quiz()
                │
                ▼
        QuizBonusSystem.registrar_respuesta()
                │
                ▼
        ScoreManager.add_bonus()
```

### Nivel 2: Acción sobre Archivo
```
Usuario selecciona herramienta
        │
        ▼
Level2GameManager.execute_action()
        │
        ├─► ResourceBar.consume()
        ├─► Progreso de acción (3s)
        ├─► Evaluar resultado
        │   │
        │   ├─► Éxito:
        │   │   ├─► ScoreManager.add_points()
        │   │   ├─► ResourceBar.restore(+3)
        │   │   ├─► SymptomManager.deactivate()
        │   │   └─► OverlayEducativo.mostrar_refuerzo()
        │   │
        │   └─► Error:
        │       ├─► ScoreManager.subtract_points()
        │       ├─► ResourceBar.consume_extra()
        │       └─► OverlayEducativo.mostrar_error()
        │
        ├─► MistakeLog.add_mistake()
        └─► VictoryChecker.check_conditions()
```

---

## Gestión de Memoria

### Assets Cargados en Inicio
- Fuentes (1-3 tipos)
- Iconos básicos (herramientas, síntomas)
- Sonidos cortos (feedback)

### Assets Cargados por Nivel
- Imágenes de fondo específicas
- Sprites de emails/archivos
- Videos de narrativa (descargados después de uso)

### Telemetría
- Buffer en memoria (max 100 entradas)
- Flush a Excel cada 50 acciones o al finalizar nivel

---

## Escalabilidad

### Agregar Nuevo Nivel
1. Crear clase `LevelXManager` heredando de `BaseLevelManager`
2. Implementar métodos abstractos: `initialize()`, `update()`, `check_victory()`
3. Registrar en `GameManager.levels`
4. Definir condiciones de desbloqueo en `PlayerStats`

### Agregar Nuevo Tipo de Malware
1. Agregar entrada en `GestorVirus.tipos_malware`
2. Definir síntoma en `SymptomManager.symptom_effects`
3. Crear quiz en `OverlayEducativo.quiz_database`
4. Actualizar `VirusFactory`

---

## Dependencias entre Módulos

```
GameManager
    └── LevelManager (Nivel 1 o 2)
            ├── ScoreManager
            ├── ResourceBar (solo Nivel 2)
            ├── OverlayEducativo
            │       └── QuizBonusSystem
            ├── SymptomManager (solo Nivel 2)
            └── MistakeLog
                    └── PlayerStats
```

**Acoplamiento**: Bajo - Los módulos se comunican por interfaces claras
**Cohesión**: Alta - Cada clase tiene una responsabilidad única

---

## Próximos Pasos de Arquitectura

- [ ] Implementar sistema de guardado/carga automático
- [ ] Añadir soporte para múltiples perfiles de jugador
- [ ] Sistema de logros y desafíos
- [ ] API REST para rankings globales
- [ ] Sistema de mods/extensiones

---

**Equipo NetDefenders** | [Volver al índice](README.md)
