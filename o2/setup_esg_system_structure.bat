@echo off
REM Create folders
mkdir input
mkdir standards
mkdir requirements
mkdir models
mkdir output
mkdir templates
mkdir logs
mkdir esg_system
mkdir esg_system\pdf_extractors
mkdir esg_system\data_extraction
mkdir esg_system\compliance_check
mkdir esg_system\report_generator
mkdir esg_system\utils

REM Create empty placeholder files
type nul > input\Company_Report.pdf

type nul > standards\ESG_Framework_GRI.pdf
type nul > standards\ESG_Framework_IFRS.pdf
type nul > standards\ESG_Framework_SASB.pdf

type nul > requirements\requirements_2023.csv
type nul > requirements\requirements_2024.csv
type nul > requirements\requirements_custom.csv

type nul > models\mistral-7b-openorca.Q4_K_M.gguf

type nul > output\audit_results.csv
type nul > output\audit_report.pdf

type nul > templates\esg_compliance_report_template.tex

type nul > logs\esg_system.log

REM esg_system source files
type nul > esg_system\__init__.py
type nul > esg_system\config.py
type nul > esg_system\main.py
type nul > esg_system\build_database.py
type nul > esg_system\run_audit.py

REM PDF extractors
type nul > esg_system\pdf_extractors\__init__.py
type nul > esg_system\pdf_extractors\pdfplumber_extract.py
type nul > esg_system\pdf_extractors\pymupdf_extract.py
type nul > esg_system\pdf_extractors\unstructured_extract.py
type nul > esg_system\pdf_extractors\pytesseract_extract.py
type nul > esg_system\pdf_extractors\text_organizer.py

REM Data extraction
type nul > esg_system\data_extraction\__init__.py
type nul > esg_system\data_extraction\mistral_extract.py

REM Compliance check
type nul > esg_system\compliance_check\__init__.py
type nul > esg_system\compliance_check\compliance_validator.py

REM Report generation
type nul > esg_system\report_generator\__init__.py
type nul > esg_system\report_generator\csv_generator.py
type nul > esg_system\report_generator\pdf_generator.py

REM Utils
type nul > esg_system\utils\__init__.py
type nul > esg_system\utils\config_loader.py
type nul > esg_system\utils\logging.py
type nul > esg_system\utils\file_utils.py

REM Other top-level files
type nul > requirements.txt
type nul > LICENSE

echo ESG System structure created successfully.
