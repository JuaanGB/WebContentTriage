#!/usr/bin/env python3
"""
Text Extractor - Extrae texto legible de páginas web.

Extrae contenido de etiquetas semánticas:
  - h1, h2, h3, h4, h5, h6  -> títulos y subtítulos
  - p                         -> párrafos de texto

Ignora navegación, footers, scripts, estilos, y otros elementos no semánticos.
"""

import re
import requests
from bs4 import BeautifulSoup, Comment
from .scraper import USER_AGENT


def fetch_html(url: str, timeout: int = 30) -> str:
    """Descarga el HTML de una URL."""
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def extract_text(html: str, url: str | None = None) -> dict:
    """
    Extrae texto legible del HTML.

    Returns:
        dict con:
          - url: URL de origen
          - title: título de la página (<title>)
          - headings: lista de {level, text} para h1-h6
          - paragraphs: lista de textos de <p>
          - full_text: texto completo concatenado
    """
    soup = BeautifulSoup(html, "html.parser")

    # Eliminar elementos no deseados
    for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
        element.decompose()

    # Eliminar comentarios HTML
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Extraer título de la página
    title_tag = soup.find("title")
    page_title = title_tag.get_text(strip=True) if title_tag else None

    # Extraer headings h1-h6
    headings = []
    for level in range(1, 7):
        for tag in soup.find_all(f"h{level}"):
            text = tag.get_text(strip=True)
            if text:
                headings.append({"level": level, "text": text})

    # Extraer párrafos
    paragraphs = []
    for tag in soup.find_all("p"):
        text = tag.get_text(strip=True)
        # Filtrar párrafos vacíos, muy cortos, o que parecen metadata
        if not text or len(text) < 20:
            continue
        # Ignorar párrafos que parecen metadata (fechas, views, etc.)
        metadata_patterns = [
            r'^\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}$',  # fechas
            r'^\d+\s+(views?|comments?|likes?|shares?)$',  # contadores
            r'^(By|Author|Posted|Updated|Published)\s*[:\-]',  # metadata de autor
            r'^\d+\s+(min|minute)s?\s+read$',  # tiempo de lectura
            r'^\d+\s+(words?|characters?)$',  # contadores de texto
            r'^(Date|From|Subject|To|Reply-To|Message-Id|In-Reply-To):',  # headers de email/RFC
            r'^\d+\s+(replies?|retweets?|followers?|following)$',  # social media metrics
            r'^(Share|Follow|Subscribe|Read more|Continue reading)\s*$',  # CTAs sueltos
        ]
        is_metadata = any(re.search(p, text, re.IGNORECASE) for p in metadata_patterns)
        if not is_metadata:
            paragraphs.append(text)

    # Construir texto completo para contexto
    full_text_parts = []
    if page_title:
        full_text_parts.append(f"TITLE: {page_title}")

    for h in headings:
        full_text_parts.append(f"H{h['level']}: {h['text']}")

    for p in paragraphs:
        full_text_parts.append(f"P: {p}")

    return {
        "url": url,
        "title": page_title,
        "headings": headings,
        "paragraphs": paragraphs,
        "full_text": "\n\n".join(full_text_parts),
    }


def extract_from_url(url: str, timeout: int = 30) -> dict:
    """
    Descarga y extrae texto de una URL en un solo paso.

    Returns:
        dict con el resultado del extracto, o None si hay error.
    """
    try:
        html = fetch_html(url, timeout=timeout)
        result = extract_text(html, url=url)
        return result
    except requests.RequestException:
        return None
    except Exception:
        return None


def print_extracted(result: dict | None, max_paragraphs: int = 5, max_chars: int = 1000):
    """Imprime el resultado extraído de forma legible."""
    if result is None:
        print("  [Sin resultado]")
        return

    print(f"\n{'='*60}")
    print(f"URL: {result['url']}")
    print(f"Título página: {result['title']}")
    print(f"{'='*60}")

    # Headings
    if result['headings']:
        print("\n--- HEADINGS ---")
        for h in result['headings'][:10]:  # Limitar a 10 headings
            indent = "  " * (h['level'] - 1)
            print(f"{indent}H{h['level']}: {h['text']}")
        if len(result['headings']) > 10:
            print(f"  ... y {len(result['headings']) - 10} más")

    # Párrafos
    if result['paragraphs']:
        print(f"\n--- PÁRRAFOS (mostrando {min(max_paragraphs, len(result['paragraphs']))} de {len(result['paragraphs'])}) ---")
        for i, p in enumerate(result['paragraphs'][:max_paragraphs], 1):
            # Truncar si es muy largo
            display = p[:max_chars]
            if len(p) > max_chars:
                display += "..."
            print(f"\n[{i}] {display}")

    print(f"\n{'='*60}")
    print(f"Total texto extraído: {len(result['full_text'])} caracteres")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Prueba manual con una URL
    test_url = "https://example.com"
    print(f"Prueba de extracción de texto: {test_url}\n")
    result = extract_from_url(test_url)
    print_extracted(result)
