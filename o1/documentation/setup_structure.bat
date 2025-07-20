@echo off
REM Create directories
mkdir config
mkdir data\standards
mkdir data\requirements
mkdir data\reports
mkdir data\output
mkdir rag\standards_rag
mkdir rag\reports_rag
mkdir rag\requirements_rag
mkdir agents\superbrain
mkdir agents\monitoring
mkdir agents\extraction
mkdir agents\evaluation
mkdir agents\summarization
mkdir utils

REM Create empty files
type nul > config\settings.py

type nul > rag\standards_rag\indexer.py
type nul > rag\standards_rag\searcher.py
type nul > rag\standards_rag\updater.py

type nul > rag\reports_rag\indexer.py
type nul > rag\reports_rag\searcher.py
type nul > rag\reports_rag\cleaner.py

type nul > rag\requirements_rag\parser.py
type nul > rag\requirements_rag\searcher.py
type nul > rag\requirements_rag\updater.py

type nul > agents\superbrain\coordinator.py
type nul > agents\superbrain\workflow.py

type nul > agents\monitoring\resource_monitor.py
type nul > agents\monitoring\file_watcher.py

type nul > agents\extraction\searcher.py
type nul > agents\extraction\concurrent.py

type nul > agents\evaluation\validator.py
type nul > agents\evaluation\retry.py

type nul > agents\summarization\summarizer.py

type nul > utils\pdf_processing.py
type nul > utils\text_processing.py
type nul > utils\vector_utils.py
type nul > utils\file_monitor.py
type nul > utils\resource_monitor.py

type nul > main.py

echo Folder structure created successfully.
