# Setup Guide for Non-Python Dependencies in ESG Compliance Verification System

## Overview

This guide provides instructions for setting up non-Python dependencies required for the ESG Compliance Verification System, as outlined in the development plan (`development.md`, artifact ID: cf4d05dd-239a-4764-aada-e794e1238b1e). These dependencies include the Mistral-7B model, LaTeX (`texlive-full`, `latexmk`) for PDF report generation, Tesseract for OCR processing, and Poppler for PDF-to-image conversion. The guide ensures flexibility to work from any project directory on a Windows system (e.g., `C:\Developments\Solutions\ESG Engine\o2`) using relative paths and environment variables. It includes a Python script to download the Mistral-7B model and details on quantization options, recommending `mistral-7b-instruct-v0.1.Q4_K_M.gguf` for balanced quality and performance.

The guide assumes a Python virtual environment handles Python packages (e.g., `pdfplumber`, `pymupdf`, `unstructured`, `pytesseract`, `pdf2image`, `llama-cpp-python`, `chromadb`, `sentence-transformers`, `pandas`, `jinja2`). It supports the system’s ~90-second processing goal (78s CSV + 12s PDF), aligns with the folder structure, and integrates with the LaTeX template (`esg_compliance_report_template.tex`, artifact ID: c7dd74e3-9eaf-43e2-ad85-ca739107e5a9). It includes official download links, verification steps, and troubleshooting for seamless setup.

## Prerequisites

Before setting up non-Python dependencies, ensure:
1. **Windows Environment**: Windows 10 or 11, 64-bit, with administrative privileges.
2. **Project Directory**: A project root (e.g., `C:\Developments\Solutions\ESG Engine\o2`) with the folder structure from `development.md`:
   ```
   <project_root>\
   ├── input\
   ├── standards\
   ├── requirements\
   ├── models\
   ├── output\
   ├── templates\
   ├── logs\
   ├── esg_system\
   └── requirements.txt
   ```
3. **Python Virtual Environment**:
   - Set up in `<project_root>\venv` with Python 3.10 or later:
     ```bash
     python -m venv <project_root>\venv
     <project_root>\venv\Scripts\activate
     ```
   - Install Python dependencies:
     ```bash
     pip install -r <project_root>\requirements.txt
     ```
     Include `huggingface-hub` for model download:
     ```bash
     pip install huggingface-hub
     ```
4. **Disk Space**: ~20 GB free for models, LaTeX, Tesseract, and Poppler.
5. **Internet Access**: Required for downloads (offline instructions provided).
6. **Command Prompt or PowerShell**: Run commands as Administrator where needed.
7. **Configuration**:
   - Update `<project_root>\esg_system\config.py` to use relative paths, e.g.:
     ```python
     import os
     MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
     TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'templates', 'esg_compliance_report_template.tex')
     OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')
     ```

## Non-Python Dependencies

The system requires the following non-Python dependencies, which cannot be installed via `pip`.

### 1. Mistral-7B Model (`mistral-7b-instruct-v0.1.Q4_K_M.gguf`)

The Mistral-7B model is used by `mistral_extract.py` and `compliance_validator.py` for data extraction and compliance validation. The recommended file is `mistral-7b-instruct-v0.1.Q4_K_M.gguf`, placed in `<project_root>\models\`.

#### Quantization Options
The model is available in multiple quantization formats, balancing size, RAM usage, and quality. The development plan specifies `Q4_K_M` for balanced quality and performance. Below are the options:

| File Name                            | Quant Method | Bits | Size   | Max RAM Required | Use Case                                  |
|--------------------------------------|--------------|------|--------|------------------|-------------------------------------------|
| mistral-7b-instruct-v0.1.Q2_K.gguf   | Q2_K         | 2    | 3.08 GB | 5.58 GB         | Smallest, significant quality loss        |
| mistral-7b-instruct-v0.1.Q3_K_S.gguf | Q3_K_S       | 3    | 3.16 GB | 5.66 GB         | Very small, high quality loss             |
| mistral-7b-instruct-v0.1.Q3_K_M.gguf | Q3_K_M       | 3    | 3.52 GB | 6.02 GB         | Very small, high quality loss             |
| mistral-7b-instruct-v0.1.Q3_K_L.gguf | Q3_K_L       | 3    | 3.82 GB | 6.32 GB         | Small, substantial quality loss           |
| mistral-7b-instruct-v0.1.Q4_0.gguf   | Q4_0         | 4    | 4.11 GB | 6.61 GB         | Legacy, high quality loss (prefer Q3_K_M) |
| mistral-7b-instruct-v0.1.Q4_K_S.gguf | Q4_K_S       | 4    | 4.14 GB | 6.64 GB         | Small, greater quality loss               |
| mistral-7b-instruct-v0.1.Q4_K_M.gguf | Q4_K_M       | 4    | 4.37 GB | 6.87 GB         | Medium, balanced quality - **recommended** |
| mistral-7b-instruct-v0.1.Q5_0.gguf   | Q5_0         | 5    | 5.00 GB | 7.50 GB         | Legacy, balanced quality (prefer Q4_K_M)  |
| mistral-7b-instruct-v0.1.Q5_K_S.gguf | Q5_K_S       | 5    | 5.00 GB | 7.50 GB         | Large, low quality loss - recommended     |
| mistral-7b-instruct-v0.1.Q5_K_M.gguf | Q5_K_M       | 5    | 5.13 GB | 7.63 GB         | Large, very low quality loss - recommended|
| mistral-7b-instruct-v0.1.Q6_K.gguf   | Q6_K         | 6    | 5.94 GB | 8.44 GB         | Very large, extremely low quality loss    |
| mistral-7b-instruct-v0.1.Q8_0.gguf   | Q8_0         | 8    | 7.70 GB | 10.20 GB        | Very large, extremely low quality loss    |

**Notes**:
- RAM figures assume no GPU offloading. GPU offloading reduces RAM usage and requires VRAM (see [https://github.com/abetlen/llama-cpp-python](https://github.com/abetlen/llama-cpp-python)).
- `Q4_K_M` is recommended for the ESG system due to its balance of size (4.37 GB), RAM usage (6.87 GB), and quality, fitting the ~78-second CSV processing goal.
- Alternatives like `Q5_K_M` or `Q5_K_S` offer lower quality loss but require more RAM and may slow processing. Use `Q3_K_M` for lower RAM systems with acceptable quality loss.

#### Installation Steps
1. **Install `huggingface-hub`**:
   - In the virtual environment:
     ```bash
     cd <project_root>
     <project_root>\venv\Scripts\activate
     pip install huggingface-hub
     ```
2. **Download the Model Programmatically**:
   - Create a script to download `mistral-7b-instruct-v0.1.Q4_K_M.gguf`:
     ```bash
     cd <project_root>
     <project_root>\venv\Scripts\activate
     python -m huggingface_hub download TheBloke/Mixtral-7B-Instruct-v0.1-GGUF mistral-7b-instruct-v0.1.Q4_K_M.gguf --local-dir models --local-dir-use-symlinks False
     ```
   - Alternatively, create `<project_root>\download_model.py`:
     ```python
     from huggingface_hub import hf_hub_download
     import os
     repo_id = "TheBloke/Mixtral-7B-Instruct-v0.1-GGUF"
     filename = "mistral-7b-instruct-v0.1.Q4_K_M.gguf"
     local_dir = os.path.join(os.path.dirname(__file__), "models")
     os.makedirs(local_dir, exist_ok=True)
     hf_hub_download(repo_id=repo_id, filename=filename, local_dir=local_dir, local_dir_use_symlinks=False)
     print(f"Model downloaded to {os.path.join(local_dir, filename)}")
     ```
     Run:
     ```bash
     python download_model.py
     ```
   - This places the model in `<project_root>\models\mistral-7b-instruct-v0.1.Q4_K_M.gguf`.
3. **Manual Download (Alternative)**:
   - Visit: [https://huggingface.co/TheBloke/Mixtral-7B-Instruct-v0.1-GGUF](https://huggingface.co/TheBloke/Mixtral-7B-Instruct-v0.1-GGUF).
   - Download `mistral-7b-instruct-v0.1.Q4_K_M.gguf` (~4.37 GB) to `C:\Downloads\`.
   - Move to:
     ```bash
     mkdir <project_root>\models
     move C:\Downloads\mistral-7b-instruct-v0.1.Q4_K_M.gguf <project_root>\models\
     ```
4. **Update Configuration**:
   - Ensure `<project_root>\esg_system\config.py` uses a relative path:
     ```python
     import os
     MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'mistral-7b-instruct-v0.1.Q4_K_M.gguf')
     ```
   - If using a different quantization (e.g., `Q5_K_M`), update the filename in `config.py`.
5. **Verify Installation**:
   - Confirm file exists: `<project_root>\models\mistral-7b-instruct-v0.1.Q4_K_M.gguf`.
   - Check size (~4.37 GB):
     ```bash
     dir <project_root>\models\mistral-7b-instruct-v0.1.Q4_K_M.gguf
     ```
   - Test loading (requires `llama-cpp-python`):
     ```bash
     cd <project_root>
     <project_root>\venv\Scripts\activate
     python -c "from llama_cpp import Llama; model = Llama('<project_root>/models/mistral-7b-instruct-v0.1.Q4_K_M.gguf'.replace('\\', '/')); print('Model loaded')"
     ```
6. **Troubleshooting**:
   - **Download Errors**: Ensure `huggingface-hub` is installed and internet is stable. For rate limits, use a Hugging Face token (see [https://huggingface.co/docs/hub/security-tokens](https://huggingface.co/docs/hub/security-tokens)).
   - **File Not Found**: Verify `MODEL_PATH` in `config.py` uses forward slashes (`/`).
   - **Model Load Error**: Install `llama-cpp-python` (`pip install llama-cpp-python`). For GPU support, see [https://github.com/abetlen/llama-cpp-python](https://github.com/abetlen/llama-cpp-python).
   - **Memory Issues**: Ensure 8 GB RAM (16 GB recommended). Use `Q3_K_M` for lower RAM systems or enable GPU offloading.
   - **Quantization Choice**: If `Q4_K_M` is slow, try `Q3_K_M` (3.52 GB, 6.02 GB RAM) or `Q5_K_M` (5.13 GB, 7.63 GB RAM) and update `config.py`.

#### Notes
- **Performance**: `Q4_K_M` supports the ~78-second CSV processing goal. Higher quantizations (e.g., `Q6_K`) may increase processing time.
- **Offline Installation**: Download manually on a connected machine, transfer via USB to `<project_root>\models\`, and verify hash:
  ```bash
  certutil -hashfile <project_root>\models\mistral-7b-instruct-v0.1.Q4_K_M.gguf SHA256
  ```
- **License**: Check the model’s license on Hugging Face (typically MIT or Apache 2.0).

### 2. LaTeX (`texlive-full`, `latexmk`)

LaTeX is used by `pdf_generator.py` to compile `<project_root>\templates\esg_compliance_report_template.tex` (artifact ID: c7dd74e3-9eaf-43e2-ad85-ca739107e5a9) into `<project_root>\output\audit_report.pdf`, requiring `texlive-full` for packages like `pgfplots`, `tikz`, and `colortbl`.

#### Installation Steps
1. **Download TeX Live**:
   - Visit: [https://tug.org/texlive/acquire-netinstall.html](https://tug.org/texlive/acquire-netinstall.html).
   - Download `install-tl-windows.exe` (~20 MB) to `C:\Downloads\`.
   - For offline installation, download the ISO (~4 GB): [https://tug.org/texlive/acquire-iso.html](https://tug.org/texlive/acquire-iso.html).
2. **Install TeX Live**:
   - Run as Administrator:
     ```bash
     C:\Downloads\install-tl-windows.exe
     ```
   - Select “full” scheme to include `pgfplots`, `tikz`, `colortbl`, `hyperref`, `geometry`, `xcolor`.
   - Install to `C:\texlive` for global access.
   - Installation takes ~10-20 minutes, ~6 GB.
   - Offline: Mount ISO and run `install-tl-windows.exe`.
3. **Install `latexmk`**:
   - Included in `texlive-full`. Verify:
     ```bash
     latexmk --version
     ```
   - If not found, add `C:\texlive\[YEAR]\bin\windows` (e.g., `C:\texlive\2025\bin\windows`) to PATH.
4. **Update System PATH**:
   - Add TeX Live to PATH:
     - Control Panel → System → Advanced System Settings → Environment Variables.
     - Edit “Path” under “System Variables,” add: `C:\texlive\[YEAR]\bin\windows`.
     - Verify:
       ```bash
       echo %PATH%
       latexmk --version
       ```
5. **Update Configuration**:
   - Ensure `<project_root>\esg_system\config.py` uses relative paths:
     ```python
     import os
     TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'templates', 'esg_compliance_report_template.tex')
     OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')
     ```
6. **Verify Installation**:
   - Create `<project_root>\test.tex`:
     ```latex
     \documentclass{article}
     \usepackage{pgfplots}
     \usepackage{tikz}
     \usepackage{colortbl}
     \begin{document}
     ESG System Test
     \end{document}
     ```
   - Compile:
     ```bash
     cd <project_root>
     latexmk -pdf test.tex
     ```
   - Check for `<project_root>\test.pdf`, ensure ~12-second compilation.
7. **Troubleshooting**:
   - **Command Not Found**: Verify `C:\texlive\[YEAR]\bin\windows` in PATH. Restart Command Prompt.
   - **Package Missing**: Use `tlmgr` to install missing packages:
     ```bash
     tlmgr install pgfplots tikz colortbl hyperref geometry xcolor
     ```
   - **Slow Compilation**: Disable antivirus during compilation. Use `latexmk -pdf`.
   - **Template Errors**: Ensure `<project_root>\templates\esg_compliance_report_template.tex` exists.

#### Notes
- **Disk Space**: `texlive-full` requires ~6 GB. Use `texlive-medium` and `tlmgr` for smaller footprint.
- **Offline Installation**: Transfer ISO via USB, mount, and run installer.
- **License**: LaTeX Project Public License (LPPL). See [https://tug.org/texlive/doc/texlive-en.html#x1-110003](https://tug.org/texlive/doc/texlive-en.html#x1-110003).

### 3. Tesseract (OCR for `pytesseract`)

Tesseract is used by `pytesseract_extract.py` for OCR on scanned PDFs.

#### Installation Steps
1. **Download Tesseract**:
   - Visit: [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki).
   - Download `tesseract-ocr-w64-setup-v5.4.0.exe` (~50 MB) to `C:\Downloads\`.
2. **Install Tesseract**:
   - Run as Administrator:
     ```bash
     C:\Downloads\tesseract-ocr-w64-setup-v5.4.0.exe
     ```
   - Install to `C:\Program Files\Tesseract-OCR`.
   - Select English language data (add others if needed).
3. **Update System PATH**:
   - Add to PATH:
     - Control Panel → System → Advanced System Settings → Environment Variables.
     - Edit “Path” under “System Variables,” add: `C:\Program Files\Tesseract-OCR`.
     - Verify:
       ```bash
       tesseract --version
       ```
4. **Configure `pytesseract`**:
   - Install `pytesseract`:
     ```bash
     cd <project_root>
     <project_root>\venv\Scripts\activate
     pip install pytesseract
     ```
   - Update `<project_root>\esg_system\config.py`:
     ```python
     import pytesseract
     pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
     ```
   - Or set environment variable:
     ```bash
     setx TESSERACT_PATH "C:\Program Files\Tesseract-OCR\tesseract.exe"
     ```
5. **Verify Installation**:
   - Create `<project_root>\test.png` with text.
   - Test OCR:
     ```bash
     cd <project_root>
     <project_root>\venv\Scripts\activate
     python -c "import pytesseract; from PIL import Image; print(pytesseract.image_to_string(Image.open('test.png')))"
     ```
   - Ensure `pdf2image` is installed:
     ```bash
     pip install pdf2image
     ```
6. **Troubleshooting**:
   - **Not Found**: Verify `C:\Program Files\Tesseract-OCR\tesseract.exe` in PATH.
   - **Poor OCR Quality**: Use 300 DPI images. Install language packs: [https://github.com/tesseract-ocr/tessdata](https://github.com/tesseract-ocr/tessdata).
   - **Permission Errors**: Run as Administrator.

#### Notes
- **License**: Apache 2.0. See [https://github.com/tesseract-ocr/tesseract/blob/main/LICENSE](https://github.com/tesseract-ocr/tesseract/blob/main/LICENSE).
- **Performance**: Optimize for high-quality PDFs to reduce OCR time.

### 4. Poppler (for `pdf2image`)

Poppler is required by `pdf2image` in `pytesseract_extract.py` for PDF-to-image conversion.

#### Installation Steps
1. **Download Poppler**:
   - Visit: [https://github.com/oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows).
   - Download `Release-24.07.0-0.zip` (~30 MB) to `C:\Downloads\`.
2. **Install Poppler**:
   - Extract:
     ```bash
     mkdir "C:\Program Files\poppler"
     tar -xf C:\Downloads\Release-24.07.0-0.zip -C "C:\Program Files\poppler"
     ```
   - Ensure `pdftoppm.exe` is in `C:\Program Files\poppler\bin`.
3. **Update System PATH**:
   - Add to PATH:
     - Control Panel → System → Advanced System Settings → Environment Variables.
     - Edit “Path,” add: `C:\Program Files\poppler\bin`.
     - Verify:
       ```bash
       pdftoppm --version
       ```
4. **Verify Installation**:
   - Test:
     ```bash
     cd <project_root>
     <project_root>\venv\Scripts\activate
     python -c "from pdf2image import convert_from_path; images = convert_from_path('<project_root>/input/Company_Report.pdf'.replace('\\', '/')); print(f'Converted {len(images)} pages')"
     ```
5. **Troubleshooting**:
   - **Not Found**: Verify `C:\Program Files\poppler\bin\pdftoppm.exe` in PATH.
   - **Conversion Errors**: Ensure PDF is not corrupted or encrypted.

#### Notes
- **License**: GPL. See [https://poppler.freedesktop.org/](https://poppler.freedesktop.org/).
- **Offline Installation**: Transfer ZIP via USB, extract to `C:\Program Files\poppler`.

## Offline Installation

For air-gapped systems:
1. **Download Files**:
   - Mistral-7B: [https://huggingface.co/TheBloke/Mixtral-7B-Instruct-v0.1-GGUF](https://huggingface.co/TheBloke/Mixtral-7B-Instruct-v0.1-GGUF).
   - TeX Live: ISO from [https://tug.org/texlive/acquire-iso.html](https://tug.org/texlive/acquire-iso.html).
   - Tesseract: [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki).
   - Poppler: [https://github.com/oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows).
2. **Transfer**: Copy to USB, transfer to `C:\Downloads\`.
3. **Install**: Follow steps using local files.
4. **Verify Hash**:
   ```bash
   certutil -hashfile <file_path> SHA256
   ```

## Verification of Full Setup

1. **Check File Placement**:
   - Mistral-7B: `<project_root>\models\mistral-7b-instruct-v0.1.Q4_K_M.gguf`.
   - Template: `<project_root>\templates\esg_compliance_report_template.tex`.
   - Tesseract: `C:\Program Files\Tesseract-OCR\tesseract.exe`.
   - Poppler: `C:\Program Files\poppler\bin\pdftoppm.exe`.
2. **Test Workflow**:
   - Place sample files in `<project_root>\input`, `<project_root>\standards`, `<project_root>\requirements`.
   - Run:
     ```bash
     cd <project_root>
     <project_root>\venv\Scripts\activate
     python esg_system\main.py --report input\Company_Report.pdf --standards standards\ESG_Framework_GRI.pdf --requirements requirements\requirements_2023.csv --output output
     ```
   - Check: `<project_root>\output\audit_results.csv`, `<project_root>\output\audit_report.pdf`.
   - Measure time:
     ```powershell
     Measure-Command { python esg_system\main.py --report input\Company_Report.pdf --standards standards\ESG_Framework_GRI.pdf --requirements requirements\requirements_2023.csv --output output }
     ```
3. **Check Logs**: Review `<project_root>\logs\esg_system.log`.
4. **Validate Outputs**:
   - CSV: 66 criteria, summary stats.
   - PDF: 13 sections, charts, gradients (emerald: RGB{5,150,105}, blue: RGB{8,145,178}).

## Troubleshooting

- **Path Errors**: Ensure `Tesseract`, `Poppler`, `latexmk` in PATH. Use relative paths in `config.py`.
- **Dependency Conflicts**:
  ```bash
  python -m venv <project_root>\venv
  <project_root>\venv\Scripts\activate
  pip install -r <project_root>\requirements.txt
  ```
- **Model Issues**: Verify `MODEL_PATH`. Use `Q3_K_M` for lower RAM.
- **LaTeX Errors**: Check `<project_root>\output\audit_report.log`.
- **OCR Failures**: Ensure Poppler and 300 DPI PDFs.

## Additional Resources

- **Mistral-7B**: [https://huggingface.co/models](https://huggingface.co/models), [https://github.com/abetlen/llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- **TeX Live**: [https://tug.org/texlive/doc.html](https://tug.org/texlive/doc.html), [https://tug.org/texlive/tlmgr.html](https://tug.org/texlive/tlmgr.html)
- **Tesseract**: [https://github.com/tesseract-ocr/tesseract/wiki](https://github.com/tesseract-ocr/tesseract/wiki)
- **Poppler**: [https://github.com/oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows)
- **Python**: [https://docs.python.org/3/library/venv.html](https://docs.python.org/3/library/venv.html), [https://pip.pypa.io/en/stable/](https://pip.pypa.io/en/stable/)

