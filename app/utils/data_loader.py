"""
Data loading utilities for the educational assistant.

This module handles loading and processing course data from the Excel knowledge base.
"""

from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger

from app.config import settings


class KnowledgeBase:
    """Class to load and manage the course knowledge base from Excel file."""

    # Define expected columns
    EXPECTED_COLUMNS = [
        "Nombre del curso",
        "Formato",
        "Costo (soles)",
        "Objetivo",
        "Link para inscripcion",
    ]

    # Define sheet name
    SHEET_NAME = "Hoja1"

    def __init__(self, file_path: Optional[Path] = None):
        """Initialize the knowledge base.

        Args:
            file_path: Path to the Excel file. Defaults to the path in settings.
        """
        # Asegurar que el file_path es un objeto Path
        if file_path is None and hasattr(settings, "knowledge_base_path"):
            self.file_path = settings.knowledge_base_path
        elif file_path is not None:
            self.file_path = Path(file_path)
        else:
            # Fallback a una ubicación por defecto
            default_path = (
                Path(__file__).parent.parent.parent
                / "data"
                / "knowledge_base_Caso.xlsx"
            )
            logger.warning(
                f"No knowledge_base_path in settings, using default: {default_path}"
            )
            self.file_path = default_path

        self._data: Optional[pd.DataFrame] = None
        self._loaded = False

    def load(self) -> "KnowledgeBase":
        """Load the course data from the Excel file into memory.

        Returns:
            self: The KnowledgeBase object for method chaining

        Raises:
            FileNotFoundError: If the Excel file doesn't exist
            ValueError: If the Excel file doesn't have the expected structure
        """
        if not self.file_path.exists():
            logger.error(f"Knowledge base file not found: {self.file_path}")
            raise FileNotFoundError(f"File not found: {self.file_path}")

        try:
            # Load the Excel file from specific sheet
            self._data = pd.read_excel(self.file_path, sheet_name=self.SHEET_NAME)

            # Validate columns
            missing_cols = set(self.EXPECTED_COLUMNS) - set(self._data.columns)
            if missing_cols:
                raise ValueError(
                    f"Missing required columns in Excel file: {', '.join(missing_cols)}"
                )

            # Clean up the data
            self._data = self._data[self.EXPECTED_COLUMNS].copy()
            self._data = self._data.fillna("")  # Replace NaN with empty string

            rows_count = len(self._data)
            logger.info(
                f"Loaded {rows_count} courses from knowledge base sheet '{self.SHEET_NAME}'"
            )

            self._loaded = True
            return self
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            raise

    def get_courses(self) -> pd.DataFrame:
        """Get the courses data.

        Returns:
            pd.DataFrame: DataFrame containing all courses
        """
        self._ensure_loaded()
        return self._data

    def search_courses(self, query: str) -> pd.DataFrame:
        """Search for courses matching the query.

        Args:
            query: Search term to look for in course names and objectives

        Returns:
            pd.DataFrame: DataFrame with matching courses
        """
        self._ensure_loaded()

        # Search in course names and objectives
        mask = self._data["Nombre del curso"].str.contains(
            query, case=False, na=False
        ) | self._data["Objetivo"].str.contains(query, case=False, na=False)

        return self._data[mask]

    def get_course_by_name(self, course_name: str) -> Optional[pd.Series]:
        """Get a specific course by its exact name.

        Args:
            course_name: Name of the course to retrieve

        Returns:
            Optional[pd.Series]: Course data if found, None otherwise
        """
        self._ensure_loaded()
        matches = self._data[self._data["Nombre del curso"] == course_name]
        return matches.iloc[0] if not matches.empty else None

    def get_courses_by_format(self, format_type: str) -> pd.DataFrame:
        """Get all courses of a specific format.

        Args:
            format_type: Format to filter by

        Returns:
            pd.DataFrame: DataFrame with courses of the specified format
        """
        self._ensure_loaded()
        return self._data[self._data["Formato"] == format_type]

    def get_courses_by_price_range(
        self, min_price: float, max_price: float
    ) -> pd.DataFrame:
        """Get courses within a price range.

        Args:
            min_price: Minimum price in soles
            max_price: Maximum price in soles

        Returns:
            pd.DataFrame: DataFrame with courses in the price range
        """
        self._ensure_loaded()

        # Convert price strings to numeric values
        price_series = pd.to_numeric(
            self._data["Costo (soles)"].str.replace("S/", "").str.strip(),
            errors="coerce",
        )

        return self._data[(price_series >= min_price) & (price_series <= max_price)]

    def _ensure_loaded(self):
        """Ensure the knowledge base is loaded before operations."""
        if not self._loaded:
            logger.info("Knowledge base not loaded yet. Loading now...")
            self.load()


# Singleton instance
_knowledge_base = None


def get_knowledge_base() -> KnowledgeBase:
    """Get the singleton knowledge base instance.

    Returns:
        KnowledgeBase: The knowledge base instance
    """
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase().load()
    return _knowledge_base
