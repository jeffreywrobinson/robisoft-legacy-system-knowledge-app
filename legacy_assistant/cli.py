from __future__ import annotations

import argparse
from pathlib import Path

from legacy_assistant.assistant import LegacyKnowledgeAssistant
from legacy_assistant.config import AppConfig
from legacy_assistant.repository import LegacyRepository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Legacy System Knowledge Assistant CLI")
    parser.add_argument("--api-key", help="OpenAI API key. Defaults to OPENAI_API_KEY from .env or environment.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Add files to the local Chroma repository.")
    ingest.add_argument("files", nargs="+", help="Files to ingest.")

    subparsers.add_parser("list", help="List files in the repository.")

    remove = subparsers.add_parser("remove", help="Remove a file by file id or exact filename.")
    remove.add_argument("file_id", help="Repository file id or exact filename.")

    analyze = subparsers.add_parser("analyze", help="Ask questions against the repository.")
    analyze.add_argument("--question", help="Ask one custom question. Defaults to the five legacy-analysis questions.")
    analyze.add_argument("--save", action="store_true", help="Save the answer as Markdown under data/responses.")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = AppConfig.from_env(openai_api_key=args.api_key)

    if args.command == "ingest":
        repository = LegacyRepository(config)
        for file_name in args.files:
            added = repository.add_file(Path(file_name))
            print(f"Added {added.name} ({added.chunk_count} chunks) [{added.file_id}]")
        return

    if args.command == "list":
        repository = LegacyRepository(config)
        files = repository.list_files()
        if not files:
            print("Repository is empty.")
            return
        for item in files:
            print(f"{item.file_id} | {item.name} | {item.chunk_count} chunks | {item.uploaded_at}")
        return

    if args.command == "remove":
        repository = LegacyRepository(config)
        removed = repository.remove_file(args.file_id)
        print(f"Removed {removed.name} [{removed.file_id}]")
        return

    if args.command == "analyze":
        assistant = LegacyKnowledgeAssistant(config)
        results = [assistant.answer(args.question)] if args.question else assistant.answer_default_questions()
        for result in results:
            print(f"\n## {result.question}\n")
            print(result.answer)
            if result.sources:
                print(f"\nSources:\n{result.sources}")
        if args.save:
            path = assistant.save_results_markdown(results)
            print(f"\nSaved analysis to {path}")


if __name__ == "__main__":
    main()
