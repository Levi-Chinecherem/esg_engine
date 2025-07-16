# ESG Engine: System Architecture

The ESG Engine is an AI-powered system designed to process, analyze, and summarize Environmental, Social, and Governance (ESG) documents. It leverages three Retrieval-Augmented Generation (RAG) databases (Standards, Reports/Documents, Requirements) and a team of specialized agents (Superbrain, Monitoring, Extraction, Evaluation, Summarization) to extract data, verify compliance with standards, and generate human-readable summaries. This document outlines the system’s architecture, divided into High-Level Architecture, Agent Architecture, RAG Architecture, Memory Architecture, and Code Structure Architecture. Each section includes a detailed discussion and a DotGraph visualization to illustrate components and interactions.

The architecture is designed to be modular, scalable, and resource-efficient, adhering to SOLID (Single Responsibility, Open-Closed, Liskov Substitution, Interface Segregation, Dependency Inversion) and DRY (Don’t Repeat Yourself) principles. The system operates within a 45% resource cap (RAM and disk) on local machines and scales to 80% on servers, ensuring stability and performance.

## High-Level Architecture

### Discussion
The High-Level Architecture describes the ESG Engine’s overall structure, focusing on the interaction between major components: input handling, RAG databases, agent system, resource monitoring, and output generation. The system is designed to process ESG documents (PDFs for reports and standards, CSVs for requirements) and produce structured JSON outputs with extracted data, compliance details, and summaries.

- **Input Handling**: Accepts ESG reports (PDFs), standards (PDFs), and requirements (CSVs). Inputs are validated for format and integrity before processing.
- **RAG Databases**: Three databases manage data:
  - **Standards RAG**: Stores ESG standards (e.g., IFRS S1, IFRS S2, ESRS) permanently for compliance checks.
  - **Reports/Documents RAG**: Temporarily processes one report at a time for data extraction.
  - **Requirements RAG**: Stores app-specific criteria for guiding searches.
- **Agent System**: A team of agents coordinates tasks:
  - **Superbrain**: Orchestrates the workflow, delegating tasks to other agents.
  - **Monitoring**: Tracks resource usage and file updates.
  - **Extraction**: Searches for data in reports based on requirements.
  - **Evaluation**: Validates extracted data against standards.
  - **Summarization**: Generates human-readable summaries.
- **Resource Monitoring**: Ensures the system stays within 45% of local RAM/disk (e.g., 7.2GB RAM, 45GB disk on a 16GB/100GB system) or 80% on servers, using real-time checks.
- **Output Generation**: Produces JSON files with category, criterion, extracted sentences (with metadata), standard info, summary, document name, and processing time.
- **Data Flow**: Inputs flow into RAG databases, agents process data through extraction, evaluation, and summarization, and results are saved to output storage. Resource monitoring provides feedback to adjust processing dynamically.
- **Design Considerations**:
  - Modularity: Components are decoupled, allowing independent development and scaling.
  - Scalability: Concurrent processing and disk-based storage support large datasets.
  - Fault Tolerance: Handles edge cases like corrupted files or missing data with logging and fallbacks.
  - Extensibility: Supports new input formats (e.g., Word documents) and languages in the future.

### DotGraph Visualization
```
digraph high_level_architecture {
    rankdir=LR;
    node [shape=box, style=filled, fillcolor=lightblue];
    edge [color=navy];

    // Components
    Input [label="Input Handling\n(PDFs, CSVs)"];
    StandardsRAG [label="Standards RAG\n(Permanent)"];
    ReportsRAG [label="Reports/Documents RAG\n(Temporary)"];
    RequirementsRAG [label="Requirements RAG\n(Permanent)"];
    AgentSystem [label="Agent System\n(Superbrain, Monitoring,\nExtraction, Evaluation,\nSummarization)"];
    ResourceMonitor [label="Resource Monitoring\n(45% Local, 80% Server)"];
    Output [label="Output Generation\n(JSON)"];
    Storage [label="Disk Storage\n(Indexes, Outputs)"];

    // Data Flow
    Input -> StandardsRAG [label="Standards PDFs"];
    Input -> ReportsRAG [label="Report PDFs"];
    Input -> RequirementsRAG [label="Requirements CSVs"];
    StandardsRAG -> AgentSystem [label="Compliance Data"];
    ReportsRAG -> AgentSystem [label="Report Data"];
    RequirementsRAG -> AgentSystem [label="Criteria"];
    AgentSystem -> Output [label="Results"];
    ResourceMonitor -> AgentSystem [label="Resource Feedback"];
    StandardsRAG -> Storage [label="Store Indexes"];
    ReportsRAG -> Storage [label="Temporary Indexes"];
    RequirementsRAG -> Storage [label="Store Criteria"];
    Output -> Storage [label="Save JSON"];

    // Layout
    {rank=same; Input}
    {rank=same; StandardsRAG; ReportsRAG; RequirementsRAG}
    {rank=same; AgentSystem; ResourceMonitor}
    {rank=same; Output; Storage}
}
```

## Agent Architecture

### Discussion
The Agent Architecture defines the structure and interactions of the five agents: Superbrain, Monitoring, Extraction, Evaluation, and Summarization. Each agent has a single responsibility (SOLID principle), ensuring modularity and ease of maintenance. Agents use LangChain for coordination and operate concurrently where possible to optimize performance.

- **Superbrain Agent**:
  - **Role**: Orchestrates the entire workflow, acting as the central coordinator.
  - **Functionality**: Initializes agents, loads inputs, delegates tasks (extraction, evaluation, summarization), and saves results. It ensures sequential task execution while managing resource constraints.
  - **Interactions**: Receives resource feedback from Monitoring, sends criteria to Extraction, passes extracted data to Evaluation, and forwards validated data to Summarization.
- **Monitoring Agent**:
  - **Role**: Oversees system resources and file updates.
  - **Functionality**: Monitors RAM/disk usage (via psutil) to enforce 45% local/80% server limits and watches input folders for changes (via watchdog). It advises Superbrain on concurrency limits and triggers RAG updates.
  - **Interactions**: Sends resource status and file update signals to Superbrain and RAG databases.
- **Extraction Agent**:
  - **Role**: Retrieves data from reports based on requirements.
  - **Functionality**: Spawns sub-agents to search Reports RAG concurrently (using concurrent.futures), retrieving target sentences with context (before and after) and metadata (page, sentence index).
  - **Interactions**: Queries Reports RAG and Requirements RAG, sends results to Evaluation.
- **Evaluation Agent**:
  - **Role**: Validates extracted data for accuracy and compliance.
  - **Functionality**: Checks if extracted sentences fully address criteria, cross-references Standards RAG, retries once if incomplete, and flags unresolved issues. Uses LangChain for reasoning.
  - **Interactions**: Receives data from Extraction, queries Standards RAG, sends validated data to Summarization.
- **Summarization Agent**:
  - **Role**: Generates human-readable summaries.
  - **Functionality**: Combines extracted data, standards, and requirements into concise summaries using LangChain’s summarization capabilities.
  - **Interactions**: Receives validated data from Evaluation, outputs summaries to Superbrain.
- **Design Considerations**:
  - Concurrency: Extraction uses parallel sub-agents for speed.
  - Fault Tolerance: Evaluation retries failed searches; Monitoring prevents resource overload.
  - Extensibility: Agents can be extended for new tasks (e.g., new validation rules).
  - Modularity: Each agent operates independently, communicating via well-defined interfaces.

### DotGraph Visualization
```
digraph agent_architecture {
    rankdir=TB;
    node [shape=box, style=filled, fillcolor=lightgreen];
    edge [color=purple];

    // Agents
    Superbrain [label="Superbrain Agent\n(Coordinates Workflow)"];
    Monitoring [label="Monitoring Agent\n(Resource & File Monitoring)"];
    Extraction [label="Extraction Agent\n(Concurrent Data Retrieval)"];
    Evaluation [label="Evaluation Agent\n(Validation & Compliance)"];
    Summarization [label="Summarization Agent\n(Summary Generation)"];
    ReportsRAG [label="Reports RAG"];
    RequirementsRAG [label="Requirements RAG"];
    StandardsRAG [label="Standards RAG"];
    Output [label="Output\n(JSON)"];

    // Interactions
    Superbrain -> Monitoring [label="Resource Feedback"];
    Superbrain -> Extraction [label="Criteria"];
    Superbrain -> Evaluation [label="Extracted Data"];
    Superbrain -> Summarization [label="Validated Data"];
    Superbrain -> Output [label="Save Results"];
    Monitoring -> Superbrain [label="Concurrency Limits"];
    Monitoring -> StandardsRAG [label="Update Trigger"];
    Monitoring -> RequirementsRAG [label="Update Trigger"];
    Extraction -> ReportsRAG [label="Search Queries"];
    Extraction -> RequirementsRAG [label="Criteria"];
    Extraction -> Evaluation [label="Extracted Data"];
    Evaluation -> StandardsRAG [label="Compliance Check"];
    Evaluation -> Summarization [label="Validated Data"];
    Summarization -> Superbrain [label="Summaries"];

    // Layout
    {rank=same; Superbrain}
    {rank=same; Monitoring; Extraction; Evaluation; Summarization}
    {rank=same; ReportsRAG; RequirementsRAG; StandardsRAG}
    {rank=same; Output}
}
```

## RAG Architecture

### Discussion
The RAG Architecture outlines the structure of the three RAG databases: Standards, Reports/Documents, and Requirements. Each database is designed to handle specific data types, enabling fast, sentence-level searches using FAISS for vector storage and retrieval, mimicking the query speed of a large language model (LLM).

- **Standards RAG**:
  - **Role**: Permanently stores ESG standards (e.g., IFRS S1, IFRS S2, ESRS) for compliance checks.
  - **Functionality**: Processes PDF standards into sentences, generates embeddings (via sentence-transformers), and stores them in a FAISS index on disk. Supports selective queries (e.g., “IFRS S1 only”) and dynamic updates every 30 minutes or on file changes.
  - **Components**:
    - **Text Extractor**: Extracts text from PDFs page by page.
    - **Tokenizer**: Splits text into sentences.
    - **Embedder**: Converts sentences to embeddings.
    - **Indexer**: Stores embeddings and metadata (document name, page, sentence index) in FAISS.
    - **Searcher**: Queries embeddings, returning top-k matches.
    - **Updater**: Monitors for new/updated PDFs and refreshes the index.
- **Reports/Documents RAG**:
  - **Role**: Temporarily processes one ESG report for data extraction.
  - **Functionality**: Loads a PDF, tokenizes sentences, generates embeddings, and creates a temporary FAISS index. Supports concurrent searches for multiple criteria, retrieving target sentences with context (before and after). Cleans up after processing.
  - **Components**: Text Extractor, Tokenizer, Embedder, Indexer, Searcher, Cleaner (removes temporary index).
- **Requirements RAG**:
  - **Role**: Stores app-specific criteria (from CSVs) for guiding searches.
  - **Functionality**: Parses CSVs (category, criterion, description), optionally embeds criteria/descriptions, and supports app-specific queries (e.g., “UNCTAD criteria”). Uses descriptions as a fallback for failed searches. Updates dynamically for new CSVs.
  - **Components**: Parser (reads CSVs), Embedder (optional), Indexer (optional), Searcher, Updater.
- **Data Flow**: Inputs (PDFs, CSVs) are processed into embeddings, stored in FAISS, and queried by agents. Results include metadata for traceability. Updates are triggered by file changes or periodic checks.
- **Design Considerations**:
  - Efficiency: Disk-based FAISS indexes minimize RAM usage.
  - Scalability: Concurrent searches and chunked processing handle large datasets.
  - Fault Tolerance: Handles corrupted files and empty inputs with logging.
  - Extensibility: Supports new input formats (e.g., Word) and multilingual processing.

### DotGraph Visualization
```
digraph rag_architecture {
    rankdir=LR;
    node [shape=box, style=filled, fillcolor=lightyellow];
    edge [color=teal];

    // Components
    Input [label="Input\n(PDFs, CSVs)"];
    StandardsRAG [label="Standards RAG\n(Permanent)"];
    ReportsRAG [label="Reports RAG\n(Temporary)"];
    RequirementsRAG [label="Requirements RAG\n(Permanent)"];
    TextExtractor [label="Text Extractor"];
    Tokenizer [label="Tokenizer"];
    Embedder [label="Embedder"];
    Indexer [label="Indexer"];
    Searcher [label="Searcher"];
    Updater [label="Updater"];
    Cleaner [label="Cleaner"];
    Storage [label="Disk Storage\n(FAISS Indexes)"];
    AgentSystem [label="Agent System"];

    // Data Flow
    Input -> TextExtractor [label="PDFs, CSVs"];
    TextExtractor -> StandardsRAG [label="Standard Text"];
    TextExtractor -> ReportsRAG [label="Report Text"];
    TextExtractor -> RequirementsRAG [label="CSV Data"];
    StandardsRAG -> Tokenizer [label="Text"];
    ReportsRAG -> Tokenizer [label="Text"];
    RequirementsRAG -> Tokenizer [label="Criteria (Optional)"];
    Tokenizer -> Embedder [label="Sentences"];
    Embedder -> Indexer [label="Embeddings"];
    Indexer -> Storage [label="Store Indexes"];
    Searcher -> Storage [label="Query Indexes"];
    Searcher -> AgentSystem [label="Results"];
    Updater -> StandardsRAG [label="Update Trigger"];
    Updater -> RequirementsRAG [label="Update Trigger"];
    Cleaner -> ReportsRAG [label="Clear Index"];
    Cleaner -> Storage [label="Remove Temporary"];

    // Layout
    {rank=same; Input}
    {rank=same; TextExtractor}
    {rank=same; StandardsRAG; ReportsRAG; RequirementsRAG}
    {rank=same; Tokenizer; Embedder; Indexer; Searcher; Updater; Cleaner}
    {rank=same; Storage; AgentSystem}
}
```

## Memory Architecture

### Discussion
The Memory Architecture defines how the ESG Engine manages memory (RAM and disk) to stay within resource limits (45% locally, 80% on servers). It ensures efficient storage and retrieval of data, prioritizing disk-based operations to minimize RAM usage.

- **Disk Storage**:
  - **FAISS Indexes**: Standards and Requirements RAG databases store embeddings on disk (e.g., `data/standards/index.faiss`). Reports RAG uses temporary disk-based indexes, cleared after processing.
  - **Output Files**: JSON results and logs (e.g., errors, updates) are stored in `data/output/`.
  - **Input Files**: Standards (PDFs), reports (PDFs), and requirements (CSVs) are stored in `data/standards/`, `data/reports/`, and `data/requirements/`.
- **Resource Monitoring**:
  - **RAM Monitoring**: Tracks RAM usage (via psutil), ensuring it stays below 45% of available RAM (e.g., 7.2GB on a 16GB system).
  - **Disk Monitoring**: Tracks disk usage, capping at 45% of free space (e.g., 45GB on a 100GB system).
  - **Dynamic Adjustment**: The Monitoring Agent reduces concurrent sub-agents or pauses tasks if limits are approached.
- **Memory Management**:
  - **Disk-Based FAISS**: Indexes are stored on disk, not RAM, queried like an LLM for efficiency.
  - **Temporary Indexes**: Reports RAG indexes are deleted after processing to free space.
  - **Chunked Processing**: Large PDFs are processed in chunks to avoid memory spikes.
- **Logging**: Errors, updates, and resource usage are logged to disk (e.g., `data/output/errors.log`) to track system health without consuming RAM.
- **Design Considerations**:
  - Efficiency: Disk-based storage minimizes RAM usage.
  - Scalability: Supports large datasets by leveraging disk storage.
  - Fault Tolerance: Handles resource limits with dynamic adjustments.
  - Extensibility: Can scale to cloud storage or larger servers.

### DotGraph Visualization
```
digraph memory_architecture {
    rankdir=TB;
    node [shape=box, style=filled, fillcolor=lightpink];
    edge [color=maroon];

    // Components
    StandardsRAG [label="Standards RAG\n(Disk Index)"];
    ReportsRAG [label="Reports RAG\n(Temporary Disk Index)"];
    RequirementsRAG [label="Requirements RAG\n(Disk Storage)"];
    DiskStorage [label="Disk Storage\n(FAISS Indexes, Outputs)"];
    ResourceMonitor [label="Resource Monitor\n(RAM & Disk)"];
    AgentSystem [label="Agent System"];
    InputFiles [label="Input Files\n(PDFs, CSVs)"];
    OutputFiles [label="Output Files\n(JSON, Logs)"];

    // Data Flow
    InputFiles -> StandardsRAG [label="Standards PDFs"];
    InputFiles -> ReportsRAG [label="Report PDFs"];
    InputFiles -> RequirementsRAG [label="Requirements CSVs"];
    StandardsRAG -> DiskStorage [label="Store Index"];
    ReportsRAG -> DiskStorage [label="Store Temporary Index"];
    RequirementsRAG -> DiskStorage [label="Store Criteria"];
    AgentSystem -> StandardsRAG [label="Query"];
    AgentSystem -> ReportsRAG [label="Query"];
    AgentSystem -> RequirementsRAG [label="Query"];
    AgentSystem -> OutputFiles [label="Save Results"];
    ResourceMonitor -> AgentSystem [label="Resource Limits"];
    OutputFiles -> DiskStorage [label="Store JSON/Logs"];

    // Layout
    {rank=same; InputFiles}
    {rank=same; StandardsRAG; ReportsRAG; RequirementsRAG}
    {rank=same; AgentSystem; ResourceMonitor}
    {rank=same; DiskStorage; OutputFiles}
}
```

## Code Structure Architecture

### Discussion
The Code Structure Architecture describes the organization of the ESG Engine’s codebase, ensuring modularity, maintainability, and adherence to SOLID and DRY principles. Unlike the other architectures, this focuses on the logical grouping of code modules, not their runtime interactions or file structure. It defines how code is organized into functional units, each with a single responsibility, to support development and maintenance.

- **Configuration Module**:
  - **Role**: Centralizes system settings (e.g., paths, resource limits, model parameters).
  - **Functionality**: Provides a single source of truth for configuration, accessible to all components.
- **Utility Modules**:
  - **PDF Processing**: Handles PDF text extraction page by page.
  - **Text Processing**: Tokenizes text into sentences and generates embeddings.
  - **Vector Operations**: Manages FAISS index creation, updates, and searches.
  - **File Monitoring**: Detects file changes in input folders.
  - **Resource Monitoring**: Tracks RAM and disk usage.
- **RAG Modules**:
  - **Standards RAG**:
    - **Indexer**: Processes and indexes standard PDFs.
    - **Searcher**: Queries standards for compliance data.
    - **Updater**: Refreshes the index on file changes.
  - **Reports RAG**:
    - **Indexer**: Processes and indexes a single report.
    - **Searcher**: Queries reports for data extraction.
    - **Cleaner**: Removes temporary indexes.
  - **Requirements RAG**:
    - **Parser**: Reads and validates CSV requirements.
    - **Searcher**: Retrieves app-specific criteria.
    - **Updater**: Refreshes criteria on file changes.
- **Agent Modules**:
  - **Superbrain**:
    - **Coordinator**: Initializes agents and databases.
    - **Workflow**: Manages task sequencing and output.
  - **Monitoring**:
    - **Resource Monitor**: Enforces resource limits.
    - **File Watcher**: Triggers updates for RAG databases.
  - **Extraction**:
    - **Searcher**: Queries reports for criteria.
    - **Concurrent**: Manages parallel searches.
  - **Evaluation**:
    - **Validator**: Checks data against standards.
    - **Retry**: Handles failed extractions.
  - **Summarization**:
    - **Summarizer**: Generates human-readable summaries.
- **Main Module**:
  - **Role**: Provides the entry point for running the system.
  - **Functionality**: Accepts user inputs, initializes components, and executes the workflow.
- **Design Considerations**:
  - Modularity: Each module has a single responsibility, reducing complexity.
  - Reusability: Utility modules are shared across RAG and agent modules.
  - Maintainability: Small, focused modules simplify debugging and updates.
  - Extensibility: Modules can be extended for new formats or tasks.

### DotGraph Visualization
```
digraph code_structure_architecture {
    rankdir=TB;
    node [shape=box, style=filled, fillcolor=lightcoral];
    edge [color=darkgreen];

    // Modules
    Config [label="Configuration\n(Settings)"];
    Utilities [label="Utilities\n(PDF, Text, Vector,\nFile, Resource)"];
    StandardsRAG [label="Standards RAG\n(Indexer, Searcher, Updater)"];
    ReportsRAG [label="Reports RAG\n(Indexer, Searcher, Cleaner)"];
    RequirementsRAG [label="Requirements RAG\n(Parser, Searcher, Updater)"];
    Superbrain [label="Superbrain\n(Coordinator, Workflow)"];
    Monitoring [label="Monitoring\n(Resource, File)"];
    Extraction [label="Extraction\n(Searcher, Concurrent)"];
    Evaluation [label="Evaluation\n(Validator, Retry)"];
    Summarization [label="Summarization\n(Summarizer)"];
    Main [label="Main\n(Entry Point)"];

    // Dependencies
    Main -> Config [label="Load Settings"];
    Main -> Superbrain [label="Initialize"];
    Superbrain -> StandardsRAG [label="Query"];
    Superbrain -> ReportsRAG [label="Query"];
    Superbrain -> RequirementsRAG [label="Query"];
    Superbrain -> Monitoring [label="Resource Feedback"];
    Superbrain -> Extraction [label="Delegate"];
    Superbrain -> Evaluation [label="Delegate"];
    Superbrain -> Summarization [label="Delegate"];
    StandardsRAG -> Utilities [label="Use PDF, Text, Vector"];
    ReportsRAG -> Utilities [label="Use PDF, Text, Vector"];
    RequirementsRAG -> Utilities [label="Use Text, Vector, File"];
    Monitoring -> Utilities [label="Use File, Resource"];
    Extraction -> ReportsRAG [label="Search"];
    Extraction -> RequirementsRAG [label="Criteria"];
    Evaluation -> StandardsRAG [label="Validate"];
    Summarization -> Evaluation [label="Validated Data"];

    // Layout
    {rank=same; Config; Utilities}
    {rank=same; StandardsRAG; ReportsRAG; RequirementsRAG}
    {rank=same; Superbrain; Monitoring; Extraction; Evaluation; Summarization}
    {rank=same; Main}
}
```

## Technical Details

- **Performance**: Processes a 100-page report with 10 criteria in under 5 minutes, with searches completing in under 0.5 seconds.
- **Resource Usage**: Caps at 45% of local RAM/disk (e.g., 7.2GB RAM, 45GB disk on a 16GB/100GB system), scaling to 80% on servers.
- **Scalability**: Concurrent searches and disk-based storage handle large datasets.
- **Fault Tolerance**: Handles corrupted files, empty inputs, and missing data with logging and fallbacks.
- **Extensibility**: Supports new input formats, languages, and agent tasks through modular design.
- **Technologies**:
  - Python 3.8+
  - pdfplumber (PDF extraction)
  - spaCy (tokenization)
  - sentence-transformers (embeddings)
  - FAISS (vector storage)
  - pandas (CSV parsing)
  - concurrent.futures (concurrency)
  - psutil (resource monitoring)
  - watchdog (file monitoring)
  - LangChain (agent coordination, summarization)

This architecture document provides a comprehensive view of the ESG Engine’s design, ensuring clarity for developers and stakeholders. The DotGraph visualizations illustrate component interactions, while the discussions detail functionality, data flows, and design considerations.
