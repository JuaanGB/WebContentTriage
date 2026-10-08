#!/usr/bin/env python3
"""
CLI - Configuración de argumentos de línea de comandos.
"""

import argparse

# Configuración por defecto para Hacker News
DEFAULT_URL = "https://news.ycombinator.com/"

DEFAULT_URL_PATTERN = (
    '<span class="titleline">'
    '.*?<a[^>]*'
    '$URL'
    '[^>]*>.*?</a>.*?</span>'
)

DEFAULT_TITLE_PATTERN = (
    '<a[^>]*href=["\'][^"\']*["\'][^>]*>'
    '$TITLE'
    '</a>'
)


def create_parser() -> argparse.ArgumentParser:
    """Crea y configura el parser de argumentos."""
    parser = argparse.ArgumentParser(
        description="Scraper y clasificador de noticias técnicas.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Patrones regex:
  $URL   -> href del enlace
  $TITLE -> texto del título

El programador analiza la estructura HTML del sitio y proporciona
patrones que capturen los enlaces a posts y sus títulos.
        """,
    )

    parser.add_argument("--url", default=DEFAULT_URL, help="URL base a scrapear")
    parser.add_argument("--url-pattern", default=DEFAULT_URL_PATTERN, help="Patrón regex con $URL")
    parser.add_argument("--title-pattern", default=DEFAULT_TITLE_PATTERN, help="Patrón regex con $TITLE")

    parser.add_argument("--pages", type=int, default=1, help="Número de páginas (default: 1)")
    parser.add_argument("--page-param", default="?p={page}", help="Template de paginación")
    parser.add_argument("--max-posts", type=int, default=None, help="Máximo de posts")

    parser.add_argument("--output", "-o", default=None, help="Archivo de salida (.csv o .json)")

    parser.add_argument("--keywords", "-k", default=None, help="CSV de keywords")
    parser.add_argument("--extract-text", action="store_true", default=True, help="Extraer texto de posts (default: True)")
    parser.add_argument("--no-extract-text", action="store_true", help="No extraer texto, solo títulos")
    parser.add_argument("--min-score", type=int, default=2, help="Puntuación mínima para relevancia (default: 2)")
    parser.add_argument("--title-weight", type=int, default=3, help="Peso del título (default: 3)")
    parser.add_argument("--heading-weight", type=int, default=2, help="Peso de headings (default: 2)")
    parser.add_argument("--paragraph-weight", type=int, default=1, help="Peso de párrafos (default: 1)")

    # LLM
    parser.add_argument("--llm", action="store_true", help="Usar LLM (OpenRouter) para refinar posts con score alto")
    parser.add_argument("--llm-threshold", type=int, default=5, help="Score mínimo para enviar a LLM (default: 5)")

    parser.add_argument("--verbose", "-v", action="store_true", help="Mostrar configuración")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar config sin ejecutar")

    return parser


def print_config(args):
    """Muestra la configuración actual."""
    print("=" * 60)
    print("CONFIGURACIÓN")
    print("=" * 60)
    print(f"URL:        {args.url}")
    print(f"Páginas:    {args.pages}")
    print(f"Max posts:  {args.max_posts or 'sin límite'}")
    print(f"Keywords:   {args.keywords or 'ninguno'}")
    print(f"Output:     {args.output or 'stdout'}")
    print("=" * 60)
    print()
