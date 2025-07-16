# ESG Engine: Development Plan

The ESG Engine is an AI-powered system designed to process, analyze, and summarize Environmental, Social, and Governance (ESG) documents. It uses three Retrieval-Augmented Generation (RAG) databases (Standards, Reports/Documents, Requirements) and a team of agents (Superbrain, Monitoring, Extraction, Evaluation, Summarization) to extract data, verify compliance, and generate human-readable summaries. This development plan outlines a phased approach to building the ESG Engine, ensuring each phase is self-contained, modular, and actionable for independent developers. Each phase includes objectives, tools, folder structure, tasks, deliverables, and success criteria, with a focus on maintainability and clarity.

The plan is structured into six phases, each addressing a distinct component. Phases adhere to SOLID (Single Responsibility, Open-Closed, Liskov Substitution, Interface Segregation, Dependency Inversion) and DRY (Don’t Repeat Yourself) principles. Files are organized into folders with single-functionality Python files to avoid large, unwieldy codebases. Each Python file follows a standard coding pattern:
- Multiline description of the file’s purpose.
- File path comment (e.g., `file path: esg_engine/rag/standards_rag/indexer.py`).
- Code body with docstrings for functions and inline comments at technical points.

The system will run on local machines with a 45% resource cap (RAM and disk) and scale to 80% on servers.

## Project Folder Structure

The ESG Engine uses a modular folder structure to enhance maintainability. RAG and agent components are organized as folders containing small, single-functionality Python files, reducing code complexity and improving debugging.

```
esg_engine/
├── config/
│   ├── settings.py
├── data/
│   ├── standards/
│   ├── requirements/
│   ├── reports/
│   ├── output/
├── rag/
│   ├── standards_rag/
│   │   ├── indexer.py
│   │   ├── searcher.py
│   │   ├── updater.py
│   ├── reports_rag/
│   │   ├── indexer.py
│   │   ├── searcher.py
│   │   ├── cleaner.py
│   ├── requirements_rag/
│   │   ├── parser.py
│   │   ├── searcher.py
│   │   ├── updater.py
├── agents/
│   ├── superbrain/
│   │   ├── coordinator.py
│   │   ├── workflow.py
│   ├── monitoring/
│   │   ├── resource_monitor.py
│   │   ├── file_watcher.py
│   ├── extraction/
│   │   ├── searcher.py
│   │   ├── concurrent.py
│   ├── evaluation/
│   │   ├── validator.py
│   │   ├── retry.py
│   ├── summarization/
│   │   ├── summarizer.py
├── utils/
│   ├── pdf_processing.py
│   ├── text_processing.py
│   ├── vector_utils.py
│   ├── file_monitor.py
│   ├── resource_monitor.py
├── main.py
```

## Technology Stack

All phases use the following open-source tools:
- **Python 3.8+**: Core language.
- **pdfplumber**: Extracts text from PDFs.
- **spaCy**: Tokenizes text into sentences.
- **sentence-transformers (all-MiniLM-L6-v2)**: Generates sentence embeddings.
- **FAISS**: Stores and searches vector embeddings on disk.
- **pandas**: Parses CSV files.
- **concurrent.futures**: Enables concurrent processing.
- **psutil**: Monitors resource usage.
- **watchdog**: Detects file changes.
- **LangChain**: Manages agents and RAG workflows.

Dependencies are installed via `pip install pdfplumber spacy sentence-transformers faiss-cpu pandas psutil watchdog langchain`.

## Coding Pattern

Every Python file must follow this structure:
```
"""
Multiline description of what the file does, its role in the system, and key functionality.
For example, this file handles PDF text extraction for the ESG Engine, processing pages and handling errors.

file path: esg_engine/utils/pdf_processing.py
"""

from ... import ...

def function_name(...):
    """
    Docstring explaining what the function does, its inputs, outputs, and how it works.
    For example, extracts text from a PDF page by page.
    Args:
        input_path (str): Path to the PDF file.
    Returns:
        list: List of dictionaries with page number and text.
    """
    # Inline comment explaining technical steps
    pass
```

Inline comments are required at technical points (e.g., complex logic, error handling) to ensure clarity.

## Phase 1: Configuration and Utility Modules

### Objective
Create the configuration and utility modules to provide reusable, modular components for PDF processing, text tokenization, vector operations, and resource monitoring, ensuring a solid foundation for the ESG Engine.

### Scope
Develop `config/settings.py`, `utils/pdf_processing.py`, `utils/text_processing.py`, `utils/vector_utils.py`, `utils/file_monitor.py`, and `utils/resource_monitor.py`. Each file handles a single responsibility, is reusable across modules, and follows the coding pattern.

### Tools
- Python 3.8+
- pdfplumber
- spaCy
- sentence-transformers
- FAISS
- psutil
- watchdog

### Tasks
1. **Develop config/settings.py**:
   - Define paths for `data/standards/`, `data/requirements/`, `data/reports/`, `data/output/`.
   - Set resource limits (45% RAM/disk locally, 80% on servers).
   - Include model parameters (e.g., `all-MiniLM-L6-v2` for sentence-transformers).
   - Store settings as a dictionary for easy access.
   - Add docstrings and inline comments for clarity.
2. **Develop utils/pdf_processing.py**:
   - Create a function to extract text from PDFs page by page using pdfplumber.
   - Return a list of dictionaries with `page_number` and `text` keys.
   - Handle errors (e.g., corrupted PDFs) by logging to `data/output/errors.log` and skipping invalid files.
   - Follow the coding pattern with description, path, and inline comments.
3. **Develop utils/text_processing.py**:
   - Create functions for sentence tokenization (spaCy) and embedding generation (sentence-transformers).
   - Return sentences and embeddings with metadata (page_number, sentence_index).
   - Handle empty text inputs by returning empty results.
   - Follow the coding pattern.
4. **Develop utils/vector_utils.py**:
   - Create functions to initialize, add to, and search a FAISS FlatL2 index stored on disk.
   - Support metadata storage (e.g., document name, page, sentence index).
   - Handle large datasets by processing in chunks.
   - Follow the coding pattern.
5. **Develop utils/file_monitor.py**:
   - Create a function to monitor folders for new or updated files using watchdog.
   - Trigger callbacks for file creation/modification events, with 30-minute polling as a fallback.
   - Log monitoring events to `data/output/monitor.log`.
   - Follow the coding pattern.
6. **Develop utils/resource_monitor.py**:
   - Create a function to monitor RAM and disk usage using psutil.
   - Calculate 45% of available resources (e.g., 7.2GB RAM, 45GB disk on a 16GB/100GB system).
   - Return a boolean for limit compliance.
   - Follow the coding pattern.
7. **Test Modules**:
   - Write unit tests using pytest for each function.
   - Test edge cases (e.g., corrupted PDFs, empty text, large datasets).

### Deliverables
- `config/settings.py`: Configuration file with paths and limits.
- `utils/pdf_processing.py`: PDF text extraction module.
- `utils/text_processing.py`: Sentence tokenization and embedding module.
- `utils/vector_utils.py`: FAISS index management module.
- `utils/file_monitor.py`: File monitoring module.
- `utils/resource_monitor.py`: Resource monitoring module.
- Unit tests for each module (in a separate `tests/` folder, if preferred).
- Documentation in docstrings and file descriptions.

### Success Criteria
- All modules pass unit tests with 95% coverage.
- PDF processing handles a 100-page PDF in under 30 seconds.
- Resource monitoring enforces 45% cap on local machines.
- File monitoring detects changes within 30 seconds.
- Modules are reusable and follow the coding pattern.

### Dependencies
- None (foundational phase).

## Phase 2: Standards RAG Database

### Objective
Build the Standards RAG Database to store ESG standards (e.g., IFRS S1, IFRS S2, ESRS) permanently, enabling sentence-level searches with metadata tracking and dynamic updates.

### Scope
Develop the `rag/standards_rag/` folder with three files: `indexer.py`, `searcher.py`, and `updater.py`. Each handles a single responsibility, using Phase 1 utilities, and supports selective queries (e.g., “IFRS S1 only”) or full searches.

### Tools
- Python 3.8+
- pdfplumber (via utils/pdf_processing.py)
- spaCy (via utils/text_processing.py)
- sentence-transformers (via utils/text_processing.py)
- FAISS (via utils/vector_utils.py)
- watchdog (via utils/file_monitor.py)

### Tasks
1. **Develop rag/standards_rag/indexer.py**:
   - Create a function to initialize a FAISS index at `data/standards/index.faiss`.
   - Load PDFs from `data/standards/` using `pdf_processing.py`.
   - Tokenize and embed sentences using `text_processing.py`.
   - Store embeddings and metadata (document name, page, sentence index) using `vector_utils.py`.
   - Follow the coding pattern with description, path, and inline comments.
2. **Develop rag/standards_rag/searcher.py**:
   - Create a function to query the FAISS index by text, returning top-k matches with metadata.
   - Support filtering by document name (e.g., “IFRS S1”).
   - Handle empty queries by returning empty results.
   - Follow the coding pattern.
3. **Develop rag/standards_rag/updater.py**:
   - Create a function to monitor `data/standards/` for new or updated PDFs using `file_monitor.py`.
   - Refresh the FAISS index every 30 minutes or on file changes.
   - Log updates to `data/output/standards_update.log`.
   - Follow the coding pattern.
4. **Handle Edge Cases**:
   - Skip corrupted PDFs and log errors.
   - Handle empty documents with empty result sets.
   - Process large PDFs in chunks within resource limits.
5. **Test Functionality**:
   - Write unit tests for indexing, searching, and updating.
   - Test selective queries and full searches with 3 sample standards.

### Deliverables
- `rag/standards_rag/indexer.py`: Indexing functionality.
- `rag/standards_rag/searcher.py`: Search functionality.
- `rag/standards_rag/updater.py`: Update functionality.
- `data/standards/index.faiss`: Persistent FAISS index.
- Unit tests for all functions.
- Documentation in docstrings and file descriptions.

### Success Criteria
- Indexes a 100-page standard in under 1 minute.
- Searches return top-5 matches in under 0.5 seconds.
- Updates detect new PDFs within 30 seconds.
- Handles 10 standards without exceeding 45% resource usage.
- Passes unit tests with 95% coverage.

### Dependencies
- Phase 1 utilities (`pdf_processing.py`, `text_processing.py`, `vector_utils.py`, `file_monitor.py`).

## Phase 3: Reports/Documents RAG Database

### Objective
Build the Reports/Documents RAG Database to process one ESG report at a time, creating a temporary FAISS index for sentence-level searches, with metadata tracking and cleanup after processing.

### Scope
Develop the `rag/reports_rag/` folder with three files: `indexer.py`, `searcher.py`, and `cleaner.py`. Each handles a single responsibility, using Phase 1 utilities, and supports concurrent searches.

### Tools
- Python 3.8+
- pdfplumber (via utils/pdf_processing.py)
- spaCy (via utils/text_processing.py)
- sentence-transformers (via utils/text_processing.py)
- FAISS (via utils/vector_utils.py)
- concurrent.futures

### Tasks
1. **Develop rag/reports_rag/indexer.py**:
   - Create a function to initialize a temporary FAISS index at `data/reports/temp_index.faiss`.
   - Load a single PDF from `data/reports/` using `pdf_processing.py`.
   - Tokenize and embed sentences using `text_processing.py`.
   - Store embeddings and metadata (document name, page, sentence index) using `vector_utils.py`.
   - Follow the coding pattern.
2. **Develop rag/reports_rag/searcher.py**:
   - Create a function to query the FAISS index, returning top-k matches with metadata (target sentence, before, after).
   - Support concurrent searches for multiple criteria using concurrent.futures.
   - Handle empty queries with empty result sets.
   - Follow the coding pattern.
3. **Develop rag/reports_rag/cleaner.py**:
   - Create a function to delete the temporary FAISS index after processing.
   - Ensure no residual files remain in `data/reports/`.
   - Log cleanup actions to `data/output/cleanup.log`.
   - Follow the coding pattern.
4. **Handle Edge Cases**:
   - Skip corrupted or empty PDFs, logging errors.
   - Process large PDFs in chunks within resource limits.
   - Ensure cleanup handles partial failures.
5. **Test Functionality**:
   - Write unit tests for indexing, searching, and cleanup.
   - Test concurrent searches with 5 criteria, returning results in under 1 second.

### Deliverables
- `rag/reports_rag/indexer.py`: Indexing functionality.
- `rag/reports_rag/searcher.py`: Search functionality.
- `rag/reports_rag/cleaner.py`: Cleanup functionality.
- Unit tests for all functions.
- Documentation in docstrings and file descriptions.

### Success Criteria
- Processes a 100-page report in under 1 minute.
- Handles 5 concurrent searches in under 1 second.
- Cleans up temporary index without residuals.
- Stays within 45% resource usage.
- Passes unit tests with 95% coverage.

### Dependencies
- Phase 1 utilities (`pdf_processing.py`, `text_processing.py`, `vector_utils.py`).

## Phase 4: Requirements RAG Database

### Objective
Build the Requirements RAG Database to store and manage app-specific CSV requirement files (category, criterion, description), enabling dynamic updates and fallback searches using descriptions.

### Scope
Develop the `rag/requirements_rag/` folder with three files: `parser.py`, `searcher.py`, and `updater.py`. Each handles a single responsibility, using Phase 1 utilities, and supports app-specific queries.

### Tools
- Python 3.8+
- pandas
- sentence-transformers (via utils/text_processing.py)
- FAISS (via utils/vector_utils.py)
- watchdog (via utils/file_monitor.py)

### Tasks
1. **Develop rag/requirements_rag/parser.py**:
   - Create a function to parse CSVs from `data/requirements/` using pandas, storing category, criterion, and description.
   - Validate CSV format (three columns) and log errors for malformed files.
   - Optionally embed criteria/descriptions using `text_processing.py`.
   - Follow the coding pattern.
2. **Develop rag/requirements_rag/searcher.py**:
   - Create a function to retrieve criteria by app name (e.g., “unctad_requirements.csv”).
   - Support fallback searches using descriptions if criteria yield no results.
   - Return results as a list of dictionaries with category, criterion, and description.
   - Follow the coding pattern.
3. **Develop rag/requirements_rag/updater.py**:
   - Create a function to monitor `data/requirements/` for new or updated CSVs using `file_monitor.py`.
   - Refresh the parsed data or FAISS index every 30 minutes or on changes.
   - Log updates to `data/output/requirements_update.log`.
   - Follow the coding pattern.
4. **Handle Edge Cases**:
   - Skip malformed CSVs and log errors.
   - Handle empty CSVs with empty result sets.
   - Ensure app-specific filtering works for multiple apps.
5. **Test Functionality**:
   - Write unit tests for parsing, searching, and updating.
   - Test fallback searches and app-specific filtering with 3 sample CSVs.

### Deliverables
- `rag/requirements_rag/parser.py`: CSV parsing functionality.
- `rag/requirements_rag/searcher.py`: Search functionality.
- `rag/requirements_rag/updater.py`: Update functionality.
- Unit tests for all functions.
- Documentation in docstrings and file descriptions.

### Success Criteria
- Parses a CSV with 1000 requirements in under 10 seconds.
- Searches return matching criteria in under 0.5 seconds.
- Updates detect new CSVs within 30 seconds.
- Stays within 45% resource usage.
- Passes unit tests with 95% coverage.

### Dependencies
- Phase 1 utilities (`text_processing.py`, `vector_utils.py`, `file_monitor.py`).

## Phase 5: Agent System

### Objective
Build the agent system to coordinate workflows, monitor resources, extract data, evaluate results, and generate summaries, ensuring modularity and concurrent processing.

### Scope
Develop the `agents/` folder with subfolders (`superbrain/`, `monitoring/`, `extraction/`, `evaluation/`, `summarization/`) containing single-functionality files. Each handles a specific task, using LangChain and Phase 1 utilities.

### Tools
- Python 3.8+
- LangChain
- concurrent.futures
- psutil (via utils/resource_monitor.py)
- watchdog (via utils/file_monitor.py)

### Tasks
1. **Develop agents/superbrain/coordinator.py**:
   - Create a function to initialize agents and RAG modules.
   - Coordinate interactions between agents and databases.
   - Follow the coding pattern with inline comments for agent setup.
2. **Develop agents/superbrain/workflow.py**:
   - Create a function to execute the workflow: load report, fetch requirements, extract, evaluate, summarize, save to `data/output/results.json`.
   - Save results with category, criterion, extracted sentences (with metadata), standard info, summary, document name, and processing time.
   - Follow the coding pattern.
3. **Develop agents/monitoring/resource_monitor.py**:
   - Create a function to check resource usage via `resource_monitor.py`, enforcing 45% local/80% server limits.
   - Advise on concurrency limits (e.g., max sub-agents).
   - Follow the coding pattern.
4. **Develop agents/monitoring/file_watcher.py**:
   - Create a function to monitor `data/standards/` and `data/requirements/` via `file_monitor.py`.
   - Notify RAG modules of updates.
   - Follow the coding pattern.
5. **Develop agents/extraction/searcher.py**:
   - Create a function to search Reports RAG for criteria, retrieving target sentence plus context (before, after) with metadata.
   - Follow the coding pattern.
6. **Develop agents/extraction/concurrent.py**:
   - Create a function to manage concurrent searches using concurrent.futures.
   - Spin up sub-agents for each criterion, respecting resource limits.
   - Follow the coding pattern.
7. **Develop agents/evaluation/validator.py**:
   - Create a function to validate extracted data against Standards RAG using LangChain reasoning.
   - Check completeness and compliance.
   - Follow the coding pattern.
8. **Develop agents/evaluation/retry.py**:
   - Create a function to retry failed extractions once, flagging unresolved issues.
   - Log retries to `data/output/evaluation.log`.
   - Follow the coding pattern.
9. **Develop agents/summarization/summarizer.py**:
   - Create a function to generate human-readable summaries using LangChain.
   - Combine extracted data, standards, and requirements.
   - Follow the coding pattern.
10. **Handle Edge Cases**:
    - Skip invalid inputs and log errors.
    - Handle no results with fallback searches or flagging.
    - Limit sub-agents if resources approach 45%.
11. **Test Functionality**:
    - Write unit tests for each function.
    - Test end-to-end workflow with a sample report, requirements, and standards.

### Deliverables
- `agents/superbrain/coordinator.py`, `workflow.py`: Coordination and workflow management.
- `agents/monitoring/resource_monitor.py`, `file_watcher.py`: Resource and file monitoring.
- `agents/extraction/searcher.py`, `concurrent.py`: Data extraction and concurrency.
- `agents/evaluation/validator.py`, `retry.py`: Result validation and retry logic.
- `agents/summarization/summarizer.py`: Summary generation.
- Unit tests for all functions.
- Documentation in docstrings and file descriptions.

### Success Criteria
- Processes a 100-page report with 10 criteria in under 5 minutes.
- Stays within 45% resource usage.
- Generates accurate summaries for 95% of valid inputs.
- Handles edge cases without crashing.
- Passes unit tests with 95% coverage.

### Dependencies
- Phase 1 utilities.
- Phase 2, 3, and 4 RAG modules.

## Phase 6: Main Entry Point and Integration

### Objective
Build the main entry point to integrate all components, enabling users to run the ESG Engine with a single command, and validate the end-to-end system.

### Scope
Develop `main.py` to initialize the system, coordinate agents, and process reports. Ensure seamless integration of RAG databases and agents, with comprehensive error handling.

### Tools
- Python 3.8+
- LangChain
- All modules from Phases 1–5

### Tasks
1. **Develop main.py**:
   - Create a command-line interface to accept inputs (report path, requirements CSV, optional standard filter).
   - Initialize `superbrain/coordinator.py` and RAG modules.
   - Execute the workflow via `superbrain/workflow.py`.
   - Save results to `data/output/results.json`.
   - Log processing time and errors to `data/output/main.log`.
   - Follow the coding pattern.
2. **Handle Edge Cases**:
   - Validate input files (report PDF, requirements CSV).
   - Handle missing standards/requirements with clear error messages.
   - Ensure cleanup of temporary indexes on failure.
3. **Test Integration**:
   - Write integration tests for end-to-end workflow with 5 reports, 10 criteria, and 3 standards.
   - Verify JSON output structure and accuracy.

### Deliverables
- `main.py`: Main entry point.
- Integration tests for end-to-end functionality.
- Documentation for running the system (e.g., `python main.py --report report.pdf --requirements unctad_requirements.csv`).

### Success Criteria
- Processes a 100-page report with 10 criteria in under 5 minutes.
- Generates correct JSON output with all required fields.
- Stays within 45% resource usage.
- Handles edge cases with clear errors.
- Passes integration tests with 95% coverage.

### Dependencies
- All modules from Phases 1–5.

## Development Guidelines

- **SOLID Principles**: Each file has a single responsibility (e.g., `standards_rag/indexer.py` only indexes). Files are open for extension (e.g., new file formats) and depend on abstractions (e.g., utility functions).
- **DRY Principles**: Shared utilities in `utils/` prevent duplication.
- **Coding Pattern**: Follow the specified structure (description, file path, docstrings, inline comments).
- **Testing**: Use pytest for unit and integration tests, targeting 95% coverage.
- **Documentation**: Include docstrings, file descriptions, and usage examples.
- **Error Handling**: Log errors to `data/output/` (e.g., `errors.log`, `standards_update.log`).
- **Resource Management**: Enforce 45% local resource cap, scaling to 80% on servers.
- **Modularity**: Files in subfolders (e.g., `standards_rag/`) ensure small, maintainable codebases.

## Timeline and Milestones

- **Phase 1 (Configuration and Utilities)**: 2 weeks  
  - Week 1: Develop `settings.py`, `pdf_processing.py`, `text_processing.py`.  
  - Week 2: Develop `vector_utils.py`, `file_monitor.py`, `resource_monitor.py`, and tests.
- **Phase 2 (Standards RAG)**: 1.5 weeks  
  - Develop and test `standards_rag/` files.
- **Phase 3 (Reports RAG)**: 1.5 weeks  
  - Develop and test `reports_rag/` files.
- **Phase 4 (Requirements RAG)**: 1 week  
  - Develop and test `requirements_rag/` files.
- **Phase 5 (Agent System)**: 3 weeks  
  - Week 1: Develop `superbrain/` and `monitoring/` files.  
  - Week 2: Develop `extraction/` and `evaluation/` files.  
  - Week 3: Develop `summarization/` files and tests.
- **Phase 6 (Main Entry Point)**: 1 week  
  - Develop and test `main.py`.

**Total Estimated Duration**: 10 weeks

## Success Metrics

- **System Performance**: Processes a 100-page report with 10 criteria in under 5 minutes.
- **Accuracy**: Achieves 95% accuracy in extraction and summarization.
- **Reliability**: Handles 99% of inputs without crashing.
- **Resource Efficiency**: Stays within 45% local, 80% server resource limits.
- **Maintainability**: All files pass unit tests with 95% coverage and follow the coding pattern.

This development plan ensures a modular, maintainable ESG Engine, with each phase providing clear, independent instructions for developers to build a robust system.
