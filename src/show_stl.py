import argparse
import base64
import html
import json
import re
import sys
import webbrowser
from pathlib import Path


THREE_VERSION = "0.161.0"


def build_html(stl_path: Path, stl_bytes: bytes) -> str:
    model_data = base64.b64encode(stl_bytes).decode("ascii")
    title = html.escape(stl_path.name)
    model_data_json = json.dumps(f"data:model/stl;base64,{model_data}")
    generated_html = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>STL viewer: {title}</title>
  <style>
    :root {{ color-scheme: dark; font-family: system-ui, sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-height: 100vh; background: #111827; color: #e5e7eb; }}
    header {{ display: flex; gap: 12px; align-items: center; padding: 12px 16px; border-bottom: 1px solid #374151; }}
    header h1 {{ margin: 0; font-size: 1rem; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    #help {{ margin-left: auto; width: auto; padding: 6px 10px; }}
    main {{ display: grid; grid-template-columns: minmax(0, 1fr) 280px; height: calc(100vh - 53px); }}
    #viewport {{ min-width: 0; min-height: 360px; position: relative; background: #0b1220; border-right: 1px solid #374151; }}
    #viewport canvas {{ display: block; width: 100%; height: 100%; }}
    #viewport-message {{ position: absolute; inset: 0; display: grid; place-items: center; padding: 24px; color: #fca5a5; white-space: pre-wrap; overflow: auto; text-align: left; pointer-events: none; }}
    aside {{ display: flex; flex-direction: column; padding: 16px; overflow-y: auto; background: #1f2937; border-left: 1px solid #374151; }}
    #controls-legend {{ order: -1; position: sticky; top: 0; z-index: 5; background: #1f2937; }}
    fieldset {{ margin: 0 0 16px; padding: 12px; border: 1px solid #4b5563; border-radius: 8px; }}
    legend {{ padding: 0 6px; color: #93c5fd; }}
    label {{ display: grid; grid-template-columns: 1fr 90px; gap: 8px; align-items: center; margin: 8px 0; font-size: .875rem; }}
    input, button {{ width: 100%; border: 1px solid #4b5563; border-radius: 5px; padding: 7px 8px; background: #111827; color: inherit; }}
    button {{ cursor: pointer; background: #2563eb; border-color: #3b82f6; }}
    button.secondary {{ background: #374151; border-color: #6b7280; }}
    .buttons {{ display: grid; gap: 8px; }}
    .operations {{ margin: 16px 0 0; padding-left: 20px; color: #d1d5db; font-size: .8rem; line-height: 1.5; }}
    .operations li {{ margin: 6px 0; }}
    .operations strong {{ color: #bfdbfe; }}
    .legend-group h3 {{ margin: 12px 0 6px; font-size: .85rem; color: #bfdbfe; }}
    #vertex-status {{ color: #9ca3af; font-size: .8rem; line-height: 1.4; }}
    #status {{ color: #9ca3af; font-size: .8rem; line-height: 1.4; }}
    @media (max-width: 700px) {{ main {{ grid-template-columns: 1fr; grid-template-rows: minmax(360px, 1fr) auto; height: auto; min-height: calc(100vh - 53px); }} aside {{ border-left: 0; border-top: 1px solid #374151; }} }}
  </style>
</head>
<body>
  <header><h1>{title}</h1><span id="status">Loading...</span><button id="help" class="secondary">Show controls</button></header>
  <main>
    <section id="viewport" aria-label="3D STL model viewer">
      <div id="viewport-message" hidden></div>
    </section>
    <aside>
      <fieldset>
        <legend>Position</legend>
        <label>X <input id="position-x" type="number" step="0.1" value="0"></label>
        <label>Y <input id="position-y" type="number" step="0.1" value="0"></label>
        <label>Z <input id="position-z" type="number" step="0.1" value="0"></label>
      </fieldset>
      <fieldset>
        <legend>Rotation (degrees)</legend>
        <label>X <input id="rotation-x" type="number" step="1" value="0"></label>
        <label>Y <input id="rotation-y" type="number" step="1" value="0"></label>
        <label>Z <input id="rotation-z" type="number" step="1" value="0"></label>
      </fieldset>
      <fieldset>
        <legend>Scale</legend>
        <label>Uniform <input id="scale" type="number" min="0.001" step="0.1" value="1"></label>
      </fieldset>
      <div class="buttons">
        <button id="reset" class="secondary">Reset view and edits</button>
        <button id="save">Save as STL</button>
      </div>
      <fieldset>
        <legend>Vertex editing</legend>
        <p id="vertex-status">Select vertex: click a vertex on model.</p>
        <button id="reset-vertices" class="secondary">Reset vertex edits</button>
      </fieldset>
      <fieldset id="controls-legend" tabindex="-1">
        <legend>Controls legend</legend>
        <div class="legend-group">
          <h3>Explore model</h3>
          <ul class="operations">
            <li><strong>[Orbit] Left mouse drag:</strong> rotate camera around model.</li>
            <li><strong>[Pan] Right mouse drag:</strong> move camera.</li>
            <li><strong>[Zoom] Mouse wheel:</strong> zoom camera in or out.</li>
          </ul>
        </div>
        <div class="legend-group">
          <h3>Manipulate model</h3>
          <ul class="operations">
            <li><strong>[Move] Position fields:</strong> move model on X, Y, or Z axis.</li>
            <li><strong>[Rotate] Rotation fields:</strong> rotate model around X, Y, or Z axis.</li>
            <li><strong>[Scale] Uniform scale:</strong> change model size.</li>
            <li><strong>[Reset] Reset view and edits:</strong> restore original transform and fitted camera.</li>
            <li><strong>[Save] Save as STL:</strong> download current edits as binary STL.</li>
          </ul>
        </div>
      </fieldset>
    </aside>
  </main>
  <script type="importmap">
    {{"imports": {{
      "three": "https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/build/three.module.js",
      "three/addons/": "https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/examples/jsm/"
    }}}}
  </script>
  <script>
    function formatViewerError(error, fallbackMessage) {{
      if (error instanceof Error) return error.stack || error.message;
      if (typeof error === 'string') return error;
      try {{ return JSON.stringify(error, null, 2); }} catch {{ return fallbackMessage || String(error); }}
    }}
    function showViewerError(error, fallbackMessage) {{
      const message = document.querySelector('#viewport-message');
      if (!message) return;
      message.hidden = false;
      message.textContent = `Viewer error:\n${{formatViewerError(error, fallbackMessage)}}`;
    }}
    window.addEventListener('error', (event) => {{
      showViewerError(event.error, event.message);
    }});
    window.addEventListener('unhandledrejection', (event) => {{
      showViewerError(event.reason, 'Unhandled promise rejection');
    }});
  </script>
  <script>
    window.STL_MODEL_DATA = {model_data_json};
    window.STL_SOURCE_NAME = {json.dumps(stl_path.name)};
  </script>
  <script type="module">
    import * as THREE from 'three';
    import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
    import {{ STLLoader }} from 'three/addons/loaders/STLLoader.js';
    import {{ TransformControls }} from 'three/addons/controls/TransformControls.js';

    const embeddedModel = {model_data_json};
    const viewport = document.querySelector('#viewport');
    const status = document.querySelector('#status');
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x111827);
    const camera = new THREE.PerspectiveCamera(45, 1, 0.01, 100000);
    const renderer = new THREE.WebGLRenderer({{ antialias: true }});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    viewport.appendChild(renderer.domElement);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    scene.add(new THREE.HemisphereLight(0xffffff, 0x334155, 2));
    const keyLight = new THREE.DirectionalLight(0xffffff, 2);
    keyLight.position.set(1, 2, 3);
    scene.add(keyLight);
    scene.add(new THREE.GridHelper(10, 10, 0x475569, 0x334155));

    let mesh;
    let sourceName = {json.dumps(stl_path.name)};
    let sourcePositions;
    let selectedVertex;
    const vertexRaycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    const vertexHandle = new THREE.Mesh(
      new THREE.SphereGeometry(1, 12, 8),
      new THREE.MeshBasicMaterial({{ color: 0xfbbf24 }})
    );
    vertexHandle.name = 'vertex-gizmo';
    vertexHandle.visible = false;
    scene.add(vertexHandle);
    const vertexGizmo = new TransformControls(camera, renderer.domElement);
    vertexGizmo.setMode('translate');
    vertexGizmo.name = 'vertex-gizmo';
    scene.add(vertexGizmo);
    const sourceTransform = {{ position: new THREE.Vector3(), rotation: new THREE.Euler(), scale: new THREE.Vector3(1, 1, 1) }};

    function resize() {{
      const width = viewport.clientWidth;
      const height = viewport.clientHeight;
      camera.aspect = width / Math.max(height, 1);
      camera.updateProjectionMatrix();
      renderer.setSize(width, height, false);
    }}

    function fitCamera() {{
      if (!mesh) return;
      const box = new THREE.Box3().setFromObject(mesh);
      const sphere = box.getBoundingSphere(new THREE.Sphere());
      const distance = sphere.radius / Math.sin(THREE.MathUtils.degToRad(camera.fov / 2));
      camera.position.set(sphere.center.x + distance, sphere.center.y + distance * 0.6, sphere.center.z + distance);
      camera.near = Math.max(distance / 1000, 0.001);
      camera.far = Math.max(distance * 100, 1000);
      camera.updateProjectionMatrix();
      controls.target.copy(sphere.center);
      controls.update();
    }}

    function inputValue(id) {{ return Number(document.querySelector(id).value) || 0; }}

    function applyTransform() {{
      if (!mesh) return;
      mesh.position.set(inputValue('#position-x'), inputValue('#position-y'), inputValue('#position-z'));
      mesh.rotation.set(
        THREE.MathUtils.degToRad(inputValue('#rotation-x')),
        THREE.MathUtils.degToRad(inputValue('#rotation-y')),
        THREE.MathUtils.degToRad(inputValue('#rotation-z'))
      );
      const scale = Math.max(inputValue('#scale'), 0.001);
      mesh.scale.setScalar(scale);
    }}

    function updateVertexStatus(message) {{
      document.querySelector('#vertex-status').textContent = message;
    }}

    function clearVertexSelection() {{
      selectedVertex = null;
      vertexHandle.visible = false;
      vertexGizmo.detach();
      updateVertexStatus('Select vertex: click a vertex on model.');
    }}

    function selectVertex(event) {{
      if (vertexGizmo.dragging || !mesh) return;
      const bounds = renderer.domElement.getBoundingClientRect();
      pointer.x = ((event.clientX - bounds.left) / bounds.width) * 2 - 1;
      pointer.y = -((event.clientY - bounds.top) / bounds.height) * 2 + 1;
      vertexRaycaster.setFromCamera(pointer, camera);
      const hit = vertexRaycaster.intersectObject(mesh, false)[0];
      if (!hit || hit.faceIndex === undefined) return;
      const positions = mesh.geometry.getAttribute('position');
      const localPoint = mesh.worldToLocal(hit.point.clone());
      const triangleStart = hit.faceIndex * 3;
      let nearestIndex = triangleStart;
      let nearestDistance = Infinity;
      for (let index = triangleStart; index < triangleStart + 3; index += 1) {{
        const candidate = new THREE.Vector3().fromBufferAttribute(positions, index);
        const distance = candidate.distanceToSquared(localPoint);
        if (distance < nearestDistance) {{
          nearestDistance = distance;
          nearestIndex = index;
        }}
      }}
      const selectedPosition = new THREE.Vector3().fromBufferAttribute(positions, nearestIndex);
      const radius = mesh.geometry.boundingSphere?.radius || 1;
      const epsilon = Math.max(radius * 0.00001, 0.000001);
      const indices = [];
      for (let index = 0; index < positions.count; index += 1) {{
        const candidate = new THREE.Vector3().fromBufferAttribute(positions, index);
        if (candidate.distanceTo(selectedPosition) <= epsilon) indices.push(index);
      }}
      selectedVertex = {{ indices, position: selectedPosition.clone() }};
      vertexHandle.position.copy(mesh.localToWorld(selectedPosition.clone()));
      vertexHandle.scale.setScalar(Math.max(radius * 0.025, 0.1));
      vertexHandle.visible = true;
      vertexGizmo.attach(vertexHandle);
      updateVertexStatus(`Selected vertex: ${{indices.length}} connected triangles. Drag axis gizmo.`);
    }}

    function updateSelectedVertex() {{
      if (!selectedVertex) return;
      const positions = mesh.geometry.getAttribute('position');
      const nextPosition = mesh.worldToLocal(vertexHandle.position.clone());
      const delta = nextPosition.clone().sub(selectedVertex.position);
      if (delta.lengthSq() === 0) return;
      selectedVertex.indices.forEach((index) => {{
        const current = new THREE.Vector3().fromBufferAttribute(positions, index).add(delta);
        positions.setXYZ(index, current.x, current.y, current.z);
      }});
      selectedVertex.position.copy(nextPosition);
      positions.needsUpdate = true;
      mesh.geometry.computeVertexNormals();
      updateVertexStatus(`Selected vertex: ${{selectedVertex.indices.length}} connected triangles updated.`);
    }}

    function resetVertices() {{
      const positions = mesh.geometry.getAttribute('position');
      positions.array.set(sourcePositions);
      positions.needsUpdate = true;
      mesh.geometry.computeVertexNormals();
      clearVertexSelection();
    }}

    function reset() {{
      document.querySelectorAll('input').forEach((input) => {{ input.value = input.id === 'scale' ? '1' : '0'; }});
      applyTransform();
      resetVertices();
      fitCamera();
    }}

    function downloadEditedStl() {{
      mesh.updateMatrixWorld(true);
      const positions = mesh.geometry.getAttribute('position');
      const triangleCount = Math.floor(positions.count / 3);
      const buffer = new ArrayBuffer(84 + triangleCount * 50);
      const view = new DataView(buffer);
      const encoder = new TextEncoder();
      const header = encoder.encode('Edited by STL HTML Viewer');
      new Uint8Array(buffer, 0, header.length).set(header);
      view.setUint32(80, triangleCount, true);
      const first = new THREE.Vector3();
      const second = new THREE.Vector3();
      const third = new THREE.Vector3();
      const normal = new THREE.Vector3();
      for (let triangle = 0; triangle < triangleCount; triangle += 1) {{
        const offset = 84 + triangle * 50;
        first.fromBufferAttribute(positions, triangle * 3).applyMatrix4(mesh.matrixWorld);
        second.fromBufferAttribute(positions, triangle * 3 + 1).applyMatrix4(mesh.matrixWorld);
        third.fromBufferAttribute(positions, triangle * 3 + 2).applyMatrix4(mesh.matrixWorld);
        normal.subVectors(second, first).cross(new THREE.Vector3().subVectors(third, first)).normalize();
        [normal, first, second, third].forEach((vector, index) => {{
          view.setFloat32(offset + index * 12, vector.x, true);
          view.setFloat32(offset + 4 + index * 12, vector.y, true);
          view.setFloat32(offset + 8 + index * 12, vector.z, true);
        }});
        view.setUint16(offset + 48, 0, true);
      }}
      const filename = sourceName.replace(/\\.stl$/i, '') + '-edited.stl';
      const link = document.createElement('a');
      link.href = URL.createObjectURL(new Blob([buffer], {{ type: 'model/stl' }}));
      link.download = filename;
      link.click();
      URL.revokeObjectURL(link.href);
    }}

    const bytes = Uint8Array.from(atob(embeddedModel.split(',')[1]), (character) => character.charCodeAt(0));
    mesh = new THREE.Mesh(new STLLoader().parse(bytes.buffer), new THREE.MeshStandardMaterial({{ color: 0x60a5fa, roughness: 0.65, metalness: 0.05 }}));
    scene.add(mesh);
    document.querySelector('#viewport-message').hidden = true;
    mesh.geometry.computeVertexNormals();
    sourcePositions = new Float32Array(mesh.geometry.getAttribute('position').array);
    renderer.domElement.addEventListener('pointerdown', selectVertex);
    vertexGizmo.addEventListener('dragging-changed', (event) => {{ controls.enabled = !event.value; }});
    vertexGizmo.addEventListener('objectChange', updateSelectedVertex);
    document.querySelectorAll('input').forEach((input) => input.addEventListener('input', applyTransform));
    document.querySelector('#reset').addEventListener('click', reset);
    document.querySelector('#reset-vertices').addEventListener('click', resetVertices);
    document.querySelector('#save').addEventListener('click', downloadEditedStl);
    document.querySelector('#help').addEventListener('click', () => {{
      const panel = document.querySelector('#controls-legend');
      const visible = !panel.hidden;
      panel.hidden = visible;
      document.querySelector('#help').textContent = visible ? 'Show controls' : 'Hide controls';
      panel.focus({{ preventScroll: true }});
    }});
    status.textContent = `${{mesh.geometry.getAttribute('position').count / 3}} triangles`;
    window.addEventListener('resize', resize);
    resize();
    fitCamera();
    renderer.setAnimationLoop(() => {{ controls.update(); renderer.render(scene, camera); }});
  </script>
</body>
</html>
'''
    viewer_script = Path(__file__).with_name("stl_viewer.js").read_text(encoding="utf-8")
    inline_viewer_script = "<script type=\"module\">\n" + viewer_script + "\n</script>"
    return re.sub(
        r'<script type="module">.*?</script>',
        lambda _: inline_viewer_script,
        generated_html,
        count=1,
        flags=re.DOTALL,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Show and edit an STL file in an HTML viewer.")
    parser.add_argument("input_file", type=Path, help="ASCII or binary STL file")
    parser.add_argument("-o", "--output", type=Path, help="HTML output path")
    parser.add_argument("--no-open", action="store_true", help="Generate HTML without opening browser")
    args = parser.parse_args()

    if not args.input_file.is_file():
        print(f"Input STL file not found: {args.input_file}", file=sys.stderr)
        return 1

    output_path = args.output or args.input_file.with_suffix(".html")
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(build_html(args.input_file, args.input_file.read_bytes()), encoding="utf-8")
        viewer_script = Path(__file__).with_name("stl_viewer.js")
        output_path.with_name("stl_viewer.js").write_text(viewer_script.read_text(encoding="utf-8"), encoding="utf-8")
    except OSError as error:
        print(f"Could not write HTML output: {error}", file=sys.stderr)
        return 1

    print(f"Generated HTML viewer: {output_path}")
    if not args.no_open:
        webbrowser.open(output_path.resolve().as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
