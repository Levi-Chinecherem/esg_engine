# ESG Compliance Verification System Development Plan

## Overview

This development plan outlines the phased implementation of the ESG Compliance Verification System, an automated tool for auditing corporate sustainability reports against Environmental, Social, and Governance (ESG) standards. The system leverages a **triangular Retrieval-Augmented Generation (RAG) system** integrating **requirements**, **standards**, and **report document** to process company PDFs, validate compliance against frameworks (GRI, IFRS S1/S2, SASB, UN Global Compact), and generate CSV and PDF outputs in ~90 seconds (78s for CSV, 12s for PDF). The plan ensures modularity, adheres to the single responsibility principle, follows the DRY (Don't Repeat Yourself) principle, and uses a strict Python file structure pattern for clarity and maintainability.

The development is divided into **five phases**, each with self-contained tasks assigned to specific files in a clear folder structure. Phases are designed for independent implementation, allowing developers to focus on their tasks without needing details of other phases. The system supports multiple requirements and standards files in dedicated folders, enabling dynamic selection during setup and audits. The final integration ensures seamless operation, producing accurate, stakeholder-friendly outputs.

## Development Principles
- **Single Responsibility Principle**: Each Python file handles one specific task (e.g., PDF extraction, compliance checking).
- **DRY Principle**: Avoid code duplication through reusable utilities and configuration-driven logic.
- **Python File Structure**: Every `.py` file must follow the specified pattern:
  - Multiline docstring with file path, role, and key functionality.
  - Function docstrings with purpose, inputs, outputs, and logic explanation.
  - Inline comments for technical steps (e.g., complex logic, error handling).
- **Performance Goal**: Total processing time ~90 seconds (78s CSV + 12s PDF).
- **Accuracy**: Ensure compliance checks align with verbatim standards, with full traceability in outputs.
- **Modularity**: Files and phases are independent, enabling parallel development.
- **Dynamic File Selection**: Support multiple requirements and standards files with configurable retrieval via CLI or configuration.

## Folder Structure
The system is organized under `C:\ESG_System\` with a modular structure supporting single responsibility and multiple requirements/standards files.

```
C:\ESG_System\
├── input\                    # Input company PDFs
│   └── Company_Report.pdf
├── standards\                # ESG standards PDFs
│   ├── ESG_Framework_GRI.pdf
│   ├── ESG_Framework_IFRS.pdf
│   └── ESG_Framework_SASB.pdf
├── requirements\             # ESG requirements CSVs
│   ├── requirements_2023.csv
│   ├── requirements_2024.csv
│   └── requirements_custom.csv
├── models\                   # AI model files
│   └── mistral-7b-openorca.Q4_K_M.gguf
├── output\                   # Generated CSV and PDF reports
│   ├── audit_results.csv
│   └── audit_report.pdf
├── templates\                # LaTeX template for PDF report
│   └── esg_compliance_report_template.tex
├── logs\                     # Log files
│   └── esg_system.log
├── esg_system\              # Source code
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── main.py             # CLI entry point
│   ├── build_database.py   # ChromaDB initialization
│   ├── run_audit.py        # Audit orchestration
│   ├── pdf_extractors\     # PDF extraction modules
│   │   ├── __init__.py
│   │   ├── pdfplumber_extract.py
│   │   ├── pymupdf_extract.py
│   │   ├── unstructured_extract.py
│   │   ├── pytesseract_extract.py
│   │   └── text_organizer.py
│   ├── data_extraction\    # AI-based data extraction
│   │   ├── __init__.py
│   │   └── mistral_extract.py
│   ├── compliance_check\   # Compliance validation
│   │   ├── __init__.py
│   │   └── compliance_validator.py
│   ├── report_generator\   # CSV and PDF report generation
│   │   ├── __init__.py
│   │   ├── csv_generator.py
│   │   └── pdf_generator.py
│   └── utils\              # Shared utilities
│       ├── __init__.py
│       ├── config_loader.py
│       ├── logging.py
│       └── file_utils.py
├── requirements.txt         # Python dependencies
└── LICENSE                 # MIT License
```

### File Responsibilities
- **config.py**: Loads and validates configuration settings, including paths to `standards` and `requirements` directories and selected files.
- **main.py**: CLI entry point for user interaction, supporting selection of specific requirements and standards files.
- **build_database.py**: Initializes ChromaDB with selected standards and requirements files.
- **run_audit.py**: Orchestrates the audit workflow (extraction, validation, reporting).
- **pdfplumber_extract.py**: Extracts text and tables using `pdfplumber`.
- **pymupdf_extract.py**: Extracts text using `PyMuPDF` for high-speed processing.
- **unstructured_extract.py**: Extracts text from complex layouts using `Unstructured.io`.
- **pytesseract_extract.py**: Performs OCR on scanned PDFs using `pytesseract`.
- **text_organizer.py**: Segments extracted text into ESG categories (Environmental, Social, Governance).
- **mistral_extract.py**: Uses Mistral-7B to extract specific data points (values, units, pages).
- **compliance_validator.py**: Compares extracted data against standards for compliance.
- **csv_generator.py**: Generates the CSV report with summary and detailed rows.
- **pdf_generator.py**: Generates the PDF report using LaTeX and `jinja2`.
- **config_loader.py**: Loads configuration from `.env` or environment variables.
- **logging.py**: Manages logging to file and console for debugging and monitoring.
- **file_utils.py**: Handles file I/O and dynamic selection of requirements/standards files.

## Development Phases

### Phase 1: Setup and Configuration
**Objective**: Establish the foundation with configuration, logging, and file utilities, supporting multiple requirements and standards files.
**Duration**: 1 week
**Tasks**:
1. **Create Folder Structure**:
   - Set up `C:\ESG_System\` with subdirectories: `input`, `standards`, `requirements`, `models`, `output`, `templates`, `logs`, `esg_system`.
   - Initialize empty `__init__.py` files in each module (`pdf_extractors`, `data_extraction`, etc.).
2. **Implement Configuration Management**:
   - File: `esg_system/config.py`
     - Load paths for directories (`input`, `standards`, `requirements`, `models`, `output`) and model settings.
     - Support dynamic selection of specific standards (e.g., `ESG_Framework_GRI.pdf`) and requirements (e.g., `requirements_2023.csv`) files via CLI arguments or `.env` file.
     - Validate all paths at startup to ensure they exist and are accessible.
   - File: `esg_system/utils/config_loader.py`
     - Load configuration from `.env` file or environment variables.
     - Provide helper functions to access configuration values (e.g., get path to selected standards file).
3. **Implement Logging**:
   - File: `esg_system/utils/logging.py`
     - Configure logging to write to `C:\ESG_System\logs\esg_system.log` with timestamps and levels (INFO, ERROR).
     - Support console output for real-time monitoring.
     - Ensure all modules use this logging utility for consistency.
4. **Implement File Utilities**:
   - File: `esg_system/utils/file_utils.py`
     - Provide functions for path validation, file reading/writing, and listing files in `standards` and `requirements` directories (e.g., list all `.csv` files in `requirements`).
     - Support dynamic selection of specific requirements/standards files based on user input or configuration.
     - Handle file I/O errors with appropriate logging.
**Deliverables**:
- Functional `config.py`, `config_loader.py`, `logging.py`, `file_utils.py`.
- Complete folder structure with `requirements` directory and empty `__init__.py` files.
- `.env` file template with default paths for `standards_dir`, `requirements_dir`, etc.
**Dependencies**: `python-dotenv`, `logging`
**Notes**:
- Ensure `file_utils.py` supports listing and selecting multiple files in `standards` and `requirements` directories.
- Configuration should allow users to specify which standards/requirements files to use via CLI (e.g., `--standards ESG_Framework_GRI.pdf`).

### Phase 2: ESG Standards and Requirements Database Initialization
**Objective**: Initialize ChromaDB with selected standards and requirements files for compliance checks.
**Duration**: 1.5 weeks
**Tasks**:
1. **Implement Database Builder**:
   - File: `esg_system/build_database.py`
     - Load the user-selected standards PDF (e.g., `ESG_Framework_GRI.pdf`) from the `standards` directory.
     - Split the PDF into logical sections (e.g., by standard code or topic) for processing.
     - Tag each section with metadata (framework, standard code, topic, e.g., {"framework": "GRI", "code": "305-1", "topic": "emissions"}).
     - Embed sections using a sentence transformer model and store in ChromaDB for efficient retrieval.
     - Load and validate the user-selected requirements CSV (e.g., `requirements_2023.csv`) from the `requirements` directory, ensuring it contains 66 criteria.
     - Log setup progress and any errors (e.g., invalid CSV format, missing standards file).
2. **Ensure DRY**:
   - Use `file_utils.py` for file operations (e.g., reading standards PDF, listing available requirements files).
   - Use `logging.py` to log database initialization steps and errors.
   - Reuse `config_loader.py` to access paths to selected standards/requirements files.
**Deliverables**:
- Functional `build_database.py`.
- Initialized ChromaDB database in `C:\ESG_System\chromadb\`.
- Validated requirements CSV with 66 criteria.
- CLI support for selecting specific standards/requirements files (e.g., `--standards ESG_Framework_GRI.pdf --requirements requirements_2023.csv`).
**Dependencies**: `chromadb`, `pdfplumber`, `sentence-transformers`
**Notes**:
- Ensure the database supports querying by standard code or topic for fast retrieval in later phases.
- Validate that the requirements CSV has the expected columns (e.g., `criterion`, `description`, `standard`, `category`).

### Phase 3: PDF Extraction and Organization
**Objective**: Implement robust PDF text extraction and ESG category organization for company reports.
**Duration**: 2 weeks
**Tasks**:
1. **Implement PDF Extractors**:
   - File: `esg_system/pdf_extractors/pdfplumber_extract.py`
     - Extract text and tables from text-based PDFs using `pdfplumber`.
     - Output a list of dictionaries with page number, text, and table data.
     - Log extraction success or errors.
   - File: `esg_system/pdf_extractors/pymupdf_extract.py`
     - Extract text from PDFs using `PyMuPDF` for high-speed processing.
     - Output a list of dictionaries with page number and text.
     - Log extraction success or errors.
   - File: `esg_system/pdf_extractors/unstructured_extract.py`
     - Extract text from complex PDF layouts using `Unstructured.io`.
     - Output a list of dictionaries with page number and text.
     - Log extraction success or errors.
   - File: `esg_system/pdf_extractors/pytesseract_extract.py`
     - Perform OCR on scanned PDFs using `pytesseract`.
     - Convert PDF pages to images and extract text.
     - Output a list of dictionaries with page number and text.
     - Log extraction success or errors.
   - Implement a fallback mechanism: try `pdfplumber`, then `PyMuPDF`, then `Unstructured.io`, then `pytesseract` if previous methods fail.
2. **Implement Text Organizer**:
   - File: `esg_system/pdf_extractors/text_organizer.py`
     - Segment extracted text into ESG categories (Environmental, Social, Governance) based on keywords (e.g., "emissions" for Environmental, "diversity" for Social) and headings.
     - Output a dictionary mapping categories to lists of page data.
     - Log segmentation results and any ambiguities in category assignment.
3. **Ensure DRY**:
   - Use `file_utils.py` for file operations (e.g., reading input PDF from `input` directory).
   - Use `logging.py` for logging extraction and organization steps.
   - Reuse `config_loader.py` to access input directory path.
**Deliverables**:
- Functional `pdfplumber_extract.py`, `pymupdf_extract.py`, `unstructured_extract.py`, `pytesseract_extract.py`, `text_organizer.py`.
- Robust PDF extraction with fallback mechanism.
- Organized text output by ESG category.
**Dependencies**: `pdfplumber`, `pymupdf`, `unstructured`, `pytesseract`, `pdf2image`
**Notes**:
- Ensure extractors handle diverse PDF formats (text-based, scanned, complex layouts).
- Test fallback mechanism to confirm it switches tools appropriately on failure.

### Phase 4: Data Extraction and Compliance Validation
**Objective**: Extract specific data points and validate compliance using Mistral-7B.
**Duration**: 2 weeks
**Tasks**:
1. **Implement Data Extraction**:
   - File: `esg_system/data_extraction/mistral_extract.py`
     - Load Mistral-7B model (`C:\ESG_System\models\mistral-7b-openorca.Q4_K_M.gguf`) using `llama.cpp` with 4-bit quantization.
     - Process categorized text and selected requirements CSV (e.g., `requirements_2023.csv`).
     - Extract specific values (e.g., "9500"), units (e.g., "MT CO2e"), and page numbers for each of the 66 criteria.
     - Process 10 criteria at a time to optimize performance and meet the ~78-second CSV generation goal.
     - Log extraction results and errors (e.g., missing values, model failures).
2. **Implement Compliance Validation**:
   - File: `esg_system/compliance_check/compliance_validator.py`
     - Retrieve relevant standards from ChromaDB based on the criterion being evaluated.
     - Use Mistral-7B to compare extracted data against verbatim standard requirements (e.g., "Disclose annual Scope 1 emissions in metric tons CO2e").
     - Assign compliance status (Compliant, Non-Compliant) and provide a reason for each criterion.
     - Log validation results and errors.
3. **Ensure DRY**:
   - Reuse `config_loader.py` for model and database paths.
   - Use `file_utils.py` for reading requirements CSV.
   - Use `logging.py` for logging extraction and validation steps.
**Deliverables**:
- Functional `mistral_extract.py`, `compliance_validator.py`.
- Extracted data points (values, units, pages) for 66 criteria.
- Compliance results with status and reasons.
**Dependencies**: `llama-cpp-python`, `chromadb`
**Notes**:
- Ensure Mistral-7B processes data efficiently to stay within the 78-second CSV generation target.
- Validate that compliance checks use verbatim standards to ensure accuracy.

### Phase 5: Report Generation and Integration
**Objective**: Generate CSV and PDF reports, integrating all components into a cohesive workflow.
**Duration**: 1.5 weeks
**Tasks**:
1. **Implement CSV Generator**:
   - File: `esg_system/report_generator/csv_generator.py`
     - Compile summary statistics (e.g., total criteria: 66, compliant: 59, compliance rate: 89.4%, processing time: 78s).
     - Generate detailed rows for each criterion (e.g., criterion, value, unit, page, status, reason).
     - Save to `C:\ESG_System\output\audit_results.csv`.
     - Log generation success or errors.
2. **Implement PDF Generator**:
   - File: `esg_system/report_generator/pdf_generator.py`
     - Load LaTeX template (`C:\ESG_System\templates\esg_compliance_report_template.tex`, artifact ID: c7dd74e3-9eaf-43e2-ad85-ca739107e5a9).
     - Populate template with CSV data (summary metrics, 66 criteria, charts) using `jinja2`.
     - Compile to PDF using `latexmk`, saving to `C:\ESG_System\output\audit_report.pdf`.
     - Log compilation steps and errors.
     - Ensure ~12-second compilation time.
3. **Implement CLI Entry Point and Audit Orchestration**:
   - File: `esg_system/main.py`
     - Parse CLI arguments: `--report` (company PDF), `--standards` (standards PDF), `--requirements` (requirements CSV), `--output` (output directory).
     - Validate file paths and call the audit orchestration script.
     - Log user interactions and CLI errors.
   - File: `esg_system/run_audit.py`
     - Coordinate the full workflow: PDF extraction, text organization, data extraction, compliance validation, and report generation.
     - Ensure the workflow completes within ~90 seconds.
     - Log each step’s progress and errors.
4. **Ensure DRY**:
   - Use `file_utils.py` for file operations (e.g., reading CSV, writing outputs).
   - Use `logging.py` for all logging.
   - Reuse `config_loader.py` for paths to input, output, standards, and requirements.
**Deliverables**:
- Functional `csv_generator.py`, `pdf_generator.py`, `main.py`, `run_audit.py`.
- CSV report with summary and detailed rows.
- PDF report with 13 sections, charts (bar, pie, radar, scatter), and gradients.
- CLI interface supporting dynamic file selection.
**Dependencies**: `pandas`, `jinja2`, `latexmk`, `texlive-full`
**Notes**:
- The PDF report should match the HTML report’s aesthetics, with:
  - Cover page on page 1 (gradient, logo, metrics).
  - Hyperlinked table of contents.
  - Sections: Executive Summary, Company Profile, Compliance Performance, Detailed Analysis (Environmental, Social, Governance), Compliance Insights, Stakeholder Engagement, Benchmarking, Case Studies, Future Goals, Conclusion, Appendices.
  - Charts with legends and captions, using `pgfplots` (bar for emissions, pie for governance, radar for stakeholder satisfaction, scatter for materiality).
  - Gradient styling with `tikz` (emerald: RGB{5,150,105}, blue: RGB{8,145,178}).
- Ensure tables fit within margins using LaTeX’s `\resizebox`.

## Report Template Details
The PDF report uses the LaTeX template (`esg_compliance_report_template.tex`, artifact ID: c7dd74e3-9eaf-43e2-ad85-ca739107e5a9) with:
- **Structure** (17+ pages):
  - Cover Page (Page 1): Gradient background, company logo, title, audit date, metrics (e.g., 89.4% compliance, 59/66 criteria).
  - Table of Contents (Page 2): Hyperlinked sections in two-column layout.
  - Executive Summary (Page 3): Metrics table, achievements, bar chart (compliant vs. non-compliant).
  - Company Profile (Page 4): Mission, vision, stats in gradient boxes.
  - Compliance Performance (Page 5): Framework scores table, bar chart.
  - Detailed Analysis (Pages 6-9): Tables and charts for Environmental (30 criteria), Social (20 criteria), Governance (16 criteria).
  - Compliance Insights (Pages 10-11): Scatter plot for materiality, recommendations in gradient boxes.
  - Stakeholder Engagement (Page 12): Metrics, radar chart for satisfaction.
  - Benchmarking (Page 13): Bar chart comparing to industry averages.
  - Case Studies (Page 14): Examples in gradient boxes.
  - Future Goals (Page 15): 2025/2030 targets, roadmap bar chart.
  - Conclusion (Page 16): Summary in gradient box.
  - Appendices (Page 17+): Full criteria table, historical trends, glossary, references.
- **Styling**:
  - Uses `tikz` for emerald-to-blue gradients (RGB{5,150,105} to RGB{8,145,178}).
  - Colored tables with `colortbl` for readability.
  - 11pt `article` class for professional typography.
- **Charts**:
  - Bar (emissions, diversity, frameworks, roadmap).
  - Pie (governance compliance).
  - Radar (stakeholder satisfaction).
  - Scatter (materiality assessment).
  - All charts include legends and captions via `pgfplots`.
- **Integration**: Populated dynamically from `audit_results.csv` using `jinja2`.

## Development Timeline
- **Total Duration**: 8 weeks
- **Phase 1**: Week 1
- **Phase 2**: Weeks 2-3
- **Phase 3**: Weeks 4-5
- **Phase 4**: Weeks 6-7
- **Phase 5**: Weeks 7-8

## Testing Strategy
- **Unit Tests**: Test each file’s functions (e.g., PDF extraction, data extraction, compliance validation).
- **Integration Tests**: Verify end-to-end workflow (PDF → text → data → compliance → CSV/PDF).
- **Performance Tests**: Confirm ~90-second processing (78s CSV + 12s PDF).
- **Accuracy Tests**: Validate compliance results against known standards and report data.
- **File Selection Tests**: Ensure dynamic selection of standards/requirements files works via CLI and configuration.

## Developer Guidelines
- **File Structure**: Strictly follow the Python pattern with docstrings and inline comments for all technical steps (e.g., PDF splitting, model loading).
- **Single Responsibility**: Each file handles one task (e.g., `pdfplumber_extract.py` only extracts with `pdfplumber`).
- **DRY**: Use `file_utils.py`, `logging.py`, and `config_loader.py` for common tasks like file I/O, logging, and configuration.
- **Logging**: Log key steps (e.g., extraction start, validation complete) and errors using `logging.py`.
- **Error Handling**: Implement try-catch blocks with logged exceptions in all files.
- **Documentation**: Include detailed docstrings and inline comments for clarity, especially for complex logic (e.g., fallback extraction, compliance comparison).

## Integration and Finalization
- **Phase 5 Completion**: Integrate all modules via `run_audit.py` to execute the full workflow.
- **Validation**: Test with sample inputs:
  - Company PDF: `C:\ESG_System\input\Company_Report.pdf`.
  - Standards: `C:\ESG_System\standards\ESG_Framework_GRI.pdf`.
  - Requirements: `C:\ESG_System\requirements\requirements_2023.csv`.
- **Output Verification**:
  - CSV: Confirm `audit_results.csv` includes 66 criteria, summary stats (e.g., 89.4% compliance), and detailed rows.
  - PDF: Verify `audit_report.pdf` matches HTML report aesthetics with 13 sections, charts, and gradients.
- **Performance Check**: Ensure total processing time is ~90 seconds.

## Future Enhancements
- Develop a Windows GUI for PDF uploads and result visualization.
- Support batch processing for multiple reports.
- Add support for additional ESG frameworks (e.g., TCFD).
- Optimize LaTeX compilation with caching for faster PDF generation.
- Enhance charts (e.g., stacked bars for multi-year trends).

## Contact
For support or clarification, contact [support@esg.rag](mailto:support@esg.rag).
