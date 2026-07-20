"""
CC3103 - Procesamiento de Lenguaje Natural
Laboratorio 1: Tokenizacion y Guardrails para LLMs

Este archivo sirve como guia practica para complementar la presentacion de
Semana 1 y 2. Incluye ejemplos, funciones base y ejercicios marcados con TODO.

Objetivos:
- Comparar diferentes formas de tokenizar texto.
- Calcular estadisticas basicas de texto.
- Detectar datos sensibles usando expresiones regulares.
- Aplicar acciones simples de guardrail: ALLOW, WARN, REDACT o BLOCK.

Ejecutar:
    python laboratorio_1_tokenizacion_guardrails_guia.py
"""

from collections import Counter
import re


# -----------------------------------------------------------------------------
# 1. Textos De Prueba
# -----------------------------------------------------------------------------

TEXTOS_DE_PRUEBA = [
    "Hola!!! necesito ayuda con mi cuenta :( mi correo es ana.lopez@uvg.edu.gt",
    "El modelo GPT-4.1 respondio: 'No tengo suficiente contexto.'",
    "Mi numero es +502 5555-1234 y mi sitio es https://uvg.edu.gt",
    "API_KEY=abc123-super-secreta no deberia compartirse con ningun modelo.",
    "anticonstitucionalmente, NLP, #IA, www.example.com/manual.pdf",
    "El codigo del curso es CC3103 y la clase inicia a las 17:20.",
]


# -----------------------------------------------------------------------------
# 2. Normalizacion Basica
# -----------------------------------------------------------------------------

def normalizar_espacios(texto):
    """Elimina espacios repetidos y saltos de linea innecesarios."""
    return re.sub(r"\s+", " ", texto).strip()


def normalizar_minusculas(texto):
    """Convierte texto a minusculas.

    Nota: no siempre conviene hacer esto. Por ejemplo, Apple y apple pueden
    significar cosas distintas.
    """
    return texto.lower()


# -----------------------------------------------------------------------------
# 3. Tokenizacion Clasica
# -----------------------------------------------------------------------------

def tokenizar_por_espacios(texto):
    """Tokenizacion simple usando espacios.

    Ventaja: facil de entender.
    Limitacion: conserva signos pegados a las palabras y no maneja bien URLs,
    correos o puntuacion.
    """
    return texto.split()


def tokenizar_con_regex_basico(texto):
    """Tokenizacion usando Regex para capturar palabras y numeros.

    Limitacion: puede destruir estructuras como correos, telefonos y URLs.
    """
    return re.findall(r"\b\w+\b", texto.lower())


def tokenizar_con_regex_mixto(texto):
    """Tokenizacion un poco mas cuidadosa.

    Este patron intenta conservar:
    - Correos electronicos
    - URLs
    - Palabras
    - Numeros
    - Algunos signos importantes
    """
    patron = r"https?://\S+|www\.\S+|[\w\.-]+@[\w\.-]+\.\w+|\b\w+\b|[^\w\s]"
    return re.findall(patron, texto, flags=re.UNICODE)


# -----------------------------------------------------------------------------
# 4. Estadisticas De Texto
# -----------------------------------------------------------------------------

def calcular_estadisticas(texto, tokens):
    """Calcula estadisticas basicas de un texto tokenizado."""
    frecuencias = Counter(tokens)

    return {
        "caracteres": len(texto),
        "tokens": len(tokens),
        "tokens_unicos": len(set(tokens)),
        "top_10": frecuencias.most_common(10),
    }


def imprimir_estadisticas(estadisticas):
    """Imprime estadisticas en formato legible."""
    print(f"Caracteres: {estadisticas['caracteres']}")
    print(f"Tokens: {estadisticas['tokens']}")
    print(f"Tokens unicos: {estadisticas['tokens_unicos']}")
    print("Top 10 tokens:")
    for token, frecuencia in estadisticas["top_10"]:
        print(f"  - {token}: {frecuencia}")


# -----------------------------------------------------------------------------
# 5. Patrones Regex Para Guardrails
# -----------------------------------------------------------------------------

PATRONES_SENSIBLES = {
    "EMAIL": r"\b[\w\.-]+@[\w\.-]+\.\w+\b",
    "URL": r"https?://\S+|www\.\S+",
    "PHONE": r"\+?\d[\d\s\-]{7,}\d",
    "SECRET_WORD": r"(?i)\b(password|contrasena|contraseña|clave|secret|token|api_key|apikey)\b",
    "LONG_NUMBER": r"\b\d{8,}\b",
}


def detectar_datos_sensibles(texto):
    """Detecta datos sensibles usando los patrones definidos.

    Retorna una lista de diccionarios con tipo y valor detectado.
    """
    hallazgos = []

    for tipo, patron in PATRONES_SENSIBLES.items():
        coincidencias = re.findall(patron, texto)

        for coincidencia in coincidencias:
            # re.findall puede devolver tuplas si el patron tiene grupos.
            if isinstance(coincidencia, tuple):
                coincidencia = " ".join(filter(None, coincidencia))

            hallazgos.append({
                "tipo": tipo,
                "valor": coincidencia,
            })

    return hallazgos


# -----------------------------------------------------------------------------
# 6. Acciones De Guardrail
# -----------------------------------------------------------------------------

def decidir_accion(hallazgos):
    """Decide que accion tomar segun los datos detectados.

    Politica simple:
    - Si hay secretos, bloquear.
    - Si hay email, telefono, URL o numero largo, redactar.
    - Si no hay hallazgos, permitir.
    """
    tipos = {hallazgo["tipo"] for hallazgo in hallazgos}

    if "SECRET_WORD" in tipos:
        return "BLOCK"

    if tipos.intersection({"EMAIL", "PHONE", "URL", "LONG_NUMBER"}):
        return "REDACT"

    return "ALLOW"


def redactar_texto(texto):
    """Reemplaza datos sensibles por etiquetas seguras."""
    texto_seguro = texto

    reemplazos = {
        "EMAIL": "[EMAIL_REDACTED]",
        "URL": "[URL_REDACTED]",
        "PHONE": "[PHONE_REDACTED]",
        "LONG_NUMBER": "[NUMBER_REDACTED]",
    }

    for tipo, reemplazo in reemplazos.items():
        patron = PATRONES_SENSIBLES[tipo]
        texto_seguro = re.sub(patron, reemplazo, texto_seguro)

    return texto_seguro


def aplicar_guardrail(texto):
    """Aplica deteccion, decision y posible redaccion al texto."""
    hallazgos = detectar_datos_sensibles(texto)
    accion = decidir_accion(hallazgos)

    if accion == "REDACT":
        texto_seguro = redactar_texto(texto)
    elif accion == "BLOCK":
        texto_seguro = None
    else:
        texto_seguro = texto

    return {
        "accion": accion,
        "hallazgos": hallazgos,
        "texto_seguro": texto_seguro,
    }


# -----------------------------------------------------------------------------
# 7. Pipeline Completo
# -----------------------------------------------------------------------------

def procesar_texto(texto):
    """Ejecuta el pipeline completo para un texto."""
    texto_normalizado = normalizar_espacios(texto)
    resultado_guardrail = aplicar_guardrail(texto_normalizado)

    texto_para_tokenizar = resultado_guardrail["texto_seguro"]

    if texto_para_tokenizar is None:
        tokens = []
        estadisticas = None
    else:
        tokens = tokenizar_con_regex_mixto(texto_para_tokenizar)
        estadisticas = calcular_estadisticas(texto_para_tokenizar, tokens)

    return {
        "texto_original": texto,
        "texto_normalizado": texto_normalizado,
        "guardrail": resultado_guardrail,
        "tokens": tokens,
        "estadisticas": estadisticas,
    }


def imprimir_resultado_pipeline(resultado, indice):
    """Imprime el resultado completo del pipeline."""
    print("=" * 80)
    print(f"TEXTO {indice}")
    print("=" * 80)

    print("Texto original:")
    print(resultado["texto_original"])

    print("\nTexto normalizado:")
    print(resultado["texto_normalizado"])

    print("\nDatos sensibles detectados:")
    hallazgos = resultado["guardrail"]["hallazgos"]
    if hallazgos:
        for hallazgo in hallazgos:
            print(f"  - {hallazgo['tipo']}: {hallazgo['valor']}")
    else:
        print("  No se detectaron datos sensibles.")

    print(f"\nAccion recomendada: {resultado['guardrail']['accion']}")

    print("\nTexto seguro:")
    if resultado["guardrail"]["texto_seguro"] is None:
        print("  [BLOQUEADO: no debe enviarse al modelo]")
    else:
        print(resultado["guardrail"]["texto_seguro"])

    print("\nTokens:")
    print(resultado["tokens"])

    print("\nEstadisticas:")
    if resultado["estadisticas"] is None:
        print("  No se calcularon estadisticas porque el texto fue bloqueado.")
    else:
        imprimir_estadisticas(resultado["estadisticas"])

    print()


# -----------------------------------------------------------------------------
# 8. Demos Para Clase
# -----------------------------------------------------------------------------

def demo_comparar_tokenizadores():
    """Compara tres formas de tokenizar el mismo texto."""
    texto = "Mi numero es +502 5555-1234 y mi correo es ana@uvg.edu.gt"

    print("=" * 80)
    print("DEMO: COMPARACION DE TOKENIZADORES")
    print("=" * 80)
    print("Texto:")
    print(texto)

    print("\nTokenizacion por espacios:")
    print(tokenizar_por_espacios(texto))

    print("\nTokenizacion Regex basica:")
    print(tokenizar_con_regex_basico(texto))

    print("\nTokenizacion Regex mixta:")
    print(tokenizar_con_regex_mixto(texto))
    print()


def demo_guardrails():
    """Ejecuta el pipeline completo sobre todos los textos de prueba."""
    print("=" * 80)
    print("DEMO: PIPELINE COMPLETO")
    print("=" * 80)
    print()

    for indice, texto in enumerate(TEXTOS_DE_PRUEBA, start=1):
        resultado = procesar_texto(texto)
        imprimir_resultado_pipeline(resultado, indice)


# -----------------------------------------------------------------------------
# 9. Ejercicios Para Estudiantes
# -----------------------------------------------------------------------------

def ejercicio_1_agregar_textos():
    """TODO para estudiantes.

    Agreguen 3 textos nuevos a TEXTOS_DE_PRUEBA:
    - Uno con un correo simulado.
    - Uno con un telefono simulado.
    - Uno con una instruccion sospechosa, por ejemplo una clave o token.
    """
    pass


def ejercicio_2_mejorar_regex_dpi():
    """TODO para estudiantes.

    Agreguen un patron llamado DPI al diccionario PATRONES_SENSIBLES.

    Pista:
    - En Guatemala, un DPI suele tener 13 digitos.
    - Puede aparecer con espacios o guiones.

    Ejemplos que podrian detectar:
    - 1234567890101
    - 1234 56789 0101
    - 1234-56789-0101
    """
    pass


def ejercicio_3_accion_warn():
    """TODO para estudiantes.

    Modifiquen decidir_accion para usar WARN.

    Politica sugerida:
    - SECRET_WORD -> BLOCK
    - EMAIL o PHONE -> REDACT
    - URL -> WARN
    - Sin hallazgos -> ALLOW
    """
    pass


def ejercicio_4_reflexion():
    """Preguntas para responder en el informe.

    1. Que falsos positivos encontraron?
    2. Que falsos negativos encontraron?
    3. Que informacion se pierde al redactar datos sensibles?
    4. Regex seria suficiente para proteger informacion de una empresa real?
    5. Que otra capa de seguridad agregarian?
    """
    pass


# -----------------------------------------------------------------------------
# 10. Programa Principal
# -----------------------------------------------------------------------------

def main():
    demo_comparar_tokenizadores()
    demo_guardrails()


if __name__ == "__main__":
    main()
