# ESG Engine Run Guide

This guide provides detailed instructions for running the ESG Engine in a local environment. The ESG Engine is an AI-powered system for processing, analyzing, and summarizing Environmental, Social, and Governance (ESG) documents. It uses three Retrieval-Augmented Generation (RAG) databases (Standards, Reports, Requirements) and a team of agents to extract data, verify compliance, and generate summaries, saving results to `data/output/results.json`. This guide covers setup, running the system, testing, verifying outputs, and troubleshooting, tailored for developers with varying experience levels.

## System Overview

The ESG Engine processes ESG reports (e.g., `btg-pactual.pdf`) against requirements (e.g., `UNCTAD_requirements.csv`) and standards (e.g., `ifrs_s1.pdf`, `ifrs_s2.pdf`, `ESRS_2.pdf`). It consists of:
- **Phase 1**: Utilities for PDF processing, text tokenization, vector operations, and resource monitoring.
- **Phase 2**: Standards RAG for indexing and searching standards.
- **Phase 3**: Reports RAG for processing reports with temporary indexes.
- **Phase 4**: Requirements RAG for parsing and searching CSV requirements.
- **Phase 5**: Agent system for coordinating workflows, extracting data, validating, and summarizing.
- **Phase 6**: Main entry point (`main.py`) for running the system via a command-line interface (CLI).

The system enforces a 45% resource cap locally (e.g., <7.2GB RAM, <45GB disk on a 16GB/100GB system) and logs to `data/output/`.

## Prerequisites

### Hardware
- **CPU**: 4 cores or more (e.g., Intel i5 or equivalent).
- **RAM**: Minimum 16GB (7.2GB available for ESG Engine).
- **Disk**: Minimum 100GB free (45GB available for ESG Engine).
- **OS**: Windows, macOS, or Linux (tested on Ubuntu 20.04).

### Software
- **Python**: 3.8 or higher (3.9 recommended).
- **pip**: Latest version for dependency installation.
- **Virtual Environment**: Recommended (e.g., `venv` or `virtualenv`).

### Dependencies
Install the following via `pip`:
- `pdfplumber`: PDF text extraction.
- `spacy`: Sentence tokenization.
- `sentence-transformers`: Sentence embeddings (use `all-MiniLM-L6-v2`).
- `faiss-cpu`: Vector storage and search.
- `pandas`: CSV parsing.
- `psutil`: Resource monitoring.
- `watchdog`: File monitoring.
- `langchain` and `langchain-community`: Agent workflows and summarization.
- `pytest`: Unit and integration testing.
- `pytest-cov`: Test coverage reporting.

## Setup

### Step 1: Clone or Create Project Structure
Create the project folder structure:
```bash
mkdir -p esg_engine/{config,data/{standards,reports,requirements,output},utils,rag/{standards_rag,reports_rag,requirements_rag},agents/{superbrain,monitoring,extraction,evaluation,summarization},tests}
```

Ensure the following structure:
```
esg_engine/
├── config/
│   ├── settings.py
├── data/
│   ├── standards/
│   │   ├── ifrs_s1.pdf
│   │   ├── ifrs_s2.pdf
│   │   ├── ESRS_2.pdf
│   ├── reports/
│   │   ├── btg-pactual.pdf
│   ├── requirements/
│   │   ├── UNCTAD_requirements.csv
│   │   ├── UNEP_requirements.csv
│   ├── output/
├── utils/
│   ├── pdf_processing.py
│   ├── text_processing.py
│   ├── vector_utils.py
│   ├── file_monitor.py
│   ├── resource_monitor.py
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
├── tests/
│   ├── test_settings.py
│   ├── test_pdf_processing.py
│   ├── test_text_processing.py
│   ├── test_vector_utils.py
│   ├── test_file_monitor.py
│   ├── test_resource_monitor.py
│   ├── test_standards_rag.py
│   ├── test_reports_rag.py
│   ├── test_requirements_rag.py
│   ├── test_agents.py
│   ├── test_main.py
├── main.py
```

### Step 2: Place Data Files
Place the following files in their respective directories:
- **Reports**: `data/reports/btg-pactual.pdf`
- **Requirements**: `data/requirements/UNCTAD_requirements.csv`, `data/requirements/UNEP_requirements.csv`
- **Standards**: `data/standards/ifrs_s1.pdf`, `data/standards/ifrs_s2.pdf`, `data/standards/ESRS_2.pdf`

**CSV Format**: The system expects CSVs to have columns `category`, `criterion`, `description` (e.g., `Environment,Emissions Reporting,Report annual carbon emissions in metric tons`). If your CSVs differ, update `rag/requirements_rag/parser.py` to match your format.

### Step 3: Set Up Virtual Environment
Create and activate a virtual environment to isolate dependencies:
```bash
python -m venv esg_engine_venv
source esg_engine_venv/bin/activate  # Linux/macOS
esg_engine_venv\Scripts\activate     # Windows
```

### Step 4: Install Dependencies
Install required packages:
```bash
pip install pdfplumber spacy sentence-transformers faiss-cpu pandas psutil watchdog langchain langchain-community pytest pytest-cov
python -m spacy download en_core_web_sm
```

If installation fails (e.g., for `sentence-transformers` or `langchain`), try specific versions:
```bash
pip install sentence-transformers==2.2.2 langchain==0.2.0 langchain-community==0.2.0 --no-cache-dir
```

Verify installations:
```bash
pip list | grep -E "pdfplumber|spacy|sentence-transformers|faiss-cpu|pandas|psutil|watchdog|langchain|pytest"
```

**Note**: If `sentence-transformers` or `langchain` are not yet installed, save the code files and proceed once installed.

### Step 5: Save Code Files
Ensure all code files from Phases 1–6 are saved in their respective directories (see structure above). These include:
- **Phase 1**: `config/settings.py`, `utils/pdf_processing.py`, `utils/text_processing.py`, `utils/vector_utils.py`, `utils/file_monitor.py`, `utils/resource_monitor.py`.
- **Phase 2**: `rag/standards_rag/indexer.py`, `searcher.py`, `updater.py`.
- **Phase 3**: `rag/reports_rag/indexer.py`, `searcher.py`, `cleaner.py`.
- **Phase 4**: `rag/requirements_rag/parser.py`, `searcher.py`, `updater.py`.
- **Phase 5**: `agents/superbrain/coordinator.py`, `workflow.py`, `monitoring/resource_monitor.py`, `file_watcher.py`, `extraction/searcher.py`, `concurrent.py`, `evaluation/validator.py`, `retry.py`, `summarization/summarizer.py`.
- **Phase 6**: `main.py`.

Test files:
- `tests/test_settings.py`
- `tests/test_pdf_processing.py`
- `tests/test_text_processing.py`
- `tests/test_vector_utils.py`
- `tests/test_file_monitor.py`
- `tests/test_resource_monitor.py`
- `tests/test_standards_rag.py`
- `tests/test_reports_rag.py`
- `tests/test_requirements_rag.py`
- `tests/test_agents.py`
- `tests/test_main.py`

## Running the System

### Step 1: Verify Resource Availability
The ESG Engine enforces a 45% resource cap (e.g., <7.2GB RAM, <45GB disk on a 16GB/100GB system). Check resources:
```bash
python -c "import psutil; print(f'RAM: {psutil.virtual_memory().available / (1024**3):.2f}GB'); print(f'Disk: {psutil.disk_usage(\"/\").free / (1024**3):.2f}GB')"
```
Ensure available RAM >7.2GB and disk >45GB. Close other applications if needed.

### Step 2: Run the System
Use the CLI in `main.py` to process a report. Example:
```bash
python main.py --report data/reports/btg-pactual.pdf --requirements data/requirements/UNCTAD_requirements.csv --standard data/standards/ifrs_s1.pdf
```

**Options**:
- `--report`: Path to the ESG report PDF (required).
- `--requirements`: Path to the requirements CSV (required).
- `--standard`: Specific standard to filter (optional, e.g., `ifrs_s1.pdf`).

**Expected Output**:
- Console: Confirmation of completion and processing time (e.g., `Workflow completed successfully in 123.45 seconds`).
- File: Results saved to `data/output/results.json`.
- Logs: Execution details in `data/output/main.log`.

**Example Output in `results.json`**:
```json
[
  {
    "category": "Environment",
    "criterion": "Emissions Reporting",
    "extracted_sentences": [
      {"sentence": "Reported 100 tons of CO2", "page": 5, "context": {"before": "Emissions data", "after": "Next section"}}
    ],
    "standard_info": [
      {"document": "ifrs_s1.pdf", "sentence": "Annual emissions reporting required", "page": 10}
    ],
    "summary": "Compliant based on 1 match and 1 standard",
    "document_name": "btg-pactual.pdf",
    "processing_time": 123.45
  }
]
```

### Step 3: Run Without Standard Filter
To process against all standards:
```bash
python main.py --report data/reports/btg-pactual.pdf --requirements data/requirements/UNCTAD_requirements.csv
```

## Testing the System

### Step 1: Run Unit and Integration Tests
Run all tests to verify functionality and coverage:
```bash
pytest tests/ --cov=config utils rag.standards_rag rag.reports_rag rag.requirements_rag agents main --cov-report=html
```

**Details**:
- **Tests**: Cover all modules (`test_settings.py`, `test_pdf_processing.py`, `test_text_processing.py`, `test_vector_utils.py`, `test_file_monitor.py`, `test_resource_monitor.py`, `test_standards_rag.py`, `test_reports_rag.py`, `test_requirements_rag.py`, `test_agents.py`, `test_main.py`).
- **Coverage**: Generates report in `htmlcov/index.html`. Target: ~95%.
- **Output**: Console shows passed/failed tests. Check `htmlcov/` for detailed coverage.

### Step 2: Test Specific Components
Run individual test files for debugging:
```bash
pytest tests/test_settings.py
pytest tests/test_pdf_processing.py
pytest tests/test_text_processing.py
pytest tests/test_vector_utils.py
pytest tests/test_file_monitor.py
pytest tests/test_resource_monitor.py
pytest tests/test_standards_rag.py
pytest tests/test_reports_rag.py
pytest tests/test_requirements_rag.py
pytest tests/test_agents.py
pytest tests/test_main.py
```

### Step 3: Verify Test Outputs
- **Success**: All tests pass, coverage ≥95%.
- **Logs**: Check `data/output/` for logs (`errors.log`, `standards_update.log`, `cleanup.log`, `requirements_update.log`, `resource.log`, `coordinator.log`, `workflow.log`, `extraction.log`, `evaluation.log`, `summarization.log`, `main.log`).
- **Results**: `test_main.py` generates `results.json` for valid inputs.

## Verifying Outputs

### Step 1: Check `results.json`
After running `main.py`, verify `data/output/results.json`:
- **Location**: `data/output/results.json`
- **Structure**: List of dictionaries with fields:
  - `category`: Requirement category (e.g., `Environment`).
  - `criterion`: Requirement criterion (e.g., `Emissions Reporting`).
  - `extracted_sentences`: List of matches with sentence, page, and context.
  - `standard_info`: List of matching standards with document, sentence, page.
  - `summary`: Human-readable compliance summary.
  - `document_name`: Report filename (e.g., `btg-pactual.pdf`).
  - `processing_time`: Time in seconds.
- **Validation**: Ensure all fields are present and non-empty for valid inputs.

### Step 2: Check Logs
Inspect logs in `data/output/`:
- `main.log`: CLI execution and errors.
- `coordinator.log`: Agent and RAG initialization.
- `workflow.log`: Workflow execution.
- `resource.log`: Resource usage (RAM, disk).
- `monitor.log`: File changes in `standards/` and `requirements/`.
- `extraction.log`: Data extraction results.
- `evaluation.log`: Validation and retry results.
- `summarization.log`: Summary generation.
- `standards_update.log`: Standards RAG updates.
- `requirements_update.log`: Requirements RAG updates.
- `cleanup.log`: Reports RAG cleanup.
- `errors.log`: General errors.

Use `cat` (Linux/macOS) or `type` (Windows) to view:
```bash
cat data/output/main.log  # Linux/macOS
type data\output\main.log  # Windows
```

## Troubleshooting

### Issue 1: Dependency Installation Fails
- **Symptom**: Errors like `pip install sentence-transformers` or `langchain` fails.
- **Solution**:
  - Try specific versions:
    ```bash
    pip install sentence-transformers==2.2.2 langchain==0.2.0 langchain-community==0.2.0 --no-cache-dir
    ```
  - Ensure compatible Python (3.8+): `python --version`.
  - Check internet connection or use `--no-cache-dir`.
  - Update pip: `pip install --upgrade pip`.

### Issue 2: Missing Data Files
- **Symptom**: `main.py` or tests fail with `not found` errors for `btg-pactual.pdf` or `UNCTAD_requirements.csv`.
- **Solution**:
  - Verify files in `data/reports/`, `data/requirements/`, `data/standards/`.
  - If missing, tests create sample files in `tmp_path`. Replace with real data.
  - Ensure CSV format matches `category,criterion,description`. If different, update `rag/requirements_rag/parser.py`.

### Issue 3: Resource Limits Exceeded
- **Symptom**: `Resource usage exceeds 45% limit` in console or `resource.log`.
- **Solution**:
  - Check resource usage: `python -c "import psutil; print(psutil.virtual_memory().available / (1024**3))"`.
  - Close other applications to free RAM/disk.
  - Reduce `k` in search functions (e.g., `search_standards`, `search_report`, `search_requirements`) to lower memory usage.

### Issue 4: Tests Fail
- **Symptom**: `pytest` reports failures or low coverage.
- **Solution**:
  - Check error messages in console or logs.
  - Run individual tests to isolate issues: `pytest tests/test_<module>.py`.
  - Ensure dependencies are installed (e.g., `sentence-transformers`, `langchain`).
  - Verify data files are present and correctly formatted.
  - Check `htmlcov/index.html` for uncovered lines and add tests if needed.

### Issue 5: LangChain Errors
- **Symptom**: Errors in `agents/evaluation/validator.py` or `agents/summarization/summarizer.py` due to `FakeListLLM`.
- **Solution**:
  - Install `langchain` and replace `FakeListLLM` with a real LLM (e.g., `HuggingFaceHub`):
    ```python
    from langchain_community.llms import HuggingFaceHub
    llm = HuggingFaceHub(repo_id="google/flan-t5-base", huggingfacehub_api_token="your_token")
    ```
  - Set `HUGGINGFACEHUB_API_TOKEN` environment variable or configure in `config/settings.py`.

### Issue 6: Slow Performance
- **Symptom**: Processing takes >5 minutes for 10 criteria.
- **Solution**:
  - Check `resource.log` for bottlenecks (e.g., high RAM usage).
  - Reduce `k` in search functions (e.g., set `k=3` instead of `k=5`).
  - Ensure concurrent searches use appropriate `max_sub_agents` in `agents/extraction/concurrent.py`.
  - Verify indexing efficiency in `rag/standards_rag/indexer.py`, `rag/reports_rag/indexer.py`.

## Maintenance

### Updating Data
- **Add New Reports**: Place new PDFs in `data/reports/`. Run `main.py` with the new report path.
- **Add New Requirements**: Place new CSVs in `data/requirements/`. The `requirements_rag/updater.py` detects changes within 30 seconds.
- **Add New Standards**: Place new PDFs in `data/standards/`. The `standards_rag/updater.py` updates the index within 30 seconds.
- **CSV Format**: If new CSVs have different columns, update `rag/requirements_rag/parser.py` and test with `tests/test_requirements_rag.py`.

### Monitoring Logs
Regularly check `data/output/` logs for errors or performance issues:
```bash
ls data/output/
cat data/output/errors.log  # View general errors
```

### Updating Code
- **New Features**: Extend `main.py` for additional CLI options or modify agent logic in `agents/`.
- **Bug Fixes**: Use test failures and logs to identify issues, then update specific modules.
- **Dependency Updates**: Re-run `pip install` with updated versions and test compatibility.

## Example Workflow
To process `btg-pactual.pdf` against `UNCTAD_requirements.csv` with `ifrs_s1.pdf`:
1. Activate virtual environment:
   ```bash
   source esg_engine_venv/bin/activate  # Linux/macOS
   esg_engine_venv\Scripts\activate     # Windows
   ```
2. Run the system:
   ```bash
   python main.py --report data/reports/btg-pactual.pdf --requirements data/requirements/UNCTAD_requirements.csv --standard data/standards/ifrs_s1.pdf
   ```
3. Check output:
   ```bash
   cat data/output/results.json  # Linux/macOS
   type data\output\results.json # Windows
   ```
4. Run tests:
   ```bash
   pytest tests/ --cov --cov-report=html
   ```
5. View coverage:
   - Open `htmlcov/index.html` in a browser.

## Success Metrics
- **Performance**: Processes a 100-page report with 10 criteria in <5 minutes.
- **Accuracy**: 95% of valid inputs produce correct `results.json` entries.
- **Reliability**: Handles 99% of inputs without crashing.
- **Resource Efficiency**: Stays within 45% RAM/disk locally.
- **Test Coverage**: ≥95% coverage across all modules.
