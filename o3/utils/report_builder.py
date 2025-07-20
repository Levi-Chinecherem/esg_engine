from typing import Dict, List, Any
from pathlib import Path
import pandas as pd
import logging
import re
import csv
import os
from config import settings

"""
Report generator for minimum requirements analysis.
Generates structured reports and saves them as CSV files.

file path: utils/report_builder.py
"""

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    Generates and saves reports based on analysis results.

    Attributes:
        output_dir (Path): Directory where CSV reports will be saved.
        criteria_file (str): Path to UNCTAD_datapoints.csv for descriptions.
    """
    def __init__(self, output_dir: Path):
        """
        Initialize the ReportGenerator with an output directory.

        Args:
            output_dir (Path): Directory where reports will be saved.
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.criteria_file = os.path.join(settings.BASE_DIR, "data", "UNCTAD_datapoints.csv")
        logger.info(f"Initialized ReportGenerator with output directory: {self.output_dir}")

    def _load_descriptions(self) -> Dict[str, str]:
        """
        Load descriptions from UNCTAD_datapoints.csv.

        Returns:
            Dict[str, str]: Mapping of criterion to description.
        """
        descriptions = {}
        try:
            with open(self.criteria_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    descriptions[row["criterion"]] = row["description"]
        except Exception as e:
            logger.error(f"Failed to load descriptions from {self.criteria_file}: {str(e)}")
        return descriptions

    def generate_report(self, analysis_results: List[Dict[str, Any]], categories: Dict[str, List[str]], report_type: str, document_name: str, audit_date: str) -> Dict[str, Any]:
        """
        Generate a structured report from analysis results.

        Args:
            analysis_results (List[Dict[str, Any]]): List of analysis results for criteria.
            categories (Dict[str, List[str]]): Base criteria organized by category.
            report_type (str): Type of the report (e.g., esg_report).
            document_name (str): Name of the processed document (e.g., btg-pactual.pdf).
            audit_date (str): Date of the audit in YYYY-MM-DD format.

        Returns:
            Dict[str, Any]: Structured report dictionary.
        """
        logger.info(f"Generating report for report type: {report_type}")
        descriptions = self._load_descriptions()
        report = {}
        for category, criteria in categories.items():
            report[category] = {}
            for crit in criteria:
                matches = [r for r in analysis_results if r["criterion"] == crit and r["found_info"]]
                
                if not matches:
                    report[category][crit] = [{
                        "Source_Page": "",
                        "Extracted_Value": "No data found.",
                        "Unit": "",
                        "Verified Result": "No evidence",
                        "Standard_Code": "",
                        "Compliance_Status": "✗",
                        "Compliance_Reason": "No data found"
                    }]
                    continue

                validated_match = matches[0]
                all_pages = sorted(set().union(*[m["page_num"] for m in matches]))
                findings = []
                page_index = 0
                for i, match in enumerate(matches, 1):
                    for j, info in enumerate(match["found_info"], 1):
                        logger.debug(f"Processing found_info for {crit}: {info}")
                        if "Error:" in info or "Not processed:" in info:
                            continue
                        # Parse sentence and relevance (permissive regex)
                        sentence_match = re.match(r"--\s*Sentence\s*\d+:\s*(.*?)\s*\[(relevant|partial|irrelevant):\s*(.*?)\](?:\s*\[(relevant|partial|irrelevant):.*?\])?", info, re.DOTALL)
                        if not sentence_match:
                            logger.warning(f"Regex mismatch for found_info: {info}")
                            # Fallback: treat as irrelevant
                            sentence = info.strip().split("[")[0].strip() if "[" in info else info.strip()
                            findings.append({
                                "Source_Page": str(all_pages[page_index]) if page_index < len(all_pages) else "",
                                "Extracted_Value": sentence,
                                "Unit": "",
                                "Verified Result": validated_match.get("verified_result", "No evidence"),
                                "Standard_Code": "",
                                "Compliance_Status": "✗",
                                "Compliance_Reason": "Unrecognized format"
                            })
                            page_index += 1
                            continue
                        sentence, relevance, reason = sentence_match.groups()[:3]
                        # Extract unit and code
                        unit = ""
                        if "%" in sentence:
                            unit = "%"
                        elif "$" in sentence or "USD" in sentence:
                            unit = "$"
                        code_match = re.search(r"(\d+-\d+\s*GRI)", reason)
                        code = code_match.group(1) if code_match else ""
                        # Use page from all_pages if available
                        page = str(all_pages[page_index]) if page_index < len(all_pages) else ""
                        page_index += 1
                        findings.append({
                            "Source_Page": page,
                            "Extracted_Value": sentence.strip(),
                            "Unit": unit,
                            "Verified Result": validated_match.get("verified_result", "No evidence"),
                            "Standard_Code": code,
                            "Compliance_Status": "✓" if relevance == "relevant" else "◑" if relevance == "partial" else "✗",
                            "Compliance_Reason": reason.strip()
                        })

                report[category][crit] = findings if findings else [{
                    "Source_Page": "",
                    "Extracted_Value": "No data found.",
                    "Unit": "",
                    "Verified Result": "No evidence",
                    "Standard_Code": "",
                    "Compliance_Status": "✗",
                    "Compliance_Reason": "No data found"
                }]
        logger.info(f"Generated report with {sum(len(crits) for crits in report.values())} entries")
        return report

    def _generate_csv_report(self, report: Dict[str, Any], filename: str, document_name: str, audit_date: str, sali_ai_summary: str):
        """
        Write the report to a CSV file.

        Args:
            report (Dict[str, Any]): Generated report dictionary.
            filename (str): Base filename for the CSV (without extension).
            document_name (str): Name of the processed document.
            audit_date (str): Date of the audit in YYYY-MM-DD format.
            sali_ai_summary (str): GPT-generated summary of findings.
        """
        rows = []
        descriptions = self._load_descriptions()
        for category, criteria in report.items():
            rows.append({
                "Document_Processed": document_name,
                "Audit_Date": audit_date,
                "Category": category,
                "Criterion": "",
                "Description": "",
                "Extracted_Value": "",
                "Unit": "",
                "Source_Page": "",
                "Verified Result": "",
                "Standard_Code": "",
                "Compliance_Status": "",
                "Compliance_Reason": "",
                "SALI_AI_Summary": ""
            })
            for crit, findings in criteria.items():
                for finding in findings:
                    rows.append({
                        "Document_Processed": document_name,
                        "Audit_Date": audit_date,
                        "Category": "",
                        "Criterion": crit,
                        "Description": descriptions.get(crit, ""),
                        "Extracted_Value": finding["Extracted_Value"],
                        "Unit": finding["Unit"],
                        "Source_Page": finding["Source_Page"],
                        "Verified Result": finding["Verified Result"],
                        "Standard_Code": finding["Standard_Code"],
                        "Compliance_Status": finding["Compliance_Status"],
                        "Compliance_Reason": finding["Compliance_Reason"],
                        "SALI_AI_Summary": sali_ai_summary
                    })
            rows.append({
                "Document_Processed": document_name,
                "Audit_Date": audit_date,
                "Category": "",
                "Criterion": "",
                "Description": "",
                "Extracted_Value": "",
                "Unit": "",
                "Source_Page": "",
                "Verified Result": "",
                "Standard_Code": "",
                "Compliance_Status": "",
                "Compliance_Reason": "",
                "SALI_AI_Summary": ""
            })

        columns = [
            "Document_Processed", "Audit_Date", "Category", "Criterion", "Description",
            "Extracted_Value", "Unit", "Source_Page", "Verified Result", "Standard_Code",
            "Compliance_Status", "Compliance_Reason", "SALI_AI_Summary"
        ]
        df = pd.DataFrame(rows, columns=columns)
        csv_path = self.output_dir / f"{filename}.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        logger.info(f"Saved CSV report to {csv_path}")