from .ball_return import BallReturnTemplate
from .base import BuildResult, Param, Part, Template
from .curved_return import CurvedReturnTemplate
from .dial_magnet import DialMagnetTemplate

TEMPLATES: list[Template] = [CurvedReturnTemplate(), BallReturnTemplate(), DialMagnetTemplate()]

__all__ = ["TEMPLATES", "BallReturnTemplate", "CurvedReturnTemplate", "DialMagnetTemplate", "BuildResult", "Param",
           "Part", "Template"]
