"""This module contains the Style class and the StyleFactory class."""
from __future__ import annotations

import toml

from modules.data import Data


class Style(Data):
    """Style class, representing a style.

    It includes definitions for colors and fonts.
    """

    name: str
    background_color: str
    text_color: str
    roads_color: str
    parks_color: str
    water_color: str
    buildings_fill: list[str]
    buildings_outline: str
    font_family: str

    def __post__init__(self):
        """Post-initialization checks."""
        if len(self.buildings_fill) < 4:
            raise ValueError("buildings_color must have at least4 elements.")

        if len(self.buildings_fill) != len(self.buildings_outline):
            raise ValueError(
                "buildings_color and buildings_outline_color must have the same length."
            )


class StyleFactory:
    """StyleFactory class, used to load styles from a TOML file."""

    _styles_file: str = "styles.toml"

    def __init__(self) -> StyleFactory:
        """Initialize the StyleFactory."""
        self._styles = self._loadStyles()

    def _loadStyles(self) -> dict[str, Style]:
        """Load styles from a TOML file."""
        with open(self._styles_file) as file:
            toml_data = toml.load(file)

        return {s["name"]: Style(**s) for s in toml_data["Styles"]}

    @property
    def available_styles(self) -> list[str]:
        """List of available styles."""
        return list(s.name for s in self._styles.values())

    def getStyle(self, name: str) -> Style:
        """Get a style by name.

        Args:
            name (str): Name of the style.

        Raises:
            ValueError: If the style is not available.

        Returns:
            Style: The style.
        """
        if name not in self.available_styles:
            raise ValueError(f"Style {name} not available.")

        return self._styles[name]
