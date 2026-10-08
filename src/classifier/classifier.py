#!/usr/bin/env python3
"""
Keyword Classifier - Clasifica posts según coincidencias de keywords.

Lee keywords de un CSV (una línea = grupo de sinónimos, separados por comas).
Busca en texto de forma case-insensitive.
"""

import csv
import re
from collections import Counter
from pathlib import Path


def load_keywords(csv_path: str) -> list[list[str]]:
    """
    Carga keywords desde CSV.
    Cada línea es un grupo de sinónimos (ej: automation,automate,automating).
    """
    groups = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            # Limpiar y filtrar vacíos
            keywords = [k.strip().lower() for k in row if k.strip()]
            if keywords:
                groups.append(keywords)
    return groups


def _count_keyword(text: str | None, keyword: str) -> int:
    """Cuenta ocurrencias de una keyword en texto (case-insensitive)."""
    if text is None:
        return 0
    text_lower = text.lower()
    keyword_lower = keyword.lower()

    if ' ' in keyword_lower or '-' in keyword_lower:
        return text_lower.count(keyword_lower)
    else:
        escaped = re.escape(keyword_lower)
        return len(re.findall(r'\b' + escaped + r'\b', text_lower))


def classify(
    title: str,
    headings: list[str],
    paragraphs: list[str],
    keyword_groups: list[list[str]],
    title_weight: int = 3,
    heading_weight: int = 2,
    paragraph_weight: int = 1,
    min_score: int = 2,
) -> dict:
    """
    Cuenta coincidencias de keywords con peso por posición.

    Args:
        title: Título del post (peso ×3).
        headings: Lista de textos de headings (peso ×2 cada uno).
        paragraphs: Lista de textos de párrafos (peso ×1 cada uno).
        keyword_groups: Lista de grupos de sinónimos cargados del CSV.
        title_weight: Multiplicador para coincidencias en título.
        heading_weight: Multiplicador para coincidencias en headings.
        paragraph_weight: Multiplicador para coincidencias en párrafos.
        min_score: Puntuación mínima para considerar relevante.

    Returns:
        dict con:
          - score: puntuación ponderada total
          - raw_matches: suma sin ponderar
          - title_matches: coincidencias en título
          - heading_matches: coincidencias en headings
          - paragraph_matches: coincidencias en párrafos
          - group_matches: {grupo_idx: score_ponderado}
          - matched_keywords: {keyword: score_ponderado}
          - is_relevant: True si score >= min_score
    """
    score = 0
    raw_matches = 0
    group_counts = Counter()
    keyword_counts = Counter()

    # Contar en título
    title_score = 0
    for group_idx, group in enumerate(keyword_groups):
        for keyword in group:
            count = _count_keyword(title, keyword)
            if count > 0:
                weighted = count * title_weight
                title_score += weighted
                score += weighted
                raw_matches += count
                group_counts[group_idx] += weighted
                keyword_counts[keyword] += weighted

    # Contar en headings
    heading_score = 0
    for heading_text in headings:
        for group_idx, group in enumerate(keyword_groups):
            for keyword in group:
                count = _count_keyword(heading_text, keyword)
                if count > 0:
                    weighted = count * heading_weight
                    heading_score += weighted
                    score += weighted
                    raw_matches += count
                    group_counts[group_idx] += weighted
                    keyword_counts[keyword] += weighted

    # Contar en párrafos
    paragraph_score = 0
    for para_text in paragraphs:
        for group_idx, group in enumerate(keyword_groups):
            for keyword in group:
                count = _count_keyword(para_text, keyword)
                if count > 0:
                    weighted = count * paragraph_weight
                    paragraph_score += weighted
                    score += weighted
                    raw_matches += count
                    group_counts[group_idx] += weighted
                    keyword_counts[keyword] += weighted

    return {
        "score": score,
        "raw_matches": raw_matches,
        "title_matches": title_score,
        "heading_matches": heading_score,
        "paragraph_matches": paragraph_score,
        "group_matches": dict(group_counts),
        "matched_keywords": dict(keyword_counts),
        "is_relevant": score >= min_score,
    }


def classify_post(
    post_data: dict,
    keyword_groups: list[list[str]],
    title_weight: int = 3,
    heading_weight: int = 2,
    paragraph_weight: int = 1,
    min_score: int = 2,
) -> dict:
    """
    Clasifica un post completo (con headings y párrafos).

    Args:
        post_data: dict con 'title', 'headings', 'paragraphs' (de text_extractor).
        keyword_groups: Grupos de keywords cargados.
        title_weight: Multiplicador para título.
        heading_weight: Multiplicador para headings.
        paragraph_weight: Multiplicador para párrafos.
        min_score: Puntuación mínima para considerar relevante.

    Returns:
        dict con resultado de clasificación + datos originales.
    """
    title = post_data.get("title") or ""
    headings = [h["text"] for h in post_data.get("headings", [])]
    paragraphs = post_data.get("paragraphs", [])

    result = classify(
        title=title,
        headings=headings,
        paragraphs=paragraphs,
        keyword_groups=keyword_groups,
        title_weight=title_weight,
        heading_weight=heading_weight,
        paragraph_weight=paragraph_weight,
        min_score=min_score,
    )
    result["post_title"] = title
    result["post_url"] = post_data.get("url", "")
    result["text_length"] = len(title) + sum(len(h) for h in headings) + sum(len(p) for p in paragraphs)

    return result


if __name__ == "__main__":
    # Prueba rápida
    csv_path = Path(__file__).parent / "keywords.csv"
    groups = load_keywords(str(csv_path))
    print(f"Cargados {len(groups)} grupos de keywords")

    test_title = "AI automation and LLM agents for workflow productivity"
    test_headings = ["Introduction to AI Tools", "API Integration"]
    test_paragraphs = ["This post is about AI automation and LLM agents. We use OpenAI APIs for workflow automation."]

    result = classify(test_title, test_headings, test_paragraphs, groups)
    print(f"\nTítulo: {test_title}")
    print(f"Score: {result['score']} (raw: {result['raw_matches']})")
    print(f"  Título: {result['title_matches']}, Headings: {result['heading_matches']}, Párrafos: {result['paragraph_matches']}")
    print(f"Keywords: {result['matched_keywords']}")
    print(f"Relevante: {result['is_relevant']}")
