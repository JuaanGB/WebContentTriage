#!/usr/bin/env python3
"""
Main entry point - Scraper y clasificador de Hacker News.

Enfoque híbrido:
  1. Keywords filtran rápido (score por peso de posición)
  2. LLM (OpenRouter) refina posts con score >= umbral_llm
"""

import sys
sys.path.insert(0, "src")

from classifier.cli import create_parser, print_config
from classifier.scraper import scrape_pages
from classifier.text_extractor import extract_from_url
from classifier.classifier import load_keywords, classify_post
from classifier.llm_classifier import classify_with_llm, build_summary_for_llm
from classifier.cache import load_cache, save_to_cache, get_veredicto
from classifier.output import (
    print_classified, print_results_pretty,
    print_results_json, save_csv, save_json,
)


def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.verbose or args.dry_run:
        print_config(args)

    if args.dry_run:
        print("🛑 Dry run - no se ejecutará.")
        return 0

    # Ajustar páginas automáticamente si se pidió max-posts
    if args.max_posts and args.pages == 1:
        estimated = (args.max_posts + 29) // 30
        if estimated > 1:
            print(f"⚠️  Ajustando a {estimated} páginas para {args.max_posts} posts")
            args.pages = estimated

    # Scrapear
    try:
        posts = scrape_pages(
            base_url=args.url,
            url_pattern=args.url_pattern,
            pages=args.pages,
            page_param=args.page_param,
            title_pattern=args.title_pattern,
            max_posts=args.max_posts,
        )
    except Exception as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        return 1

    # Clasificar
    if args.keywords:
        keyword_groups = load_keywords(args.keywords)
        llm_cache = load_cache() if args.llm else {}
        total = len(posts)

        classified = []
        for i, post in enumerate(posts, 1):
            print(f"  [{i}/{total}] {post.get('title', '')[:50]}...", end=" ")

            # Extraer texto si es posible
            extracted = None
            if args.extract_text and not args.no_extract_text:
                extracted = extract_from_url(post["url"])

            # Clasificación por keywords
            if extracted:
                result = classify_post(
                    extracted, keyword_groups,
                    title_weight=args.title_weight,
                    heading_weight=args.heading_weight,
                    paragraph_weight=args.paragraph_weight,
                    min_score=args.min_score,
                )
            else:
                result = classify_post(
                    {"title": post.get("title"), "headings": [], "paragraphs": []},
                    keyword_groups,
                    title_weight=args.title_weight,
                    heading_weight=args.heading_weight,
                    paragraph_weight=args.paragraph_weight,
                    min_score=args.min_score,
                )
                result["post_url"] = post["url"]

            # Fase 2: LLM para posts con score alto
            llm_result = None
            cached_veredicto = None

            if args.llm and result["score"] >= args.llm_threshold:
                # Verificar caché primero
                cached_veredicto = get_veredicto(llm_cache, post["url"])

                if cached_veredicto is not None:
                    print("→ cache", end=" ")
                    llm_result = {
                        "veredicto": cached_veredicto,
                        "score_llm": 0,
                        "razon": "(desde caché)",
                        "total_tokens": 0,
                    }
                else:
                    print("→ LLM", end=" ")
                    text_for_llm = build_summary_for_llm(extracted) if extracted else f"Título: {post.get('title', '')}"
                    llm_result = classify_with_llm(
                        title=post.get("title", ""),
                        url=post["url"],
                        text=text_for_llm,
                    )
                    if llm_result:
                        # Guardar en caché
                        save_to_cache(
                            post["url"],
                            post.get("title", ""),
                            "Sí" if llm_result["veredicto"] else "No",
                        )

            if llm_result:
                tokens = llm_result.get("total_tokens", 0)
                veredicto_str = "Sí" if llm_result['veredicto'] else "No"
                if cached_veredicto is not None:
                    print(f"({veredicto_str}, caché)", end=" ")
                else:
                    print(f"({veredicto_str}, {llm_result['score_llm']}/100, {tokens}tk)", end=" ")

            # Determinar relevancia final
            if llm_result and llm_result["veredicto"] is not None:
                result["is_relevant"] = llm_result["veredicto"]
                result["llm_score"] = llm_result["score_llm"]
                result["llm_razon"] = llm_result["razon"]
                result["llm_tokens"] = llm_result.get("total_tokens", 0)
            else:
                result["llm_score"] = None
                result["llm_razon"] = None
                result["llm_tokens"] = 0

            status = "✅" if result["is_relevant"] else "❌"
            print(f"{status} score={result['score']}")
            classified.append(result)

        print()
        print_classified(classified)

        if args.output:
            if args.output.endswith('.csv'):
                save_csv(classified, args.output)
            else:
                save_json(classified, args.output)
            print(f"Guardado en: {args.output}")

        return 0

    # Sin clasificar: mostrar posts scrapeados
    print_results_pretty(posts)
    if args.output:
        if args.output.endswith('.json'):
            save_json(posts, args.output)
        else:
            save_json(posts, args.output)
        print(f"Guardado en: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
