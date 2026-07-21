"""
CC3103 - Procesamiento de Lenguaje Natural
Laboratorio 1: Tokenizacion y Guardrails para LLMs

Autor: Puente, Joaquin
Auror: García, Nelson

Pipeline implementado:
    Texto de entrada
      -> normalizacion basica
      -> deteccion de datos sensibles
      -> accion de guardrail (ALLOW / WARN / REDACT / BLOCK)
      -> tokenizacion
      -> estadisticas
      -> salida final

Objetivos:
- Comparar diferentes formas de tokenizar texto.
- Calcular estadisticas basicas de texto.
- Detectar datos sensibles usando expresiones regulares.
- Aplicar acciones simples de guardrail: ALLOW, WARN, REDACT o BLOCK.

Ejecutar:
    python laboratorio_1_puente_joaquin.py

Nota: Todos los datos (correos, telefonos, DPI, tokens) son SIMULADOS.
"""

from collections import Counter
import re


# -----------------------------------------------------------------------------
# 1. Textos De Prueba
# -----------------------------------------------------------------------------
# Al menos 5 textos. La coleccion cubre, en conjunto:
#   - correo electronico  (Texto 1)
#   - telefono            (Texto 3)
#   - URL                 (Texto 3 y Texto 5)
#   - palabra sensible    (Texto 4: API_KEY)
#   - DPI / numero largo  (Texto 6)

TEXTOS_DE_PRUEBA = [
    "Hola!!! necesito ayuda con mi cuenta :( mi correo es ana.lopez@uvg.edu.gt",
    "El modelo GPT-4.1 respondio: 'No tengo suficiente contexto.'",
    "Mi numero es +502 5555-1234 y mi sitio es https://uvg.edu.gt",
    "API_KEY=abc123-super-secreta no deberia compartirse con ningun modelo.",
    "anticonstitucionalmente, NLP, #IA, www.example.com/manual.pdf",
    "Mi DPI simulado es 1234 56789 0101 y no debe salir del sistema.",
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
# Orden importante para la redaccion: DPI antes que LONG_NUMBER, porque un DPI
# de 13 digitos corridos tambien coincide con LONG_NUMBER (\d{8,}).

PATRONES_SENSIBLES = {
    "EMAIL": r"\b[\w\.-]+@[\w\.-]+\.\w+\b",
    "URL": r"https?://\S+|www\.\S+",
    "PHONE": r"\+?\d[\d\s\-]{7,}\d",
    "SECRET_WORD": r"(?i)\b(password|contrasena|contraseña|clave|secret|token|api_key|apikey)\b",
    # Ejercicio 2: DPI de Guatemala (13 digitos), con o sin espacios/guiones.
    #   1234567890101 | 1234 56789 0101 | 1234-56789-0101
    "DPI": r"\b\d{4}[\s\-]?\d{5}[\s\-]?\d{4}\b",
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

    Politica (Ejercicio 3):
    - SECRET_WORD                         -> BLOCK
    - EMAIL, PHONE, DPI o LONG_NUMBER     -> REDACT
    - Solo URL                            -> WARN
    - Sin hallazgos                       -> ALLOW
    """
    tipos = {hallazgo["tipo"] for hallazgo in hallazgos}

    if "SECRET_WORD" in tipos:
        return "BLOCK"

    if tipos.intersection({"EMAIL", "PHONE", "DPI", "LONG_NUMBER"}):
        return "REDACT"

    if "URL" in tipos:
        return "WARN"

    return "ALLOW"


def redactar_texto(texto):
    """Reemplaza datos sensibles por etiquetas seguras.

    El orden importa: DPI se redacta antes que PHONE y LONG_NUMBER porque un DPI
    (13 digitos, formato 4-5-4) tambien coincide con esos patrones mas laxos. Un
    telefono real (p. ej. +502 5555-1234, 11 digitos) no cumple el formato DPI,
    asi que sigue etiquetandose como [PHONE_REDACTED].
    """
    texto_seguro = texto

    # dict conserva el orden de insercion: DPI antes que PHONE y LONG_NUMBER.
    reemplazos = {
        "EMAIL": "[EMAIL_REDACTED]",
        "URL": "[URL_REDACTED]",
        "DPI": "[DPI_REDACTED]",
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
        # ALLOW y WARN dejan el texto sin modificar; WARN solo advierte.
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

    # Si el texto fue BLOQUEADO, no se tokeniza ni se calculan estadisticas
    # sobre el contenido original.
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
# 9. Programa Principal
# -----------------------------------------------------------------------------

def main():
    demo_comparar_tokenizadores()
    demo_guardrails()


if __name__ == "__main__":
    main()
