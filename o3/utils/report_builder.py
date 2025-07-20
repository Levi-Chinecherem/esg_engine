from typing import Dict, List, Any
from pathlib import Path
import pandas as pd
import logging

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
    """
    def __init__(self, output_dir: Path):
        """
        Initialize the ReportGenerator with an output directory.

        Args:
            output_dir (Path): Directory where reports will be saved.
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)

    def generate_report(self, analysis_results: List[Dict[str, Any]], categories: Dict[str, List[str]], report_type: str, type_criteria: Dict[str, Dict], sector_criteria: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate a structured report from analysis results.

        Args:
            analysis_results (List[Dict[str, Any]]): List of analysis results for criteria.
            categories (Dict[str, List[str]]): Base criteria organized by category.
            report_type (str): Type of the report (e.g., esg_report).
            type_criteria (Dict[str, Dict]): Type-specific criteria.
            sector_criteria (Dict[str, str]): Sector-specific criteria priorities.

        Returns:
            Dict[str, Any]: Structured report dictionary.
        """
        report = {}
        for category, criteria in categories.items():
            report[category] = {}
            for crit in criteria:
                matches = [r for r in analysis_results if r["criterion"] == crit and r["found_info"]]
                
                if not matches or not matches[0]["found_info"] or all("No relevant data found" in info for info in matches[0]["found_info"]):
                    report[category][crit] = {
                        "Location in Report": [],
                        "Details": "No relevant data found.",
                        "Status": "✗",
                        "Verified Result": "No evidence",
                        "Relevance": "",
                        "Percentage": 0.0
                    }
                    continue

                all_pages = sorted(set().union(*[m["page_num"] for m in matches]))
                all_sentences = []
                for i, match in enumerate(matches, 1):
                    for j, info in enumerate(match["found_info"], 1):
                        if "Error:" in info or "Not processed:" in info:
                            continue
                        all_sentences.append(f"{i}.{j}. {info}")

                validated_match = matches[0]
                report[category][crit] = {
                    "Location in Report": all_pages,
                    "Details": "\n".join(all_sentences),
                    "Status": validated_match.get("status", "✗"),
                    "Verified Result": validated_match.get("verified_result", "No evidence"),
                    "Relevance": validated_match.get("relevance", ""),
                    "Percentage": validated_match.get("percentage", 0.0)
                }
        return report

    def _generate_csv_report(self, report: Dict[str, Any], filename: str):
        """
        Write the report to a CSV file.

        Args:
            report (Dict[str, Any]): Generated report dictionary.
            filename (str): Base filename for the CSV (without extension).
        """
        rows = []
        for category, criteria in report.items():
            rows.append({"Category": category, "Requirement": "", "Location in Report": "", "Details": "", "Status": "", "Verified Result": "", "Relevance": "", "Percentage": ""})
            for crit, details in criteria.items():
                rows.append({
                    "Category": "",
                    "Requirement": crit,
                    "Location in Report": ", ".join(map(str, details["Location in Report"])),
                    "Details": details["Details"],
                    "Status": details["Status"],
                    "Verified Result": details["Verified Result"],
                    "Relevance": details["Relevance"],
                    "Percentage": f"{details['Percentage']}%"
                })
            rows.append({"Category": "", "Requirement": "", "Location in Report": "", "Details": "", "Status": "", "Verified Result": "", "Relevance": "", "Percentage": ""})

        columns = ["Category", "Requirement", "Location in Report", "Details", "Status", "Verified Result", "Relevance", "Percentage"]
        df = pd.DataFrame(rows, columns=columns)
        csv_path = self.output_dir / f"{filename}.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        logger.info(f"Saved CSV report to {csv_path}")