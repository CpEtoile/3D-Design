import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMMAND = PROJECT_ROOT / "src" / "show_stl.py"


ASCII_STL = """solid test
facet normal 0 0 1
 outer loop
  vertex 0 0 0
  vertex 1 0 0
  vertex 0 1 0
 endloop
endfacet
endsolid test
"""


def run_viewer(*arguments):
    return subprocess.run(
        [sys.executable, str(COMMAND), *map(str, arguments)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )


def test_generates_html_with_embedded_stl_and_editing_controls(tmp_path):
    stl_path = tmp_path / "model.stl"
    stl_path.write_text(ASCII_STL)

    result = run_viewer(stl_path, "--no-open")

    assert result.returncode == 0
    html_path = tmp_path / "model.html"
    assert html_path.exists()
    html = html_path.read_text()
    assert "STLLoader" in html
    assert "Save as STL" in html
    assert "position" in html
    assert "rotation" in html
    assert "scale" in html
    assert "Controls legend" in html
    assert "Explore model" in html
    assert "Manipulate model" in html
    assert "controls-legend" in html
    assert "Show controls" in html
    assert "Hide controls" in html
    assert "Left mouse drag" in html
    assert "Right mouse drag" in html
    assert "Mouse wheel" in html
    assert "Save as STL" in html
    assert "data:model/stl;base64," in html


def test_supports_explicit_output_path(tmp_path):
    stl_path = tmp_path / "model.stl"
    stl_path.write_text(ASCII_STL)
    output_path = tmp_path / "viewer" / "custom.html"

    result = run_viewer(stl_path, "--output", output_path, "--no-open")

    assert result.returncode == 0
    assert output_path.exists()
    assert stl_path.exists()


def test_missing_input_returns_error(tmp_path):
    result = run_viewer(tmp_path / "missing.stl", "--no-open")

    assert result.returncode != 0
    assert "not found" in result.stderr.lower()
