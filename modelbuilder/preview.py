"""Matplotlib 3D preview shared by the GUI and the command line."""

from __future__ import annotations

import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from .templates.base import Part


def draw_parts(ax, parts: list[Part], title: str = "") -> None:
    ax.clear()
    light = np.array([0.4, -0.5, 0.8])
    light /= np.linalg.norm(light)
    lo = np.full(3, np.inf)
    hi = np.full(3, -np.inf)
    for part in parts:
        mesh = part.to_mesh()
        tris = mesh.vertices[mesh.triangles]
        normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
        lengths = np.linalg.norm(normals, axis=1, keepdims=True)
        normals = normals / np.where(lengths == 0, 1, lengths)
        shade = 0.45 + 0.55 * np.clip(normals @ light, 0, 1)
        base = np.array([int(part.color[i : i + 2], 16) / 255 for i in (1, 3, 5)])
        colors = np.clip(shade[:, None] * base[None, :], 0, 1)
        ax.add_collection3d(Poly3DCollection(tris, facecolors=colors, edgecolors="none"))
        lo = np.minimum(lo, mesh.vertices.min(axis=0))
        hi = np.maximum(hi, mesh.vertices.max(axis=0))
    centre = (lo + hi) / 2
    half = (hi - lo).max() / 2 * 1.05
    ax.set_xlim(centre[0] - half, centre[0] + half)
    ax.set_ylim(centre[1] - half, centre[1] + half)
    ax.set_zlim(centre[2] - half, centre[2] + half)
    ax.set_box_aspect((1, 1, 1))
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")
    if title:
        ax.set_title(title)


def save_preview_png(parts: list[Part], path: str, title: str = "", elev=22, azim=-60) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(7, 6))
    ax = fig.add_subplot(projection="3d")
    draw_parts(ax, parts, title)
    ax.view_init(elev=elev, azim=azim)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
