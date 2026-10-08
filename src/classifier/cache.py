#!/usr/bin/env python3
"""
Cache - Gestión de caché de veredictos LLM en CSV.

Evita llamadas repetidas al LLM para URLs ya evaluadas.
"""

import csv
import os
from pathlib import Path


def _get_cache_path() -> str:
    """Ruta al archivo de caché."""
    # Buscar en data/ relativo al proyecto
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    cache_dir = project_root / "data"
    cache_dir.mkdir(exist_ok=True)
    return str(cache_dir / "cache.csv")


def load_cache(filepath: str | None = None) -> dict[str, str]:
    """
    Carga la caché como dict {url: veredicto}.
    """
    path = filepath or _get_cache_path()
    cache = {}

    if not os.path.exists(path):
        return cache

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("url", "").strip()
            veredicto = row.get("veredicto", "").strip()
            if url and veredicto:
                cache[url] = veredicto

    return cache


def save_to_cache(url: str, titulo: str, veredicto: str, filepath: str | None = None):
    """
    Añade una entrada a la caché. Si la URL ya existe, no duplica.
    """
    path = filepath or _get_cache_path()
    file_exists = os.path.exists(path)

    # Verificar si ya está para no duplicar
    if file_exists:
        cache = load_cache(path)
        if url in cache:
            return

    with open(path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["url", "titulo", "veredicto"])
        writer.writerow([url, titulo, veredicto])


def get_veredicto(cache: dict[str, str], url: str) -> bool | None:
    """
    Obtiene el veredicto de la caché.
    Returns True/False o None si no está.
    """
    val = cache.get(url)
    if not val:
        return None
    return val.upper() in ("SÍ", "SI", "YES", "TRUE")
