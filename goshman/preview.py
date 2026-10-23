"""Interactive software-projected GLB polygon viewport.

This alpha viewport displays *actual triangles* parsed from glTF/GLB; it does not
produce or hallucinate geometry. It is intentionally dependency-light (Qt+numpy+
trimesh), and is not a replacement for Blender's shaded 3D viewport.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPolygonF
from PySide6.QtWidgets import QWidget


class GLBPreview(QWidget):
    """Orbit/zoom of real mesh geometry, flat-shaded via QPainter's Z sort."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 430)
        self.setMouseTracking(True)
        self.setStyleSheet("background: #171e28;")
        self.mesh_file: Path | None = None
        self.triangles = None
        self.colors = None
        self.center = None
        self.radius = 1.0
        self.yaw = 0.0
        self.pitch = 0.02
        self.zoom = 1.0
        self.last_mouse = None
        self.error = None

    def load_glb(self, filepath: str | Path, *, max_faces: int = 10000) -> dict:
        import numpy as np
        import trimesh

        path = Path(filepath).resolve(strict=True)
        if path.suffix.lower() != '.glb':
            raise ValueError('3D preview currently supports .glb files only')
        if path.stat().st_size > 250_000_000:
            raise ValueError('GLB too large for software preview (250 MB limit)')
        scene = trimesh.load(str(path), force='scene', process=False)
        nodes = list(scene.graph.nodes_geometry)
        total_faces = sum(len(scene.geometry[scene.graph.get(node)[1]].faces) for node in nodes)
        if total_faces == 0:
            raise ValueError('No triangles present in GLB scene')
        vertices = []
        colors = []
        max_faces = max(200, min(int(max_faces), 50000))
        # Sample across all meshes without hiding minority meshes.
        step = max(1, (total_faces + max_faces - 1) // max_faces)
        for node in nodes:
            pose, geo_name = scene.graph.get(node)
            mesh = scene.geometry[geo_name]
            faces = mesh.faces[::step]
            if not len(faces):
                continue
            v = np.asarray(mesh.vertices, dtype=np.float32)
            part = v[faces]
            part = np.matmul(part, np.asarray(pose[:3, :3], dtype=np.float32).T) + np.asarray(pose[:3, 3], dtype=np.float32)
            vertices.append(part)
            material = getattr(mesh.visual, 'material', None)
            rgba = getattr(material, 'baseColorFactor', None)
            rgb = np.asarray(rgba[:3] if rgba is not None else [158, 174, 155], dtype=np.float32)
            if rgb.max() <= 1:
                rgb = rgb * 255
            colors.append(np.broadcast_to(rgb, (len(faces), 3)).copy())
        if not vertices:
            raise ValueError('GLB scene contains no renderable geometry')
        geometry = np.concatenate(vertices, axis=0)
        bounds = np.concatenate([geometry.min(axis=(0, 1)), geometry.max(axis=(0, 1))])
        self.center = (bounds[:3] + bounds[3:]) * .5
        self.radius = max(float((bounds[3:] - bounds[:3]).max()) / 2, .1)
        self.triangles = geometry.astype(np.float32, copy=False)
        self.colors = np.concatenate(colors, axis=0)
        self.mesh_file = path
        self.yaw, self.pitch, self.zoom = 0.0, 0.02, 1.0
        self.update()
        return {'source': str(path), 'mesh_nodes': len(nodes), 'source_faces': total_faces, 'preview_faces': len(geometry)}

    def paintEvent(self, event):
        import math
        import numpy as np
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('#141b25'))
        painter.setRenderHint(QPainter.Antialiasing, False)
        if self.triangles is None:
            painter.setPen(QColor('#bbc7d5'))
            painter.drawText(self.rect(), Qt.AlignCenter, 'GLB не открыт\nОткройте вкладку «3D» после генерации модели')
            return
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        rot_y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float32)
        rot_x = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]], dtype=np.float32)
        coords = np.matmul(self.triangles-self.center, np.matmul(rot_x, rot_y).T)
        edges1 = coords[:,1,:] - coords[:,0,:]
        edges2 = coords[:,2,:] - coords[:,0,:]
        normal = np.cross(edges1, edges2)
        normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True),1e-7)
        # Camera looks along -Z; visible CCW triangles face camera (+Z).
        facing = normal[:,2] > 0.0
        order = np.argsort(coords[:,:,2].mean(axis=1))
        width, height = self.width(), self.height()
        scale = max(1.0, min(width,height) * .38 * self.zoom / self.radius)
        xs = width/2 + coords[:,:,0] * scale
        ys = height/2 - coords[:,:,1] * scale
        light = np.maximum(0.25, np.minimum(1.1, .55 + .45 * (normal @ np.array([.4,.7,.65]))))
        color_data = np.clip(self.colors*light[:,None], 0, 255).astype(np.uint8)
        painter.setPen(Qt.NoPen)
        for i in order:
            if not facing[i]:
                continue
            triangle = QPolygonF([QPointF(float(xs[i,j]), float(ys[i,j])) for j in range(3)])
            r,g,b = color_data[i]
            painter.setBrush(QColor(int(r),int(g),int(b)))
            painter.drawPolygon(triangle)
        painter.setPen(QColor('#b9c6d7'))
        painter.drawText(10,22,f'{self.mesh_file.name}  •  {len(self.triangles)} triangles (preview)')
        painter.drawText(10,42,'ЛКМ: вращение  •  колесо: масштаб  •  точное редактирование — в Blender')

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_mouse = event.position()

    def mouseMoveEvent(self, event):
        if self.last_mouse is None:
            return
        delta = event.position() - self.last_mouse
        self.yaw += delta.x() * .012
        self.pitch = max(-1.4,min(1.4,self.pitch + delta.y() * .012))
        self.last_mouse = event.position()
        self.update()

    def mouseReleaseEvent(self, event):
        self.last_mouse = None

    def wheelEvent(self, event):
        self.zoom = max(.2,min(6,self.zoom * (1.15 if event.angleDelta().y()>0 else .87)))
        self.update()
