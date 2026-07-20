from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from legacy_assistant.config import AppConfig
from legacy_assistant.repository import LegacyRepository, format_sources


DEFAULT_QUESTIONS = [
    "What does this program do?",
    "What business rules exist?",
    "What are the inputs and outputs expected?",
    "What modernization opportunities exist?",
    "What dependencies are visible?",
]


SYSTEM_PROMPT = """You are the Legacy System Knowledge Assistant.
Analyze legacy source code and technical documentation using only the retrieved context.
Be precise, explain uncertainty, and cite source filenames or chunks when helpful.
When source code is ambiguous, say what evidence would be needed to confirm the behavior."""


USER_PROMPT = """Question:
{question}

Retrieved context:
{context}

Return a concise but useful answer with:
- Direct answer
- Evidence from the retrieved context
- Risks, assumptions, or modernization notes when relevant"""


@dataclass(frozen=True)
class AnalysisResult:
    question: str
    answer: str
    sources: str


class LegacyKnowledgeAssistant:
    def __init__(self, config: AppConfig):
        self.config = config
        self.repository = LegacyRepository(config)
        self._llm = ChatOpenAI(
            model=self.config.openai_model,
            api_key=self.config.openai_api_key,
            temperature=0.1,
        )
        self._prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("user", USER_PROMPT),
            ]
        )

    def answer(self, question: str, k: int = 8) -> AnalysisResult:
        documents = self.repository.similarity_search(question, k=k)
        context = "\n\n".join(
            f"Source: {doc.metadata.get('source')} | Chunk: {doc.metadata.get('chunk_index')}\n{doc.page_content}"
            for doc in documents
        )
        chain = self._prompt | self._llm
        response = chain.invoke({"question": question, "context": context})
        return AnalysisResult(question=question, answer=response.content, sources=format_sources(documents))

    def answer_default_questions(self) -> list[AnalysisResult]:
        return [self.answer(question) for question in DEFAULT_QUESTIONS]

    def save_results_markdown(self, results: list[AnalysisResult], filename_prefix: str = "legacy-analysis") -> str:
        self.config.response_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = self.config.response_dir / f"{filename_prefix}-{timestamp}.md"
        sections = ["# Legacy System Knowledge Assistant Analysis", ""]
        for result in results:
            sections.extend(
                [
                    f"## {result.question}",
                    "",
                    result.answer,
                    "",
                    "### Retrieved Sources",
                    result.sources or "No sources returned.",
                    "",
                ]
            )
        path.write_text("\n".join(sections), encoding="utf-8")
        return str(path)
