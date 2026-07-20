# Legacy System Knowledge Assistant

Python web application that uses LangChain, ChromaDB, and the OpenAI API to analyze legacy source code and technical documentation.

The following five questions are asked. (Alternatively, the user may ask a custom question).

"What does this program do?"
"What business rules exist?"
"What are the inputs and outputs expected?",
"What modernization opportunities exist?",
"What dependencies are visible?",

## Features

- Upload single or multiple files from Streamlit.
- Supports source/text files plus PDF and Word `.docx` documents.
- Chunks uploaded content and stores embeddings in a local ChromaDB repository.
- Lists and removes files from the repository.
- Answers legacy-system analysis questions with retrieval augmented generation.
- Lets users review and save AI responses as Markdown.
- Includes a CLI for ingestion, listing, removal, and analysis.

## Local Setup

1. Create and activate a Python environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`, or enter the key in the Streamlit sidebar.
4. Start the app:

```powershell
streamlit run streamlit_app.py
```

The local ChromaDB repository is stored under `data/chroma` by default.

## CLI Usage

```powershell
python -m legacy_assistant.cli ingest path\to\program.cob path\to\design.docx
python -m legacy_assistant.cli list
python -m legacy_assistant.cli analyze --save
python -m legacy_assistant.cli analyze --question "Where are customer balances updated?"
python -m legacy_assistant.cli remove <file-id-or-exact-name>
```

## Application Structure

```text
Python
|
+-- File Loader         legacy_assistant/file_loader.py
+-- Text Chunker        legacy_assistant/chunker.py
+-- ChromaDB            legacy_assistant/repository.py
+-- OpenAI API          legacy_assistant/assistant.py
+-- CLI Interface       legacy_assistant/cli.py
+-- Streamlit UI        streamlit_app.py
```
