# ESG Engine: User Story and Product Requirements Document (PRD)

This document outlines the user story and Product Requirements Document (PRD) for the ESG Engine, an AI-powered system designed to process, analyze, and summarize Environmental, Social, and Governance (ESG) documents. The user story details how different personas interact with the system to achieve their goals, while the PRD provides a clear blueprint for building the ESG Engine, including its purpose, features, requirements, and success criteria. Together, they ensure the system meets diverse user needs and is developed with precision and clarity.

## User Story

The ESG Engine is a transformative tool that simplifies the complex world of ESG data, helping users extract critical information from reports, verify compliance with standards, and generate clear summaries. Below, we introduce five personas representing key user types, detailing their backgrounds, goals, challenges, and how the ESG Engine empowers them to succeed. Each persona reflects a real-world stakeholder in the ESG ecosystem, ensuring the system addresses a wide range of needs.

### Persona 1: Sarah, the Corporate Sustainability Manager

- **Background**: Sarah is a 38-year-old sustainability manager at a mid-sized manufacturing company. She’s responsible for preparing annual ESG reports to meet regulatory and shareholder requirements. She has a background in environmental science but limited technical expertise in AI or data processing.
- **Goals**:  
  - Produce accurate, compliant ESG reports quickly to meet deadlines.  
  - Extract specific data points (e.g., carbon emissions, diversity metrics) from internal documents.  
  - Ensure reports align with standards like IFRS S1 and ESRS.  
  - Present clear, concise summaries to executives and stakeholders.
- **Challenges**:  
  - Manually sifting through hundreds of pages of internal reports is time-consuming.  
  - Understanding complex ESG standards and ensuring compliance is daunting.  
  - Summarizing data for non-technical executives is challenging without clear outputs.  
  - Limited budget and staff make automation critical.
- **How ESG Engine Helps**:  
  - Sarah uploads internal reports to the Reports/Documents RAG database, which processes them page by page, extracting key data points like emissions or labor practices.  
  - The system uses the Standards RAG database to verify compliance with IFRS S1 or ESRS, flagging any gaps.  
  - The Requirements RAG database applies her company’s specific criteria (e.g., “emissions reduction targets”) to focus the search.  
  - Summarization Agents generate executive-friendly summaries, saving Sarah hours of writing.  
  - Results include page numbers and sentence indexes, making it easy to verify data sources.  
  - The system’s low resource usage (45% of local machine capacity) ensures it runs smoothly on her office laptop.

### Persona 2: Raj, the Financial Analyst

- **Background**: Raj is a 29-year-old analyst at a large investment bank, tasked with assessing ESG risks for potential investments. He has a finance degree and is comfortable with data analysis but not with deep technical systems.
- **Goals**:  
  - Evaluate companies’ ESG performance to inform investment decisions.  
  - Identify risks like high emissions or poor governance in company reports.  
  - Compare company data against industry standards (e.g., IFRS S2).  
  - Deliver quick, reliable insights to his team.
- **Challenges**:  
  - Company ESG reports vary in format and quality, making comparisons difficult.  
  - Manually extracting risk-related data is slow and error-prone.  
  - Limited time to analyze multiple companies before investment deadlines.  
  - Needs clear, traceable data to justify recommendations.
- **How ESG Engine Helps**:  
  - Raj uploads company reports to the temporary Reports/Documents RAG database, which extracts data like emissions or board diversity concurrently for speed.  
  - The Standards RAG database checks data against IFRS S2, highlighting compliance or risks.  
  - The Requirements RAG database uses his bank’s risk criteria (e.g., “carbon intensity”) to focus searches.  
  - Evaluation Agents ensure extracted data is complete, retrying once if needed, reducing errors.  
  - Results include metadata (page, sentence index) for traceability, helping Raj justify his analysis.  
  - Summaries provide quick insights for his team, streamlining decision-making.

### Persona 3: Maria, the Regulatory Compliance Officer

- **Background**: Maria is a 45-year-old compliance officer at a government regulatory agency, ensuring companies meet ESG mandates. She has a legal background and prefers straightforward tools over complex tech.
- **Goals**:  
  - Verify that company ESG reports comply with regulations like ESRS.  
  - Identify non-compliance issues quickly across multiple reports.  
  - Provide clear evidence of findings to support enforcement actions.  
  - Maintain an up-to-date knowledge base of ESG standards.
- **Challenges**:  
  - Reviewing dozens of reports manually is overwhelming and slow.  
  - Standards evolve, requiring constant updates to her reference materials.  
  - Needs precise data (e.g., exact sentences) to build legal cases.  
  - Limited technical skills to handle advanced systems.
- **How ESG Engine Helps**:  
  - Maria uses the Standards RAG database, which auto-updates with new or revised standards (e.g., ESRS changes) every 30 minutes.  
  - She uploads company reports to the Reports/Documents RAG database, which processes them sentence by sentence.  
  - The Requirements RAG database applies her agency’s compliance criteria, pulling relevant data.  
  - Extraction Agents retrieve exact sentences with context (before and after), plus page numbers, for legal evidence.  
  - Evaluation Agents flag non-compliant data, retrying once to ensure accuracy.  
  - The system’s simple JSON output makes findings easy to review, even for non-technical users like Maria.

### Persona 4: Liam, the ESG Consultant

- **Background**: Liam is a 32-year-old consultant at a sustainability firm, helping clients across industries improve their ESG performance. He’s tech-savvy and works with diverse datasets but needs scalable tools.
- **Goals**:  
  - Analyze multiple client ESG reports quickly to provide tailored advice.  
  - Compare client performance against industry standards and competitors.  
  - Deliver clear, actionable reports to clients.  
  - Handle varying client requirements efficiently.
- **Challenges**:  
  - Clients provide reports in different formats, complicating analysis.  
  - Each client has unique ESG priorities, requiring flexible tools.  
  - Time constraints limit in-depth manual analysis.  
  - Needs to scale analysis for dozens of clients.
- **How ESG Engine Helps**:  
  - Liam uploads client reports to the Reports/Documents RAG database, which handles varying formats and processes them concurrently.  
  - The Requirements RAG database supports client-specific criteria (e.g., UNCTAD or UNEP standards), switching seamlessly between clients.  
  - Standards RAG database ensures comparisons against relevant standards (e.g., IFRS S1).  
  - Summarization Agents produce client-ready reports, saving Liam writing time.  
  - The system’s modular design (via reusable Python modules) and 45% resource cap ensure it scales on his local machine without crashes.

### Persona 5: Emma, the Non-Profit Researcher

- **Background**: Emma is a 27-year-old researcher at a non-profit focused on exposing corporate greenwashing. She has a social science background and limited resources but is passionate about transparency.
- **Goals**:  
  - Identify discrepancies between company ESG claims and actual performance.  
  - Use standards like IFRS S1 to validate or challenge claims.  
  - Produce reports for public advocacy with minimal resources.  
  - Track ESG trends across industries.
- **Challenges**:  
  - Limited budget restricts access to expensive tools or staff.  
  - Greenwashing is hard to detect without precise data extraction.  
  - Needs clear, credible evidence to support advocacy campaigns.  
  - Time-consuming to analyze multiple reports manually.
- **How ESG Engine Helps**:  
  - Emma uploads company reports to the Reports/Documents RAG database, which extracts claims like “net-zero emissions” with context.  
  - The Standards RAG database compares claims to IFRS S1 or other standards, flagging inconsistencies.  
  - The Requirements RAG database uses her non-profit’s criteria (e.g., “emissions transparency”) to focus searches.  
  - Evaluation Agents verify findings, ensuring credibility for advocacy.  
  - Summarization Agents create public-friendly reports, amplifying her impact.  
  - The system’s low resource use (45% locally) fits her non-profit’s limited hardware.

### Summary of User Story

These personas—Sarah, Raj, Maria, Liam, and Emma—represent the diverse stakeholders in the ESG ecosystem, from corporate managers to researchers. The ESG Engine empowers them by automating data extraction, ensuring compliance with standards, and delivering clear summaries, all while running efficiently on limited resources. It addresses their challenges—time constraints, complex standards, manual errors, and resource limitations—by providing a fast, accurate, and flexible solution tailored to their needs.

## Product Requirements Document (PRD)

### 1. Product Overview

**Product Name**: ESG Engine  
**Purpose**: The ESG Engine is an AI-powered system that automates the processing, analysis, and summarization of ESG documents, enabling users to extract key data points, verify compliance with standards, and generate actionable insights. It serves corporations, financial institutions, regulators, consultants, non-profits, and researchers by simplifying ESG data management.  
**Vision**: To be the go-to tool for ESG analysis, transforming complex documents into clear, compliant, and usable insights for diverse stakeholders.  
**Target Audience**: Corporate sustainability teams, financial analysts, regulatory officers, ESG consultants, non-profits, researchers, and small businesses.

### 2. Objectives

- **Efficiency**: Reduce ESG document processing time by 80% compared to manual methods.  
- **Accuracy**: Achieve 95% accuracy in data extraction and compliance verification.  
- **Accessibility**: Deliver outputs understandable by non-technical users.  
- **Scalability**: Handle single reports or batches without performance degradation.  
- **Resource Efficiency**: Use no more than 45% of local machine resources (RAM and disk) or 80% on servers.

### 3. Features and Functionality

#### 3.1 Core Features

- **Three RAG Databases**:  
  - **Standards RAG Database (Permanent)**: Stores ESG standards (e.g., IFRS S1, IFRS S2, ESRS) with sentence-level indexing, supporting selective or full queries, auto-updating every 30 minutes for new or revised standards.  
  - **Reports/Documents RAG Database (Temporary)**: Processes one report at a time, indexing sentences with page and position metadata, clearing after use.  
  - **Requirements RAG Database (Permanent)**: Stores app-specific CSV files (category, criterion, description), supporting dynamic updates and fallback searches using descriptions.  

- **Agent System**:  
  - **Superbrain Agent**: Coordinates workflow (load, extract, evaluate, summarize, save).  
  - **Monitoring Agent**: Caps resource usage (45% local, 80% server) and monitors folders for updates.  
  - **Extraction Agents**: Perform concurrent searches, retrieving target sentences with context (before and after).  
  - **Evaluation Agents**: Validate results, retrying once if incomplete, flagging unresolved issues.  
  - **Summarization Agents**: Generate human-readable summaries from extracted data, standards, and requirements.

- **Output Structure**: JSON files with category, criterion, extracted sentences (with page and sentence index), standard info, summary, document name, and processing time.

#### 3.2 Additional Features

- **Concurrent Processing**: Parallel searches by Extraction Agents for speed.  
- **Metadata Tracking**: Records page numbers and sentence indexes for traceability.  
- **Dynamic Updates**: Standards and Requirements databases refresh every 30 minutes or on file changes.  
- **Error Handling**: Manages empty documents, corrupted files, or missing criteria with fallbacks and logging.  
- **Resource Management**: Ensures system stability with real-time monitoring.

### 4. Functional Requirements

- **Data Input**:  
  - Accept PDF reports for Reports/Documents RAG.  
  - Accept PDF standards (e.g., IFRS S1) for Standards RAG.  
  - Accept CSV files (category, criterion, description) for Requirements RAG.  
- **Data Processing**:  
  - Extract text page by page using pdfplumber.  
  - Tokenize sentences with spaCy, generate embeddings with sentence-transformers, and index with FAISS.  
  - Support concurrent searches with concurrent.futures.  
- **Data Storage**:  
  - Store Standards and Requirements RAGs on disk, updating dynamically.  
  - Store Reports/Documents RAG temporarily, clearing after processing.  
- **Output**:  
  - Generate JSON files with structured results, including metadata and summaries.  
  - Ensure outputs are human-readable and traceable to source documents.

### 5. Non-Functional Requirements

- **Performance**: Process a 100-page report in under 5 minutes with concurrent agents.  
- **Scalability**: Handle 1 to 100 reports without crashing, scaling to server environments.  
- **Resource Usage**: Cap at 45% of available RAM and disk locally, 80% on servers, monitored by psutil.  
- **Reliability**: Achieve 99% uptime, handling edge cases like corrupted files or empty documents.  
- **Usability**: Outputs must be clear to non-technical users; system should run with minimal configuration.  
- **Maintainability**: Modular folder structure (as described in README) with SOLID and DRY principles for easy updates.

### 6. Technical Requirements

- **Technology Stack**: Python, LangChain, sentence-transformers, FAISS, pdfplumber, spaCy, pandas, concurrent.futures, psutil, watchdog.  
- **Folder Structure**:  
  - `config/settings.py`: Stores settings (paths, limits).  
  - `data/standards/`, `data/requirements/`, `data/reports/`, `data/output/`: Store input and output files.  
  - `rag/standards_rag.py`, `rag/reports_rag.py`, `rag/requirements_rag.py`: Manage RAG databases.  
  - `agents/superbrain.py`, `agents/monitoring.py`, `agents/extraction.py`, `agents/evaluation.py`, `agents/summarization.py`: Handle agent logic.  
  - `utils/pdf_processing.py`, `utils/text_processing.py`, `utils/vector_utils.py`, `utils/file_monitor.py`, `utils/resource_monitor.py`: Shared utilities.  
  - `main.py`: Entry point for running the system.  
- **Operating Environment**: Local machines (Windows, macOS, Linux) with Python 3.8+, scaling to cloud servers.  
- **Dependencies**: Installable via pip (e.g., `pip install pdfplumber spacy sentence-transformers faiss-cpu`).

### 7. User Interface

- **Current**: Command-line interface for running the system (via `main.py`) with file inputs and JSON outputs.  
- **Future**: Optional web or desktop dashboard for non-technical users to upload files, select requirements, and view results.

### 8. Constraints

- **Resource Limits**: 45% of local machine resources (RAM and disk) to prevent crashes; 80% on servers.  
- **File Formats**: Currently supports PDFs for reports/standards and CSVs for requirements.  
- **Language**: English-only documents (future enhancement for multilingual support).  
- **Hardware**: Runs on standard laptops (8GB RAM, 50GB disk minimum) or servers.

### 9. Success Criteria

- **User Adoption**: Used by at least three persona types (e.g., corporate, financial, regulatory) within six months.  
- **Performance**: Processes a 100-page report in under 5 minutes with 95% accuracy in extractions.  
- **Reliability**: Handles 99% of inputs without errors, including edge cases.  
- **User Satisfaction**: Non-technical users (e.g., Sarah, Maria) report outputs as “easy to understand” in feedback.  
- **Scalability**: Processes 100 reports in a batch without exceeding resource limits.

### 10. Risks and Mitigation

- **Risk**: System exceeds resource limits on low-end machines.  
  - **Mitigation**: Monitoring Agent enforces strict caps; optimize FAISS for disk-based storage.  
- **Risk**: Complex standards lead to missed data.  
  - **Mitigation**: Evaluation Agents retry searches and use requirement descriptions as fallbacks.  
- **Risk**: Users find command-line interface intimidating.  
  - **Mitigation**: Plan for a future GUI; ensure JSON outputs are simple and clear.  
- **Risk**: File corruption or format issues disrupt processing.  
  - **Mitigation**: Implement error handling to skip invalid files and log issues.

### 11. Future Enhancements

- **Multi-Format Support**: Add Word, web pages, and scanned PDFs.  
- **Multilingual Processing**: Support non-English documents for global use.  
- **GUI Dashboard**: Enable non-technical users to interact via clicks, not commands.  
- **Real-Time Analysis**: Process documents instantly for urgent tasks.  
- **API Integration**: Allow external systems to connect to the ESG Engine.  
- **Custom Outputs**: Support user-defined report formats (e.g., PDF, Excel).  
- **Advanced AI**: Use larger language models for smarter extraction and summarization.

### 12. Assumptions

- Users have basic Python setup knowledge for initial deployment.  
- Input PDFs and CSVs are well-formed (error handling covers exceptions).  
- Local machines have at least 8GB RAM and 50GB free disk space.  
- Standards and requirements evolve, but updates are provided as new files.

This PRD provides a clear roadmap for building the ESG Engine, ensuring it meets user needs, performs reliably, and scales effectively.