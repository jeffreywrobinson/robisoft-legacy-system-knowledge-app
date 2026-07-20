from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from legacy_assistant.chunker import build_text_splitter
from legacy_assistant.config import AppConfig
from legacy_assistant.file_loader import is_supported, load_file_text


MANIFEST_FILE = "repository_manifest.json"


@dataclass(frozen=True)
class RepositoryFile:
    file_id: str
    name: str
    path: str
    chunk_count: int
    uploaded_at: str


class LegacyRepository:
    def __init__(self, config: AppConfig):
        if not config.openai_api_key:
            raise ValueError("An OpenAI API key is required. Set OPENAI_API_KEY or enter it in the app.")
        self.config = config
        self.config.ensure_dirs()
        self._manifest_path = self.config.chroma_persist_dir / MANIFEST_FILE
        self._embeddings = OpenAIEmbeddings(
            model=self.config.embedding_model,
            api_key=self.config.openai_api_key,
        )
        self._vector_store = Chroma(
            collection_name=self.config.collection_name,
            embedding_function=self._embeddings,
            persist_directory=str(self.config.chroma_persist_dir),
        )

    @property
    def vector_store(self) -> Chroma:
        return self._vector_store

    def add_file(self, path: Path, original_name: str | None = None) -> RepositoryFile:
        if not is_supported(path):
            raise ValueError(f"Unsupported file type: {path.suffix}")

        file_id = str(uuid.uuid4())
        display_name = original_name or path.name
        stored_path = self._store_source_file(file_id, path, display_name)
        text = load_file_text(stored_path)
        if not text.strip():
            raise ValueError(f"No readable text found in {display_name}")

        splitter = build_text_splitter()
        chunks = splitter.split_text(text)
        ids = [f"{file_id}:{index}" for index in range(len(chunks))]
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "file_id": file_id,
                    "source": display_name,
                    "stored_path": str(stored_path),
                    "chunk_index": index,
                },
            )
            for index, chunk in enumerate(chunks)
        ]
        self._vector_store.add_documents(documents, ids=ids)

        repo_file = RepositoryFile(
            file_id=file_id,
            name=display_name,
            path=str(stored_path),
            chunk_count=len(chunks),
            uploaded_at=datetime.now(timezone.utc).isoformat(),
        )
        manifest = self._read_manifest()
        manifest[file_id] = {
            "file_id": repo_file.file_id,
            "name": repo_file.name,
            "path": repo_file.path,
            "chunk_count": repo_file.chunk_count,
            "uploaded_at": repo_file.uploaded_at,
            "ids": ids,
        }
        self._write_manifest(manifest)
        return repo_file

    def list_files(self) -> list[RepositoryFile]:
        files = []
        for item in self._read_manifest().values():
            files.append(
                RepositoryFile(
                    file_id=item["file_id"],
                    name=item["name"],
                    path=item["path"],
                    chunk_count=item["chunk_count"],
                    uploaded_at=item["uploaded_at"],
                )
            )
        return sorted(files, key=lambda item: item.uploaded_at, reverse=True)

    def remove_file(self, file_id: str) -> RepositoryFile:
        manifest = self._read_manifest()
        item = manifest.get(file_id)
        if not item:
            matches = [value for value in manifest.values() if value["name"] == file_id]
            if len(matches) == 1:
                item = matches[0]
                file_id = item["file_id"]
            else:
                raise KeyError(f"No repository file found for '{file_id}'")

        ids = item.get("ids", [])
        if ids:
            self._vector_store.delete(ids=ids)

        stored_path = Path(item["path"])
        if stored_path.exists():
            stored_path.unlink()

        del manifest[file_id]
        self._write_manifest(manifest)
        return RepositoryFile(
            file_id=item["file_id"],
            name=item["name"],
            path=item["path"],
            chunk_count=item["chunk_count"],
            uploaded_at=item["uploaded_at"],
        )

    def similarity_search(self, query: str, k: int = 8) -> list[Document]:
        return self._vector_store.similarity_search(query, k=k)

    def _store_source_file(self, file_id: str, path: Path, display_name: str) -> Path:
        safe_name = "".join(char if char.isalnum() or char in "._-" else "_" for char in display_name)
        stored_path = self.config.upload_dir / f"{file_id}_{safe_name}"
        shutil.copyfile(path, stored_path)
        return stored_path

    def _read_manifest(self) -> dict:
        if not self._manifest_path.exists():
            return {}
        return json.loads(self._manifest_path.read_text(encoding="utf-8"))

    def _write_manifest(self, manifest: dict) -> None:
        self._manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def format_sources(documents: Iterable[Document]) -> str:
    lines = []
    seen = set()
    for doc in documents:
        source = doc.metadata.get("source", "unknown")
        chunk = doc.metadata.get("chunk_index", "?")
        key = (source, chunk)
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"- {source}, chunk {chunk}")
    return "\n".join(lines)
