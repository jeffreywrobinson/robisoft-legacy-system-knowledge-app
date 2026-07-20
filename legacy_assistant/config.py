from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    openai_api_key: str | None
    openai_model: str
    embedding_model: str
    chroma_persist_dir: Path
    upload_dir: Path
    response_dir: Path
    collection_name: str = "legacy_system_knowledge"

    @classmethod
    def from_env(cls, openai_api_key: str | None = None) -> "AppConfig":
        return cls(
            openai_api_key=openai_api_key or os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            chroma_persist_dir=Path(os.getenv("CHROMA_PERSIST_DIR", "data/chroma")),
            upload_dir=Path(os.getenv("UPLOAD_DIR", "data/uploads")),
            response_dir=Path(os.getenv("RESPONSE_DIR", "data/responses")),
        )

    def ensure_dirs(self) -> None:
        self.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.response_dir.mkdir(parents=True, exist_ok=True)
