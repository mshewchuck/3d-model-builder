"""Minimal 3MF (3D Manufacturing Format) writer.

A .3mf file is a ZIP archive containing:
  [Content_Types].xml   - declares the MIME types inside the package
  _rels/.rels           - points to the main model part
  3D/3dmodel.model      - XML with vertices, triangles and build items
Bambu Studio, PrusaSlicer, OrcaSlicer and Cura all read this core format.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from xml.sax.saxutils import escape

import numpy as np

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>
"""

RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""


@dataclass
class Mesh:
    """A named triangle mesh. Units are millimetres."""

    name: str
    vertices: np.ndarray  # (N, 3) float
    triangles: np.ndarray  # (M, 3) int, counter-clockwise when viewed from outside


def _fmt(v: float) -> str:
    return f"{v:.4f}".rstrip("0").rstrip(".") or "0"


def model_xml(meshes: list[Mesh], title: str = "Model") -> str:
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">',
        f'  <metadata name="Title">{escape(title)}</metadata>',
        '  <metadata name="Application">3D Model Builder</metadata>',
        "  <resources>",
    ]
    for oid, mesh in enumerate(meshes, start=1):
        out.append(f'    <object id="{oid}" type="model" name="{escape(mesh.name, {chr(34): "&quot;"})}">')
        out.append("      <mesh>")
        out.append("        <vertices>")
        for x, y, z in np.asarray(mesh.vertices, dtype=float):
            out.append(f'          <vertex x="{_fmt(x)}" y="{_fmt(y)}" z="{_fmt(z)}"/>')
        out.append("        </vertices>")
        out.append("        <triangles>")
        for a, b, c in np.asarray(mesh.triangles, dtype=int):
            out.append(f'          <triangle v1="{a}" v2="{b}" v3="{c}"/>')
        out.append("        </triangles>")
        out.append("      </mesh>")
        out.append("    </object>")
    out.append("  </resources>")
    out.append("  <build>")
    for oid in range(1, len(meshes) + 1):
        out.append(f'    <item objectid="{oid}"/>')
    out.append("  </build>")
    out.append("</model>")
    return "\n".join(out) + "\n"


def write_3mf(path: str, meshes: list[Mesh], title: str = "Model") -> None:
    if not meshes:
        raise ValueError("Nothing to export")
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("3D/3dmodel.model", model_xml(meshes, title))
