#!/usr/bin/env python3
"""
Generic Web Scraper - Librería reutilizable.

Soporta extracción de enlaces mediante expresiones regulares con marcador $URL.
El programador analiza la estructura HTML y proporciona un patrón regex donde:
  - $URL   -> será sustituido por el patrón que captura el href
  - $TITLE -> marca dónde está el texto del título
  - El resto del patrón define el contexto alrededor del enlace para evitar ambigüedad
"""

import re
import requests
from urllib.parse import urljoin

USER_AGENT = "WebContentTriage/1.0 (+https://github.com/JuaanGB/WebContentTriage)"

def fetch_html(url: str, timeout: int = 30) -> str:
    """Descarga el HTML de una URL."""
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def build_regex(pattern: str, marker: str, capture: str) -> re.Pattern:
    """
    Construye un regex reemplazando un marcador por un grupo capturador.

    El patrón del usuario ya es un regex válido. Simplemente reemplazamos
    el marcador por el grupo capturador.
    """
    if marker not in pattern:
        raise ValueError(
            f"El patrón debe contener el marcador '{marker}'."
        )

    parts = pattern.split(marker, 1)
    if len(parts) != 2:
        raise ValueError(f"El marcador '{marker}' debe aparecer exactamente una vez.")

    before, after = parts
    full_pattern = before + capture + after
    return re.compile(full_pattern, re.DOTALL)


def extract_posts(
    html: str,
    url_pattern: str,
    title_pattern: str | None = None,
    base_url: str | None = None,
) -> list[dict]:
    """
    Extrae posts con título y URL usando patrones regex.

    Args:
        html: HTML a analizar.
        url_pattern: Patrón regex con $URL para capturar el href.
        title_pattern: Patrón regex con $TITLE para capturar el título.
        base_url: URL base para resolver enlaces relativos.

    Returns:
        Lista de dicts con 'url' y 'title'.
    """
    posts = []
    url_regex = build_regex(url_pattern, "$URL", r'href=["\']([^"\']+)["\']')

    for match in url_regex.finditer(html):
        post = {
            "url": match.group(1),
            "match_text": match.group(0),
        }

        # Resolver URL relativa
        if base_url and not post["url"].startswith(("http://", "https://", "//")):
            post["url"] = urljoin(base_url, post["url"])

        # Extraer título si se proporcionó patrón
        if title_pattern:
            title_regex = build_regex(title_pattern, "$TITLE", r'([^<]+)')
            title_match = title_regex.search(match.group(0))
            if title_match:
                raw_title = title_match.group(1)
                post["title"] = raw_title.lstrip('>').strip()
            else:
                # Intentar en contexto cercano
                start = max(0, match.start() - 500)
                end = min(len(html), match.end() + 500)
                context = html[start:end]
                title_match = title_regex.search(context)
                if title_match:
                    raw_title = title_match.group(1)
                    post["title"] = raw_title.lstrip('>').strip()
                else:
                    post["title"] = None
        else:
            post["title"] = None

        posts.append(post)

    return posts


def scrape_pages(
    base_url: str,
    url_pattern: str,
    pages: int = 1,
    page_param: str = "?p={page}",
    title_pattern: str | None = None,
    max_posts: int | None = None,
) -> list[dict]:
    """
    Scrapea múltiples páginas y devuelve todos los posts.

    Args:
        base_url: URL base del sitio.
        url_pattern: Patrón regex con $URL.
        pages: Número de páginas a scrapear.
        page_param: Template para el parámetro de página, usa {page}.
        title_pattern: Patrón regex con $TITLE para extraer títulos.
        max_posts: Máximo número de posts a devolver (None = todos).

    Returns:
        Lista de posts extraídos.
    """
    all_posts = []

    for page_num in range(1, pages + 1):
        if page_num == 1:
            url = base_url
        else:
            page_suffix = page_param.format(page=page_num)
            if "?" in base_url:
                url = f"{base_url}{page_suffix.replace('?', '&', 1)}"
            else:
                url = f"{base_url}{page_suffix}"

        print(f"  [página {page_num}/{pages}] {url}")

        try:
            html = fetch_html(url)
            posts = extract_posts(
                html=html,
                url_pattern=url_pattern,
                title_pattern=title_pattern,
                base_url=base_url,
            )
            all_posts.extend(posts)
            print(f"    → {len(posts)} posts")

            if max_posts and len(all_posts) >= max_posts:
                all_posts = all_posts[:max_posts]
                break

        except requests.RequestException:
            print(f"    → error en página {page_num}")
            continue

    return all_posts
