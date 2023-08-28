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
            raise ValueError("buildings_color must have at least 4 elements.")

        # buildings outlines are fill colors shaded by 2
        self.buildings_outline = [self._shade(c, 2) for c in self.buildings_fill]

    def _hex_to_rgb(self, color: str) -> tuple[int, int, int]:
        """Convert a hex color to RGB."""
        color = color.lstrip("#")
        return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))

    def _shade(self, color: str, amount: int = 2) -> str:
        r, g, b = self._hex_to_rgb(color)
        return f"#{r//amount:02x}{g//amount:02x}{b//amount:02x}"


class StyleFactory:
    """StyleFactory class, used to load styles from a TOML file."""

    _styles_file: str = "styles.toml"
    _styles: list[Style]

    def __init__(self) -> StyleFactory:
        """Initialize the StyleFactory."""
        self._styles = self._loadStyles()

        # every palette must have the same number of colors
        min_colors = min(len(s.buildings_fill) for s in self._styles.values())
        max_colors = max(len(s.buildings_fill) for s in self._styles.values())
        if min_colors != max_colors:
            raise ValueError("All palettes must have the same length.")

    def _loadStyles(self) -> dict[str, Style]:
        """Load styles from a TOML file."""
        with open(self._styles_file) as file:
            toml_data = toml.load(file)

        return {s["name"]: Style(**s) for s in toml_data["Styles"]}

    @property
    def map_styles(self) -> list[str]:
        """List of available styles."""
        return sorted(list(s.name for s in self._styles.values()))

    def getStyle(self, name: str) -> Style:
        """Get a style by name.

        Args:
            name (str): Name of the style.

        Raises:
            ValueError: If the style is not available.

        Returns:
            Style: The style.
        """
        if name not in self.map_styles:
            raise ValueError(f"Style {name} not available.")

        return self._styles[name]
