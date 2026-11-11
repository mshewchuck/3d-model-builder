from .ball_return import BallReturnTemplate
from .base import BuildResult, Param, Part, Template

TEMPLATES: list[Template] = [BallReturnTemplate()]

__all__ = ["TEMPLATES", "BallReturnTemplate", "BuildResult", "Param", "Part", "Template"]
