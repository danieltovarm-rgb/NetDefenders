"""
Herramienta de Análisis de Datos - NetDefenders Quiz
Analiza los datos recolectados del quiz inicial y final
"""

import json
import os
from datetime import datetime
from collections import Counter

def cargar_datos_quiz():
    """Carga los datos del archivo JSON"""
    archivo = "quiz_data_collection.json"
    if not os.path.exists(archivo):
        print(f"❌ No se encontró el archivo {archivo}")
        print("   Asegúrate de que al menos un usuario haya completado el quiz final.")
        return None
    
    with open(archivo, 'r', encoding='utf-8') as f:
        return json.load(f)

def analisis_general(datos):
    """Muestra estadísticas generales de todos los usuarios"""
    if not datos:
        return
    
    print("\n" + "="*70)
    print("📊 ANÁLISIS GENERAL - TODOS LOS USUARIOS")
    print("="*70)
    
    total_usuarios = len(datos)
    print(f"\n👥 Total de usuarios analizados: {total_usuarios}")
    
    # Mejora promedio
    mejoras_pct = [s['resumen']['mejora_porcentual'] for s in datos]
    mejora_promedio = sum(mejoras_pct) / len(mejoras_pct)
    print(f"📈 Mejora porcentual promedio: {mejora_promedio:.2f}%")
    
    # Mejora absoluta promedio
    mejoras_abs = [s['resumen']['mejora_absoluta'] for s in datos]
    mejora_abs_promedio = sum(mejoras_abs) / len(mejoras_abs)
    print(f"📈 Mejora absoluta promedio: {mejora_abs_promedio:.2f} preguntas")
    
    # Puntuaciones promedio
    iniciales = [s['resumen']['quiz_inicial_correctas'] for s in datos]
    finales = [s['resumen']['quiz_final_correctas'] for s in datos]
    print(f"\n📝 Promedio quiz inicial: {sum(iniciales)/len(iniciales):.2f}/12")
    print(f"📝 Promedio quiz final: {sum(finales)/len(finales):.2f}/12")
    
    # Distribución de mejora
    mejoraron = sum(1 for m in mejoras_abs if m > 0)
    igual = sum(1 for m in mejoras_abs if m == 0)
    empeoraron = sum(1 for m in mejoras_abs if m < 0)
    
    print(f"\n📊 Distribución de resultados:")
    print(f"   ✅ Mejoraron: {mejoraron} ({mejoraron/total_usuarios*100:.1f}%)")
    print(f"   ➖ Sin cambio: {igual} ({igual/total_usuarios*100:.1f}%)")
    print(f"   ❌ Empeoraron: {empeoraron} ({empeoraron/total_usuarios*100:.1f}%)")

def analisis_por_categoria(datos):
    """Analiza el rendimiento por categoría (Phishing vs Malware)"""
    if not datos:
        return
    
    print("\n" + "="*70)
    print("🎯 ANÁLISIS POR CATEGORÍA")
    print("="*70)
    
    # Nivel 1 - Phishing
    phishing_inicial = [s['desglose_por_categoria']['phishing_nivel1']['inicial_correctas'] for s in datos]
    phishing_final = [s['desglose_por_categoria']['phishing_nivel1']['final_correctas'] for s in datos]
    phishing_mejora = [s['desglose_por_categoria']['phishing_nivel1']['mejora'] for s in datos]
    
    print(f"\n🎣 PHISHING (Nivel 1):")
    print(f"   Promedio inicial: {sum(phishing_inicial)/len(phishing_inicial):.2f}/6")
    print(f"   Promedio final: {sum(phishing_final)/len(phishing_final):.2f}/6")
    print(f"   Mejora promedio: {sum(phishing_mejora)/len(phishing_mejora):.2f} preguntas")
    
    # Nivel 2 - Malware
    malware_inicial = [s['desglose_por_categoria']['malware_nivel2']['inicial_correctas'] for s in datos]
    malware_final = [s['desglose_por_categoria']['malware_nivel2']['final_correctas'] for s in datos]
    malware_mejora = [s['desglose_por_categoria']['malware_nivel2']['mejora'] for s in datos]
    
    print(f"\n🦠 MALWARE (Nivel 2):")
    print(f"   Promedio inicial: {sum(malware_inicial)/len(malware_inicial):.2f}/6")
    print(f"   Promedio final: {sum(malware_final)/len(malware_final):.2f}/6")
    print(f"   Mejora promedio: {sum(malware_mejora)/len(malware_mejora):.2f} preguntas")
    
    # Comparación
    mejora_phishing = sum(phishing_mejora)/len(phishing_mejora)
    mejora_malware = sum(malware_mejora)/len(malware_mejora)
    
    print(f"\n💡 Conclusión:")
    if mejora_phishing > mejora_malware:
        print(f"   Los usuarios mejoraron más en PHISHING ({mejora_phishing:.2f} vs {mejora_malware:.2f})")
        print(f"   Sugerencia: Reforzar contenido de MALWARE en el juego")
    elif mejora_malware > mejora_phishing:
        print(f"   Los usuarios mejoraron más en MALWARE ({mejora_malware:.2f} vs {mejora_phishing:.2f})")
        print(f"   Sugerencia: Reforzar contenido de PHISHING en el juego")
    else:
        print(f"   La mejora fue equilibrada en ambas categorías")

def analisis_por_pregunta(datos):
    """Identifica las preguntas más difíciles y donde más se mejoró"""
    if not datos:
        return
    
    print("\n" + "="*70)
    print("❓ ANÁLISIS POR PREGUNTA")
    print("="*70)
    
    # Acumular datos de todas las sesiones
    preguntas_mejora = Counter()
    preguntas_empeoro = Counter()
    preguntas_error_inicial = Counter()
    preguntas_error_final = Counter()
    
    for session in datos:
        for pregunta in session['analisis_por_pregunta']:
            num = pregunta['pregunta_num']
            if pregunta['mejoro']:
                preguntas_mejora[num] += 1
            if pregunta['empeoro']:
                preguntas_empeoro[num] += 1
            if not pregunta['inicial_correcta']:
                preguntas_error_inicial[num] += 1
            if not pregunta['final_correcta']:
                preguntas_error_final[num] += 1
    
    # Top 3 preguntas con más mejora
    print("\n✅ Top 3 preguntas donde MÁS usuarios mejoraron:")
    for num, count in preguntas_mejora.most_common(3):
        # Obtener texto de la pregunta
        texto = next((p['pregunta'] for s in datos for p in s['analisis_por_pregunta'] if p['pregunta_num'] == num), "")
        porcentaje = (count / len(datos)) * 100
        print(f"\n   Pregunta {num}: {count} usuarios ({porcentaje:.1f}%)")
        print(f"   \"{texto[:70]}...\"")
    
    # Top 3 preguntas más difíciles (más errores en quiz final)
    print("\n❌ Top 3 preguntas MÁS DIFÍCILES (errores en quiz final):")
    for num, count in preguntas_error_final.most_common(3):
        texto = next((p['pregunta'] for s in datos for p in s['analisis_por_pregunta'] if p['pregunta_num'] == num), "")
        porcentaje = (count / len(datos)) * 100
        print(f"\n   Pregunta {num}: {count} usuarios fallaron ({porcentaje:.1f}%)")
        print(f"   \"{texto[:70]}...\"")
    
    # Preguntas donde empeoraron (si hay)
    if preguntas_empeoro:
        print("\n⚠️  Preguntas donde usuarios EMPEORARON:")
        for num, count in preguntas_empeoro.most_common():
            texto = next((p['pregunta'] for s in datos for p in s['analisis_por_pregunta'] if p['pregunta_num'] == num), "")
            porcentaje = (count / len(datos)) * 100
            print(f"\n   Pregunta {num}: {count} usuarios ({porcentaje:.1f}%)")
            print(f"   \"{texto[:70]}...\"")

def analisis_individual(datos):
    """Muestra análisis detallado de cada usuario"""
    if not datos:
        return
    
    print("\n" + "="*70)
    print("👤 ANÁLISIS INDIVIDUAL POR USUARIO")
    print("="*70)
    
    for i, session in enumerate(datos, 1):
        print(f"\n{'─'*70}")
        print(f"Usuario #{i} - Sesión: {session['session_id']}")
        print(f"Fecha: {session['fecha_hora_completado']}")
        print(f"{'─'*70}")
        
        resumen = session['resumen']
        print(f"\n📊 Rendimiento:")
        print(f"   Quiz Inicial: {resumen['quiz_inicial_correctas']}/12 ({resumen['porcentaje_inicial']:.1f}%)")
        print(f"   Quiz Final: {resumen['quiz_final_correctas']}/12 ({resumen['porcentaje_final']:.1f}%)")
        print(f"   Mejora: {resumen['mejora_absoluta']} preguntas ({resumen['mejora_porcentual']:.1f}%)")
        
        stats = session['estadisticas']
        print(f"\n📈 Detalle:")
        print(f"   ✅ Preguntas mejoradas: {stats['preguntas_mejoradas']}")
        print(f"   ❌ Preguntas empeoradas: {stats['preguntas_empeoradas']}")
        print(f"   ➖ Sin cambio: {stats['preguntas_sin_cambio']}")
        print(f"   🎯 Siempre correctas: {stats['preguntas_siempre_correctas']}")
        print(f"   ⚠️  Siempre incorrectas: {stats['preguntas_siempre_incorrectas']}")
        
        # Identificar debilidades
        print(f"\n💡 Análisis:")
        
        desglose = session['desglose_por_categoria']
        phishing = desglose['phishing_nivel1']
        malware = desglose['malware_nivel2']
        
        if phishing['final_correctas'] < 4:
            print(f"   ⚠️ Debilidad en PHISHING: {phishing['final_correctas']}/6 en quiz final")
        if malware['final_correctas'] < 4:
            print(f"   ⚠️ Debilidad en MALWARE: {malware['final_correctas']}/6 en quiz final")
        
        if resumen['mejora_absoluta'] > 0:
            print(f"   ✅ Usuario mostró aprendizaje efectivo")
        elif resumen['mejora_absoluta'] == 0:
            if resumen['quiz_inicial_correctas'] >= 10:
                print(f"   🌟 Usuario ya tenía conocimiento sólido")
            else:
                print(f"   ⚠️ No hubo mejora observable")
        else:
            print(f"   ❌ Usuario empeoró - revisar experiencia de juego")

def exportar_csv(datos):
    """Exporta resumen a CSV para análisis en Excel"""
    if not datos:
        return
    
    import csv
    
    archivo_csv = "quiz_analisis_resumen.csv"
    
    with open(archivo_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Encabezados
        writer.writerow([
            'Session_ID', 'Fecha', 'Quiz_Inicial', 'Quiz_Final', 
            'Mejora_Absoluta', 'Mejora_Porcentual',
            'Phishing_Inicial', 'Phishing_Final',
            'Malware_Inicial', 'Malware_Final',
            'Preguntas_Mejoradas', 'Preguntas_Empeoradas'
        ])
        
        # Datos
        for session in datos:
            writer.writerow([
                session['session_id'],
                session['fecha_hora_completado'],
                session['resumen']['quiz_inicial_correctas'],
                session['resumen']['quiz_final_correctas'],
                session['resumen']['mejora_absoluta'],
                session['resumen']['mejora_porcentual'],
                session['desglose_por_categoria']['phishing_nivel1']['inicial_correctas'],
                session['desglose_por_categoria']['phishing_nivel1']['final_correctas'],
                session['desglose_por_categoria']['malware_nivel2']['inicial_correctas'],
                session['desglose_por_categoria']['malware_nivel2']['final_correctas'],
                session['estadisticas']['preguntas_mejoradas'],
                session['estadisticas']['preguntas_empeoradas']
            ])
    
    print(f"\n✅ Resumen exportado a: {archivo_csv}")
    print("   Puedes abrirlo con Excel para análisis adicional")

def menu_principal():
    """Menú interactivo"""
    print("\n" + "="*70)
    print("🛡️  NETDEFENDERS - ANÁLISIS DE DATOS DEL QUIZ")
    print("="*70)
    
    datos = cargar_datos_quiz()
    if not datos:
        return
    
    while True:
        print("\n" + "─"*70)
        print("Selecciona una opción:")
        print("─"*70)
        print("1. 📊 Análisis General (todos los usuarios)")
        print("2. 🎯 Análisis por Categoría (Phishing vs Malware)")
        print("3. ❓ Análisis por Pregunta (dificultad y mejora)")
        print("4. 👤 Análisis Individual (cada usuario)")
        print("5. 📄 Exportar resumen a CSV")
        print("6. 🔄 Análisis Completo (todas las opciones)")
        print("0. ❌ Salir")
        print("─"*70)
        
        opcion = input("\nOpción: ").strip()
        
        if opcion == '1':
            analisis_general(datos)
        elif opcion == '2':
            analisis_por_categoria(datos)
        elif opcion == '3':
            analisis_por_pregunta(datos)
        elif opcion == '4':
            analisis_individual(datos)
        elif opcion == '5':
            exportar_csv(datos)
        elif opcion == '6':
            analisis_general(datos)
            analisis_por_categoria(datos)
            analisis_por_pregunta(datos)
            analisis_individual(datos)
            exportar_csv(datos)
        elif opcion == '0':
            print("\n👋 ¡Hasta luego!")
            break
        else:
            print("\n❌ Opción inválida")
        
        input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    menu_principal()
