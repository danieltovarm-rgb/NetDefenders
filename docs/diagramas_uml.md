# 📊 Diagramas UML - NetDefenders

## Diagrama de Clases Principal

```mermaid
classDiagram
    class GameManager {
        -pygame: Module
        -clock: Clock
        -screen: Surface
        -current_state: GameState
        -level_manager: LevelManager
        -player_stats: PlayerStats
        +__init__()
        +run()
        +change_state(state)
        +handle_events()
    }
    
    class PlayerStats {
        -current_level: int
        -best_scores: Dict
        -unlocked_levels: Set
        -mistake_log: MistakeLog
        -quiz_stats: Dict
        +complete_level(level, score)
        +get_ranking(score)
        +save_to_excel()
        +load_from_excel()
    }
    
    class LevelManager {
        <<abstract>>
        #score_manager: ScoreManager
        #mistake_log: MistakeLog
        +initialize()*
        +update(dt)*
        +render(screen)*
        +check_victory()*
    }
    
    class PhishingDetectorManager {
        -emails: List~Email~
        -current_email_index: int
        -overlay_educativo: OverlayEducativo
        +load_emails()
        +display_email(email)
        +classify_email(decision)
        +show_educational_moment()
    }
    
    class Level2GameManager {
        -resource_bar: ResourceBar
        -symptom_manager: SymptomManager
        -virus_manager: GestorVirus
        -overlay_educativo: OverlayEducativo
        -quiz_bonus: QuizBonusSystem
        +spawn_viruses()
        +execute_action(tool, file)
        +check_game_state()
        +apply_final_bonus()
    }
    
    class ScoreManager {
        -current_score: int
        -combo_multiplier: float
        -level: int
        +add_points(base)
        +apply_combo()
        +reset_combo()
        +get_final_score()
    }
    
    class ResourceBar {
        -current: int
        -max_resources: int
        -display_value: float
        +consume(amount)
        +restore(amount)
        +is_depleted()
        +render(screen)
    }
    
    class OverlayEducativo {
        -active_overlays: List
        -cooldowns: Dict
        -tipos_tip_mostrados: Set
        +mostrar_tip(tipo, mensaje)
        +mostrar_quiz_interactivo(data, callback)
        +mostrar_error_educativo(info)
        +actualizar(dt)
        +renderizar(screen)
    }
    
    class SymptomManager {
        -active_symptoms: Set
        -drain_rates: Dict
        -visual_effects: Dict
        +activate_symptom(type)
        +deactivate_symptom(type)
        +apply_effects(dt, resource_bar)
        +render_effects(screen)
    }
    
    class QuizBonusSystem {
        -quiz_correctas: int
        -quiz_totales: int
        +registrar_respuesta(correcta)
        +calcular_bonus()
        +get_porcentaje_aciertos()
    }
    
    class MistakeLog {
        -mistakes: List~Dict~
        +add_mistake(level, tipo, detalles)
        +export_to_excel(filename)
        +get_statistics()
    }
    
    GameManager --> PlayerStats
    GameManager --> LevelManager
    LevelManager <|-- PhishingDetectorManager
    LevelManager <|-- Level2GameManager
    LevelManager --> ScoreManager
    LevelManager --> MistakeLog
    PhishingDetectorManager --> OverlayEducativo
    Level2GameManager --> ResourceBar
    Level2GameManager --> SymptomManager
    Level2GameManager --> OverlayEducativo
    Level2GameManager --> QuizBonusSystem
    PlayerStats --> MistakeLog
```

## Diagrama de Secuencia: Nivel 1 - Clasificación de Email

```mermaid
sequenceDiagram
    actor Usuario
    participant PM as PhishingDetectorManager
    participant SM as ScoreManager
    participant OE as OverlayEducativo
    participant QB as QuizBonusSystem
    participant ML as MistakeLog
    
    Usuario->>PM: Clasificar email como phishing
    PM->>PM: Verificar clasificación
    
    alt Clasificación correcta
        PM->>SM: add_points(100)
        SM-->>PM: Puntos agregados
        PM->>OE: mostrar_tip(tipo_phishing)
        OE-->>Usuario: Mostrar tip educativo
        PM->>OE: mostrar_quiz_interactivo(quiz_data)
        OE-->>Usuario: Mostrar quiz 3 opciones
        Usuario->>OE: Seleccionar respuesta A
        OE->>QB: registrar_respuesta(True)
        QB->>SM: add_points(50)
        OE-->>Usuario: ✅ Correcto +50 pts
    else Clasificación incorrecta
        PM->>SM: subtract_points(50)
        PM->>OE: mostrar_error_educativo(detalles)
        OE-->>Usuario: ⚠️ Error explicado
    end
    
    PM->>ML: add_mistake(level, tipo, detalles)
    ML-->>PM: Registro guardado
```

## Diagrama de Secuencia: Nivel 2 - Escanear Archivo

```mermaid
sequenceDiagram
    actor Usuario
    participant L2 as Level2GameManager
    participant RB as ResourceBar
    participant SM as ScoreManager
    participant SymM as SymptomManager
    participant OE as OverlayEducativo
    participant QB as QuizBonusSystem
    
    Usuario->>L2: Seleccionar archivo
    Usuario->>L2: Escanear (-10 recursos)
    L2->>RB: consume(10)
    RB-->>L2: Recursos: 100→90
    L2->>L2: Progreso 3 segundos
    L2->>L2: Evaluar archivo
    
    alt Archivo infectado
        L2->>SM: add_points(20)
        L2-->>Usuario: 🦠 MINER detectado
        
        alt Primera vez este tipo
            L2->>OE: mostrar_quiz_interactivo(quiz_miner)
            OE-->>Usuario: Quiz: ¿Señal de miner?
            Usuario->>OE: Responder opción A
            
            alt Respuesta correcta
                OE->>QB: registrar_respuesta(True)
                OE->>RB: restore(4)
                RB-->>Usuario: +4 recursos (90→94)
                OE-->>Usuario: ✅ Correcto +4 rec
            else Respuesta incorrecta
                OE->>QB: registrar_respuesta(False)
                OE->>RB: consume(2)
                RB-->>Usuario: -2 recursos (90→88)
                OE-->>Usuario: ❌ Incorrecto -2 rec
            end
        end
        
        Usuario->>L2: Limpiar archivo
        L2->>SM: add_points(100)
        L2->>RB: restore(3)
        L2->>SymM: deactivate_symptom("ralentizacion")
        SymM-->>Usuario: FPS 30→60
        L2->>OE: mostrar_refuerzo_sintoma()
        OE-->>Usuario: ✅ Bien hecho +3 rec
        
    else Archivo limpio
        L2-->>Usuario: ✅ Archivo seguro
    end
```

## Diagrama de Componentes

```mermaid
graph TB
    subgraph Frontend["🎮 Frontend (Pygame)"]
        UI[UI Manager]
        Renderer[Renderer]
        EventHandler[Event Handler]
    end
    
    subgraph GameLogic["🧠 Lógica de Juego"]
        GM[Game Manager]
        LM1[Level 1 Manager]
        LM2[Level 2 Manager]
        StateM[State Manager]
    end
    
    subgraph Systems["⚙️ Sistemas"]
        Score[Score Manager]
        Resource[Resource Manager]
        Overlay[Overlay Educativo]
        Quiz[Quiz System]
        Symptom[Symptom Manager]
    end
    
    subgraph Data["💾 Datos y Persistencia"]
        Stats[Player Stats]
        Log[Mistake Log]
        Excel[Excel Exporter]
    end
    
    subgraph Assets["🎨 Assets"]
        Images[Imágenes]
        Fonts[Fuentes]
        Videos[Videos]
        Sounds[Sonidos]
    end
    
    UI --> GM
    EventHandler --> GM
    GM --> LM1
    GM --> LM2
    GM --> StateM
    
    LM1 --> Score
    LM1 --> Overlay
    LM2 --> Resource
    LM2 --> Score
    LM2 --> Overlay
    LM2 --> Symptom
    LM2 --> Quiz
    
    Score --> Stats
    Overlay --> Quiz
    Log --> Excel
    Stats --> Log
    
    Renderer --> Assets
    UI --> Assets
```

## Diagrama de Estados del Juego

```mermaid
stateDiagram-v2
    [*] --> Inicio
    Inicio --> TestInicial
    TestInicial --> AsignarModoTutor
    AsignarModoTutor --> MenuPrincipal
    
    MenuPrincipal --> SeleccionNivel
    SeleccionNivel --> Nivel1
    SeleccionNivel --> Nivel2
    SeleccionNivel --> TestFinal
    
    state Nivel1 {
        [*] --> CargandoEmails
        CargandoEmails --> MostrandoEmail
        MostrandoEmail --> ClasificandoEmail
        ClasificandoEmail --> MomentEducativo
        MomentEducativo --> Quiz
        Quiz --> ActualizandoScore
        ActualizandoScore --> SiguienteEmail
        SiguienteEmail --> MostrandoEmail: Hay más emails
        SiguienteEmail --> EvaluacionFinal: Todos analizados
        EvaluacionFinal --> Victoria: Score >= 500
        EvaluacionFinal --> Derrota: Score < 500
    }
    
    state Nivel2 {
        [*] --> InicializandoRecursos
        InicializandoRecursos --> GenerandoVirus
        GenerandoVirus --> ActivandoSintomas
        ActivandoSintomas --> NavegandoSistema
        NavegandoSistema --> SeleccionandoArchivo
        SeleccionandoArchivo --> EjecutandoAccion
        EjecutandoAccion --> MostrandoQuiz: Primera vez malware
        MostrandoQuiz --> ActualizandoEstado
        EjecutandoAccion --> ActualizandoEstado: Acción completada
        ActualizandoEstado --> VerificandoCondiciones
        VerificandoCondiciones --> NavegandoSistema: Jugando
        VerificandoCondiciones --> VictoriaN2: Todos eliminados
        VerificandoCondiciones --> DerrotaN2: Recursos agotados
    }
    
    Victoria --> PantallaResultados
    Derrota --> PantallaResultados
    VictoriaN2 --> PantallaResultados
    DerrotaN2 --> PantallaResultados
    PantallaResultados --> MenuPrincipal
    
    TestFinal --> Certificacion: >= 70%
    TestFinal --> TestFinal: < 70% (reintentar)
    Certificacion --> MenuPrincipal
    
    MenuPrincipal --> [*]: Salir
```

## Diagrama de Actividades: Flujo de un Nivel Completo

```mermaid
flowchart TD
    Start([Iniciar Nivel]) --> Init[Inicializar componentes]
    Init --> Load[Cargar datos nivel]
    Load --> Tutorial[Mostrar tutorial]
    Tutorial --> Loop{Bucle principal}
    
    Loop -->|Actualizar| Update[Update dt]
    Update --> CheckInput{Hay input?}
    
    CheckInput -->|Sí| ProcessAction[Procesar acción]
    CheckInput -->|No| CheckPassive
    
    ProcessAction --> Evaluate{Evaluar resultado}
    
    Evaluate -->|Éxito| Success[Score +<br/>Feedback positivo]
    Evaluate -->|Error| Error[Score -<br/>Feedback correctivo]
    
    Success --> ShowQuiz{Activar quiz?}
    Error --> ShowQuiz
    
    ShowQuiz -->|Sí| DisplayQuiz[Mostrar quiz]
    ShowQuiz -->|No| LogData
    
    DisplayQuiz --> WaitAnswer[Esperar respuesta]
    WaitAnswer --> EvalQuiz{Correcta?}
    
    EvalQuiz -->|Sí| BonusPoints[Bonus puntos<br/>+ recursos]
    EvalQuiz -->|No| Penalty[Penalización<br/>+ tip educativo]
    
    BonusPoints --> LogData
    Penalty --> LogData
    
    LogData[Registrar en telemetría] --> CheckPassive
    
    CheckPassive[Efectos pasivos<br/>Síntomas, drenaje] --> CheckConditions{Verificar estado}
    
    CheckConditions -->|Recursos agotados| Defeat[Derrota]
    CheckConditions -->|Objetivos completados| Victory[Victoria]
    CheckConditions -->|Continuar| Loop
    
    Victory --> CalcBonus[Calcular bonus finales]
    CalcBonus --> SaveResults[Guardar resultados]
    
    Defeat --> SaveProgress[Guardar progreso]
    
    SaveResults --> ShowStats[Mostrar estadísticas]
    SaveProgress --> ShowStats
    
    ShowStats --> End([Fin Nivel])
```

---

**Equipo NetDefenders** | [Volver al índice](README.md)
