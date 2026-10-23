"""Smoke-test the actual polygon Qt renderer on CI hosts with PySide6."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

import pytest


def test_glb_interactive_preview(tmp_path):
    qt = pytest.importorskip('PySide6.QtWidgets')
    import trimesh
    from goshman.preview import GLBPreview

    app = qt.QApplication.instance() or qt.QApplication([])
    glb = tmp_path / 'box.glb'
    trimesh.creation.box(extents=(1.0, 2.0, 1.0)).export(glb)
    viewer = GLBPreview()
    info = viewer.load_glb(glb)
    assert info['source_faces'] == 12
    assert info['mesh_nodes'] >= 1
    assert info['preview_faces'] > 0
    viewer.resize(440, 460)
    image = viewer.grab().toImage()
    assert not image.isNull()
    viewer.close()
