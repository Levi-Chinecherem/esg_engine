import os
import csv
import logging
from config import settings

"""
Loads criteria from UNCTAD_datapoints.csv for minimum requirements analysis.
Provides criteria for all report types based on a single CSV file.

file path: utils/criteria_loader.py
"""

logger = logging.getLogger(__name__)

def load_criteria(criteria_name: str = "indicator_name", criteria_file: str = os.path.join(settings.BASE_DIR, "data", "UNCTAD_datapoints.csv")) -> dict:
    """
    Load criteria from UNCTAD_datapoints.csv.

    Args:
        criteria_name (str): Column name in the CSV containing criteria (default: "indicator_name").
        criteria_file (str): Path to the UNCTAD_datapoints.csv file.

    Returns:
        dict: Dictionary with 'base' key containing criteria by category.
    """
    logger.info(f"Loading criteria from {criteria_file} using column '{criteria_name}'")
    criteria = {"base": {}}

    if not os.path.exists(criteria_file):
        logger.error(f"Criteria file {criteria_file} does not exist")
        return criteria

    try:
        with open(criteria_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            if not fieldnames:
                logger.error(f"No columns found in {criteria_file}")
                return criteria

            # Auto-detect criteria column if criteria_name not found
            if criteria_name not in fieldnames:
                possible_columns = ["Indicator", "criterion", "name", "Criteria", "Indicator_Name"]
                for col in possible_columns:
                    if col in fieldnames:
                        logger.warning(f"Column '{criteria_name}' not found, using '{col}' instead")
                        criteria_name = col
                        break
                else:
                    logger.error(f"Column '{criteria_name}' not found in {criteria_file}. Available columns: {', '.join(fieldnames)}")
                    return criteria

            for row in reader:
                category = row.get("category", "General")  # Use 'category' or fallback to "General"
                criterion = row[criteria_name]
                if category not in criteria["base"]:
                    criteria["base"][category] = []
                criteria["base"][category].append(criterion)
    except Exception as e:
        logger.error(f"Failed to load {criteria_file}: {str(e)}")
        return criteria

    logger.info(f"Loaded {sum(len(crits) for crits in criteria['base'].values())} criteria from {criteria_file}")
    return criteria