import json
import re
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
    assert '<script type="module">' in html
    assert "Save as STL" in html
    assert "position" in html
    assert "rotation" in html
    assert "scale" in html
    assert "Controls legend" in html
    assert "Explore model" in html
    assert "Manipulate model" in html
    assert "controls-legend" in html
    assert 'id="show-control"' in html
    assert "querySelector('#show-control')" in html
    assert "position: sticky" in html
    assert "order: -1" in html
    assert "Show controls" in html
    assert "Hide controls" in html
    assert "Left mouse drag" in html
    assert "Right mouse drag" in html
    assert "Mouse wheel" in html
    assert "Save as STL" in html
    assert "data:model/stl;base64," in html
    assert "getHelper" not in html
    assert "viewport-message" in html
    assert "Loading 3D model..." not in html
    assert "Viewer error:" in html
    assert "formatViewerError" in html
    assert "event.error" in html
    assert "event.reason" in html


def test_supports_explicit_output_path(tmp_path):
    stl_path = tmp_path / "model.stl"
    stl_path.write_text(ASCII_STL)
    output_path = tmp_path / "viewer" / "custom.html"

    result = run_viewer(stl_path, "--output", output_path, "--no-open")

    assert result.returncode == 0
    assert output_path.exists()
    assert stl_path.exists()


def test_declares_vertex_editing_controls(tmp_path):
    stl_path = tmp_path / "model.stl"
    stl_path.write_text(ASCII_STL)

    result = run_viewer(stl_path, "--no-open")

    assert result.returncode == 0
    html = (tmp_path / "model.html").read_text()
    assert "Vertex editing" in html
    assert "Select vertex" in html
    assert "vertex-gizmo" in html
    assert "selectedVertex" in html
    assert "connected triangles" in html
    assert "Reset vertex edits" in html
    assert "Save as STL" in html


def execute_viewer_js(js_body: str) -> dict:
    viewer_js = (PROJECT_ROOT / "src" / "stl_viewer.js").read_text(encoding="utf-8")
    add_fn = re.search(r"function addVertex[\s\S]*?^}", viewer_js, re.M).group(0)
    conn_fn = re.search(r"function connectVertices[\s\S]*?^}", viewer_js, re.M).group(0)
    reset_fn = re.search(r"function resetVertices[\s\S]*?^}", viewer_js, re.M).group(0)

    harness = f"""
const THREE = {{
  BufferAttribute: class {{
    constructor(array, itemSize) {{
      this.array = array;
      this.itemSize = itemSize;
      this.count = array.length / itemSize;
    }}
  }}
}};
let status = {{ textContent: "" }};
let initialPositions = new Float32Array([
  0, 0, 0,  1, 0, 0,  0, 1, 0,
  10, 10, 10,  11, 10, 10,  10, 11, 10
]);
let mesh = {{
  geometry: {{
    _attributes: {{
      position: new THREE.BufferAttribute(new Float32Array(initialPositions), 3)
    }},
    getAttribute(name) {{ return this._attributes[name]; }},
    setAttribute(name, attr) {{ this._attributes[name] = attr; }},
    computeVertexNormals() {{ this.normalsComputed = true; }},
    computeBoundingBox() {{ this.boundingBoxComputed = true; }},
    computeBoundingSphere() {{ this.boundingSphereComputed = true; }}
  }}
}};
let selectedVertex = null;
let vertexHandle = {{ visible: false }};
let vertexGizmo = {{ detach: () => {{}} }};
let connectPendingVertices = [];
function clearVertexSelection() {{}}

{add_fn}
{conn_fn}
{reset_fn}

{js_body}
"""
    result = subprocess.run(["node", "-e", harness], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def test_declares_add_and_connect_vertex_controls(tmp_path):
    stl_path = tmp_path / "model.stl"
    stl_path.write_text(ASCII_STL)

    result = run_viewer(stl_path, "--no-open")

    assert result.returncode == 0
    html = (tmp_path / "model.html").read_text()
    assert "Add vertex" in html
    assert "add-vertex" in html
    assert "addVertex" in html
    assert "split" in html.lower()
    assert "connect" in html.lower()
    assert "connectVertices" in html


def test_add_vertex_splits_triangle_geometry_correctly():
    payload = execute_viewer_js("""
addVertex({ x: 1, y: 1, z: 0 }, 0);
const pos = Array.from(mesh.geometry.getAttribute("position").array);
const count = mesh.geometry.getAttribute("position").count;
console.log(JSON.stringify({
  count,
  pos,
  status: status.textContent,
  normalsComputed: Boolean(mesh.geometry.normalsComputed),
  boundingBoxComputed: Boolean(mesh.geometry.boundingBoxComputed),
  boundingSphereComputed: Boolean(mesh.geometry.boundingSphereComputed)
}));
""")
    # 2 initial triangles (6 vertices) + split (+2 triangles / +6 vertices) = 4 triangles (12 vertices)
    assert payload["count"] == 12
    assert payload["status"] == "4 triangles"
    assert payload["normalsComputed"] is True
    assert payload["boundingBoxComputed"] is True
    assert payload["boundingSphereComputed"] is True

    # Face 0 split into 3 triangles: (A, B, P), (B, C, P), (C, A, P)
    pos = payload["pos"]
    tri1 = pos[0:9]
    tri2 = pos[9:18]
    tri3 = pos[18:27]
    assert tri1 == [0, 0, 0, 1, 0, 0, 1, 1, 0]
    assert tri2 == [1, 0, 0, 0, 1, 0, 1, 1, 0]
    assert tri3 == [0, 1, 0, 0, 0, 0, 1, 1, 0]

    # Preserved triangle 1 (originally at index 1, now shifted to index 3)
    tri4 = pos[27:36]
    assert tri4 == [10, 10, 10, 11, 10, 10, 10, 11, 10]


def test_connect_vertices_appends_triangle_with_chosen_vertices():
    payload = execute_viewer_js("""
connectVertices({ x: 5, y: 5, z: 5 }, { x: 1, y: 0, z: 0 }, { x: 0, y: 1, z: 0 });
const pos = Array.from(mesh.geometry.getAttribute("position").array);
const count = mesh.geometry.getAttribute("position").count;
console.log(JSON.stringify({
  count,
  pos,
  status: status.textContent,
  normalsComputed: Boolean(mesh.geometry.normalsComputed),
  boundingBoxComputed: Boolean(mesh.geometry.boundingBoxComputed),
  boundingSphereComputed: Boolean(mesh.geometry.boundingSphereComputed)
}));
""")
    # 2 initial triangles (6 vertices) + 1 added triangle (3 vertices) = 3 triangles (9 vertices)
    assert payload["count"] == 9
    assert payload["status"] == "3 triangles"
    assert payload["normalsComputed"] is True
    assert payload["boundingBoxComputed"] is True
    assert payload["boundingSphereComputed"] is True

    # Initial 2 triangles untouched
    assert payload["pos"][:18] == [0, 0, 0, 1, 0, 0, 0, 1, 0, 10, 10, 10, 11, 10, 10, 10, 11, 10]
    # Appended triangle matches (newVertex, v1, v2)
    assert payload["pos"][18:] == [5, 5, 5, 1, 0, 0, 0, 1, 0]


def test_reset_vertices_restores_original_mesh_after_additions():
    payload = execute_viewer_js("""
addVertex({ x: 1, y: 1, z: 0 }, 0);
connectVertices({ x: 5, y: 5, z: 5 }, { x: 1, y: 0, z: 0 }, { x: 0, y: 1, z: 0 });
const countBeforeReset = mesh.geometry.getAttribute("position").count;

resetVertices();
const countAfterReset = mesh.geometry.getAttribute("position").count;
const posAfterReset = Array.from(mesh.geometry.getAttribute("position").array);
console.log(JSON.stringify({
  countBeforeReset,
  countAfterReset,
  posAfterReset,
  initial: Array.from(initialPositions),
  status: status.textContent
}));
""")
    assert payload["countBeforeReset"] == 15
    assert payload["countAfterReset"] == 6
    assert payload["posAfterReset"] == payload["initial"]
    assert payload["status"] == "2 triangles"


def test_html_viewer_add_vertex_interaction_contract(tmp_path):
    stl_path = tmp_path / "model.stl"
    stl_path.write_text(ASCII_STL)

    result = run_viewer(stl_path, "--no-open")
    assert result.returncode == 0
    html = (tmp_path / "model.html").read_text()

    # Toggle button and click event
    assert 'id="add-vertex"' in html
    assert "addVertexMode = !addVertexMode" in html
    assert "Exit add vertex" in html

    # Shift-click vertex connection workflow
    assert "event.shiftKey" in html
    assert "connectPendingVertices.push" in html
    assert "connectPendingVertices.length === 2" in html
    assert "connectVertices(selectedVertex.position" in html

    # Triangle split workflow with auto selection
    assert "selectVertexAtPosition(localPoint)" in html

    # Reset wiring
    assert "document.querySelector('#reset-vertices').addEventListener('click', resetVertices)" in html
    assert "resetVertices();" in html


def test_controls_legend_documents_add_vertex_options(tmp_path):
    stl_path = tmp_path / "model.stl"
    stl_path.write_text(ASCII_STL)

    result = run_viewer(stl_path, "--no-open")
    assert result.returncode == 0
    html = (tmp_path / "model.html").read_text()

    assert "[Vertex] Add vertex:" in html
    assert "split triangle or connect to chosen vertices" in html


def test_mesh_disables_frustum_culling_and_updates_bounds_for_cpu_rendering(tmp_path):
    stl_path = tmp_path / "model.stl"
    stl_path.write_text(ASCII_STL)

    result = run_viewer(stl_path, "--no-open")
    assert result.returncode == 0
    html = (tmp_path / "model.html").read_text()

    # Disable CPU frustum culling so mesh never drops when editing
    assert "mesh.frustumCulled = false;" in html

    # Ensure bounds recomputation prevents disappearing mesh
    assert "mesh.geometry.computeBoundingBox" in html
    assert "mesh.geometry.computeBoundingSphere" in html


def test_missing_input_returns_error(tmp_path):
    result = run_viewer(tmp_path / "missing.stl", "--no-open")

    assert result.returncode != 0
    assert "not found" in result.stderr.lower()
