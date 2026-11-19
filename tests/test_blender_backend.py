from pathlib import Path
import pytest
from finance_campus.blender_backend import BlenderRenderError, render_blender_project

def test_blender_backend_reports_missing_executable(tmp_path: Path):
    project = tmp_path / "scene.blend"
    project.write_bytes(b"not a blend file")
    with pytest.raises(BlenderRenderError, match="Blender was not found"):
        render_blender_project(project, tmp_path / "out.mp4", blender="missing-blender-executable")

def test_blender_backend_rejects_non_blend_input(tmp_path: Path):
    project = tmp_path / "scene.py"
    project.write_text("print('not a blend')", encoding="utf-8")
    with pytest.raises(BlenderRenderError, match="existing .blend file"):
        render_blender_project(project, tmp_path / "out.mp4", blender="blender")
