# ESG Engine

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.2.0-orange.svg)
![spaCy](https://img.shields.io/badge/spaCy-3.7+-green.svg)
![sentence-transformers](https://img.shields.io/badge/sentence--transformers-2.2.2-blue.svg)
![FAISS](https://img.shields.io/badge/FAISS-cpu-lightgrey.svg)
![pandas](https://img.shields.io/badge/pandas-2.0+-yellow.svg)
![pdfplumber](https://img.shields.io/badge/pdfplumber-0.11+-purple.svg)
![psutil](https://img.shields.io/badge/psutil-5.9+-red.svg)
![watchdog](https://img.shields.io/badge/watchdog-4.0+-cyan.svg)
![pytest](https://img.shields.io/badge/pytest-7.4+-black.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![GitHub Issues](https://img.shields.io/github/issues/Levi-Chinecherem/esg_engine)
![GitHub Stars](https://img.shields.io/github/stars/Levi-Chinecherem/esg_engine)

The **ESG Engine** is an AI-powered system for processing, analyzing, and summarizing Environmental, Social, and Governance (ESG) documents. It leverages Retrieval-Augmented Generation (RAG) databases and a modular agent system to extract data from reports (e.g., `btg-pactual.pdf`), validate compliance against standards (e.g., IFRS S1, IFRS S2, ESRS), and generate human-readable summaries based on app-specific requirements (e.g., `UNCTAD_requirements.csv`). Results are saved to `data/output/results.json`. The system is designed for modularity, scalability, and resource efficiency, enforcing a 45% resource cap locally (e.g., <7.2GB RAM on a 16GB system).

Built with Python and open-source tools (LangChain, spaCy, sentence-transformers, FAISS, pandas, and more), the ESG Engine follows SOLID and DRY principles, ensuring maintainability and extensibility. This project is ideal for developers, researchers, and organizations working with ESG data.

**Advanced Version**: For an enhanced version with advanced LLMs, additional features, and a full-stack system with a frontend dashboard and backend, contact me at [semantic.space](https://semantic.space).

## Features

- **RAG Databases**: Three databases for standards, reports, and requirements, enabling sentence-level searches with metadata.
- **Agent System**: Coordinates workflows, extracts data, validates compliance, and generates summaries.
- **Command-Line Interface**: Run with a single command (e.g., `python main.py --report data/reports/btg-pactual.pdf --requirements data/requirements/UNCTAD_requirements.csv`).
- **Resource Efficiency**: Stays within 45% RAM/disk locally, scalable to 80% on servers.
- **Comprehensive Testing**: Unit and integration tests with ≥95% coverage.
- **Dynamic Updates**: Monitors and updates standards and requirements automatically.

## Installation

### Prerequisites
- **Python**: 3.8+ (3.9 recommended).
- **Hardware**: 16GB RAM, 100GB disk (7.2GB RAM, 45GB disk available).
- **OS**: Windows, macOS, or Linux.
- **Dependencies**: `pdfplumber`, `spacy`, `sentence-transformers`, `faiss-cpu`, `pandas`, `psutil`, `watchdog`, `langchain`, `langchain-community`, `pytest`, `pytest-cov`.

### Quick Setup
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Levi-Chinecherem/esg_engine.git
   cd esg_engine
   ```

2. **Set Up Virtual Environment**:
   ```bash
   python -m venv esg_engine_venv
   source esg_engine_venv/bin/activate  # Linux/macOS
   esg_engine_venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install pdfplumber spacy sentence-transformers faiss-cpu pandas psutil watchdog langchain langchain-community pytest pytest-cov
   python -m spacy download en_core_web_sm
   ```

   If issues arise (e.g., with `sentence-transformers` or `langchain`), try:
   ```bash
   pip install sentence-transformers==2.2.2 langchain==0.2.0 langchain-community==0.2.0 --no-cache-dir
   ```

4. **Place Data Files**:
   - Reports: `data/reports/btg-pactual.pdf`
   - Requirements: `data/requirements/UNCTAD_requirements.csv`, `data/requirements/UNEP_requirements.csv`
   - Standards: `data/standards/ifrs_s1.pdf`, `data/standards/ifrs_s2.pdf`, `data/standards/ESRS_2.pdf`

   **Note**: CSVs should have columns `category`, `criterion`, `description`. Update `rag/requirements_rag/parser.py` if different.

For detailed setup, see [run.md](run.md).

## Usage

Run the ESG Engine via the CLI in `main.py`. Example:
```bash
python main.py --report data/reports/btg-pactual.pdf --requirements data/requirements/UNCTAD_requirements.csv --standard data/standards/ifrs_s1.pdf
```

### Options
- `--report`: Path to the ESG report PDF (required).
- `--requirements`: Path to the requirements CSV (required).
- `--standard`: Specific standard to filter (optional, e.g., `ifrs_s1.pdf`).

### Output
- **Console**: Processing status and time (e.g., `Workflow completed successfully in 123.45 seconds`).
- **File**: Results in `data/output/results.json` with fields: `category`, `criterion`, `extracted_sentences`, `standard_info`, `summary`, `document_name`, `processing_time`.
- **Logs**: Details in `data/output/main.log` and other logs (e.g., `workflow.log`, `resource.log`).

### Example Output (`results.json`)
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

For detailed instructions, see [run.md](run.md).

## Project Structure

```
esg_engine/
├── config/                    # Configuration files
│   ├── settings.py
├── data/                      # Data storage
│   ├── standards/             # ESG standards (e.g., ifrs_s1.pdf)
│   ├── reports/               # ESG reports (e.g., btg-pactual.pdf)
│   ├── requirements/          # Requirement CSVs (e.g., UNCTAD_requirements.csv)
│   ├── output/                # Results and logs (e.g., results.json)
├── utils/                     # Utility modules
├── rag/                       # RAG databases
│   ├── standards_rag/         # Standards RAG
│   ├── reports_rag/           # Reports RAG
│   ├── requirements_rag/      # Requirements RAG
├── agents/                    # Agent system
│   ├── superbrain/            # Workflow coordination
│   ├── monitoring/            # Resource and file monitoring
│   ├── extraction/            # Data extraction
│   ├── evaluation/            # Compliance validation
│   ├── summarization/         # Summary generation
├── tests/                     # Unit and integration tests
├── main.py                    # Main CLI entry point
├── run.md                     # Detailed run guide
├── README.md                  # This file
```

## Testing

Run unit and integration tests to verify functionality:
```bash
pytest tests/ --cov=config utils rag.standards_rag rag.reports_rag rag.requirements_rag agents main --cov-report=html
```

### Test Files
- `test_settings.py`
- `test_pdf_processing.py`
- `test_text_processing.py`
- `test_vector_utils.py`
- `test_file_monitor.py`
- `test_resource_monitor.py`
- `test_standards_rag.py`
- `test_reports_rag.py`
- `test_requirements_rag.py`
- `test_agents.py`
- `test_main.py`

### Coverage
- Target: ≥95% coverage.
- Report: View in `htmlcov/index.html`.

See [run.md](run.md) for detailed testing instructions.

## Advanced Version

Interested in an advanced version of the ESG Engine? Features include:
- Integration with advanced LLMs for enhanced reasoning and summarization.
- Additional functionalities (e.g., batch processing, custom reporting).
- Full-stack system with a frontend dashboard and robust backend.

Contact me at [semantic.space](https://semantic.space) to discuss or request a custom implementation.

## Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature`.
3. Commit changes: `git commit -m "Add your feature"`.
4. Push to the branch: `git push origin feature/your-feature`.
5. Open a pull request.

Please include:
- Clear description of changes.
- Unit tests for new features.
- Adherence to the coding pattern (see `development.md`).

## Contact

- **GitHub**: [Levi-Chinecherem](https://github.com/Levi-Chinecherem)
- **Portfolio**: [semantic.space](https://semantic.space)
- **Issues**: Report bugs or feature requests on [GitHub Issues](https://github.com/Levi-Chinecherem/esg_engine/issues).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
