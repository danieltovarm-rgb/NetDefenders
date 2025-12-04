# ⚖️ Sistema de Recursos - NetDefenders

## Descripción General

El **Sistema de Recursos** es exclusivo del **Nivel 2** y representa la capacidad del sistema (CPU, RAM, Ancho de Banda) para ejecutar acciones de seguridad. Es un recurso unificado que el jugador debe gestionar cuidadosamente.

---

## Barra de Recursos

### Especificaciones Técnicas

```python
class ResourceBar:
    max_resources: int = 100
    current: float = 100.0
    display_value: float = 100.0  # Para animaciones suaves
    
    # Colores según nivel
    color_critical: (255, 0, 0)     # < 20%: Rojo
    color_warning: (255, 165, 0)    # 20-50%: Naranja
    color_normal: (0, 255, 0)       # > 50%: Verde
```

### Representación Visual

```
┌─────────────────────────────────────────────────┐
│ RECURSOS DEL SISTEMA                            │
├─────────────────────────────────────────────────┤
│ ████████████████████████░░░░░░░░░░░░░░░  65/100 │
│                                                 │
│ CPU: ██████████░░░░░░░░░░ 50%                  │
│ RAM: ████████████████░░░░ 70%                  │
│ RED: ████████████░░░░░░░░ 60%                  │
└─────────────────────────────────────────────────┘
```

**Nota**: Los sub-componentes (CPU, RAM, RED) son visuales. La mecánica usa un solo valor unificado.

---

## Economía de Recursos

### 1. **Consumo por Acción**

| Herramienta | Costo Base | Duración | Costo Total (c/síntomas) |
|-------------|------------|----------|--------------------------|
| 🔍 Escanear | -10 | 3 seg | -10 a -13 |
| 🧹 Limpiar | -15 | 5 seg | -15 a -20 |
| 📦 Cuarentena | -5 | 2 seg | -5 a -8 |
| 🗑️ Eliminar | -8 | 3 seg | -8 a -11 |

**Modificador por Síntomas Activos**:
```python
# Si hay Miner activo:
costo_real = costo_base + 3

# Si hay Troyano activo:
costo_real = costo_base + 5
```

---

### 2. **Regeneración de Recursos**

#### A. Regeneración Pasiva
```python
Cada 5 segundos: +2 recursos
Máximo: 100 recursos

# Código conceptual
if tiempo_transcurrido >= 5.0:
    recursos = min(recursos + 2, 100)
    tiempo_transcurrido = 0
```

**Nota**: La regeneración pasiva se detiene si hay síntomas críticos activos (Ransomware).

---

#### B. Regeneración por Aciertos

| Evento | Bonus Recursos |
|--------|----------------|
| Escanear archivo infectado | +0 (solo puntos) |
| Limpiar correctamente | +3 |
| Cuarentena correcta | +2 |
| Eliminar malware | +5 |
| Quiz correcto | +4 |
| Desactivar síntoma crítico | +8 |

**Ejemplo de Ciclo Virtuoso**:
```
Estado inicial: 65 recursos

1. Escanear archivo (-10) → 55 recursos
2. Detecta MINER (+0) → 55 recursos
3. Limpiar MINER (-15) → 40 recursos
4. Éxito: Limpiar (+3) → 43 recursos
5. Desactivar síntoma CPU (+8) → 51 recursos
6. Quiz MINER correcto (+4) → 55 recursos

Balance neto: 55 - 65 = -10 recursos
Pero eliminaste una amenaza crítica
```

---

### 3. **Drenaje por Síntomas**

Cada tipo de malware activo drena recursos por segundo:

```python
class SymptomDrain:
    VIRUS_RALENTIZACION = -1.0  # por segundo
    TROYANO_RAM = -2.0
    RANSOMWARE_CIFRADO = -3.0  # CRÍTICO
    SPYWARE_RED = -1.5
    MINER_CPU = -2.5
```

#### Drenaje Acumulativo

```python
# Si tienes 3 malware activos simultáneamente:
# VIRUS + TROYANO + MINER

drenaje_total = -1.0 + (-2.0) + (-2.5)
                = -5.5 recursos por segundo

# En 10 segundos:
pérdida_total = -5.5 * 10 = -55 recursos
```

**Estrategia**: Prioriza eliminar malware con mayor drenaje (Ransomware > Miner > Troyano).

---

## Mecánicas Avanzadas

### 1. **Estado Crítico** (< 20 recursos)

```python
if recursos < 20:
    # Efectos visuales
    - Barra parpadea en rojo
    - Sonido de alerta
    - Mensaje: "¡RECURSOS CRÍTICOS!"
    
    # Penalizaciones
    - Acciones cuestan +5 extra
    - Regeneración pasiva se detiene
    - No se pueden usar herramientas costosas (Limpiar)
```

**Única opción**: Cuarentena (-5) o esperar regeneración.

---

### 2. **Estado de Emergencia** (< 10 recursos)

```python
if recursos < 10:
    # Restricciones severas
    - Solo Cuarentena disponible (-5)
    - Regeneración muy lenta (+1 cada 10 seg)
    - Pantalla con tinte rojo
    - Advertencia: "SISTEMA A PUNTO DE COLAPSAR"
    
    # Riesgo alto de derrota
```

---

### 3. **Agotamiento Total** (0 recursos)

```python
if recursos <= 0:
    # DERROTA INMEDIATA
    - Pantalla de "SISTEMA COLAPSADO"
    - Mostrar estadísticas parciales
    - Malware eliminado: X/10
    - Opción: Reintentar / Volver al menú
```

---

## Balance del Sistema

### Recursos Totales Teóricos

```python
# Escenario ideal (sin errores)
Inicio: 100 recursos

Fase 1 - Escanear todo (20 archivos):
  20 * (-10) = -200 recursos

Fase 2 - Limpiar malware (10 infectados):
  10 * (-15) = -150 recursos
  10 * (+3) = +30 recursos (bonus)
  Neto: -120 recursos

Fase 3 - Quizzes (5 tipos):
  5 * (+4) = +20 recursos

Fase 4 - Regeneración pasiva (10 min):
  600 seg / 5 = 120 ciclos
  120 * (+2) = +240 recursos

Fase 5 - Drenaje síntomas (promedio -2/seg * 300 seg):
  -600 recursos

BALANCE TOTAL:
100 - 200 - 120 + 20 + 240 - 600 = -560 recursos

¡IMPOSIBLE sin gestión estratégica!
```

### Estrategia Óptima

```python
# Para completar el nivel con recursos positivos:

1. NO escanear todo primero
   → Escanear solo archivos sospechosos
   → Ahorrar -100 recursos

2. Priorizar malware crítico
   → Eliminar Ransomware primero (drenaje -3/seg)
   → Reducir drenaje acumulado

3. Responder todos los quizzes
   → 5 * (+4) = +20 recursos garantizados

4. Usar Cuarentena estratégicamente
   → Más barato (-5 vs -15)
   → Desactiva síntomas igual

5. Aprovechar regeneración pasiva
   → Esperar 5 seg entre acciones
   → +2 recursos cada pausa

BALANCE OPTIMIZADO:
100 - 100 - 100 + 30 + 20 + 150 - 300 = -200 recursos

Aún difícil, pero viable si:
- Respondes quizzes (+20)
- Bonos por eficiencia (+50)
- Minimizas errores (0 penalizaciones)
```

---

## Casos de Uso

### Caso 1: Jugador Agresivo
```
Estrategia: Limpiar todo rápido sin escanear

Resultado:
  - 50% de aciertos (5/10 correctos)
  - 5 errores * (-10 recursos) = -50
  - 5 aciertos * (+3 recursos) = +15
  - Tiempo total: 3 minutos
  - Drenaje: -360 recursos
  
  BALANCE: 100 - 150 + 15 - 360 = -395
  
  DERROTA en minuto 4
```

### Caso 2: Jugador Conservador
```
Estrategia: Escanear todo, luego limpiar

Resultado:
  - 100% de aciertos (10/10 correctos)
  - 0 errores
  - 10 aciertos * (+3) = +30
  - Tiempo total: 8 minutos
  - Drenaje: -960 recursos (por tiempo)
  
  BALANCE: 100 - 200 - 150 + 30 - 960 = -1180
  
  DERROTA en minuto 5 (por drenaje acumulado)
```

### Caso 3: Jugador Estratégico ✅
```
Estrategia: Escanear selectivo, priorizar críticos

Resultado:
  - Escanear solo sospechosos (12 archivos): -120
  - 8/10 aciertos en limpieza: +24
  - 2 errores: -20 penalización
  - Tiempo total: 5 minutos
  - Priorizar Ransomware y Miner: -480 drenaje
  - Quizzes: +20
  - Regeneración aprovechada: +40
  
  BALANCE: 100 - 120 - 120 + 24 - 20 - 480 + 20 + 40 = -556
  
  Aún DERROTA... pero cerca. Con bonos finales:
    - Bonus eficiencia: +50
    - Bonus velocidad: +30
    
  BALANCE FINAL: -556 + 80 = -476
  
  ¡Aún derrota! El nivel 2 es DIFÍCIL por diseño.
```

---

## Mejoras Propuestas para Balance

### Opción A: Aumentar Regeneración Pasiva
```python
ACTUAL: +2 cada 5 segundos
PROPUESTA: +3 cada 5 segundos

Impacto: +60 recursos en 5 minutos
```

### Opción B: Reducir Drenaje de Síntomas
```python
ACTUAL: Ransomware -3/seg
PROPUESTA: Ransomware -2/seg

Impacto: -120 recursos menos en 2 minutos
```

### Opción C: Aumentar Bonus por Aciertos
```python
ACTUAL: Limpiar correctamente +3
PROPUESTA: Limpiar correctamente +5

Impacto: +20 recursos extras (10 malware)
```

### Opción D: Recursos Iniciales Mayores
```python
ACTUAL: 100 recursos iniciales
PROPUESTA: 120 recursos iniciales

Impacto: +20% de margen de error
```

---

## Telemetría de Recursos

```python
# Registrado cada segundo
{
  "timestamp": "2025-12-03 12:15:43",
  "recursos_actuales": 45,
  "drenaje_activo": -3.5,
  "sintomas_activos": ["ransomware", "miner"],
  "regeneracion_pasiva_activa": True,
  "estado": "warning"  # normal, warning, critical, emergency
}

# Registrado por acción
{
  "accion": "limpiar",
  "recursos_antes": 65,
  "recursos_despues": 53,
  "costo_real": -15,
  "bonus_aplicado": +3,
  "sintomas_afectando_costo": ["troyano"]
}
```

---

## Indicadores Visuales

### Barra Principal
```python
if recursos > 50:
    color = VERDE
elif recursos > 20:
    color = NARANJA
    parpadeo = False
else:
    color = ROJO
    parpadeo = True  # Alerta visual
```

### Iconos de Estado
```
[✅] Recursos normales (> 50)
[⚠️] Recursos bajos (20-50)
[🚨] Recursos críticos (< 20)
[💀] Sistema colapsando (< 10)
```

---

**Equipo NetDefenders** | [Volver al índice](README.md)
