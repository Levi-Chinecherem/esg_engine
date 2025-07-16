# ESG Engine

The ESG Engine is a powerful AI-powered system designed to streamline the processing, analysis, and summarization of Environmental, Social, and Governance (ESG) documents. ESG refers to three critical areas—Environmental (impact on the planet), Social (treatment of people), and Governance (organizational management)—that are vital for businesses, governments, investors, and regulators. The ESG Engine automates the extraction of key information from complex ESG documents, evaluates it against official standards, and delivers clear, actionable summaries. It’s built to save time, reduce errors, and make ESG data accessible to everyone, from corporate sustainability teams to financial analysts.

This system is ideal for anyone navigating the growing world of ESG, whether you’re ensuring compliance with regulations, assessing investment risks, or reporting sustainability efforts. It’s like a super-smart librarian who can instantly find, verify, and summarize the information you need from a vast library of ESG documents.

## Purpose and Overview

The ESG landscape is complex, with lengthy reports, dense standards (like IFRS S1, IFRS S2, or ESRS frameworks), and specific requirements that vary by organization or regulator. Manually sifting through these documents is time-consuming and error-prone. The ESG Engine solves this by:

- **Extracting** specific data points (e.g., carbon emissions or diversity metrics) from reports using tailored questions or criteria.
- **Evaluating** whether the data meets official ESG standards, ensuring accuracy and completeness.
- **Summarizing** the findings in a clear, human-readable format, making it easy for anyone to understand.

Who benefits? Corporations preparing ESG reports, banks assessing investment risks, regulators enforcing compliance, consultants analyzing client data, non-profits exposing greenwashing, and researchers studying ESG trends. The ESG Engine transforms overwhelming documents into concise, reliable insights, enabling better decision-making and communication.

## Technology Stack

The ESG Engine is built with a robust set of open-source tools, chosen for their reliability, flexibility, and performance. These tools work together like the gears of a well-oiled machine:

- **Python**: The core language, widely used for its simplicity and power in handling data and AI tasks. It’s the foundation that ties everything together.
- **LangChain**: Manages the team of AI agents, coordinates retrieval-augmented generation (RAG) tasks, and handles summarization, like a conductor leading an orchestra.
- **sentence-transformers**: Converts sentences into numerical “fingerprints” (embeddings) for fast searching, like giving every sentence a unique ID.
- **FAISS (Facebook AI Similarity Search)**: Stores and searches these fingerprints quickly, like a high-speed library catalog.
- **pdfplumber**: Extracts text from PDFs while preserving page structure, like a scanner that organizes pages into readable text.
- **spaCy**: Breaks documents into sentences and words for analysis, like a librarian sorting a book into chapters and lines. (NLTK is a backup option for flexibility.)
- **pandas**: Organizes structured data like requirement lists, acting like a digital filing clerk for spreadsheets.
- **concurrent.futures**: Enables multiple tasks to run at once, like assigning several workers to a job for speed.
- **psutil**: Monitors memory and storage usage, ensuring the system doesn’t overwork your computer, like a safety manager.
- **watchdog**: Watches for new or updated files in folders, like a guard dog alerting you to changes.

These tools ensure the ESG Engine is fast, accurate, and capable of handling large volumes of ESG data efficiently.

## Project Folder Structure

The ESG Engine is organized into a clear, modular folder structure to make development, maintenance, and scaling straightforward. Each Python file has a specific role, adhering to SOLID principles (each file has one responsibility, is open for extension but closed for modification, etc.) and DRY principles (avoiding code duplication through reusable modules). Below is the folder structure, followed by a detailed explanation of each file’s purpose.

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
│   ├── standards_rag.py
│   ├── reports_rag.py
│   ├── requirements_rag.py
├── agents/
│   ├── superbrain.py
│   ├── monitoring.py
│   ├── extraction.py
│   ├── evaluation.py
│   ├── summarization.py
├── utils/
│   ├── pdf_processing.py
│   ├── text_processing.py
│   ├── vector_utils.py
│   ├── file_monitor.py
│   ├── resource_monitor.py
├── main.py
```

### File Descriptions

Each file is designed to be modular and reusable, with a single responsibility (SOLID’s Single Responsibility Principle) and shared utilities to avoid duplication (DRY). They’re built to be extended or swapped out if needed (Open-Closed Principle) and depend on abstractions for flexibility (Dependency Inversion).

- **config/settings.py**  
  - **Purpose**: Stores configuration settings, like folder paths, memory limits (45% for local machines, 80% for servers), and model parameters.  
  - **Why It’s Needed**: Centralizes all settings in one place, making it easy to tweak without changing other files (DRY). It’s reusable across all modules and supports extension for new settings (Open-Closed).

- **data/standards/**  
  - **Purpose**: Holds ESG standard PDFs (e.g., IFRS S1, IFRS S2, ESRS). Not a Python file, but a storage folder monitored for updates.  
  - **Why It’s Needed**: Keeps permanent standards organized for the Standards RAG database.

- **data/requirements/**  
  - **Purpose**: Stores requirement CSV files (e.g., unctad_requirements.csv) with columns for category, criterion, and description.  
  - **Why It’s Needed**: Organizes app-specific requirements for the Requirements RAG database.

- **data/reports/**  
  - **Purpose**: Temporary storage for ESG report PDFs being processed.  
  - **Why It’s Needed**: Provides a workspace for the Reports/Documents RAG database.

- **data/output/**  
  - **Purpose**: Stores result files (JSON format) with extracted data, summaries, and metadata.  
  - **Why It’s Needed**: Keeps outputs organized and accessible for users.

- **rag/standards_rag.py**  
  - **Purpose**: Manages the Standards RAG database, handling PDF text extraction, sentence tokenization, embedding generation, and FAISS indexing. Updates the index when new standards are added or existing ones change.  
  - **Why It’s Needed**: Encapsulates all standards-related logic in one place (Single Responsibility). Reusable for any standard document and extensible for new formats (Open-Closed).

- **rag/reports_rag.py**  
  - **Purpose**: Manages the Reports/Documents RAG database, processing one report at a time, creating temporary FAISS indexes, and clearing them after use.  
  - **Why It’s Needed**: Keeps report processing separate and temporary, ensuring efficient memory use (Single Responsibility). Reusable for any report type.

- **rag/requirements_rag.py**  
  - **Purpose**: Manages the Requirements RAG database, parsing CSV files, storing criteria and descriptions, and enabling app-specific access. Updates when new CSVs or changes are detected.  
  - **Why It’s Needed**: Isolates requirement handling (Single Responsibility) and supports multiple apps through parameterized access (Reusable).

- **agents/superbrain.py**  
  - **Purpose**: Coordinates all agents and orchestrates the workflow (load, extract, evaluate, summarize, save).  
  - **Why It’s Needed**: Acts as the central controller (Single Responsibility), reusable for any ESG processing task, and extensible for new workflows (Open-Closed).

- **agents/monitoring.py**  
  - **Purpose**: Monitors memory (RAM and disk) usage, ensuring it stays below 45% locally or 80% on servers. Watches standards and requirements folders for updates.  
  - **Why It’s Needed**: Handles resource and file monitoring (Single Responsibility), reusable across systems, and prevents crashes.

- **agents/extraction.py**  
  - **Purpose**: Manages data extraction, spinning up sub-agents to search for criteria concurrently, retrieving target sentences with context (before and after sentences).  
  - **Why It’s Needed**: Focuses on extraction logic (Single Responsibility), reusable for any search task, and supports parallel processing for speed.

- **agents/evaluation.py**  
  - **Purpose**: Validates extracted data against standards, retrying once if incomplete, and flagging issues if needed.  
  - **Why It’s Needed**: Ensures result quality (Single Responsibility), reusable for any validation task, and extensible for new validation rules.

- **agents/summarization.py**  
  - **Purpose**: Generates human-readable summaries from extracted data, standards, and requirements.  
  - **Why It’s Needed**: Handles summarization (Single Responsibility), reusable for any ESG summary, and adaptable for different styles.

- **utils/pdf_processing.py**  
  - **Purpose**: Handles PDF text extraction and page-by-page processing, used by standards_rag.py and reports_rag.py.  
  - **Why It’s Needed**: Centralizes PDF handling (DRY), reusable across RAG modules, and supports new document types (Open-Closed).

- **utils/text_processing.py**  
  - **Purpose**: Manages sentence tokenization and embedding generation, used by all RAG modules.  
  - **Why It’s Needed**: Avoids duplicating text processing logic (DRY), reusable for any text-based task.

- **utils/vector_utils.py**  
  - **Purpose**: Manages FAISS index creation, updates, and searches, used by RAG modules.  
  - **Why It’s Needed**: Centralizes vector operations (DRY), reusable for any vector-based search, and extensible for new index types.

- **utils/file_monitor.py**  
  - **Purpose**: Monitors folders for new or updated files, used by monitoring.py for standards and requirements.  
  - **Why It’s Needed**: Isolates file monitoring logic (DRY), reusable for any folder-watching task.

- **utils/resource_monitor.py**  
  - **Purpose**: Tracks memory and storage usage, used by monitoring.py to enforce limits.  
  - **Why It’s Needed**: Centralizes resource monitoring (DRY), reusable for any system needing resource checks.

- **main.py**  
  - **Purpose**: The entry point for running the ESG Engine, initializing agents and kicking off the workflow.  
  - **Why It’s Needed**: Provides a simple way to start the system (Single Responsibility), reusable for different configurations.

This structure ensures modularity, reusability, and maintainability, with each file focusing on one task and shared utilities reducing redundancy.

## RAG Databases

The ESG Engine uses three Retrieval-Augmented Generation (RAG) databases, each acting like a specialized filing cabinet for ESG data. They store information on disk (not RAM) for efficiency and use FAISS for fast, vector-based searches, mimicking the query speed of a large language model (LLM).

### Standards RAG Database (Permanent)

- **Purpose**: Stores ESG standards (e.g., IFRS S1, IFRS S2, ESRS framework) permanently for reference.  
- **How It Works**:  
  - Extracts text from PDFs page by page, splits it into sentences, and creates numerical “fingerprints” (embeddings).  
  - Stores these in a FAISS index with metadata (document name, page number, sentence index).  
  - Allows apps to query specific standards (e.g., “IFRS S1 only”) or all standards (“ALL”).  
  - Monitors the standards folder for new or updated PDFs every 30 minutes, refreshing the index.  
- **Key Features**: Tracks document names for selective queries, supports fast sentence-level searches, and keeps data up-to-date.  
- **Why It Matters**: Acts as the rulebook for checking compliance, always ready and current.

### Reports/Documents RAG Database (Temporary)

- **Purpose**: Processes one ESG report at a time, extracting data, then discarding it to save space.  
- **How It Works**:  
  - Loads a PDF, extracts text page by page, and splits it into sentences.  
  - Creates a temporary FAISS index with embeddings and metadata (page, sentence index).  
  - Multiple agents search concurrently for required data points.  
  - Clears the index after processing to prepare for the next document.  
- **Key Features**: Tracks page and sentence positions, supports concurrent searches for speed, and minimizes memory use.  
- **Why It Matters**: Provides a focused workspace for analyzing reports without cluttering the system.

### Requirements RAG Database (Permanent with App-Specific Access)

- **Purpose**: Stores requirement lists (CSV files with category, criterion, description) for different apps (e.g., UNCTAD, UNEP), permanently, with app-specific access.  
- **How It Works**:  
  - Parses CSVs into structured data, optionally creating embeddings for criteria and descriptions.  
  - Allows apps to specify which requirement set to use (e.g., “unctad_requirements.csv”).  
  - Uses the description as a fallback if a criterion search fails.  
  - Monitors the requirements folder for new CSVs or updates every 30 minutes.  
- **Key Features**: Supports multiple apps, tracks requirements by name, and updates dynamically.  
- **Why It Matters**: Provides a flexible, tailored guide for what to look for in reports.

## Agents

The ESG Engine employs a team of AI agents, each with a specific role, working together like a crew on a mission. They’re built with LangChain for coordination and follow SOLID principles for modularity.

### Superbrain Agent

- **Role**: The central coordinator, directing all other agents.  
- **Tasks**:  
  - Plans the workflow: load document, fetch requirements, extract data, evaluate results, summarize, and save.  
  - Listens to the Monitoring Agent to adjust operations based on resource limits.  
  - Ensures agents work in harmony, avoiding conflicts.  
- **Why It’s Needed**: Acts as the brain, keeping the system organized and efficient.

### Monitoring Agent

- **Role**: Oversees system resources and file updates.  
- **Tasks**:  
  - Tracks RAM and disk usage, capping at 45% locally or 80% on servers.  
  - Monitors standards and requirements folders for changes, triggering updates every 30 minutes.  
  - Advises the Superbrain on how many sub-agents to run or when to pause tasks.  
- **Why It’s Needed**: Prevents crashes and keeps data fresh, like a system health manager.

### Extraction Agents

- **Role**: Searches for data in reports based on requirements.  
- **Tasks**:  
  - Spins up sub-agents to search for each criterion concurrently, speeding up the process.  
  - Retrieves the target sentence, plus the sentence before and after for context (three sentences total).  
  - Records metadata like page number and sentence index.  
- **Why It’s Needed**: Quickly finds the exact data needed, like a team of researchers.

### Evaluation Agents

- **Role**: Validates extracted data for accuracy and completeness.  
- **Tasks**:  
  - Checks if extracted sentences fully answer the criterion, cross-referencing standards.  
  - Requests one retry if results are lacking, flagging issues if the retry fails.  
  - Uses knowledge of all RAG databases to ensure quality.  
- **Why It’s Needed**: Ensures results are trustworthy, acting as a quality control team.

### Summarization Agents

- **Role**: Creates clear, human-readable summaries.  
- **Tasks**:  
  - Combines extracted data, standard details, and requirement context into concise summaries.  
  - Ensures summaries are easy to understand for all users.  
- **Why It’s Needed**: Makes complex data accessible, like a writer simplifying a technical report.

## Workflow

The ESG Engine follows a clear, step-by-step process to analyze ESG documents, like a recipe for turning raw data into insights:

1. **Load Document**: The Superbrain loads a report into the temporary Reports/Documents RAG database, breaking it into sentences and indexing it.  
2. **Fetch Requirements**: The Superbrain selects the app-specific requirement list (e.g., UNCTAD’s criteria).  
3. **Extract Data**: Extraction Agents search concurrently for each criterion, pulling the target sentence and its context, with metadata.  
4. **Evaluate Results**: Evaluation Agents verify the data, retrying once if needed, and flag issues if unresolved.  
5. **Generate Summaries**: Summarization Agents create clear summaries based on extracted data, standards, and requirements.  
6. **Save Output**: Results are saved in a JSON file, including category, criterion, extracted sentences, standard info, summary, document name, and processing time (in seconds).  
7. **Clear Temporary Data**: The report’s index is deleted to free space for the next document.

This workflow ensures consistent, high-quality results with minimal resource waste.

## Result Structure

For each processed document, the ESG Engine produces a JSON file with:

- **category**: The ESG category from the requirements (e.g., Environmental).  
- **criterion**: The specific question or data point (e.g., “Carbon emissions”).  
- **extracted_sentences**: A list of dictionaries with the target sentence, its context (before and after), page number, and sentence index.  
- **standard_info**: Relevant text from standards (e.g., IFRS S1 rules on emissions).  
- **summary**: A concise, human-readable summary of the findings.  
- **document_name**: The report’s filename.  
- **processing_time**: How long the process took (in seconds).

This structure makes results easy to read, trace, and use for reporting or analysis.

## Use Cases

The ESG Engine is versatile, serving a wide range of users and needs. Here are its key applications:

- **Financial Institutions**: Banks and investors use it to assess ESG risks in companies, pulling data like emissions or labor practices from reports and checking compliance with standards.  
- **Regulators**: Government agencies verify if companies meet ESG rules, flagging non-compliance quickly.  
- **Corporate Sustainability Teams**: Companies prepare their own ESG reports, extracting and summarizing data to meet reporting requirements.  
- **Consulting Firms**: Analyze client ESG data in bulk, delivering insights for multiple industries.  
- **Non-Profits**: Expose greenwashing by comparing company claims to standards, highlighting discrepancies.  
- **Researchers**: Study ESG trends across sectors, extracting data for analysis.  
- **Small Businesses**: Understand ESG requirements to compete with larger firms, using simplified outputs.  
- **Auditors**: Conduct ESG audits, ensuring data accuracy and regulatory alignment.  
- **Educational Institutions**: Teach ESG concepts using real-world data extracted by the system.

These use cases show the ESG Engine’s flexibility, making it a valuable tool across industries.

## Competitors

The ESG Engine faces competition from other solutions, but it stands out in key ways. Here’s how it compares:

- **General AI Document Platforms (e.g., IBM Watson Discovery, Google Cloud NLP)**  
  - **What They Do**: Analyze all types of documents with AI.  
  - **Strengths**: Broad functionality, well-established, and versatile for many industries.  
  - **Weaknesses**: Not ESG-specific, so they lack tailored handling of standards and requirements.  
  - **ESG Engine Advantage**: Built for ESG, with specialized RAG databases and agents for precise analysis.

- **ESG Data Providers (e.g., Sustainalytics, MSCI ESG Research)**  
  - **What They Do**: Collect and rate ESG data from companies.  
  - **Strengths**: Deep ESG expertise and trusted ratings for investors.  
  - **Weaknesses**: Focus on data aggregation, not document processing or automation.  
  - **ESG Engine Advantage**: Automates document analysis, giving users hands-on control over data extraction.

- **Open-Source NLP Tools (e.g., Hugging Face Transformers, spaCy)**  
  - **What They Do**: Provide flexible text analysis tools for custom solutions.  
  - **Strengths**: Free, customizable, and supported by a large community.  
  - **Weaknesses**: Require significant setup and expertise for ESG tasks, not ready-to-use.  
  - **ESG Engine Advantage**: Pre-built for ESG, saving time and integrating all needed tools.

- **Manual ESG Consulting Services**  
  - **What They Do**: Human experts analyze ESG documents for clients.  
  - **Strengths**: Deep human insight and tailored advice.  
  - **Weaknesses**: Slow, expensive, and prone to human error.  
  - **ESG Engine Advantage**: Fast, automated, and scalable, with consistent results.

The ESG Engine’s focus on ESG-specific automation, modularity, and ease of use sets it apart, balancing the depth of specialized platforms with the flexibility of open-source tools.

## Technical Details

Here’s a deeper look at how the ESG Engine manages its resources and performance, explained for clarity:

### Resource Management

- **Local Machines**: Caps usage at 45% of available RAM and disk space (e.g., 7.2GB RAM and 45GB disk on a 16GB/100GB system) to prevent crashes.  
- **Servers**: Scales to 80% for maximum performance on dedicated hardware.  
- **Monitoring**: The Monitoring Agent uses real-time checks to adjust task concurrency, pausing sub-agents if limits are approached.  
- **Storage**: FAISS indexes are stored on disk, not RAM, for efficiency, queried like an LLM for fast access.

### Performance Optimizations

- **Concurrent Processing**: Extraction Agents run searches in parallel, reducing processing time.  
- **Fast Searches**: FAISS enables near-instant sentence-level searches, even in large datasets.  
- **Dynamic Updates**: Standards and Requirements RAG databases refresh every 30 minutes or on file changes, ensuring data is current.  
- **Metadata Tracking**: Page numbers and sentence indexes are stored with every result, enabling precise traceability.  
- **Error Handling**: Evaluation Agents retry failed searches once, flagging persistent issues to avoid endless loops.

### Edge Cases

- **Empty Documents**: If a report is blank or unreadable, the system flags it and moves to the next.  
- **Missing Criteria**: If a criterion isn’t found, it tries the description as a fallback, then flags if still unresolved.  
- **Corrupted Files**: The system detects and skips corrupted PDFs or CSVs, logging the issue.  
- **Large Files**: For oversized documents, it processes in chunks to stay within memory limits.  
- **Conflicting Standards**: If standards contradict, the system prioritizes the user-specified standard (e.g., IFRS S1 only).

These details ensure the ESG Engine is robust, efficient, and reliable in real-world scenarios.

## Non-Technical Explanation

Think of the ESG Engine as a super-smart library for ESG information, staffed by a team of expert librarians:

- **Storage Areas**:  
  - **Standards Section**: A permanent shelf of ESG rulebooks, like a reference section always ready to check.  
  - **Reports Section**: A temporary desk where one report is studied at a time, then cleared away.  
  - **Requirements Section**: A question desk with tailored lists of what to look for, unique to each user.

- **Librarian Team**:  
  - **Superbrain**: The head librarian, directing the team and keeping everything on track.  
  - **Monitoring Agent**: The maintenance manager, ensuring the library doesn’t run out of space or power.  
  - **Extraction Agents**: Researchers, flipping through pages to find exactly what’s needed.  
  - **Evaluation Agents**: Inspectors, checking that the findings are correct and complete.  
  - **Summarization Agents**: Writers, turning piles of notes into clear, short summaries.

Here’s how it works: A report arrives at the desk. The head librarian hands out questions to the researchers, who search the report and pull out key info with some context. The inspectors review it, asking for a redo if needed. The writers then craft summaries anyone can understand. The results are saved neatly, and the desk is cleared for the next report. It’s like a busy library turning chaos into clarity, making ESG easy for everyone.

## Future Enhancements

The ESG Engine is powerful but can grow even stronger. Potential improvements include:

- **Multi-Format Support**: Handle Word documents, web pages, or scanned PDFs alongside current PDFs.  
- **Advanced AI Models**: Use larger language models for smarter extraction and summarization.  
- **User Interface**: Add a dashboard for non-tech users to run the system with clicks, not code.  
- **Real-Time Processing**: Enable instant analysis for urgent tasks, like live audits.  
- **Multilingual Support**: Process documents in other languages for global use.  
- **Custom Outputs**: Let users design their own report formats (e.g., PDF, Excel).  
- **Integration APIs**: Allow other software to connect directly to the ESG Engine.  
- **Automated Alerts**: Notify users of new standards or critical findings automatically.

These enhancements would keep the ESG Engine cutting-edge, meeting evolving ESG needs.

This README is your ultimate guide to the ESG Engine, covering every detail—from its purpose and structure to its files, features, and future. It’s designed to be the one place you’ll always turn to for understanding this system, whether you’re technical or not.
