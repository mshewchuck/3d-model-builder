from .ball_return import BallReturnTemplate
from .base import BuildResult, Param, Part, Template
from .curved_return import CurvedReturnTemplate

TEMPLATES: list[Template] = [CurvedReturnTemplate(), BallReturnTemplate()]

__all__ = ["TEMPLATES", "BallReturnTemplate", "CurvedReturnTemplate", "BuildResult", "Param",
           "Part", "Template"]
