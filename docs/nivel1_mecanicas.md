# 📧 Nivel 1: Detector de Phishing - Mecánicas Detalladas

## Descripción General

El Nivel 1 enseña al jugador a identificar correos electrónicos fraudulentos (phishing) mediante análisis de señales características. Es el nivel introductorio enfocado en **ingeniería social y ataques de phishing**.

---

## Objetivos de Aprendizaje

### Conceptuales
- Identificar dominios sospechosos
- Reconocer urgencia artificial
- Detectar errores ortográficos
- Evaluar autenticidad de remitentes
- Analizar enlaces y archivos adjuntos

### Procedimentales
- Inspeccionar elementos de un email
- Verificar dominios de remitentes
- Analizar cuerpo del mensaje
- Tomar decisiones rápidas

### Actitudinales
- Desarrollar escepticismo saludable
- Práctica de verificación antes de actuar
- Conciencia de consecuencias

---

## Mecánicas del Juego

### 1. **Bandeja de Correos**

**Total de Emails**: 10 correos
- **5 emails phishing** (variados tipos)
- **5 emails legítimos**
- **Distribución aleatoria**

#### Tipos de Phishing Incluidos:
1. **Dominio falso** - banco-seguro.ru vs banco-oficial.com
2. **Urgencia artificial** - "¡ACTÚA AHORA O PERDERÁS TU CUENTA!"
3. **Solicitud de credenciales** - "Verifica tu contraseña aquí"
4. **Archivo adjunto malicioso** - factura.exe
5. **Suplantación de identidad** - Email "de tu jefe"

---

### 2. **Herramientas de Análisis**

#### Inspección Visual
```
┌─────────────────────────────────────┐
│ De: soporte@banco-seguro.info       │ ← Hover: Ver dominio real
│ Asunto: ¡Alerta de seguridad!       │ ← Indicador de urgencia
│                                     │
│ Estimado cliente,                   │
│ Su cuenta ha sido comprometida.     │
│ Haga clic aquí para verificar:     │
│ http://banco-falso.ru/login.php     │ ← Hover: Ver URL destino
│                                     │
│ Adjunto: verificacion.exe (2MB)     │ ← Extensión sospechosa
└─────────────────────────────────────┘
```

#### Opciones de Interacción
- **Hover en enlaces**: Muestra URL real de destino
- **Click en remitente**: Muestra dominio completo
- **Click en adjuntos**: Muestra extensión y tamaño
- **Análisis de cuerpo**: Resalta palabras clave (urgencia, amenazas)

---

### 3. **Sistema de Decisión**

El jugador puede tomar **3 acciones**:

#### A. Marcar como Phishing 🚨
```python
Consecuencias si CORRECTO:
  +200 puntos base
  +Combo multiplicador (x1.2, x1.5, x2.0)
  threats_detected++
  
  → Activar Momento Educativo:
     1. Tip explicativo (señales detectadas)
     2. Quiz interactivo (3 opciones)
     
Consecuencias si INCORRECTO (falso positivo):
  -100 puntos
  Combo = 0
  false_positives++
  
  → Overlay de error:
     - Por qué era legítimo
     - Señales de confianza ignoradas
```

#### B. Marcar como Legítimo ✅
```python
Consecuencias si CORRECTO:
  +150 puntos base
  +Pequeño combo (x1.1)
  
  → Feedback breve: "Bien identificado"
  
Consecuencias si INCORRECTO (falso negativo):
  -150 puntos (CRÍTICO)
  Combo = 0
  threats_missed++
  
  → Overlay de error crítico:
     - Amenaza que se dejó pasar
     - Consecuencias potenciales
     - Señales que se ignoraron
```

#### C. Ignorar/Saltar ⏭️
```python
Si era phishing:
  -100 puntos
  Telemetría: email_ignorado_amenaza
  
Si era legítimo:
  Sin cambios
  Telemetría: email_ignorado_seguro
```

---

### 4. **Momento Educativo**

Activado cuando el jugador **detecta correctamente un phishing por primera vez de cada tipo**.

#### Estructura:

##### Fase 1: Tip Explicativo (5 segundos)
```
┌───────────────────────────────────────┐
│ ⚠️ SEÑALES DE PHISHING DETECTADAS     │
│ ─────────────────────────────────────│
│ • Dominio sospechoso: .ru            │
│ • Urgencia artificial: "¡AHORA!"     │
│ • Solicita credenciales              │
│ • Errores ortográficos               │
│                                      │
│ ¿Sabías que...?                      │
│ El 91% de ciberataques empiezan      │
│ con un email de phishing             │
└───────────────────────────────────────┘
```

##### Fase 2: Quiz Interactivo
```
┌───────────────────────────────────────┐
│ 🎯 ¿Cuál era la señal más clara?     │
│                                      │
│ ⬜ A) Dominio terminado en .ru       │
│ ⬜ B) Logo del banco oficial         │
│ ⬜ C) Gramática perfecta             │
│                                      │
│ Haz clic en tu respuesta             │
└───────────────────────────────────────┘
```

**Botones interactivos** con efectos hover.

**Respuesta Correcta (A)**:
```
✅ ¡Bien hecho! +200 puntos bonus
   
   Explicación:
   Los dominios .ru, .tk, .ml son comúnmente
   usados en phishing por ser gratuitos y
   difíciles de rastrear.
```

**Respuesta Incorrecta**:
```
❌ Incorrecto. Sin bonus.
   
   La respuesta correcta era: A
   
   Explicación:
   Aunque el logo parezca oficial, los
   atacantes pueden copiarlo. El dominio
   es la señal más confiable.
```

---

### 5. **Sistema de Combos**

```python
Combo Multiplier:
├─ 0 detecciones seguidas: x1.0 (base)
├─ 3 detecciones seguidas: x1.2 (+20%)
├─ 5 detecciones seguidas: x1.5 (+50%)
└─ 10 detecciones seguidas: x2.0 (+100%)

Reset de combo:
- Al clasificar incorrectamente
- Al ignorar un email
- Al pasar de nivel
```

**Ejemplo**:
```
Email 1 (phishing): +200 pts x1.0 = 200 pts
Email 2 (phishing): +200 pts x1.0 = 200 pts
Email 3 (phishing): +200 pts x1.0 = 200 pts
Email 4 (phishing): +200 pts x1.2 = 240 pts ← Combo activado
Email 5 (legítimo): +150 pts x1.2 = 180 pts
Email 6 (phishing): +200 pts x1.5 = 300 pts
Email 7 (error): Combo = 0
```

---

### 6. **Condiciones de Victoria**

```python
Victoria:
  - Analizar los 10 emails
  - Score final >= 1000 puntos
  
  → Desbloquear Nivel 2
  → Exportar telemetría a Excel
  → Mostrar video de victoria
  → Pantalla de resultados
```

### 7. **Condiciones de Derrota**

```python
Derrota:
  - Score final < 1000 puntos
  
  → Mostrar áreas de mejora
  → Opción de reintentar
  → Guardar progreso parcial
```

---

## Tabla de Puntuación Detallada

| Acción | Resultado | Puntos | Combo |
|--------|-----------|--------|-------|
| Detectar phishing | Correcto | +200 | +1 |
| Detectar phishing | Incorrecto (FP) | -100 | Reset |
| Quiz phishing | Correcto | +200 | - |
| Quiz phishing | Incorrecto | 0 | - |
| Marcar legítimo | Correcto | +150 | +0.5 |
| Marcar legítimo | Incorrecto (FN) | -150 | Reset |
| Ignorar email | Era phishing | -100 | Reset |
| Ignorar email | Era legítimo | 0 | - |

---

## Ejemplos de Emails

### Email Phishing #1: Dominio Falso
```
De: soporte@paypa1.com (1 en lugar de l)
Asunto: Verifica tu cuenta PayPal
Cuerpo:
  Estimado usuario,
  
  Hemos detectado actividad sospechosa en tu cuenta.
  Por favor verifica tu identidad aquí:
  http://paypal-verify.tk/login.php
  
  Si no verificas en 24 horas, tu cuenta será suspendida.
  
  Equipo de PayPal
```

**Señales**:
- Dominio falso: `paypa1.com` (número 1 en lugar de letra L)
- URL sospechosa: `.tk` dominio gratuito
- Urgencia: "24 horas"
- Solicita credenciales

---

### Email Legítimo #1: Confirmación Real
```
De: notificaciones@amazon.com
Asunto: Tu pedido #12345-67890 ha sido enviado
Cuerpo:
  Hola Roberto,
  
  Tu pedido ha sido enviado y llegará el 15 de diciembre.
  
  Número de seguimiento: 1Z999AA10123456784
  
  Puedes rastrear tu pedido en:
  https://amazon.com/tu-cuenta/pedidos
  
  Gracias por tu compra,
  Amazon
```

**Señales de confianza**:
- Dominio oficial: `@amazon.com`
- URL real: `amazon.com`
- Sin urgencia artificial
- Información específica (número de pedido)

---

## Telemetría Registrada

```python
Por cada decisión se registra:
{
  "level": 1,
  "timestamp": "2025-12-03 10:25:43",
  "email_id": 3,
  "tipo_email": "phishing",
  "subtipo": "dominio_falso",
  "decision_usuario": "marcar_phishing",
  "es_correcto": True,
  "puntos_ganados": 200,
  "combo_actual": 1.2,
  "quiz_mostrado": True,
  "quiz_respondido": True,
  "quiz_correcto": True,
  "tiempo_analisis_segundos": 12
}
```

---

## Tips Pedagógicos

### Para el Tutor Reforzado (Modo Bajo)
- Tips automáticos cada 10 segundos
- Explicaciones muy detalladas
- Todos los quizzes son obligatorios
- Resaltar señales visualmente

### Para el Tutor Estándar (Modo Medio)
- Tips en momentos clave
- Explicaciones moderadas
- Quizzes opcionales
- Balance entre ayuda y autonomía

### Para el Tutor Rápido (Modo Alto)
- Mínimos tips esenciales
- Explicaciones breves
- Sin quizzes automáticos
- Enfoque en gameplay fluido

---

## Próximas Mejoras

- [ ] Emails más variados (redes sociales, gobierno)
- [ ] Modo difícil con tiempo límite
- [ ] Análisis de headers completos
- [ ] Integración con API de VirusTotal

---

**Equipo NetDefenders** | [Volver al índice](README.md)
