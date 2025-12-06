# 📊 ¿QUÉ DATOS SE RECOPILAN EXACTAMENTE?

## Resumen Visual Rápido

```
┌─────────────────────────────────────────────────────────────────┐
│  USUARIO COMPLETA EL JUEGO                                      │
│  1. Quiz Inicial (12 preguntas)                                │
│  2. Nivel 1 y/o Nivel 2                                        │
│  3. Quiz Final (mismas 12 preguntas)                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  SE GENERA AUTOMÁTICAMENTE:                                     │
│  📁 quiz_data_collection.json                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Estructura de Datos por Usuario

### 1️⃣ INFORMACIÓN BÁSICA

```json
{
  "session_id": "20251206_143022",          ← ID único de la sesión
  "fecha_hora_completado": "2025-12-06 14:35:18",  ← Cuándo terminó
  "nombre_jugador": "Jugador"               ← Nombre del usuario
}
```

**¿Por qué?** Para identificar cada sesión de juego única.

---

### 2️⃣ RESUMEN DE PUNTUACIONES

```json
"resumen": {
  "quiz_inicial_correctas": 7,      ← Cuántas acertó al inicio
  "quiz_final_correctas": 10,       ← Cuántas acertó al final
  "total_preguntas": 12,            ← Total de preguntas (fijo)
  "mejora_absoluta": 3,             ← Diferencia: 10 - 7 = 3
  "mejora_porcentual": 25.0,        ← Porcentaje de mejora
  "porcentaje_inicial": 58.33,      ← 7/12 = 58.33%
  "porcentaje_final": 83.33         ← 10/12 = 83.33%
}
```

**¿Para qué?** Medir rápidamente si el usuario mejoró y cuánto.

---

### 3️⃣ DESGLOSE POR CATEGORÍA

```json
"desglose_por_categoria": {
  "phishing_nivel1": {
    "inicial_correctas": 3,    ← Acertó 3 de 6 preguntas de phishing
    "final_correctas": 5,      ← Acertó 5 de 6 al final
    "total_preguntas": 6,      ← 6 preguntas de phishing
    "mejora": 2                ← Mejoró en 2 preguntas
  },
  "malware_nivel2": {
    "inicial_correctas": 4,    ← Acertó 4 de 6 preguntas de malware
    "final_correctas": 5,      ← Acertó 5 de 6 al final
    "total_preguntas": 6,      ← 6 preguntas de malware
    "mejora": 1                ← Mejoró en 1 pregunta
  }
}
```

**¿Para qué?** Identificar si el usuario tiene más dificultad con phishing o con malware.

---

### 4️⃣ RESPUESTAS DETALLADAS (Quiz Inicial)

Cada pregunta del quiz inicial se guarda así:

```json
{
  "pregunta_num": 1,
  "pregunta": "¿Qué indica una URL acortada sospechosa?",
  "respuesta_seleccionada": 0,      ← Eligió la opción 0
  "respuesta_correcta": 1,           ← La correcta era la opción 1
  "es_correcta": false,              ← Falló esta pregunta
  "categoria": "level1",             ← Es de phishing
  "timestamp": "2025-12-06 14:30:35" ← Cuándo respondió
}
```

**Se guardan las 12 preguntas del quiz inicial.**

---

### 5️⃣ RESPUESTAS DETALLADAS (Quiz Final)

Lo mismo para el quiz final:

```json
{
  "pregunta_num": 1,
  "pregunta": "¿Qué indica una URL acortada sospechosa?",
  "respuesta_seleccionada": 1,      ← Esta vez eligió la opción 1
  "respuesta_correcta": 1,           ← La correcta es la opción 1
  "es_correcta": true,               ← ✅ Acertó!
  "categoria": "level1",
  "timestamp": "2025-12-06 14:34:22"
}
```

**Se guardan las 12 preguntas del quiz final.**

---

### 6️⃣ ANÁLISIS PREGUNTA POR PREGUNTA

Para cada pregunta, se compara el resultado inicial vs final:

```json
{
  "pregunta_num": 1,
  "pregunta": "¿Qué indica una URL acortada sospechosa?",
  "categoria": "level1",
  
  "inicial_correcta": false,   ← Falló al inicio
  "final_correcta": true,      ← Acertó al final
  
  "mejoro": true,              ← ✅ MEJORÓ en esta pregunta
  "empeoro": false,            ← No empeoró
  "sin_cambio": false,         ← Hubo cambio
  
  "respuesta_inicial": 0,      ← Eligió opción 0 al inicio
  "respuesta_final": 1,        ← Eligió opción 1 al final
  "respuesta_correcta": 1      ← La correcta es 1
}
```

**Casos posibles:**
- `mejoro: true` → Falló inicial, acertó final ✅
- `empeoro: true` → Acertó inicial, falló final ❌
- `sin_cambio: true` → Mismo resultado en ambos (acertó ambos o falló ambos)

---

### 7️⃣ ESTADÍSTICAS AGREGADAS

```json
"estadisticas": {
  "preguntas_mejoradas": 4,              ← En 4 preguntas mejoró
  "preguntas_empeoradas": 1,             ← En 1 pregunta empeoró
  "preguntas_sin_cambio": 7,             ← En 7 no hubo cambio
  "errores_iniciales": 5,                ← Falló 5 al inicio
  "errores_finales": 2,                  ← Falló 2 al final
  "preguntas_siempre_correctas": 7,      ← Acertó 7 en ambos quizzes
  "preguntas_siempre_incorrectas": 0     ← No hay preguntas que siempre falló
}
```

**¿Para qué?** Análisis rápido del progreso del usuario.

---

## 🎯 Ejemplo Completo Simplificado

```
USUARIO: María
SESIÓN: 20251206_153045

PUNTUACIÓN:
  Quiz Inicial: 6/12 (50%)
  Quiz Final: 11/12 (91.67%)
  Mejora: +5 preguntas (41.67%)

POR CATEGORÍA:
  Phishing: 2/6 → 6/6 (+4) ✅ Gran mejora
  Malware: 4/6 → 5/6 (+1)

PREGUNTA #1: "¿Qué indica una URL acortada?"
  Inicial: ❌ (eligió opción 0)
  Final: ✅ (eligió opción 1)
  Resultado: MEJORÓ ✅

PREGUNTA #2: "Señal de phishing en mensaje"
  Inicial: ✅ (eligió opción 0)
  Final: ✅ (eligió opción 0)
  Resultado: SIN CAMBIO (siempre correcta)

...y así para las 12 preguntas

CONCLUSIÓN:
- María mejoró significativamente
- Su debilidad inicial era phishing
- Después del juego, dominó el tema de phishing
- Solo falló 1 pregunta en el quiz final
```

---

## 🔍 ¿Cómo Ver Estos Datos?

### Opción 1: Ver Archivo Directo
Abre `quiz_data_collection.json` en cualquier editor de texto.

### Opción 2: Visualización Rápida
```bash
python ver_datos_rapido.py
```
Muestra resumen visual de todos los usuarios.

### Opción 3: Análisis Completo
```bash
python analizar_quiz.py
```
Menú interactivo con múltiples opciones de análisis.

---

## 📈 Insights que Puedes Obtener

### Por Usuario Individual
- ¿Mejoró después de jugar?
- ¿En qué categoría tiene más dificultad?
- ¿Qué preguntas específicas falló?
- ¿Qué preguntas aprendió después del juego?

### Por Grupo de Usuarios
- ¿Cuál es el promedio de mejora?
- ¿Qué preguntas son más difíciles?
- ¿Qué categoría (phishing vs malware) es más efectiva educativamente?
- ¿Hay preguntas donde los usuarios empeoran? (indica confusión)

### Para Mejorar el Juego
- Identificar preguntas ambiguas
- Reforzar contenido donde hay menos mejora
- Balancear dificultad entre categorías
- Validar efectividad educativa

---

## 🔐 Privacidad

✅ **Todo se guarda localmente** en tu computadora  
✅ **No se envía nada a internet**  
✅ **Puedes borrar los datos cuando quieras**  
✅ **Formato JSON fácil de leer y procesar**

---

## 💡 Ejemplo de Análisis Real

```
DATOS DE 10 USUARIOS:

HALLAZGOS:
1. 90% de usuarios mejoraron (9 de 10)
2. Mejora promedio: 28.5%
3. Pregunta más difícil: #11 (50% de error final)
4. Pregunta donde más mejoraron: #4 (80% mejoró)
5. Phishing: mejora promedio de 2.3 preguntas
6. Malware: mejora promedio de 1.1 preguntas

CONCLUSIÓN:
- El juego es efectivo educativamente
- Contenido de phishing es más efectivo que malware
- Pregunta #11 necesita revisión (muy difícil)
- Pregunta #4 está bien balanceada (reto justo)
```

---

## ❓ Preguntas Frecuentes

**P: ¿Se guardan datos si no completo el quiz final?**  
R: No, solo se guardan al completar el quiz final.

**P: ¿Puedo ver los datos de un usuario específico?**  
R: Sí, cada sesión tiene un `session_id` único.

**P: ¿Cuánto espacio ocupan los datos?**  
R: ~15-20 KB por usuario. Con 100 usuarios, ~2 MB.

**P: ¿Puedo exportar a Excel?**  
R: Sí, usa `analizar_quiz.py` opción 5.

**P: ¿Se guardan respuestas de texto del usuario?**  
R: No, solo qué opción seleccionó (0, 1, 2, o 3).

---

**📚 Más información:**
- `INSTRUCCIONES_RECOLECCION.md` - Guía rápida
- `DATOS_RECOLECTADOS_README.md` - Documentación completa
- `quiz_data_collection_EJEMPLO.json` - Ejemplo de datos reales
