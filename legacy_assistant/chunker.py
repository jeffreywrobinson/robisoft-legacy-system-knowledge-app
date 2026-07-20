from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter


def build_text_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=1400,
        chunk_overlap=180,
        separators=[
            "\n\n",
            "\n",
            ". ",
            ";",
            ",",
            " ",
            "",
        ],
    )
