#!/usr/bin/env python3
"""
Output - Funciones de presentación y guardado de resultados.
"""

import csv
import json


def print_classified(results: list[dict]):
    """Muestra resumen de resultados clasificados."""
    relevant = [r for r in results if r.get("is_relevant", False)]
    irrelevant = [r for r in results if not r.get("is_relevant", False)]

    print(f"\n{len(results)} posts | {len(relevant)} relevantes | {len(irrelevant)} no relevantes\n")

    # Mostrar top 5 relevantes con detalle
    top_relevant = sorted(
        [r for r in results if r.get("is_relevant", False)],
        key=lambda r: r["score"],
        reverse=True,
    )[:5]


def save_csv(results: list[dict], filepath: str):
    """Guarda resultados clasificados en CSV, ordenados por score decreciente."""
    sorted_results = sorted(results, key=lambda r: r["score"], reverse=True)

    fieldnames = [
        "score", "relevante", "titulo", "url", "keywords",
        "title_matches", "heading_matches", "paragraph_matches",
        "llm_score", "llm_razon", "llm_tokens",
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in sorted_results:
            writer.writerow({
                "score": r["score"],
                "relevante": "Sí" if r["is_relevant"] else "No",
                "titulo": r.get("post_title", ""),
                "url": r.get("post_url", ""),
                "keywords": ", ".join(r.get("matched_keywords", {}).keys()),
                "title_matches": r.get("title_matches", 0),
                "heading_matches": r.get("heading_matches", 0),
                "paragraph_matches": r.get("paragraph_matches", 0),
                "llm_score": r.get("llm_score") if r.get("llm_score") is not None else "",
                "llm_razon": r.get("llm_razon", ""),
                "llm_tokens": r.get("llm_tokens", 0),
            })


def save_json(results: list[dict], filepath: str):
    """Guarda resultados en JSON."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def print_results_pretty(posts: list[dict]):
    """Muestra posts scrapeados sin clasificar."""
    print(f"\n{'=' * 70}")
    print(f"RESULTADOS: {len(posts)} posts encontrados")
    print(f"{'=' * 70}\n")

    for i, post in enumerate(posts, 1):
        title = post.get("title") or "[Sin título]"
        url = post.get("url") or "[Sin URL]"

        print(f"{i}. {title}")
        print(f"   URL: {url}")
        print()


def print_results_json(posts: list[dict]):
    """Muestra posts en JSON por stdout."""
    print(json.dumps(posts, indent=2, ensure_ascii=False))
