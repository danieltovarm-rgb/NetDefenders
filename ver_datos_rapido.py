"""
VISUALIZACIÓN RÁPIDA DE DATOS RECOLECTADOS
Muestra de forma simple qué datos se guardan por cada usuario
"""

import json
import os

def mostrar_resumen_simple():
    archivo = "quiz_data_collection.json"
    
    print("=" * 80)
    print("🛡️  NETDEFENDERS - RESUMEN VISUAL DE DATOS RECOLECTADOS")
    print("=" * 80)
    
    if not os.path.exists(archivo):
        print("\n⚠️  Todavía no hay datos recolectados.")
        print("   Completa el juego (quiz inicial + niveles + quiz final) para generar datos.\n")
        return
    
    with open(archivo, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    
    print(f"\n📊 TOTAL DE USUARIOS REGISTRADOS: {len(datos)}\n")
    
    for i, session in enumerate(datos, 1):
        print("─" * 80)
        print(f"👤 USUARIO #{i}")
        print("─" * 80)
        
        # Info básica
        print(f"🆔 Sesión: {session['session_id']}")
        print(f"📅 Fecha: {session['fecha_hora_completado']}")
        
        # Resumen de puntuaciones
        r = session['resumen']
        print(f"\n📝 QUIZ:")
        print(f"   Inicial: {r['quiz_inicial_correctas']}/12 ({r['porcentaje_inicial']:.1f}%)")
        print(f"   Final:   {r['quiz_final_correctas']}/12 ({r['porcentaje_final']:.1f}%)")
        
        # Mejora visual
        mejora = r['mejora_absoluta']
        if mejora > 0:
            print(f"   📈 Mejoró: +{mejora} preguntas ({r['mejora_porcentual']:.1f}%)")
            emoji = "🌟" * min(5, mejora)
            print(f"      {emoji}")
        elif mejora == 0:
            if r['quiz_inicial_correctas'] >= 10:
                print(f"   💯 Experto: Ya sabía (sin cambio)")
            else:
                print(f"   ➖ Sin cambio")
        else:
            print(f"   📉 Empeoró: {mejora} preguntas")
        
        # Desglose por categoría
        phishing = session['desglose_por_categoria']['phishing_nivel1']
        malware = session['desglose_por_categoria']['malware_nivel2']
        
        print(f"\n🎯 POR CATEGORÍA:")
        print(f"   🎣 Phishing: {phishing['inicial_correctas']}/6 → {phishing['final_correctas']}/6 ", end="")
        if phishing['mejora'] > 0:
            print(f"(+{phishing['mejora']})")
        elif phishing['mejora'] < 0:
            print(f"({phishing['mejora']})")
        else:
            print("(sin cambio)")
            
        print(f"   🦠 Malware:  {malware['inicial_correctas']}/6 → {malware['final_correctas']}/6 ", end="")
        if malware['mejora'] > 0:
            print(f"(+{malware['mejora']})")
        elif malware['mejora'] < 0:
            print(f"({malware['mejora']})")
        else:
            print("(sin cambio)")
        
        # Estadísticas
        stats = session['estadisticas']
        print(f"\n📊 DETALLE:")
        print(f"   ✅ Mejoradas: {stats['preguntas_mejoradas']} preguntas")
        print(f"   ❌ Empeoradas: {stats['preguntas_empeoradas']} preguntas")
        print(f"   💯 Siempre correctas: {stats['preguntas_siempre_correctas']} preguntas")
        print(f"   ⚠️  Siempre incorrectas: {stats['preguntas_siempre_incorrectas']} preguntas")
        
        # Preguntas que mejoró (si hay)
        mejoradas = [p for p in session['analisis_por_pregunta'] if p['mejoro']]
        if mejoradas:
            print(f"\n🎓 APRENDIÓ EN:")
            for p in mejoradas[:3]:  # Mostrar máximo 3
                print(f"   • Pregunta #{p['pregunta_num']}: {p['pregunta'][:60]}...")
        
        # Preguntas que sigue fallando (si hay)
        dificiles = [p for p in session['analisis_por_pregunta'] 
                    if not p['inicial_correcta'] and not p['final_correcta']]
        if dificiles:
            print(f"\n❗ NECESITA REFUERZO EN:")
            for p in dificiles[:3]:  # Mostrar máximo 3
                print(f"   • Pregunta #{p['pregunta_num']}: {p['pregunta'][:60]}...")
        
        print()
    
    # Resumen global
    print("\n" + "=" * 80)
    print("📈 RESUMEN GLOBAL")
    print("=" * 80)
    
    # Calcular promedios
    mejora_total = sum(s['resumen']['mejora_porcentual'] for s in datos)
    mejora_promedio = mejora_total / len(datos)
    
    inicial_promedio = sum(s['resumen']['quiz_inicial_correctas'] for s in datos) / len(datos)
    final_promedio = sum(s['resumen']['quiz_final_correctas'] for s in datos) / len(datos)
    
    print(f"\n👥 Usuarios analizados: {len(datos)}")
    print(f"📝 Promedio inicial: {inicial_promedio:.1f}/12")
    print(f"📝 Promedio final: {final_promedio:.1f}/12")
    print(f"📈 Mejora promedio: {mejora_promedio:.1f}%")
    
    # Preguntas más difíciles globalmente
    errores_por_pregunta = {}
    mejoras_por_pregunta = {}
    
    for session in datos:
        for p in session['analisis_por_pregunta']:
            num = p['pregunta_num']
            if not p['final_correcta']:
                errores_por_pregunta[num] = errores_por_pregunta.get(num, 0) + 1
            if p['mejoro']:
                mejoras_por_pregunta[num] = mejoras_por_pregunta.get(num, 0) + 1
    
    if errores_por_pregunta:
        print(f"\n❌ PREGUNTA MÁS DIFÍCIL:")
        pregunta_dificil = max(errores_por_pregunta.items(), key=lambda x: x[1])
        texto = next(p['pregunta'] for s in datos for p in s['analisis_por_pregunta'] 
                    if p['pregunta_num'] == pregunta_dificil[0])
        print(f"   Pregunta #{pregunta_dificil[0]}: {pregunta_dificil[1]} usuarios fallaron")
        print(f"   \"{texto}\"")
    
    if mejoras_por_pregunta:
        print(f"\n✅ PREGUNTA DONDE MÁS APRENDIERON:")
        pregunta_mejora = max(mejoras_por_pregunta.items(), key=lambda x: x[1])
        texto = next(p['pregunta'] for s in datos for p in s['analisis_por_pregunta'] 
                    if p['pregunta_num'] == pregunta_mejora[0])
        print(f"   Pregunta #{pregunta_mejora[0]}: {pregunta_mejora[1]} usuarios mejoraron")
        print(f"   \"{texto}\"")
    
    print("\n" + "=" * 80)
    print("💡 Para análisis más detallado, ejecuta: python analizar_quiz.py")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    mostrar_resumen_simple()
