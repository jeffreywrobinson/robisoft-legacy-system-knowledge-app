from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from legacy_assistant.assistant import DEFAULT_QUESTIONS, LegacyKnowledgeAssistant
from legacy_assistant.config import AppConfig
from legacy_assistant.file_loader import SUPPORTED_EXTENSIONS
from legacy_assistant.repository import LegacyRepository


st.set_page_config(page_title="Legacy System Knowledge Assistant", layout="wide")


def get_api_key() -> str | None:
    env_config = AppConfig.from_env()
    with st.sidebar:
        st.header("OpenAI")
        entered_key = st.text_input(
            "API key",
            type="password",
            placeholder="Uses OPENAI_API_KEY from .env when blank",
        )
        st.caption("Keys entered here are used for this session only.")
    return entered_key or env_config.openai_api_key


def get_repository(config: AppConfig) -> LegacyRepository:
    return LegacyRepository(config)


def show_repository(repository: LegacyRepository) -> None:
    st.subheader("Repository Files")
    files = repository.list_files()
    if not files:
        st.info("No files have been added yet.")
        return

    for item in files:
        cols = st.columns([3, 1, 2, 1])
        cols[0].write(item.name)
        cols[1].write(f"{item.chunk_count} chunks")
        cols[2].caption(item.file_id)
        if cols[3].button("Remove", key=f"remove-{item.file_id}"):
            repository.remove_file(item.file_id)
            st.success(f"Removed {item.name}")
            st.rerun()


def upload_files(repository: LegacyRepository) -> None:
    st.subheader("Upload Legacy Files")
    accepted_types = sorted(extension.lstrip(".") for extension in SUPPORTED_EXTENSIONS)
    uploaded_files = st.file_uploader(
        "Add source code, text, PDF, or Word documents",
        type=accepted_types,
        accept_multiple_files=True,
    )
    if not uploaded_files:
        return

    if st.button("Add selected files to repository", type="primary"):
        for uploaded in uploaded_files:
            suffix = Path(uploaded.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.getbuffer())
                tmp_path = Path(tmp.name)
            try:
                added = repository.add_file(tmp_path, original_name=uploaded.name)
                st.success(f"Added {added.name} ({added.chunk_count} chunks)")
            finally:
                tmp_path.unlink(missing_ok=True)
        st.rerun()


def analyze_repository(config: AppConfig) -> None:
    st.subheader("AI Analysis")
    st.write("Run the standard legacy-system questions or ask your own.")

    selected_questions = st.multiselect(
        "Standard questions",
        options=DEFAULT_QUESTIONS,
        default=DEFAULT_QUESTIONS,
    )
    custom_question = st.text_area("Custom question", placeholder="Ask a question about the uploaded system...")

    run_standard = st.button("Analyze selected questions", type="primary")
    run_custom = st.button("Ask custom question")

    if run_standard or run_custom:
        assistant = LegacyKnowledgeAssistant(config)
        questions = [custom_question.strip()] if run_custom and custom_question.strip() else selected_questions
        if not questions:
            st.warning("Choose at least one question.")
            return

        results = []
        for question in questions:
            with st.spinner(f"Analyzing: {question}"):
                results.append(assistant.answer(question))
        st.session_state["last_results"] = results

    results = st.session_state.get("last_results", [])
    if not results:
        return

    reviewed_results = []
    for index, result in enumerate(results):
        with st.expander(result.question, expanded=True):
            edited = st.text_area(
                "Review or edit response",
                value=result.answer,
                height=260,
                key=f"answer-{index}",
            )
            st.markdown("**Retrieved sources**")
            st.code(result.sources or "No sources returned.")
            reviewed_results.append(type(result)(question=result.question, answer=edited, sources=result.sources))

    if st.button("Save reviewed responses"):
        assistant = LegacyKnowledgeAssistant(config)
        st.session_state["last_results"] = reviewed_results
        path = assistant.save_results_markdown(reviewed_results)
        st.success(f"Saved analysis to {path}")


def main() -> None:
    st.title("Legacy System Knowledge Assistant")
    st.caption("AI-assisted RAG analysis for source code and technical documentation.")

    api_key = get_api_key()
    if not api_key:
        st.warning("Enter an OpenAI API key in the sidebar or set OPENAI_API_KEY in your .env file.")
        st.stop()

    config = AppConfig.from_env(openai_api_key=api_key)
    try:
        repository = get_repository(config)
    except Exception as exc:
        st.error(f"Repository initialization failed: {exc}")
        st.stop()

    left, right = st.columns([1, 1])
    with left:
        upload_files(repository)
    with right:
        show_repository(repository)

    st.divider()
    analyze_repository(config)


if __name__ == "__main__":
    main()
