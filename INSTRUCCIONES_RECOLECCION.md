# 🛡️ Sistema de Recolección de Datos - Guía de Inicio Rápido

## 📋 ¿Qué se recolecta?

NetDefenders ahora incluye un **sistema completo de recolección de datos** que registra automáticamente:

### ✅ Datos del Quiz (Nuevo Sistema)
- **Respuestas individuales** de cada pregunta (12 preguntas totales)
- **Comparación pregunta por pregunta** entre quiz inicial y final
- **Identificación de mejoras**: qué preguntas el usuario falló primero y luego acertó
- **Identificación de empeoramientos**: qué preguntas el usuario acertó primero y luego falló
- **Análisis por categoría**: Phishing (Nivel 1) vs Malware (Nivel 2)
- **Porcentaje de mejora** personalizado por usuario

### ✅ Datos del Juego (Sistema Existente)
- Aciertos y errores en cada nivel
- Detalles de errores en logo, dominio y texto
- Acciones correctas e incorrectas

---

## 🚀 Inicio Rápido

### 1. Jugar el juego normalmente
```bash
python NetDefenders_AVANCE.py
```

El usuario debe:
1. Completar el **quiz inicial** (12 preguntas)
2. Jugar el **Nivel 1** y/o **Nivel 2**
3. Completar el **quiz final** (mismas 12 preguntas)

### 2. Los datos se guardan automáticamente en:
- `quiz_data_collection.json` - Datos completos del quiz
- `datos_recolectados.json` - Acciones durante el juego

### 3. Analizar los datos
```bash
python analizar_quiz.py
```

Este script interactivo te permite:
- Ver estadísticas generales de todos los usuarios
- Analizar rendimiento por categoría (Phishing vs Malware)
- Identificar las preguntas más difíciles
- Ver análisis individual de cada usuario
- Exportar resumen a CSV para Excel

---

## 📊 Ejemplo de Uso del Análisis

```bash
$ python analizar_quiz.py

🛡️  NETDEFENDERS - ANÁLISIS DE DATOS DEL QUIZ
======================================================================

Selecciona una opción:
----------------------------------------------------------------------
1. 📊 Análisis General (todos los usuarios)
2. 🎯 Análisis por Categoría (Phishing vs Malware)
3. ❓ Análisis por Pregunta (dificultad y mejora)
4. 👤 Análisis Individual (cada usuario)
5. 📄 Exportar resumen a CSV
6. 🔄 Análisis Completo (todas las opciones)
0. ❌ Salir

Opción: 1

======================================================================
📊 ANÁLISIS GENERAL - TODOS LOS USUARIOS
======================================================================

👥 Total de usuarios analizados: 15
📈 Mejora porcentual promedio: 28.50%
📈 Mejora absoluta promedio: 3.40 preguntas

📝 Promedio quiz inicial: 6.80/12
📝 Promedio quiz final: 10.20/12

📊 Distribución de resultados:
   ✅ Mejoraron: 13 (86.7%)
   ➖ Sin cambio: 1 (6.7%)
   ❌ Empeoraron: 1 (6.7%)
```

---

## 📁 Estructura de Archivos

```
NetDefenders/
├── NetDefenders_AVANCE.py           # Juego principal
├── stats_system.py                  # Sistema de estadísticas (modificado)
├── analizar_quiz.py                 # 🆕 Herramienta de análisis
├── quiz_data_collection.json        # 🆕 Datos del quiz (generado automáticamente)
├── quiz_data_collection_EJEMPLO.json # Ejemplo de estructura de datos
├── datos_recolectados.json          # Datos de acciones en el juego
├── DATOS_RECOLECTADOS_README.md     # 🆕 Documentación completa
└── INSTRUCCIONES_RECOLECCION.md     # Este archivo
```

---

## 🔍 ¿Qué puedes descubrir?

### Para Educadores
- ¿Qué preguntas causan más dificultad?
- ¿El juego realmente enseña? (medido por mejora %)
- ¿Qué categoría necesita más refuerzo? (Phishing vs Malware)

### Para Investigadores
- Efectividad de gamificación en educación de ciberseguridad
- Patrones de aprendizaje en conceptos de phishing vs malware
- Correlación entre tiempo de juego y mejora en conocimiento

### Para Desarrolladores
- Identificar preguntas ambiguas o demasiado difíciles
- Optimizar contenido educativo del juego
- Balancear dificultad entre niveles

---

## 📈 Métricas Disponibles

### Por Usuario
- Mejora absoluta (número de preguntas)
- Mejora porcentual (%)
- Preguntas que mejoró
- Preguntas que empeoró
- Preguntas siempre correctas
- Preguntas siempre incorrectas

### Por Pregunta
- Cuántos usuarios mejoraron en cada pregunta
- Cuántos usuarios empeoraron
- Tasa de error inicial vs final
- Identificación de preguntas más difíciles

### Por Categoría
- Rendimiento en Phishing (6 preguntas)
- Rendimiento en Malware (6 preguntas)
- Comparación de mejora entre categorías

---

## 💡 Ejemplo de Insights

### Pregunta más mejorada
```
✅ Pregunta #4: "Acción correcta ante un correo que pide credenciales urgente"
   → 12 usuarios mejoraron (80%)
   → Indica que el nivel 1 enseña efectivamente este concepto
```

### Pregunta más difícil
```
❌ Pregunta #11: "Medida segura al detectar archivo sospechoso infectado"
   → 5 usuarios fallaron en quiz final (33%)
   → Sugiere necesidad de reforzar este concepto en nivel 2
```

### Categoría con mayor mejora
```
🎯 PHISHING: Mejora promedio de 2.3 preguntas
🦠 MALWARE: Mejora promedio de 1.1 preguntas
   → El contenido de phishing es más efectivo educativamente
```

---

## 🔐 Privacidad y Seguridad

- ✅ Todos los datos se guardan **localmente**
- ✅ No hay conexión a internet ni servidores externos
- ✅ Los datos están en formato JSON (fácil de analizar)
- ✅ Puedes anonimizar o eliminar datos en cualquier momento

---

## 🛠️ Análisis Avanzado

### Exportar a Excel
```bash
python analizar_quiz.py
# Seleccionar opción 5 para exportar CSV
```

### Análisis con Python
```python
import json

# Cargar datos
with open('quiz_data_collection.json', 'r', encoding='utf-8') as f:
    datos = json.load(f)

# Ejemplo: Calcular mejora promedio
mejoras = [sesion['resumen']['mejora_porcentual'] for sesion in datos]
print(f"Mejora promedio: {sum(mejoras)/len(mejoras):.2f}%")
```

### Análisis con R
```r
library(jsonlite)

# Cargar datos
datos <- fromJSON("quiz_data_collection.json")

# Análisis estadístico
summary(datos$resumen$mejora_porcentual)
```

---

## 📚 Recursos Adicionales

- **Documentación completa**: `DATOS_RECOLECTADOS_README.md`
- **Ejemplo de datos**: `quiz_data_collection_EJEMPLO.json`
- **Script de análisis**: `analizar_quiz.py`

---

## ❓ Preguntas Frecuentes

### ¿Los datos se guardan cada vez que juego?
Sí, cada sesión completa (quiz inicial + juego + quiz final) genera una nueva entrada con un `session_id` único.

### ¿Puedo borrar los datos?
Sí, simplemente elimina los archivos JSON. El juego creará nuevos archivos vacíos cuando sea necesario.

### ¿Cuánto espacio ocupan los datos?
Aproximadamente 15-20 KB por usuario. Con 100 usuarios serían ~2 MB.

### ¿Necesito instalar algo adicional?
No para la recolección. Para el script de análisis, solo Python 3.7+ (ya incluido si juegas el juego).

### ¿Puedo usar los datos para mi investigación?
Sí, los datos son tuyos. Solo asegúrate de cumplir con las regulaciones de privacidad de tu institución.

---

## 🎯 Próximos Pasos

1. ✅ Juega el juego completo (quiz inicial + niveles + quiz final)
2. ✅ Ejecuta `python analizar_quiz.py` para ver los resultados
3. ✅ Revisa `DATOS_RECOLECTADOS_README.md` para análisis más profundos
4. ✅ Exporta a CSV si necesitas análisis en Excel
5. ✅ Comparte tus insights para mejorar el juego

---

**¿Necesitas ayuda?** Revisa la documentación completa en `DATOS_RECOLECTADOS_README.md`
