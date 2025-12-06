# 📊 Sistema de Recolección de Datos - NetDefenders

## Descripción General

NetDefenders incluye un sistema completo de recolección y análisis de datos que registra automáticamente el rendimiento de cada usuario en los quizzes inicial y final.

## 📁 Archivos Generados

### 1. `quiz_data_collection.json`
**Propósito:** Almacena todos los datos detallados de los quizzes de cada sesión de juego.

**Contenido por sesión:**

#### Información de Sesión
- `session_id`: Identificador único (fecha_hora)
- `fecha_hora_completado`: Timestamp de finalización
- `nombre_jugador`: Nombre del usuario

#### Resumen General
```json
"resumen": {
  "quiz_inicial_correctas": 8,
  "quiz_final_correctas": 11,
  "total_preguntas": 12,
  "mejora_absoluta": 3,
  "mejora_porcentual": 25.0,
  "porcentaje_inicial": 66.67,
  "porcentaje_final": 91.67
}
```

#### Desglose por Categoría
Separa los resultados entre:
- **Phishing (Nivel 1):** 6 preguntas
- **Malware (Nivel 2):** 6 preguntas

```json
"desglose_por_categoria": {
  "phishing_nivel1": {
    "inicial_correctas": 4,
    "final_correctas": 6,
    "total_preguntas": 6,
    "mejora": 2
  },
  "malware_nivel2": {
    "inicial_correctas": 4,
    "final_correctas": 5,
    "total_preguntas": 6,
    "mejora": 1
  }
}
```

#### Respuestas Detalladas
Cada respuesta incluye:
- `pregunta_num`: Número de pregunta (1-12)
- `pregunta`: Texto completo de la pregunta
- `respuesta_seleccionada`: Índice de la opción elegida (0-3)
- `respuesta_correcta`: Índice de la opción correcta
- `es_correcta`: Boolean indicando si acertó
- `categoria`: "level1" o "level2"
- `timestamp`: Momento exacto de la respuesta

#### Análisis Pregunta por Pregunta
Comparación detallada entre quiz inicial y final:

```json
"analisis_por_pregunta": [
  {
    "pregunta_num": 1,
    "pregunta": "¿Qué indica una URL acortada sospechosa?",
    "categoria": "level1",
    "inicial_correcta": false,
    "final_correcta": true,
    "mejoro": true,
    "empeoro": false,
    "sin_cambio": false,
    "respuesta_inicial": 0,
    "respuesta_final": 1,
    "respuesta_correcta": 1
  }
]
```

**Campos de análisis:**
- `mejoro`: Falló inicialmente pero acertó al final ✅
- `empeoro`: Acertó inicialmente pero falló al final ❌
- `sin_cambio`: Mantuvo el mismo resultado (acertó ambas o falló ambas)

#### Estadísticas Agregadas
```json
"estadisticas": {
  "preguntas_mejoradas": 3,
  "preguntas_empeoradas": 0,
  "preguntas_sin_cambio": 9,
  "errores_iniciales": 4,
  "errores_finales": 1,
  "preguntas_siempre_correctas": 8,
  "preguntas_siempre_incorrectas": 1
}
```

### 2. `datos_recolectados.json`
**Propósito:** Registro de todas las acciones durante el juego (errores y aciertos en los niveles).

**Tipo de datos registrados:**
- Phishing detectado correctamente
- Phishing no detectado (error)
- Falsos positivos
- Correos legítimos identificados
- Detalles de errores en logo, dominio y texto

## 📈 Métricas Clave Disponibles

### Por Usuario (Sesión)
1. **Mejora Porcentual:** Diferencia entre % final e inicial
2. **Mejora Absoluta:** Número de preguntas adicionales correctas
3. **Tasa de Aprendizaje:** Cuántas preguntas inicialmente incorrectas se corrigieron

### Por Categoría
- Rendimiento en Phishing vs Malware
- Identificación de debilidades específicas (nivel 1 o 2)

### Por Pregunta
- Preguntas más difíciles (mayor tasa de error)
- Preguntas donde más usuarios mejoraron
- Preguntas donde usuarios empeoraron (raras pero importantes)

### Patrones de Error
- Errores en logo, dominio o texto
- Correlación entre tipos de error
- Evolución del reconocimiento de patrones

## 🔍 Casos de Uso para Análisis

### 1. Efectividad Educativa
```python
# Ejemplo de análisis
import json

with open('quiz_data_collection.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Calcular mejora promedio
mejoras = [session['resumen']['mejora_porcentual'] for session in data]
mejora_promedio = sum(mejoras) / len(mejoras)
print(f"Mejora promedio: {mejora_promedio:.2f}%")
```

### 2. Identificar Preguntas Difíciles
Analizar `analisis_por_pregunta` para encontrar preguntas con:
- Mayor número de `empeoro` (usuarios que sabían pero olvidaron)
- Mayor número de `inicial_correcta: false` y `final_correcta: false`
- Menor tasa de mejora

### 3. Validar Contenido Educativo
- Si nivel 1 mejora más que nivel 2, el contenido de phishing es más efectivo
- Si muchas preguntas mantienen errores, necesitan refuerzo en el juego

### 4. Segmentación de Usuarios
```json
{
  "expertos": "mejora < 10% (ya sabían)",
  "aprendices": "mejora entre 10-40%",
  "principiantes": "mejora > 40%"
}
```

## 📊 Visualización de Datos (Ejemplo Python)

```python
import json
import matplotlib.pyplot as plt

# Cargar datos
with open('quiz_data_collection.json', 'r', encoding='utf-8') as f:
    sessions = json.load(f)

# Gráfico de mejora por usuario
mejoras = [s['resumen']['mejora_absoluta'] for s in sessions]
plt.hist(mejoras, bins=10)
plt.xlabel('Preguntas Mejoradas')
plt.ylabel('Número de Usuarios')
plt.title('Distribución de Mejora en Quiz')
plt.show()

# Gráfico de preguntas más mejoradas
preguntas_mejora = {}
for session in sessions:
    for pregunta in session['analisis_por_pregunta']:
        num = pregunta['pregunta_num']
        if pregunta['mejoro']:
            preguntas_mejora[num] = preguntas_mejora.get(num, 0) + 1

plt.bar(preguntas_mejora.keys(), preguntas_mejora.values())
plt.xlabel('Número de Pregunta')
plt.ylabel('Usuarios que Mejoraron')
plt.title('Preguntas con Mayor Mejora')
plt.show()
```

## 🔐 Privacidad

- Los datos se almacenan **localmente** en la carpeta del juego
- No se envía información a servidores externos
- Cada sesión tiene un ID único basado en timestamp
- El nombre de jugador se puede anonimizar si es necesario

## 📝 Notas Importantes

1. **Persistencia:** Los datos se guardan automáticamente al completar el quiz final
2. **Formato:** JSON para facilitar procesamiento con cualquier lenguaje
3. **Backup:** Recomendado hacer copias periódicas de los archivos JSON
4. **Análisis:** Compatible con Python, R, Excel, Tableau, y otras herramientas de análisis

## 🎯 Preguntas Específicas del Quiz

### Nivel 1 - Phishing (6 preguntas)
1. URL acortada sospechosa
2. Señales de phishing en mensaje
3. Dominio legítimo de empresa
4. Acción correcta ante solicitud de credenciales
5. Objetivo principal del phishing
6. Adjunto .exe inesperado

### Nivel 2 - Malware (6 preguntas)
1. Características de ransomware
2. Efectos de adware
3. Síntomas de cryptominer
4. Objetivo de spyware
5. Medida ante archivo infectado
6. Primera acción al analizar carpeta sospechosa

## 💡 Recomendaciones de Uso

1. **Educadores:** Analizar patrones de error para mejorar contenido
2. **Investigadores:** Estudiar efectividad de gamificación en ciberseguridad
3. **Desarrolladores:** Identificar preguntas ambiguas o demasiado difíciles
4. **Instituciones:** Evaluar nivel de conciencia en ciberseguridad

---

**Fecha de implementación:** Diciembre 2025  
**Versión del sistema:** 2.0
