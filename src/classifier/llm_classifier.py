#!/usr/bin/env python3
"""
LLM Classifier - Clasifica posts usando un modelo vía OpenRouter API.

Uso:
    1. Crear archivo .env con OPENROUTER_API_KEY=tu_key
    2. El módulo evalúa si un post es útil para la búsqueda

El prompt debería explicar qué tipo de contenido quieres buscar y con qué finalidad.
"""

import os
import json
import re
import requests
from dotenv import load_dotenv

# Cargar .env desde el directorio del script
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Modelo barato y rápido
DEFAULT_MODEL = "openai/gpt-4o-mini"

# Este prompt es genérico. Debes rellenarlo con los datos correspondientes para que el LLM pueda entender el 
# contexto de la búsqueda
PROMPT_TEMPLATE = """
Eres...

Tu tarea: evaluar si el siguiente post es ÚTIL para ...

Un post es ÚTIL si describe:
...

NO es útil si es:
...

Post:
Título: {title}
URL: {url}

Texto extraído:
{text}

Responde ÚNICAMENTE en este formato:
VEREDICTO: SÍ o NO
SCORE: 0-100 (qué tan útil, 100 = extremadamente útil)
RAZÓN: máximo 15 palabras explicando por qué
"""


def classify_with_llm(title: str, url: str, text: str, model: str = DEFAULT_MODEL) -> dict | None:
    """
    Consulta el LLM para evaluar si un post es útil.

    Returns:
        dict con 'veredicto' (bool), 'score' (int), 'razon' (str)
        o None si hay error / no hay API key.
    """
    if not API_KEY:
        print("    ⚠️  OPENROUTER_API_KEY no configurada. Saltando LLM.")
        return None

    prompt = PROMPT_TEMPLATE.format(title=title, url=url, text=text[:3000])

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",
        "X-Title": "Web-Content-Triage",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.1,
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"]
        result = _parse_response(content)

        # Extraer uso de tokens si está disponible
        usage = data.get("usage", {})
        result["prompt_tokens"] = usage.get("prompt_tokens", 0)
        result["completion_tokens"] = usage.get("completion_tokens", 0)
        result["total_tokens"] = usage.get("total_tokens", 0)

        return result

    except requests.RequestException as e:
        print(f"    ⚠️  Error API: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"    ⚠️  Error parseando respuesta: {e}")
        return None


def _parse_response(content: str) -> dict:
    """Parsea la respuesta del LLM buscando VEREDICTO, SCORE y RAZÓN."""
    veredicto = None
    score = 0
    razon = ""

    # Buscar VEREDICTO
    v_match = re.search(r'VEREDICTO:\s*(SÍ|SI|NO|Si|No|sí|si|no)', content, re.IGNORECASE)
    if v_match:
        veredicto = v_match.group(1).upper() in ("SÍ", "SI")

    # Buscar SCORE
    s_match = re.search(r'SCORE:\s*(\d+)', content)
    if s_match:
        score = int(s_match.group(1))

    # Buscar RAZÓN
    r_match = re.search(r'RAZÓN:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
    if r_match:
        razon = r_match.group(1).strip()

    return {
        "veredicto": veredicto,
        "score_llm": score,
        "razon": razon,
        "raw": content,
    }


def build_summary_for_llm(post_data: dict, max_chars: int = 3000) -> str:
    """
    Construye un resumen del post para enviar al LLM.
    Incluye headings y primeros párrafos.
    """
    parts = []

    if post_data.get("title"):
        parts.append(f"Título página: {post_data['title']}")

    for h in post_data.get("headings", [])[:5]:
        parts.append(f"H{h['level']}: {h['text']}")

    for i, p in enumerate(post_data.get("paragraphs", [])[:8], 1):
        parts.append(f"P{i}: {p}")

    text = "\n\n".join(parts)
    return text[:max_chars]


if __name__ == "__main__":
    # Prueba manual
    test = {
        "title": "Building a speedrun tool for retro consoles",
        "headings": [{"level": 1, "text": "Emulation and homebrew"}],
        "paragraphs": ["This post explains how to build a speedrun tool for a retro console emulator."],
    }
    summary = build_summary_for_llm(test)
    result = classify_with_llm("Building a speedrun tool for retro consoles", "https://example.com", summary)
    print(json.dumps(result, indent=2, ensure_ascii=False))
