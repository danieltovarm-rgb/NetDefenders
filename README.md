# 🛡️ NetDefenders

**Videojuego educativo de ciberseguridad desarrollado en Python con Programación Orientada a Objetos**

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)
![License](https://img.shields.io/badge/License-Educational-yellow.svg)

---

## 📖 Descripción General

**NetDefenders** es un juego educativo interactivo diseñado para enseñar conceptos fundamentales de ciberseguridad a través de mecánicas de juego dinámicas y desafiantes. Los jugadores asumen el rol de un defensor de sistemas que debe proteger computadoras contra amenazas de malware, aplicando herramientas de seguridad y tomando decisiones estratégicas en tiempo real.

### ¿Por qué existe NetDefenders?

En un mundo cada vez más digitalizado, la ciberseguridad es una habilidad esencial. NetDefenders busca:
- **Educar** sobre amenazas comunes (phishing, virus, troyanos, ransomware, spyware)
- **Entrenar** en el uso de herramientas de seguridad (antivirus, firewall, limpieza de sistema)
- **Concientizar** sobre la importancia de la protección digital y el reconocimiento de ataques
- **Gamificar** el aprendizaje de conceptos técnicos complejos

---

## ✨ Características Principales

### 🎮 Mecánicas de Juego

- **Sistema de Niveles Progresivos**: 2 niveles con dificultad creciente
  - **Nivel 1 - Detector de Phishing**: Identifica y bloquea intentos de phishing protegiendo las puertas de acceso al sistema
  - **Nivel 2 - Cazador de Malware**: Escanea, limpia y pone en cuarentena archivos infectados con diferentes tipos de malware

- **Gestión de Recursos**: Administra CPU, RAM y Ancho de Banda para ejecutar acciones
- **Sistema de Puntuación**: Gana puntos por acciones correctas, pierde por errores
- **Overlays Educativos**: Tips contextuales y refuerzos positivos durante el juego
- **Sistema de Quizzes**: Preguntas interactivas sobre conceptos de ciberseguridad
- **Feedback Adaptativo**: Mensajes personalizados según el desempeño del jugador

### 🔧 Tecnologías y Herramientas Utilizadas

- **Lenguaje**: Python 3.8+
- **Framework de Juego**: Pygame 2.0+
- **Multimedia**: MoviePy (reproducción de videos)
- **Análisis de Datos**: NumPy, Pandas, Openpyxl
- **Arquitectura**: Programación Orientada a Objetos (POO)
  - Clases abstractas (ABC)
  - Herencia y polimorfismo
  - Patrones de diseño (Manager, Strategy)

### 📊 Sistema de Telemetría

- **Registro de Estadísticas**: Seguimiento de acciones del jugador
- **Análisis de Errores**: Log detallado de decisiones incorrectas
- **Exportación de Datos**: Generación de reportes en JSON y Excel
- **Métricas de Rendimiento**: Puntuación, tiempo, recursos utilizados

### 🎨 Recursos Visuales

- Sprites animados para personajes y enemigos
- Interfaz gráfica intuitiva con barras de recursos
- Efectos visuales y retroalimentación visual
- Videos de introducción, victoria y derrota

---

## 🚀 Instalación y Ejecución

### Requisitos Previos

- **Python**: Versión 3.8 o superior
- **Sistema Operativo**: Windows, Linux, macOS
- **Espacio en Disco**: ~50 MB (juego + dependencias)

### Instalación en Windows

1. **Verificar instalación de Python**:
   ```powershell
   python --version
   ```
   Si no tienes Python, descárgalo desde [python.org](https://www.python.org/downloads/)

2. **Clonar o descargar el repositorio**:
   ```powershell
   git clone https://github.com/danieltovarm-rgb/NetDefenders.git
   cd NetDefenders
   ```

3. **Instalar dependencias**:
   ```powershell
   pip install pygame moviepy numpy pandas openpyxl
   ```
   
   O usando el archivo de requisitos (cuando esté disponible):
   ```powershell
   pip install -r requerimientos.txt
   ```

4. **Ejecutar el juego**:
   ```powershell
   python NetDefenders_AVANCE.py
   ```

### Instalación en Linux/macOS

1. **Verificar Python**:
   ```bash
   python3 --version
   ```

2. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/danieltovarm-rgb/NetDefenders.git
   cd NetDefenders
   ```

3. **Instalar dependencias**:
   ```bash
   pip3 install pygame moviepy numpy pandas openpyxl
   ```

4. **Ejecutar el juego**:
   ```bash
   python3 NetDefenders_AVANCE.py
   ```


## 📁 Estructura del Proyecto

```
NetDefenders/
│
├── NetDefenders_AVANCE.py      # Archivo principal del juego
├── stats_system.py              # Sistema de estadísticas y telemetría
├── README.md                    # Documentación del proyecto
├── requerimientos.txt           # Dependencias del proyecto
│
├── assets/                      # Recursos visuales y multimedia
│   ├── protagonista/           # Sprites del jugador
│   ├── hacker/                 # Sprites de enemigos
│   ├── tools/                  # Iconos de herramientas
│   ├── files/                  # Iconos de archivos
│   ├── doors/                  # Sprites de puertas (Nivel 1)
│   ├── logos/                  # Logos del juego
│   ├── fondo_menu.png          # Fondo del menú principal
│   ├── fondo_niveles.png       # Fondo de niveles
│   └── cursor_hover.png        # Cursor personalizado
│
├── intro.mp4                    # Video de introducción
├── ganaste.mp4                  # Video de victoria
├── perdiste.mp4                 # Video de derrota
│
├── texto.ttf                    # Fuente personalizada
├── datos_recolectados.json      # Datos de telemetría (JSON)
├── datos_recolectados.xlsx      # Datos de telemetría (Excel)
│
└── __pycache__/                 # Archivos compilados de Python
```

### Descripción de Módulos Principales

- **`NetDefenders_AVANCE.py`**: Contiene toda la lógica del juego, incluyendo:
  - Gestión de pantallas (menú, niveles, resultados)
  - Clases de enemigos (virus, troyanos, ransomware, spyware)
  - Sistema de herramientas de seguridad
  - Gestión de recursos y puntuación
  - Overlays educativos y sistema de quizzes

- **`stats_system.py`**: Maneja el sistema de telemetría:
  - `PlayerStats`: Registro de estadísticas del jugador
  - `ScoreManager`: Gestión de puntuación
  - `MistakeLog`: Registro de errores
  - `Level2GameManager`: Coordinación de mecánicas del Nivel 2

---

## 🎯 Cómo Jugar

### Controles Básicos

- **Ratón**: Navegación por menús, selección de herramientas y objetivos
- **Click Izquierdo**: Seleccionar/Activar
- **ESC**: Pausar juego o volver al menú

### Objetivo del Juego

**Nivel 1 - Detector de Phishing**:
- Identifica intentos de phishing que intentan acceder a tu sistema
- Bloquea puertas comprometidas y protege contra ataques de ingeniería social
- Usa herramientas de seguridad apropiadas para cada tipo de ataque
- Gestiona tus recursos (CPU, RAM, Ancho de Banda)
- Responde quizzes sobre phishing y técnicas de engaño

**Nivel 2 - Cazador de Malware**:
- Escanea archivos para detectar diferentes tipos de malware (virus, troyanos, ransomware, spyware)
- Limpia archivos infectados de manera segura
- Envía amenazas a cuarentena
- Evita eliminar archivos legítimos
- Aprende sobre síntomas de infección y características de cada malware

### Tips para Principiantes

1. **Lee los overlays educativos**: Contienen información valiosa
2. **Administra tus recursos**: No gastes todo en una sola acción
3. **Aprende de tus errores**: El sistema te dará feedback específico
4. **Presta atención a los síntomas**: Cada malware tiene características únicas
5. **Responde los quizzes**: Te ayudan a reforzar conceptos clave

---

## 🏆 Sistema de Puntuación

### Puntuación Base

**Nivel 1 - Detector de Phishing:**
- **Bloquear ataque de phishing correctamente**: +200 puntos
- **Usar herramienta apropiada**: +150 puntos
- **Identificar puerta comprometida**: +100 puntos
- **Dejar pasar un ataque**: -150 puntos
- **Usar herramienta incorrecta**: -100 puntos
- **Eliminar amenaza legítima**: -200 puntos

**Nivel 2 - Cazador de Malware:**
- **Escanear archivo infectado**: +100 puntos
- **Limpiar malware exitosamente**: +300 puntos
- **Enviar a cuarentena correctamente**: +250 puntos
- **Identificar tipo de malware**: +150 puntos
- **Eliminar archivo legítimo**: -200 puntos
- **Ignorar archivo infectado**: -150 puntos
- **Acción incorrecta sobre malware**: -100 puntos

### Bonificaciones

- **Respuestas correctas en Quizzes**: +200 a +500 puntos (según dificultad)
- **Racha de aciertos**: 
  - 3 acciones correctas consecutivas: +100 puntos bonus
  - 5 acciones correctas consecutivas: +250 puntos bonus
  - 10 acciones correctas consecutivas: +500 puntos bonus
- **Eficiencia en Recursos**: 
  - Completar nivel usando menos del 50% de recursos: +300 puntos
  - Completar sin quedarse sin recursos: +150 puntos
- **Velocidad de Respuesta**:
  - Respuesta inmediata (< 2 segundos): Multiplicador x1.5
  - Respuesta rápida (< 5 segundos): Multiplicador x1.2
- **Combo de Herramientas**: Usar la combinación perfecta de herramientas: +200 puntos

### Criterios de Victoria/Derrota

**Victoria:**
- **Nivel 1**: Bloquear al menos 70% de ataques de phishing y mantener puntuación > 1000
- **Nivel 2**: Limpiar al menos 80% de malware sin eliminar archivos legítimos, puntuación > 1500

**Derrota:**
- Puntuación cae por debajo de 0
- Recursos (CPU/RAM/Ancho de Banda) se agotan completamente
- Más del 50% de amenazas no neutralizadas

### Sistema de Ranking

- **🥇 Experto en Seguridad**: > 5000 puntos
- **🥈 Defensor Avanzado**: 3000 - 4999 puntos
- **🥉 Guardián Digital**: 1500 - 2999 puntos
- **⭐ Aprendiz**: 500 - 1499 puntos
- **📚 Novato**: < 500 puntos

---

## 📚 Conceptos Educativos

NetDefenders enseña sobre:

- **Phishing y Ingeniería Social**: Reconocimiento de ataques, técnicas de engaño, protección de credenciales
- **Tipos de Malware**: Virus, Troyanos, Ransomware, Spyware
- **Herramientas de Seguridad**: Antivirus, Firewall, Limpieza de Sistema, Detección de Phishing
- **Gestión de Recursos**: CPU, RAM, Ancho de Banda
- **Síntomas de Infección**: Lentitud, pop-ups, archivos cifrados, comportamiento anómalo
- **Mejores Prácticas**: Verificación de enlaces, escaneo regular, cuarentena, eliminación segura

---

## 👥 Contribuciones

Este es un proyecto educativo desarrollado por estudiantes. Las contribuciones son bienvenidas:

1. Fork del repositorio
2. Crear una rama para tu feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit de cambios (`git commit -am 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crear un Pull Request

---

## 📄 Licencia

Este proyecto es de naturaleza educativa y está desarrollado con fines académicos.

---

## 👨‍💻 Autores

**Equipo NetDefenders** - Proyecto de Programación Orientada a Objetos

- **Tovar Moscol, Daniel Aarom**
- **Hernández Marcelo, Dulce Ariana**
- **Palma Tito, Roberto Enrique**
- **Becerra Chauca, Isaac Amir**
- **Uchasara Quispe, Miguel**

---

## 📞 Contacto

Para preguntas, sugerencias o reportar problemas:
- **Repository**: [github.com/danieltovarm-rgb/NetDefenders](https://github.com/danieltovarm-rgb/NetDefenders)
- **Issues**: Usa la sección de Issues en GitHub

---

## 🙏 Agradecimientos

- A los profesores y tutores que apoyaron el desarrollo del proyecto
- A la comunidad de Pygame por los recursos y documentación
- A todos los jugadores que ayudan a mejorar la experiencia educativa

---

**¡Defiende la red, aprende ciberseguridad y conviértete en un NetDefender!** 🛡️🔒

